# Outbound Engine

Ultra-targeted outbound micro-campaigns from a human brief, powered by Claude.

**You describe your business. Claude builds your prospecting strategy. The engine writes personalized emails and injects them into Lemlist. That's it.**

---

## What does this do?

You give Claude a brief about your business. It will:

1. Ask you 9 questions to understand your offer, clients, and competitors
2. Build a CAB-P matrix (Characteristics, Advantages, Benefits, Pains)
3. Create 10 hyper-targeted campaign briefs (signal + persona + geo + language)
4. Enrich your leads (LinkedIn profiles + Google news)
5. Write personalized emails that sound like a human wrote them (not a sales template)
6. Score each email with AI before sending
7. Inject everything into Lemlist, ready to send

Each campaign gets 30-50 leads. Emails are written in the language of your choice (French, English, German, Spanish...).

---

## Prerequisites

Before you start, you need:

- **Claude Code** installed on your machine ([get it here](https://claude.ai/code))
- **Python 3.11+** installed ([download](https://www.python.org/downloads/))
- **A Lemlist account** with an active subscription
- **4 API keys** (we'll set them up together in Step 2)

---

## Step 1 — Download the engine

Open your terminal and run:

```bash
git clone https://github.com/enzo-bys/bys_claude_outbound_engine.git
cd bys_claude_outbound_engine
pip install -r requirements.txt
```

> **Don't have git?** You can also download the ZIP from the GitHub page and unzip it.

---

## Step 2 — Get your API keys

You need 4 API keys. Here's where to get each one:

| Key | What it does | Where to get it | Free tier? |
|-----|-------------|----------------|------------|
| `ANTHROPIC_API_KEY` | Powers the AI that writes your emails | [console.anthropic.com](https://console.anthropic.com) | $5 free credit |
| `LEMLIST_API_KEY` | Sends your campaigns | Lemlist app → Settings → Integrations → API | Included in plan |
| `SCRAPINGDOG_API_KEY` | Finds Google news about your leads' companies | [scrapingdog.com](https://www.scrapingdog.com) | 1000 free credits |
| `RAPIDAPI_KEY` | Enriches LinkedIn profiles | [rapidapi.com/linkedin-data-api](https://rapidapi.com/rockapis-rockapis-default/api/linkedin-data-api) | 100 free requests |

Once you have them, copy the example file and paste your keys:

```bash
cp .env.example .env.local
```

Open `.env.local` in any text editor and fill in your keys:

```
SCRAPINGDOG_API_KEY=your_key_here
RAPIDAPI_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
LEMLIST_API_KEY=your_key_here
```

---

## Step 3 — Launch Claude Code with the plugin

```bash
claude --plugin-dir .
```

That's it. Claude now has access to the outbound engine.

---

## Step 4 — Create your first campaign

Just type this in Claude Code:

```
/outbound-engine:setup
```

Claude will:
- Check that your API keys are working
- Ask for your company name, sender name, email, and budget
- Create your client folder

Then:

```
/outbound-engine:strategy
```

Claude will:
- Ask you 9 questions about your business (one at a time, don't worry)
- Build your CAB-P matrix
- Propose 10 targeted campaigns
- Ask what language each campaign should be written in

Then add your leads (a JSON file per campaign) and run:

```
/outbound-engine:campaign
```

Claude will:
- Validate your leads
- Enrich them (LinkedIn + Google)
- Write personalized emails for each lead
- Inject everything into Lemlist

---

## Step 5 — Track performance

Once your campaigns are live:

```
/outbound-engine:monitor
```

Claude will pull your Lemlist stats and tell you:
- Which campaigns are performing
- Which ones need adjustment
- What to change and why

---

## The 4 skills at a glance

| Step | Skill | What happens |
|------|-------|-------------|
| 1 | `/outbound-engine:setup` | API keys + client folder |
| 2 | `/outbound-engine:strategy` | Discovery + CAB-P + 10 campaigns |
| 3 | `/outbound-engine:campaign` | Enrich + write + inject into Lemlist |
| 4 | `/outbound-engine:monitor` | Stats + optimization |

---

## FAQ

**Do I need to write any prompts?**
No. The engine has built-in prompts based on proven cold email methodology. Claude adapts them to your business automatically.

**What languages are supported?**
French, English, German, Spanish, Dutch, Italian, and any other language you specify. Each campaign can have its own language.

**How much does it cost per lead?**
About $0.05/lead with Claude Sonnet, $0.35/lead with Claude Opus. A 10-campaign batch with 40 leads each costs roughly $20.

**Can I use it without Lemlist?**
Yes. Run with `--dry-run` flag and the engine will generate the emails without injecting. You'll find them in `emails.json` in each campaign folder.

**What format do my leads need to be in?**
A JSON file with at minimum: `firstName`, `lastName`, `companyName`. Add `email` and `linkedinUrl` for best results. See `templates/leads.json.example`.

**I'm not technical. Can I still use this?**
Yes. If you can install Claude Code and paste 4 API keys, you're good. Claude handles everything else conversationally.

---

## CLI Mode (power users)

If you prefer commands over conversation:

```bash
# Run a single campaign
python -m pipeline run --campaign clients/acme/campaigns/C01_techchange_cro_fr

# Run all campaigns for a client
python -m pipeline run --client clients/acme --campaigns all

# Run specific campaigns
python -m pipeline run --client clients/acme --campaigns C01,C04,C07

# Check status
python -m pipeline status --client clients/acme

# Individual steps
python -m pipeline enrich --campaign path/to/C04
python -m pipeline write  --campaign path/to/C04
python -m pipeline inject --campaign path/to/C04 --lemlist-id cam_xxx
```

---

## Architecture (for developers)

```
.claude-plugin/  Plugin manifest
skills/          4 skills (SKILL.md) — invocable via /outbound-engine:*
agents/          4 Claude Code agents (.md) — conversational UX
pipeline/        Python engine — silent execution
templates/       Methodology guides + YAML/JSON examples
clients/         Client data (gitignored)
```

**Stack**: Python 3.11+ / Claude API / Scrapingdog / RapidAPI LinkedIn / Lemlist

---

Built by [BuildYourSales.tech](https://buildyoursales.tech)
