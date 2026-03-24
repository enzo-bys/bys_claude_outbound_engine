> **INSTRUCTIONS FOR CLAUDE** — If a user pastes this document into your conversation, you are an onboarding assistant for the Outbound Engine. Your job is to guide them through setup step by step. **CRITICAL: This project requires Claude Code (the CLI tool that runs in a terminal).** It does NOT work in Claude.ai web chat, Claude Desktop chat, or any interface without terminal/filesystem access. If you cannot run bash commands or edit files, STOP immediately and tell the user:
>
> *"This project needs **Claude Code** to work. You have 2 options:*
>
> ***Option A — Claude Code on the web (easiest, no install)***
> *1. You need a GitHub account — create one at https://github.com/signup if you don't have one*
> *2. Fork this project: go to https://github.com/enzo-bys/bys_claude_outbound_engine and click "Fork"*
> *3. Open Claude Code web: https://claude.ai/code*
> *4. Connect your GitHub account and open your fork*
> *5. Paste this README in the chat and I'll guide you through everything.*
>
> ***Option B — Claude Code CLI (local, on your machine)***
> *1. Go to https://claude.ai/code and follow the install instructions*
> *2. Open your terminal*
> *3. Run: `claude`*
> *4. Paste this README and I'll walk you through everything step by step.*
>
> *Here's a 3-min video walkthrough: https://youtu.be/Foou3pCHXIM"*
>
> If you ARE inside Claude Code, follow the setup flow described in this README. Guide the user ONE step at a time. Ask ONE question at a time. Never dump all steps at once. Always show clickable links for API keys. If the user seems lost, simplify — explain like they've never used a terminal. If they don't have git, Python, or Node.js installed, help them install those first. If they already have the project set up, skip to the step they need. The Lemlist MCP handles all Lemlist operations — no separate LEMLIST_API_KEY is needed in .env.local.

---

# Outbound Engine

You describe your business. Claude builds your prospecting pipeline. 10 campaigns, 400 leads, personalized emails — injected into Lemlist in one session.

> **Video walkthrough (3 min):** https://youtu.be/Foou3pCHXIM
>
> **Requires [Claude Code](https://claude.ai/code)** — two ways to use it:
> - **Web** (no install): fork this repo on GitHub, then open it in [Claude Code web](https://claude.ai/code)
> - **CLI** (local): install Claude Code, open your terminal, run `claude`
>
> Copy-paste this README into Claude Code and it will guide you step by step.

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
- **3 API keys** for enrichment (we'll set them up together in Step 2)
- **Lemlist MCP** connected to Claude Code (we'll set it up in Step 2 — this is how Claude talks to Lemlist)

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
>
> **Don't have Python?** Download it from [python.org/downloads](https://www.python.org/downloads/). On Mac, you can also run `brew install python`.
>
> **Don't have Node.js?** You'll need it for the Lemlist MCP in Step 2. Download it from [nodejs.org](https://nodejs.org) (LTS version recommended).

---

## Step 2 — Connect Lemlist MCP + get your API keys

### 2a. Connect Lemlist MCP (required)

This is how Claude Code talks directly to Lemlist — creating campaigns, sourcing leads, pulling stats, everything.

Run this in your terminal:

```bash
claude mcp add --transport http lemlist https://app.lemlist.com/mcp
```

On first use, your browser will open a consent page. Authorize your Lemlist team and you're connected.

> **Prefer API key auth?** If your setup doesn't support OAuth:
> ```bash
> claude mcp add --transport http lemlist https://app.lemlist.com/mcp --header "X-API-Key:YOUR_LEMLIST_API_KEY"
> ```
> Get your API key at **https://app.lemlist.com/settings/integrations** (Settings → Integrations → API → Copy Key).

### 2b. Get your 3 enrichment API keys

These keys power the AI writing and lead enrichment. Click each link:

| # | Key | What it does | Get it here | How to find it |
|---|-----|-------------|-------------|---------------|
| 1 | `ANTHROPIC_API_KEY` | Powers the AI that writes your emails | **https://console.anthropic.com/account/keys** | Click "Create Key" → copy it |
| 2 | `SCRAPINGDOG_API_KEY` | Finds Google news about leads | **https://api.scrapingdog.com/dashboard** | Your API key is at the top of the dashboard |
| 3 | `RAPIDAPI_KEY` | Enriches LinkedIn profiles | **[https://rapidapi.com](https://rapidapi.com/pnd-team-pnd-team/api/professional-network-data/playground)** | Subscribe (free) → copy `X-RapidAPI-Key` from any code snippet |

---

## Step 3 — Save your API keys

Run this command to create your config file:

```bash
cp .env.example .env.local
```

Then open `.env.local` with any text editor and paste your 3 keys:

```
ANTHROPIC_API_KEY=sk-ant-...
SCRAPINGDOG_API_KEY=...
RAPIDAPI_KEY=...
```

Save the file.

> **Note:** You don't need a `LEMLIST_API_KEY` in `.env.local` — the Lemlist MCP you set up in Step 2a handles all Lemlist communication directly.

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

## Step 7 — Get your leads and launch

You have 3 ways to get leads into a campaign. Pick the one that fits you:

### Option A — Source from Lemlist (recommended)

Just tell Claude what you're looking for:

```
Find 40 CROs at SaaS companies in France with 50-200 employees
```

Claude uses Lemlist's built-in lead database to search, filter, and add leads directly to your campaign. No file needed.

### Option B — Import a CSV or Excel file

If you already have a lead list (exported from LinkedIn, a CRM, or a spreadsheet):

```
Here's my lead list: /path/to/leads.csv
```

Claude reads the file, maps the columns automatically, converts it to the right format, and pushes the leads into the campaign. Minimum columns: first name, last name, company. Email and LinkedIn URL improve results.

### Option C — Manual JSON (power users)

Drop a `leads.json` file in the campaign folder:

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

### Launch

Once your leads are ready (any option above), run:

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
| 5 | `/outbound-engine:setup` | API keys check + Lemlist MCP check + client folder |
| 6 | `/outbound-engine:strategy` | 9 questions + CAB-P + 10 campaigns |
| 7 | "Find 40 CROs in France" or drop a CSV | Leads sourced via Lemlist, CSV import, or manual JSON |
| 8 | `/outbound-engine:campaign` | Enrich leads + write emails + inject Lemlist |
| 9 | `/outbound-engine:monitor` | Stats + recommendations |

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
You can source leads directly from Lemlist (no file needed), import a CSV/Excel file, or provide a JSON file. Minimum fields: first name, last name, company. Add email and LinkedIn URL for best results.

**I'm not technical. Can I still use this?**
Yes. If you can install Claude Code, connect Lemlist, and paste 3 API keys, you're good. Claude handles everything else conversationally.

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

**Stack**: Python 3.11+ / Claude API / Lemlist MCP / Scrapingdog / RapidAPI LinkedIn

---

Built by [BuildYourSales.tech](https://buildyoursales.tech)
