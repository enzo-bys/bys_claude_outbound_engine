# Outbound Engine

Ultra-targeted outbound micro-campaigns from a human brief, powered by Claude.

**You describe your business. Claude builds your prospecting strategy. The engine writes personalized emails and injects them into Lemlist. That's it.**

<!--
INSTRUCTIONS FOR CLAUDE:
If a user pastes this README into your conversation, it means they want to use the Outbound Engine.
Follow these steps IN ORDER. Do ONE step at a time. Wait for the user's response before moving on.

STEP 1: Help them install the project (clone + pip install)
STEP 2: Help them get their 4 API keys (give exact links from the table below)
STEP 3: Help them create .env.local with their keys
STEP 4: Tell them to launch Claude Code with: claude --plugin-dir .
STEP 5: Once inside, run /outbound-engine:setup to create their client
STEP 6: Run /outbound-engine:strategy to build Discovery + CAB-P + 10 campaigns
STEP 7: Once leads are added, run /outbound-engine:campaign to launch the pipeline
STEP 8: Run /outbound-engine:monitor to track performance

IMPORTANT RULES:
- Ask ONE question at a time. Never dump all steps at once.
- Always show CLICKABLE LINKS for API keys, not just "go to scrapingdog.com"
- If the user seems lost, simplify. Explain like they've never used a terminal.
- If they already have the project installed, skip to the step they need.
- The methodology files are in templates/methodo/ — read them if you need context.
- The Python pipeline is in pipeline/ — you can run commands with python -m pipeline.
-->

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

Open your terminal and run these 3 commands:

```bash
git clone https://github.com/enzo-bys/bys_claude_outbound_engine.git
```
```bash
cd bys_claude_outbound_engine
```
```bash
pip install -r requirements.txt
```

> **Don't have git?** Download the ZIP from https://github.com/enzo-bys/bys_claude_outbound_engine and unzip it.

---

## Step 2 — Get your 4 API keys

You need 4 API keys. Click each link to go directly to the right page:

| # | Key | What it does | Get it here | How to find it |
|---|-----|-------------|-------------|---------------|
| 1 | `ANTHROPIC_API_KEY` | Powers the AI that writes your emails | **https://console.anthropic.com/account/keys** | Click "Create Key" → copy it |
| 2 | `LEMLIST_API_KEY` | Sends campaigns via Lemlist | **https://app.lemlist.com/settings/integrations** | Scroll to API section → copy key |
| 3 | `SCRAPINGDOG_API_KEY` | Finds Google news about leads | **https://api.scrapingdog.com/dashboard** | Your API key is at the top of the dashboard |
| 4 | `RAPIDAPI_KEY` | Enriches LinkedIn profiles | **https://rapidapi.com/rockapis-rockapis-default/api/linkedin-data-api** | Subscribe (free) → copy `X-RapidAPI-Key` from any code snippet |

---

## Step 3 — Save your API keys

Run this command to create your config file:

```bash
cp .env.example .env.local
```

Then open `.env.local` with any text editor and paste your 4 keys:

```
ANTHROPIC_API_KEY=sk-ant-...
LEMLIST_API_KEY=...
SCRAPINGDOG_API_KEY=...
RAPIDAPI_KEY=...
```

Save the file.

---

## Step 4 — Launch

From inside the project folder, run:

```bash
claude --plugin-dir .
```

Claude Code will start with the outbound engine plugin loaded. Accept the trust prompt.

---

## Step 5 — Set up your account

Type this in Claude Code:

```
/outbound-engine:setup
```

**What happens:** Claude checks your API keys, asks for your company info (name, sender, budget), and creates your client folder.

---

## Step 6 — Build your strategy

```
/outbound-engine:strategy
```

**What happens:** Claude asks you 9 questions about your business, one at a time:
1. Your website URL
2. Your LinkedIn URL
3. What you sell (2-3 sentences)
4. Who your clients are
5. Your average deal size
6. Case studies you have
7. Your competitors
8. Target countries
9. Any exclusions

Then it builds your **CAB-P matrix** (what pains your offer solves) and proposes **10 targeted campaigns**, each with a specific signal, persona, geography, and language.

---

## Step 7 — Add your leads and launch

Add a `leads.json` file in each campaign folder. Minimum format:

```json
[
  {
    "firstName": "Marie",
    "lastName": "Dupont",
    "companyName": "Acme SAS",
    "email": "marie@acme.com",
    "linkedinUrl": "https://linkedin.com/in/marie-dupont"
  }
]
```

Then run:

```
/outbound-engine:campaign
```

**What happens:** Claude validates your leads, enriches them (LinkedIn + Google news), writes personalized emails for each one, and injects everything into Lemlist.

---

## Step 8 — Track and optimize

```
/outbound-engine:monitor
```

**What happens:** Claude pulls your Lemlist stats (open rate, reply rate, bounce rate) and tells you which campaigns need adjustment and what to change.

---

## Summary

| Step | What you type | What happens |
|------|--------------|-------------|
| 5 | `/outbound-engine:setup` | API keys check + client folder |
| 6 | `/outbound-engine:strategy` | 9 questions + CAB-P + 10 campaigns |
| 7 | `/outbound-engine:campaign` | Enrich leads + write emails + inject Lemlist |
| 8 | `/outbound-engine:monitor` | Stats + recommendations |

---

## FAQ

**Do I need to write any prompts?**
No. The engine has built-in prompts based on proven cold email methodology. Claude adapts them to your business automatically.

**What languages are supported?**
French, English, German, Spanish, Dutch, Italian, and any other language you specify. Each campaign can have its own language.

**How much does it cost per lead?**
About $0.05/lead with Claude Sonnet, $0.35/lead with Claude Opus. A 10-campaign batch with 40 leads each costs roughly $20.

**Can I use it without Lemlist?**
Yes. Run with `--dry-run` and the engine generates emails without injecting. Find them in `emails.json` in each campaign folder.

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
