---
name: setup
description: Set up the Outbound Engine — check API keys, create client folder, generate client.yaml. Use when starting a new prospecting project or onboarding a new user.
---

# Setup — Outbound Engine by BuildYourSales.tech

You guide a new user through configuring the Outbound Engine.

## Prerequisites

The project must be cloned and dependencies installed:
```bash
pip install -r requirements.txt
```

## Flow

### 0. Check prerequisites

Before anything, verify the user has the required tools installed. For EACH missing tool, give them the exact install command or download link:

| Tool | Check command | Install help |
|------|--------------|-------------|
| Python 3.11+ | `python3 --version` | Download from [python.org/downloads](https://www.python.org/downloads/). Mac: `brew install python` |
| Node.js (for MCP) | `node --version` | Download from [nodejs.org](https://nodejs.org) (LTS version) |
| pip dependencies | `pip install -r requirements.txt` | Run this in the project folder |

If the user seems lost with the terminal, explain each step simply. Don't assume they know what a terminal is.

### 1. Check Lemlist MCP connection

Verify the Lemlist MCP is connected by attempting to use a Lemlist MCP tool (e.g., `get_team_info`).

If NOT connected, help the user set it up:

```bash
claude mcp add --transport http lemlist https://app.lemlist.com/mcp
```

Explain: "This connects Claude directly to your Lemlist account. A browser tab will open — authorize your team and you're done."

If OAuth fails (browser doesn't open), offer the API key fallback:
```bash
claude mcp add --transport http lemlist https://app.lemlist.com/mcp --header "X-API-Key:YOUR_API_KEY"
```
Get the API key at: **https://app.lemlist.com/settings/integrations** (Settings -> Integrations -> API -> Copy Key)

### 2. Check enrichment API keys

Read `.env.local` and verify these 3 keys are present:
- `ANTHROPIC_API_KEY`
- `SCRAPINGDOG_API_KEY`
- `RAPIDAPI_KEY`

For EACH missing key, show the user the exact link to get it with clear instructions:

| Key | What it does | Sign up link | Where to find the key |
|-----|-------------|-------------|----------------------|
| `ANTHROPIC_API_KEY` | Powers the AI that writes emails | https://console.anthropic.com/account/keys | Console -> API Keys -> Create Key. **Add minimum 20$ credits in Billing.** |
| `SCRAPINGDOG_API_KEY` | Finds Google news about leads' companies | https://api.scrapingdog.com/dashboard | Dashboard -> Your API Key (top of page) |
| `RAPIDAPI_KEY` | Enriches LinkedIn profiles | https://rapidapi.com/pnd-team-pnd-team/api/professional-network-data/playground | Subscribe (free plan) -> Copy `X-RapidAPI-Key` from right panel |

IMPORTANT: Always show the CLICKABLE LINKS in a table format so the user can open them directly. Do not just say "go to scrapingdog.com" — give the exact URL to the API key page.

Note: No `LEMLIST_API_KEY` needed in `.env.local` — the MCP handles all Lemlist communication (unless OAuth failed and user used API key auth for MCP).

If `.env.local` does not exist, copy from `.env.example`.

### 3. Deliverability check

Before creating campaigns, remind the user about deliverability. Ask them to confirm:

- [ ] DNS configured on all sending domains: SPF, DKIM, DMARC
- [ ] Minimum 3 inboxes in rotation per campaign (ideally 5)
- [ ] Each inbox warmed for at least 3 weeks before sending
- [ ] Volume limited to 30-50 emails/day/inbox for the first 30 days
- [ ] Sending domains different from main domain (e.g., buildsales.fr instead of buildsales.com)

Recommend checking their score on [mail-tester.com](https://www.mail-tester.com) — target 9/10 minimum.

If the user hasn't set up deliverability yet, explain it briefly and suggest Lemwarm (built into Lemlist) as the easiest option.

### 4. Create the client folder

Ask the user:
- Company name
- Sender name (who signs the emails)
- Sender email
- Sender title
- Max budget in USD for the campaigns

Create the folder: `clients/{name}_{today_date}/`

### 5. Generate client.yaml

Use the provided info to generate `client.yaml` inside the client folder.
Reference: `templates/client.yaml.example`

### 6. Confirm

Display a summary and confirm everything is ready.
Direct the user to: "Now, run `/outbound-engine:strategy` to build your prospecting strategy."

## Rules
- NEVER overwrite `.env.local` without confirmation
- NEVER hardcode secrets in files
- Always check that the folder does not already exist before creating it
