"""Enrich leads with Google SERP + LinkedIn profiles (RapidAPI primary, Scrapingdog fallback).

Performance-optimized: all APIs run in parallel.
  - Google SERP + RapidAPI LinkedIn run simultaneously (parallel)
  - Scrapingdog LinkedIn fallback only for leads where RapidAPI returned empty

Usage:
    python -m pipeline enrich --campaign-dir path/to/C04
"""

from __future__ import annotations
import asyncio
import json
from pathlib import Path

import aiohttp

from pipeline.config import (
    SCRAPINGDOG_API_KEY, SCRAPINGDOG_BASE_URL,
    RAPIDAPI_KEY, RAPIDAPI_BASE_URL,
    ENRICH_CONCURRENCY, LINKEDIN_CONCURRENCY,
)
from pipeline.models import Lead, EnrichedLead, CampaignContext
from pipeline.utils import RateLimiter, retry_async, ProgressTracker, log


# --- Helpers ---

def _extract_username(linkedin_url: str) -> str:
    """Extract username from LinkedIn URL."""
    return linkedin_url.rstrip("/").split("/")[-1]


def _is_profile_empty(profile: dict) -> bool:
    """Check if a LinkedIn profile has no useful data."""
    if profile.get("error"):
        return True
    headline = profile.get("headline", "")
    about = profile.get("about", "")
    experience = profile.get("experience", [])
    has_exp_titles = any(e.get("title") for e in experience) if experience else False
    return not headline and not about and not has_exp_titles


# --- Scrapingdog Google SERP ---

async def _google_search(
    session: aiohttp.ClientSession,
    company_name: str,
    rate_limiter: RateLimiter,
) -> dict:
    """Search Google via Scrapingdog (5 credits/req)."""
    if not company_name or company_name == "?":
        return {"results": [], "error": "no company name"}

    async with rate_limiter:
        params = {
            "api_key": SCRAPINGDOG_API_KEY,
            "query": f"{company_name} actualite levee recrutement",
            "results": "5",
            "country": "fr",
            "language": "fr",
        }

        async with session.get(f"{SCRAPINGDOG_BASE_URL}/google/", params=params) as resp:
            if resp.status == 429:
                raise Exception("Scrapingdog rate limit (429)")
            if resp.status in (401, 403):
                return {"results": [], "error": f"scrapingdog error ({resp.status})"}
            resp.raise_for_status()
            data = await resp.json()

        return {"results": [
            {
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", "")[:500],
                "date": r.get("date", ""),
            }
            for r in data.get("organic_results", [])[:3]
        ]}


# --- RapidAPI LinkedIn (primary, parallel) ---

async def _rapidapi_linkedin(
    session: aiohttp.ClientSession,
    linkedin_url: str,
    rate_limiter: RateLimiter,
) -> dict:
    """Fetch LinkedIn profile via RapidAPI (parallel-safe)."""
    if not linkedin_url:
        return {"error": "no linkedin url"}

    username = _extract_username(linkedin_url)
    if not username:
        return {"error": "invalid linkedin url"}

    async with rate_limiter:
        headers = {
            "x-rapidapi-host": "professional-network-data.p.rapidapi.com",
            "x-rapidapi-key": RAPIDAPI_KEY,
            "Content-Type": "application/json",
        }

        async with session.get(
            RAPIDAPI_BASE_URL, headers=headers, params={"username": username}
        ) as resp:
            if resp.status == 429:
                raise Exception("RapidAPI rate limit (429)")
            if resp.status in (401, 403):
                return {"error": f"RapidAPI auth error ({resp.status})"}
            if resp.status == 404:
                return {"error": "profile not found"}
            resp.raise_for_status()
            data = await resp.json()

    d = data.get("data", data) or {}

    return {
        "source": "rapidapi",
        "headline": d.get("headline", "") or "",
        "about": (d.get("summary", d.get("about", "")) or "")[:500],
        "location": d.get("geo", {}).get("full", "") if isinstance(d.get("geo"), dict) else "",
        "current_company": ((d.get("position") or [{}])[0] or {}).get("companyName", ""),
        "experience": [
            {
                "title": exp.get("title", ""),
                "company": exp.get("companyName", ""),
                "starts_at": str(exp.get("start", "")),
                "ends_at": str(exp.get("end", "")),
                "duration": "",
            }
            for exp in (d.get("position", []) or [])[:3]
        ],
        "skills": [
            s.get("name", "") if isinstance(s, dict) else str(s)
            for s in (d.get("skills", []) or [])[:10]
        ],
    }


# --- Scrapingdog LinkedIn (fallback, sequential) ---

async def _scrapingdog_linkedin(
    session: aiohttp.ClientSession,
    linkedin_url: str,
) -> dict:
    """Fetch LinkedIn profile via Scrapingdog premium (100 credits, fallback)."""
    profile_id = _extract_username(linkedin_url)
    if not profile_id:
        return {"error": "invalid linkedin url"}

    params = {
        "api_key": SCRAPINGDOG_API_KEY,
        "type": "profile",
        "id": profile_id,
        "premium": "true",
    }

    async with session.get(f"{SCRAPINGDOG_BASE_URL}/profile/", params=params) as resp:
        if resp.status == 429:
            raise Exception("Scrapingdog rate limit (429)")
        if resp.status in (401, 403, 404, 410):
            return {"error": f"scrapingdog error ({resp.status})"}
        resp.raise_for_status()
        data = await resp.json()

    profile = data[0] if isinstance(data, list) and data else data

    return {
        "source": "scrapingdog",
        "headline": profile.get("headline", ""),
        "about": (profile.get("about", "") or "")[:500],
        "location": profile.get("location", ""),
        "current_company": (profile.get("experience", [{}]) or [{}])[0].get("company_name", ""),
        "experience": [
            {
                "title": exp.get("position", ""),
                "company": exp.get("company_name", ""),
                "starts_at": exp.get("starts_at", ""),
                "ends_at": exp.get("ends_at", ""),
                "duration": exp.get("duration", ""),
            }
            for exp in (profile.get("experience", []) or [])[:3]
        ],
        "skills": [
            s.get("name", "") if isinstance(s, dict) else str(s)
            for s in (profile.get("skills", []) or [])[:10]
        ],
    }


# --- Intent scoring ---

def _compute_intent_score(lead: EnrichedLead) -> int:
    """Score 0-10 based on enrichment signals."""
    score = 0

    profile = lead.linkedin_profile
    if profile.get("about"):
        score += 1
    if profile.get("skills"):
        score += 1

    experience = profile.get("experience", [])
    if experience:
        first_exp = experience[0]
        if not first_exp.get("ends_at"):
            duration = first_exp.get("duration", "")
            if duration and ("month" in duration.lower() or "mois" in duration.lower()):
                score += 2

    context = lead.firecrawl_context
    results = context.get("results", [])
    if results:
        score += 1
        for r in results:
            text = (r.get("snippet", "") + " " + r.get("title", "")).lower()
            if any(kw in text for kw in ["levée", "levee", "funding", "série", "serie"]):
                score += 2
            if any(kw in text for kw in ["recrute", "recrutement", "hiring", "embauche"]):
                score += 1
            if any(kw in text for kw in ["lancement", "nouveau produit", "expansion"]):
                score += 1

    return min(score, 10)


# --- Orchestration ---

async def enrich_leads(ctx: CampaignContext) -> list[EnrichedLead]:
    """Enrich all leads with max parallelism.

    Architecture:
      Phase 1 (parallel): Google SERP + RapidAPI LinkedIn simultaneously
      Phase 2 (sequential fallback): Scrapingdog for leads where RapidAPI returned empty
    """
    leads = ctx.leads
    if not leads:
        log("No leads to enrich", "warn")
        return []

    if not SCRAPINGDOG_API_KEY:
        log("SCRAPINGDOG_API_KEY not set", "error")
        return []

    log(f"Enriching {len(leads)} leads "
        f"(google={ENRICH_CONCURRENCY}x, linkedin={LINKEDIN_CONCURRENCY}x parallel)")

    enriched_leads = [EnrichedLead.from_lead(lead) for lead in leads]

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=65)
    ) as session:

        # === Phase 1: Google SERP + RapidAPI LinkedIn in parallel ===
        log("Phase 1: Google SERP + RapidAPI LinkedIn (all parallel)")
        google_limiter = RateLimiter(ENRICH_CONCURRENCY)
        linkedin_limiter = RateLimiter(LINKEDIN_CONCURRENCY)

        async def _google_one(idx: int) -> None:
            try:
                result = await retry_async(
                    _google_search, session, leads[idx].companyName, google_limiter,
                    label=f"google:{leads[idx].companyName}",
                    retry_on=(aiohttp.ClientError, Exception),
                )
                enriched_leads[idx].firecrawl_context = result
            except Exception as e:
                enriched_leads[idx].enrichment_errors.append(f"google: {e}")
                enriched_leads[idx].firecrawl_context = {}

        async def _linkedin_one(idx: int) -> None:
            if not leads[idx].linkedinUrl:
                enriched_leads[idx].linkedin_profile = {"error": "no linkedin url"}
                return
            try:
                result = await retry_async(
                    _rapidapi_linkedin, session, leads[idx].linkedinUrl, linkedin_limiter,
                    label=f"rapidapi:{leads[idx].firstName} {leads[idx].lastName}",
                    retry_on=(aiohttp.ClientError, Exception),
                    backoff_base=3.0,
                )
                enriched_leads[idx].linkedin_profile = result
            except Exception as e:
                enriched_leads[idx].enrichment_errors.append(f"rapidapi: {e}")
                enriched_leads[idx].linkedin_profile = {}

        # Fire all Google + LinkedIn tasks simultaneously
        all_tasks = (
            [_google_one(i) for i in range(len(leads))] +
            [_linkedin_one(i) for i in range(len(leads))]
        )
        await asyncio.gather(*all_tasks)

        google_ok = sum(1 for e in enriched_leads if e.firecrawl_context.get("results"))
        linkedin_ok = sum(1 for e in enriched_leads if not _is_profile_empty(e.linkedin_profile))
        linkedin_empty = [i for i in range(len(leads))
                          if _is_profile_empty(enriched_leads[i].linkedin_profile)
                          and leads[i].linkedinUrl]

        log(f"Phase 1 done: google={google_ok}/{len(leads)}, "
            f"linkedin={linkedin_ok}/{len(leads)} ({len(linkedin_empty)} need fallback)",
            "success")

        # === Phase 2: Scrapingdog fallback for empty LinkedIn profiles ===
        if linkedin_empty and SCRAPINGDOG_API_KEY:
            log(f"Phase 2: Scrapingdog fallback for {len(linkedin_empty)} empty profiles")
            fallback_ok = 0

            for idx in linkedin_empty:
                lead = leads[idx]
                try:
                    result = await _scrapingdog_linkedin(session, lead.linkedinUrl)
                    if not _is_profile_empty(result):
                        enriched_leads[idx].linkedin_profile = result
                        fallback_ok += 1
                except Exception as e:
                    log(f"Scrapingdog fallback failed for {lead.firstName} {lead.lastName}: {e}",
                        "warn")

                await asyncio.sleep(1)  # Brief pause for Scrapingdog

            log(f"Fallback done: {fallback_ok}/{len(linkedin_empty)} recovered", "success")

    # Compute intent scores
    for e in enriched_leads:
        e.intent_score = _compute_intent_score(e)

    # Stats
    total_errors = sum(1 for e in enriched_leads if e.enrichment_errors)
    final_linkedin = sum(1 for e in enriched_leads
                         if e.linkedin_profile and not e.linkedin_profile.get("error"))
    sources: dict[str, int] = {}
    for e in enriched_leads:
        src = e.linkedin_profile.get("source", "none")
        sources[src] = sources.get(src, 0) + 1
    source_str = ", ".join(f"{k}={v}" for k, v in sources.items())
    avg_score = sum(e.intent_score for e in enriched_leads) / len(enriched_leads)
    log(f"Enrichment done: {len(enriched_leads)} leads, "
        f"google={google_ok}, linkedin={final_linkedin} ({source_str}), "
        f"{total_errors} with errors, avg intent={avg_score:.1f}", "success")

    return enriched_leads


def save_enriched(enriched: list[EnrichedLead], campaign_dir: Path) -> Path:
    """Save enriched leads to leads_enriched.json."""
    from dataclasses import asdict
    output_path = campaign_dir / "leads_enriched.json"
    data = [asdict(e) for e in enriched]
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    log(f"Saved {len(enriched)} enriched leads to {output_path.name}", "success")
    return output_path
