"""Agentic copywriting pipeline — orchestrates 4 specialized agents.

Flow per lead:
    Analyst → Strategist → Copywriter → Reviewer → (Rewrite if score < 7)

Usage:
    python -m pipeline write --campaign-dir path/to/C04
"""

from __future__ import annotations
import asyncio
import json
from pathlib import Path
from dataclasses import asdict

import anthropic

from pipeline.config import ANTHROPIC_API_KEY, CLAUDE_MODEL as DEFAULT_MODEL, WRITE_CONCURRENCY
from pipeline.models import EnrichedLead, PersonalizedSections, CampaignContext
from pipeline.agents import run_analyst, run_strategist, run_copywriter, run_reviewer, run_rewrite
from pipeline.postprocess import postprocess_emails
from pipeline.utils import RateLimiter, ProgressTracker, log


REVIEW_THRESHOLD = 7  # Score minimum pour passer sans rewrite
MAX_REWRITES = 1      # Max rewrites par lead (pour ne pas exploser le budget)


async def _write_one_lead(
    client: anthropic.AsyncAnthropic,
    lead: EnrichedLead,
    ctx: CampaignContext,
    rate_limiter: RateLimiter,
    progress: ProgressTracker,
) -> PersonalizedSections:
    """Run the full agentic pipeline for one lead."""
    sections = PersonalizedSections(
        firstName=lead.firstName,
        lastName=lead.lastName,
        companyName=lead.companyName,
    )

    try:
        # Agent 1: ANALYST — comprend qui est le lead
        async with rate_limiter:
            brief = await run_analyst(client, lead, ctx)

        # Agent 2: STRATEGIST — choisit l'angle et le gap
        async with rate_limiter:
            strategy = await run_strategist(client, brief, ctx)

        # Agent 3: COPYWRITER — ecrit les emails
        async with rate_limiter:
            sections = await run_copywriter(client, brief, strategy, ctx)

        # Agent 4: REVIEWER — evalue la qualite
        async with rate_limiter:
            score, feedback = await run_reviewer(client, sections, brief, strategy, ctx)

        # REWRITE si score < seuil
        if score < REVIEW_THRESHOLD and feedback:
            log(f"{lead.firstName} {lead.lastName}: score={score}/10, rewriting...", "warn")
            async with rate_limiter:
                sections = await run_rewrite(client, sections, brief, strategy, feedback, ctx)
            # Re-review after rewrite
            async with rate_limiter:
                score, _ = await run_reviewer(client, sections, brief, strategy, ctx)
            log(f"{lead.firstName} {lead.lastName}: rewrite score={score}/10", "info")

        await progress.tick(success=True)

    except anthropic.RateLimitError:
        sections.generation_error = "Claude rate limit"
        log(f"Rate limit for {lead.firstName} {lead.lastName}", "warn")
        await asyncio.sleep(5)
        await progress.tick(success=False)
    except Exception as e:
        sections.generation_error = str(e)
        log(f"Error for {lead.firstName} {lead.lastName}: {e}", "error")
        await progress.tick(success=False)

    return sections


async def write_personalized(
    enriched_leads: list[EnrichedLead],
    ctx: CampaignContext,
) -> list[PersonalizedSections]:
    """Generate full personalized emails for all leads via agentic pipeline."""
    if not enriched_leads:
        log("No leads to write for", "warn")
        return []

    if not ANTHROPIC_API_KEY:
        log("ANTHROPIC_API_KEY not set", "error")
        return []

    model = ctx.campaign_config.model if ctx.campaign_config else DEFAULT_MODEL
    concurrency = ctx.campaign_config.concurrency if ctx.campaign_config else WRITE_CONCURRENCY

    log(f"Agentic copywriting for {len(enriched_leads)} leads "
        f"(model={model}, concurrency={concurrency}, "
        f"agents=analyst→strategist→copywriter→reviewer)")

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    rate_limiter = RateLimiter(concurrency)
    progress = ProgressTracker(len(enriched_leads), "Agentic Copywriting")

    tasks = [
        _write_one_lead(client, lead, ctx, rate_limiter, progress)
        for lead in enriched_leads
    ]
    sections = await asyncio.gather(*tasks)

    # Post-process: banned words, dashes, variable resolution
    valid_sections = [s for s in sections if not s.generation_error]
    if valid_sections:
        emails_data = [asdict(s) for s in valid_sections]
        campaign_config = ctx.campaign_config
        postprocess_emails(emails_data, campaign_config)
        for s, d in zip(valid_sections, emails_data):
            for field_name in ("email1Subject", "email1Body", "email2Subject", "email2Body",
                               "email3Subject", "email3Body", "linkedinInvite", "linkedinDm", "callScript"):
                setattr(s, field_name, d.get(field_name, getattr(s, field_name)))

    errors = sum(1 for s in sections if s.generation_error)
    log(f"Agentic copywriting done: {len(sections)} leads, {errors} errors", "success")

    return list(sections)


def save_personalized(
    sections: list[PersonalizedSections],
    campaign_dir: Path,
) -> Path:
    """Save personalized sections to emails_personalized.json."""
    output_path = campaign_dir / "emails.json"
    data = [asdict(s) for s in sections]
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    log(f"Saved {len(sections)} personalized emails to {output_path.name}", "success")
    return output_path
