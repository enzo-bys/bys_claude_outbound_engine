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

### 1. Check API keys

Read `.env.local` and verify these 4 keys are present:
- `SCRAPINGDOG_API_KEY`
- `RAPIDAPI_KEY`
- `ANTHROPIC_API_KEY`
- `LEMLIST_API_KEY`

For EACH missing key, show the user the exact link to get it with clear instructions:

| Key | What it does | Sign up link | Where to find the key |
|-----|-------------|-------------|----------------------|
| `ANTHROPIC_API_KEY` | Powers the AI that writes emails | https://console.anthropic.com/account/keys | Console → API Keys → Create Key |
| `LEMLIST_API_KEY` | Injects leads into Lemlist campaigns | https://app.lemlist.com/settings/integrations | Settings → Integrations → API → Copy Key |
| `SCRAPINGDOG_API_KEY` | Finds Google news about leads' companies | https://api.scrapingdog.com/dashboard | Dashboard → Your API Key (top of page) |
| `RAPIDAPI_KEY` | Enriches LinkedIn profiles | https://rapidapi.com/rockapis-rockapis-default/api/linkedin-data-api | Subscribe → Copy `X-RapidAPI-Key` from code snippet |

IMPORTANT: Always show the CLICKABLE LINKS in a table format so the user can open them directly. Do not just say "go to scrapingdog.com" — give the exact URL to the API key page.

If `.env.local` does not exist, copy from `.env.example`.

### 2. Create the client folder

Ask the user:
- Company name
- Sender name (who signs the emails)
- Sender email
- Sender title
- Max budget in USD for the campaigns

Create the folder: `clients/{name}_{today_date}/`

### 3. Generate client.yaml

Use the provided info to generate `client.yaml` inside the client folder.
Reference: `templates/client.yaml.example`

### 4. Confirm

Display a summary and confirm everything is ready.
Direct the user to: "Now, run `/outbound-engine:strategy` to build your prospecting strategy."

## Rules
- NEVER overwrite `.env.local` without confirmation
- NEVER hardcode secrets in files
- Always check that the folder does not already exist before creating it
