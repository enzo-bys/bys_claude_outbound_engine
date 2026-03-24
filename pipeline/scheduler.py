"""Batch multi-campaign orchestration with budget tracking and resume-on-error."""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

import yaml

from pipeline.models import (
    CampaignContext, ClientConfig, CampaignConfig,
    EnrichedLead, PersonalizedSections,
)
from pipeline.enricher import enrich_leads, save_enriched
from pipeline.copywriter import write_personalized, save_personalized
from pipeline.injector import inject_leads, save_report
from pipeline.utils import log

import asyncio


COST_PER_LEAD: dict[str, float] = {
    "claude-sonnet-4-6": 0.05,
    "claude-opus-4-6": 0.35,
}

STATUS_ORDER = ["draft", "enriched", "written", "injected", "live"]


def _estimate_cost(campaign_dir: Path, model: str) -> float:
    """Estimate campaign cost based on lead count and model."""
    leads_file = campaign_dir / "leads.json"
    if not leads_file.exists():
        return 0.0
    leads = json.loads(leads_file.read_text())
    return len(leads) * COST_PER_LEAD.get(model, 0.05)


def _update_status(campaign_dir: Path, status: str, error: str | None = None) -> None:
    """Update campaign.yaml status field."""
    yaml_path = campaign_dir / "campaign.yaml"
    if not yaml_path.exists():
        return
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    data["status"] = status
    data["last_step_at"] = datetime.now(timezone.utc).isoformat()
    data["error_message"] = error
    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def _list_campaigns(client_dir: Path, filter_ids: list[str] | None = None) -> list[Path]:
    """List campaign directories, optionally filtered by ID."""
    campaigns_dir = client_dir / "campaigns"
    if not campaigns_dir.exists():
        return []
    dirs = sorted(d for d in campaigns_dir.iterdir() if d.is_dir())
    if filter_ids:
        dirs = [d for d in dirs if any(d.name.startswith(fid) for fid in filter_ids)]
    return dirs


def _load_enriched(campaign_dir: Path) -> list[EnrichedLead]:
    """Load enriched leads from JSON file."""
    enriched_path = campaign_dir / "leads_enriched.json"
    raw = json.loads(enriched_path.read_text())
    enriched = []
    for data in raw:
        lead = EnrichedLead(
            firstName=data.get("firstName", ""),
            lastName=data.get("lastName", ""),
            companyName=data.get("companyName", ""),
            linkedinUrl=data.get("linkedinUrl", ""),
            headline=data.get("headline", ""),
            seniority=data.get("seniority", ""),
            industry=data.get("industry", ""),
            techStack=data.get("techStack", ""),
            icebreaker=data.get("icebreaker", ""),
            email=data.get("email", ""),
            firecrawl_context=data.get("firecrawl_context", {}),
            linkedin_profile=data.get("linkedin_profile", {}),
            intent_score=data.get("intent_score", 0),
            enrichment_errors=data.get("enrichment_errors", []),
        )
        enriched.append(lead)
    return enriched


async def run_single_campaign(
    campaign_dir: Path,
    campaign_id_lemlist: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Run pipeline for a single campaign with status-based resume."""
    ctx = CampaignContext.load(campaign_dir)
    cfg = ctx.campaign_config or CampaignConfig(campaign_id=campaign_dir.name)
    status = cfg.status
    result: dict = {
        "campaign": campaign_dir.name,
        "status_before": status,
        "status_after": status,
        "error": None,
        "cost_usd": 0.0,
    }

    try:
        # Step 1: Enrich (if draft)
        if status in ("draft",):
            log(f"[{campaign_dir.name}] Step 1/3: Enrichment")
            enriched = await enrich_leads(ctx)
            save_enriched(enriched, campaign_dir)
            _update_status(campaign_dir, "enriched")
            status = "enriched"

        # Step 2: Write (if enriched)
        if status in ("enriched",):
            log(f"[{campaign_dir.name}] Step 2/3: Copywriting")
            enriched = _load_enriched(campaign_dir)
            sections = await write_personalized(enriched, ctx)
            save_personalized(sections, campaign_dir)
            model = cfg.model
            result["cost_usd"] = len(enriched) * COST_PER_LEAD.get(model, 0.05)
            _update_status(campaign_dir, "written")
            status = "written"

        # Step 3: Inject (if written and not dry_run)
        if status in ("written",) and not dry_run:
            if not campaign_id_lemlist:
                log(f"[{campaign_dir.name}] No Lemlist campaign ID, skipping injection", "warn")
            else:
                log(f"[{campaign_dir.name}] Step 3/3: Injection")
                enriched = _load_enriched(campaign_dir)

                personalized = None
                perso_path = campaign_dir / "emails.json"
                if perso_path.exists():
                    perso_raw = json.loads(perso_path.read_text())
                    personalized = [
                        PersonalizedSections(**{k: v for k, v in s.items()
                                                if k in PersonalizedSections.__dataclass_fields__})
                        for s in perso_raw
                    ]

                report = await inject_leads(campaign_id_lemlist, enriched, personalized)
                save_report(report, campaign_dir)
                _update_status(campaign_dir, "live")
                status = "live"

        result["status_after"] = status

    except Exception as e:
        result["error"] = str(e)
        result["status_after"] = "error"
        _update_status(campaign_dir, "error", str(e))
        log(f"[{campaign_dir.name}] Pipeline error: {e}", "error")

    return result


async def run_batch(
    client_dir: str | Path,
    campaign_ids: list[str] | None = None,
    dry_run: bool = False,
) -> dict:
    """Run pipeline for multiple campaigns with budget tracking."""
    client_path = Path(client_dir)
    client_config = ClientConfig.load(client_path)
    started_at = datetime.now(timezone.utc).isoformat()

    # List campaigns to process
    filter_ids = campaign_ids if campaign_ids and campaign_ids != ["all"] else None
    campaign_dirs = _list_campaigns(client_path, filter_ids)

    if not campaign_dirs:
        log("No campaigns found", "warn")
        return {"error": "no campaigns"}

    # Sort by status (least advanced first for sequential processing)
    def sort_key(d: Path) -> int:
        cfg_path = d / "campaign.yaml"
        if cfg_path.exists():
            with open(cfg_path) as f:
                s = yaml.safe_load(f).get("status", "draft")
            return STATUS_ORDER.index(s) if s in STATUS_ORDER else 99
        return 0
    campaign_dirs.sort(key=sort_key)

    budget_total = client_config.total_budget_usd
    budget_used = 0.0
    results: dict = {
        "client": client_path.name,
        "campaigns_completed": [],
        "campaigns_failed": [],
        "campaigns_skipped": [],
        "budget_total": budget_total,
        "budget_used": 0.0,
        "budget_remaining": budget_total,
        "started_at": started_at,
        "completed_at": None,
    }

    for cdir in campaign_dirs:
        cfg_path = cdir / "campaign.yaml"
        cfg_data: dict = {}
        if cfg_path.exists():
            with open(cfg_path) as f:
                cfg_data = yaml.safe_load(f) or {}
            status = cfg_data.get("status", "draft")
            if status in ("live", "injected"):
                log(f"[{cdir.name}] Already {status}, skipping")
                continue

        # Budget check
        model = cfg_data.get("model", client_config.model)
        estimated_cost = _estimate_cost(cdir, model)
        if budget_used + estimated_cost > budget_total:
            log(f"[{cdir.name}] Budget exceeded (need ${estimated_cost:.2f}, "
                f"remaining ${budget_total - budget_used:.2f}), skipping", "warn")
            results["campaigns_skipped"].append(cdir.name)
            continue

        log(f"=== Campaign: {cdir.name} (est. ${estimated_cost:.2f}) ===")
        campaign_result = await run_single_campaign(cdir, dry_run=dry_run)

        if campaign_result["error"]:
            results["campaigns_failed"].append(cdir.name)
        else:
            results["campaigns_completed"].append(cdir.name)
            budget_used += campaign_result["cost_usd"]

    results["budget_used"] = round(budget_used, 2)
    results["budget_remaining"] = round(budget_total - budget_used, 2)
    results["completed_at"] = datetime.now(timezone.utc).isoformat()

    # Save batch report
    report_path = client_path / "report_batch.json"
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    log(f"Batch done: {len(results['campaigns_completed'])} completed, "
        f"{len(results['campaigns_failed'])} failed, "
        f"{len(results['campaigns_skipped'])} skipped. "
        f"Budget: ${budget_used:.2f}/{budget_total:.2f}", "success")

    return results
