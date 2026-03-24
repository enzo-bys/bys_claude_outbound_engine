# Outbound Engine

Ultra-targeted outbound micro-campaigns from a human brief, powered by Claude.

## Quick Start

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env.local` and fill in your API keys.

3. Open Claude Code in this folder and say:
   > "I want to create my first prospecting campaign"

   Claude will guide you through the entire process.

## Available Agents

| Agent | What it does |
|-------|-------------|
| setup | Configure your API keys and create your client folder |
| strategy | Build your strategy: Discovery, CAB-P, 10 ciblages |
| campaign | Run the pipeline and inject into Lemlist |
| monitor | Track performance and optimize |

## CLI Mode (power users)

```bash
# Single campaign
python -m pipeline run --campaign clients/acme_2026-03-24/campaigns/C01_techchange_cro_fr

# Batch (all campaigns)
python -m pipeline run --client clients/acme_2026-03-24 --campaigns all

# Selection
python -m pipeline run --client clients/acme_2026-03-24 --campaigns C01,C04,C07

# Status
python -m pipeline status --client clients/acme_2026-03-24

# Individual steps
python -m pipeline enrich --campaign path/to/C04
python -m pipeline write  --campaign path/to/C04
python -m pipeline inject --campaign path/to/C04 --lemlist-id cam_xxx
```

## Stack

- Python 3.11+ (anthropic, aiohttp, typer, pyyaml, pydantic)
- Claude API (Sonnet by default, Opus optional)
- Scrapingdog (Google SERP) + RapidAPI (LinkedIn)
- Lemlist (injection + sequences)

## Architecture

```
agents/          4 Claude Code agents (.md) — conversational UX
pipeline/        Python engine — silent execution
templates/       Methodology guides + YAML/JSON examples
clients/         Client data (gitignored)
```

---

Built by [BuildYourSales.tech](https://buildyoursales.tech)
