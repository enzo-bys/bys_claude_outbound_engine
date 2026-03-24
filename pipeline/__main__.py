"""Outbound Pipeline CLI.

Usage:
    python -m pipeline enrich --campaign path/to/C04
    python -m pipeline write  --campaign path/to/C04
    python -m pipeline inject --campaign path/to/C04 --lemlist-id cam_xxx
    python -m pipeline run    --client path/to/client --campaigns all
    python -m pipeline run    --client path/to/client --campaigns C01,C04
    python -m pipeline status --client path/to/client
"""

from __future__ import annotations
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="outbound-pipeline",
    help="Outbound Pipeline — Built by BuildYourSales.tech",
    no_args_is_help=True,
)


@app.command()
def enrich(
    campaign: str = typer.Option(..., help="Path to campaign directory"),
) -> None:
    """Step 1: Enrich leads with Scrapingdog + RapidAPI LinkedIn."""
    from pipeline.models import CampaignContext
    from pipeline.enricher import enrich_leads, save_enriched

    ctx = CampaignContext.load(campaign)
    enriched = asyncio.run(enrich_leads(ctx))
    save_enriched(enriched, Path(campaign))

    result = {"leads": len(enriched), "errors": sum(1 for e in enriched if e.enrichment_errors)}
    json.dump(result, sys.stdout, indent=2)
    print()


@app.command()
def write(
    campaign: str = typer.Option(..., help="Path to campaign directory"),
) -> None:
    """Step 2: Write personalized emails with Claude API."""
    from pipeline.models import CampaignContext, EnrichedLead
    from pipeline.copywriter import write_personalized, save_personalized

    ctx = CampaignContext.load(campaign)
    enriched_path = Path(campaign) / "leads_enriched.json"
    if not enriched_path.exists():
        typer.echo("Error: leads_enriched.json not found. Run 'enrich' first.", err=True)
        raise typer.Exit(1)

    raw = json.loads(enriched_path.read_text())
    enriched = [EnrichedLead(**{k: v for k, v in d.items()
                                if k in EnrichedLead.__dataclass_fields__}) for d in raw]
    sections = asyncio.run(write_personalized(enriched, ctx))
    save_personalized(sections, Path(campaign))

    result = {"leads": len(sections), "errors": sum(1 for s in sections if s.generation_error)}
    json.dump(result, sys.stdout, indent=2)
    print()


@app.command()
def inject(
    campaign: str = typer.Option(..., help="Path to campaign directory"),
    lemlist_id: str = typer.Option(..., help="Lemlist campaign ID (cam_xxx)"),
) -> None:
    """Step 3: Inject leads into Lemlist campaign."""
    from pipeline.models import EnrichedLead, PersonalizedSections
    from pipeline.injector import inject_leads, save_report

    cdir = Path(campaign)
    enriched_path = cdir / "leads_enriched.json"
    if not enriched_path.exists():
        typer.echo("Error: leads_enriched.json not found.", err=True)
        raise typer.Exit(1)

    raw = json.loads(enriched_path.read_text())
    enriched = [EnrichedLead(**{k: v for k, v in d.items()
                                if k in EnrichedLead.__dataclass_fields__}) for d in raw]

    personalized = None
    perso_path = cdir / "emails.json"
    if perso_path.exists():
        perso_raw = json.loads(perso_path.read_text())
        personalized = [
            PersonalizedSections(**{k: v for k, v in s.items()
                                    if k in PersonalizedSections.__dataclass_fields__})
            for s in perso_raw
        ]

    report = asyncio.run(inject_leads(lemlist_id, enriched, personalized))
    save_report(report, cdir)

    result = {"injected": report.injected, "excluded": report.excluded,
              "errors": report.errors, "total": report.total}
    json.dump(result, sys.stdout, indent=2)
    print()


@app.command()
def run(
    client: Optional[str] = typer.Option(None, help="Path to client directory (batch mode)"),
    campaign: Optional[str] = typer.Option(None, help="Path to single campaign directory"),
    campaigns: str = typer.Option("all", help="Campaign IDs: all, or C01,C04,C07"),
    dry_run: bool = typer.Option(False, help="Skip injection step"),
) -> None:
    """Run full pipeline: enrich -> write -> inject (single or batch)."""
    if campaign:
        from pipeline.scheduler import run_single_campaign
        result = asyncio.run(run_single_campaign(
            campaign_dir=Path(campaign),
            dry_run=dry_run,
        ))
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    elif client:
        from pipeline.scheduler import run_batch
        campaign_ids = None if campaigns == "all" else campaigns.split(",")
        result = asyncio.run(run_batch(
            client_dir=client,
            campaign_ids=campaign_ids,
            dry_run=dry_run,
        ))
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    else:
        typer.echo("Error: provide --client (batch) or --campaign (single)", err=True)
        raise typer.Exit(1)
    print()


@app.command()
def status(
    client: str = typer.Option(..., help="Path to client directory"),
) -> None:
    """Show status of all campaigns for a client."""
    import yaml

    client_path = Path(client)
    campaigns_dir = client_path / "campaigns"
    if not campaigns_dir.exists():
        typer.echo("No campaigns directory found", err=True)
        raise typer.Exit(1)

    statuses = []
    for cdir in sorted(campaigns_dir.iterdir()):
        if not cdir.is_dir():
            continue
        cfg_path = cdir / "campaign.yaml"
        leads_path = cdir / "leads.json"
        info: dict = {"campaign": cdir.name, "status": "unknown", "leads": 0}
        if cfg_path.exists():
            with open(cfg_path) as f:
                cfg = yaml.safe_load(f)
            info["status"] = cfg.get("status", "draft")
            info["model"] = cfg.get("model", "")
            info["error"] = cfg.get("error_message")
        if leads_path.exists():
            try:
                leads = json.loads(leads_path.read_text())
                info["leads"] = len(leads)
            except json.JSONDecodeError:
                info["leads"] = 0
                info["error"] = info.get("error") or "Invalid leads.json"
        statuses.append(info)

    json.dump(statuses, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    app()
