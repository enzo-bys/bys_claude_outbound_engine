"""Inject leads into Lemlist campaigns via REST API in bulk.

Usage:
    python -m pipeline inject --campaign-dir path/to/C04 --campaign-id cam_xxx
"""

from __future__ import annotations
import asyncio
import json
from pathlib import Path
from dataclasses import asdict
from base64 import b64encode

import aiohttp

from pipeline.config import (
    LEMLIST_API_KEY, LEMLIST_BASE_URL,
    INJECT_BATCH_SIZE, INJECT_BATCH_PAUSE,
)
from pipeline.models import (
    EnrichedLead, PersonalizedSections,
    InjectionResult, InjectionReport,
)
from pipeline.utils import log


def _auth_header() -> str:
    """Build Basic auth header for Lemlist API (empty user : API_KEY)."""
    token = b64encode(f":{LEMLIST_API_KEY}".encode()).decode()
    return f"Basic {token}"


def _build_lead_payload(
    lead: EnrichedLead,
    sections: PersonalizedSections | None,
) -> dict:
    """Build the lead payload for Lemlist API."""
    payload: dict = {
        "firstName": lead.firstName,
        "lastName": lead.lastName,
        "companyName": lead.companyName,
        "linkedinUrl": lead.linkedinUrl,
    }

    # Custom variables — full personalized emails, pre-resolved
    custom_vars: dict = {
        "jobTitle": lead.headline,
    }

    if sections and not sections.generation_error:
        custom_vars["email1Subject"] = sections.email1Subject
        custom_vars["email1Body"] = sections.email1Body
        custom_vars["email2Subject"] = sections.email2Subject
        custom_vars["email2Body"] = sections.email2Body
        custom_vars["email3Subject"] = sections.email3Subject
        custom_vars["email3Body"] = sections.email3Body
        custom_vars["linkedinInvite"] = sections.linkedinInvite
        custom_vars["linkedinDm"] = sections.linkedinDm
        if sections.callScript:
            custom_vars["callScript"] = sections.callScript

    # Merge custom vars into payload (Lemlist expects flat structure)
    payload.update(custom_vars)

    return payload


async def _inject_one_lead(
    session: aiohttp.ClientSession,
    campaign_id: str,
    lead: EnrichedLead,
    sections: PersonalizedSections | None,
) -> InjectionResult:
    """Inject a single lead into Lemlist."""
    payload = _build_lead_payload(lead, sections)

    url = (
        f"{LEMLIST_BASE_URL}/campaigns/{campaign_id}/leads/"
        f"?deduplicate=true&verifyEmail=true&findEmail=true"
    )
    headers = {
        "Authorization": _auth_header(),
        "Content-Type": "application/json",
    }

    try:
        async with session.post(url, json=payload, headers=headers) as resp:
            body = await resp.text()

            if resp.status in (200, 201):
                data = json.loads(body)
                return InjectionResult(
                    firstName=lead.firstName,
                    lastName=lead.lastName,
                    companyName=lead.companyName,
                    status="injected",
                    lead_id=data.get("_id", ""),
                )

            if resp.status == 409 or "already" in body.lower():
                return InjectionResult(
                    firstName=lead.firstName,
                    lastName=lead.lastName,
                    companyName=lead.companyName,
                    status="excluded",
                    error_message="Lead already in campaign or other campaign",
                )

            # Retry-worthy errors
            if resp.status == 429:
                raise aiohttp.ClientError(f"Rate limit 429: {body[:200]}")

            if resp.status >= 500:
                raise aiohttp.ClientError(f"Server error {resp.status}: {body[:200]}")

            return InjectionResult(
                firstName=lead.firstName,
                lastName=lead.lastName,
                companyName=lead.companyName,
                status="error",
                error_message=f"HTTP {resp.status}: {body[:200]}",
            )

    except aiohttp.ClientError as e:
        return InjectionResult(
            firstName=lead.firstName,
            lastName=lead.lastName,
            companyName=lead.companyName,
            status="error",
            error_message=str(e),
        )


async def inject_leads(
    campaign_id: str,
    enriched_leads: list[EnrichedLead],
    personalized: list[PersonalizedSections] | None = None,
) -> InjectionReport:
    """Inject leads in batches of INJECT_BATCH_SIZE with pauses."""
    if not LEMLIST_API_KEY:
        log("LEMLIST_API_KEY not set", "error")
        return InjectionReport(campaign_id=campaign_id, campaign_name="")

    # Build sections lookup
    sections_map: dict[str, PersonalizedSections] = {}
    if personalized:
        for s in personalized:
            key = f"{s.firstName}_{s.lastName}_{s.companyName}"
            sections_map[key] = s

    report = InjectionReport(
        campaign_id=campaign_id,
        campaign_name="",
        total=len(enriched_leads),
    )

    log(f"Injecting {len(enriched_leads)} leads into {campaign_id} "
        f"(batches of {INJECT_BATCH_SIZE}, {INJECT_BATCH_PAUSE}s pause)")

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30)
    ) as session:
        # Process in batches
        for i in range(0, len(enriched_leads), INJECT_BATCH_SIZE):
            batch = enriched_leads[i:i + INJECT_BATCH_SIZE]
            batch_num = (i // INJECT_BATCH_SIZE) + 1
            total_batches = (len(enriched_leads) + INJECT_BATCH_SIZE - 1) // INJECT_BATCH_SIZE

            log(f"Batch {batch_num}/{total_batches} ({len(batch)} leads)")

            # Inject batch sequentially (rate limit 20 req/2s)
            for lead in batch:
                key = f"{lead.firstName}_{lead.lastName}_{lead.companyName}"
                sections = sections_map.get(key)
                result = await _inject_one_lead(session, campaign_id, lead, sections)
                report.results.append(result)

                if result.status == "injected":
                    report.injected += 1
                elif result.status == "excluded":
                    report.excluded += 1
                else:
                    report.errors += 1
                    log(f"Error: {lead.firstName} {lead.lastName} "
                        f"({lead.companyName}): {result.error_message}", "error")

            # Pause between batches
            if i + INJECT_BATCH_SIZE < len(enriched_leads):
                log(f"Waiting {INJECT_BATCH_PAUSE}s before next batch...")
                await asyncio.sleep(INJECT_BATCH_PAUSE)

    log(f"Injection done: {report.injected}/{report.total} injected, "
        f"{report.excluded} excluded, {report.errors} errors", "success")

    return report


def save_report(report: InjectionReport, campaign_dir: Path) -> Path:
    """Save injection report to injection_report.json."""
    output_path = campaign_dir / "report.json"
    data = asdict(report)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    log(f"Saved injection report to {output_path.name}", "success")
    return output_path
