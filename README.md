# Outbound Engine

Ultra-targeted outbound micro-campaigns from a human brief, powered by Claude.

## Install as Claude Code Plugin

```bash
# Clone the repo
git clone https://github.com/Enzo-salesrun/bys_claude_outbound_engine.git

# Install dependencies
cd bys_claude_outbound_engine
pip install -r requirements.txt

# Launch Claude Code with the plugin
claude --plugin-dir .
```

Then use the skills:
```
/outbound-engine:setup       → Set up API keys and create your client
/outbound-engine:strategy    → Build Discovery, CAB-P, 10 targeted campaigns
/outbound-engine:campaign    → Run the pipeline and inject into Lemlist
/outbound-engine:monitor     → Track performance and optimize
```

Or just say: **"I want to create my first prospecting campaign"** — Claude will guide you.

## Quick Start (without plugin)

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env.local` and fill in your API keys.

3. Open Claude Code in this folder and say:
   > "I want to create my first prospecting campaign"

## Skills

| Skill | What it does |
|-------|-------------|
| `/outbound-engine:setup` | Configure your API keys and create your client folder |
| `/outbound-engine:strategy` | Build your strategy: Discovery, CAB-P, 10 ciblages |
| `/outbound-engine:campaign` | Run the pipeline and inject into Lemlist |
| `/outbound-engine:monitor` | Track performance and optimize |

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

## Required API Keys

| Key | Where to get it |
|-----|----------------|
| `SCRAPINGDOG_API_KEY` | [scrapingdog.com](https://www.scrapingdog.com) — Google SERP API |
| `RAPIDAPI_KEY` | [rapidapi.com](https://rapidapi.com/rockapis-rockapis-default/api/linkedin-data-api) — LinkedIn profiles |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) — Claude API |
| `LEMLIST_API_KEY` | Lemlist → Settings → Integrations → API |

## Stack

- Python 3.11+ (anthropic, aiohttp, typer, pyyaml, pydantic)
- Claude API (Sonnet by default, Opus optional)
- Scrapingdog (Google SERP) + RapidAPI (LinkedIn)
- Lemlist (injection + sequences)

## Architecture

```
.claude-plugin/  Plugin manifest
skills/          4 skills (SKILL.md) — invocable via /outbound-engine:*
agents/          4 Claude Code agents (.md) — conversational UX
pipeline/        Python engine — silent execution
templates/       Methodology guides + YAML/JSON examples
clients/         Client data (gitignored)
```

## Multi-language Support

Each campaign has a `language` field in `campaign.yaml` that controls the copywriting language. Supported: `fr`, `en`, `de`, `es`, `nl`, `it`, and any custom language code.

---

Built by [BuildYourSales.tech](https://buildyoursales.tech)
