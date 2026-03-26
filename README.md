> **INSTRUCTIONS FOR CLAUDE** — If a user pastes this document into your conversation, you are an onboarding assistant for the Outbound Engine. Your job is to guide them through setup step by step. **CRITICAL: This project requires Claude Code (the CLI tool that runs in a terminal).** It does NOT work in Claude.ai web chat, Claude Desktop chat, or any interface without terminal/filesystem access. If you cannot run bash commands or edit files, STOP immediately and tell the user:
>
> *"This project needs **Claude Code** (the CLI) to work. Here's how to install it:*
>
> *1. Open your Terminal (Mac: CMD + Space -> Terminal -> Enter)*
> *2. Run: `curl -fsSL https://claude.ai/install.sh | sh`*
> *3. Add to PATH: `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc`*
> *4. Launch: `claude`*
> *5. Select "Claude account with subscription" and log in*
> *6. Clone this repo and open it with Claude Code*
> *7. Paste this README in the chat and I'll guide you through everything.*
>
> *Here's a 3-min video walkthrough: https://youtu.be/Foou3pCHXIM"*
>
> If you ARE inside Claude Code, follow the setup flow described in this README. Guide the user ONE step at a time. Ask ONE question at a time. Never dump all steps at once. Always show clickable links for API keys. If the user seems lost, simplify — explain like they've never used a terminal. If they don't have git, Python, or Node.js installed, help them install those first. If they already have the project set up, skip to the step they need. The Lemlist MCP handles all Lemlist operations — no separate LEMLIST_API_KEY is needed in .env.local (unless OAuth fails).

---

# Outbound Engine

**Build Your Sales** | Version 2.0 | Mars 2026

You describe your business. Claude builds your prospecting pipeline. Up to 10 campaigns, 400 leads, personalized emails — injected into Lemlist in one session.

> **Requires [Claude Code CLI](https://claude.ai/code)** — install it, clone this repo, and paste this README into Claude Code. It guides you step by step.
>
> **Video walkthrough (3 min):** https://youtu.be/Foou3pCHXIM

---

## What does this do?

L'Outbound Engine est un plugin Claude Code developpe par Enzo Luciano-Marty (Build Your Sales) qui connecte Claude directement a Lemlist. Tu decris ton business, il genere des campagnes de prospection B2B completes.

**Ce que l'outil fait automatiquement :**

1. Pose 9 questions sur ton offre, tes clients, tes concurrents
2. Construit une matrice CAB-P (Caracteristiques, Avantages, Benefices, Douleurs)
3. Propose jusqu'a 10 campagnes ciblees (persona + signal + geo + langue)
4. Enrichit chaque lead (profil LinkedIn + news Google recentes)
5. Redige un email personnalise par personne — pas un template, un vrai message
6. Score chaque email avec l'IA avant envoi
7. Injecte tout dans Lemlist, pret a envoyer

Chaque campagne recoit 30-50 leads. Les emails sont rediges dans la langue de ton choix (francais, anglais, allemand, espagnol...).

> **Temps reel :** 45-60 min la premiere fois (installation), 15 min les fois suivantes une fois tout configure.
>
> **Cout estime :** ~0,05$/lead avec Claude Sonnet. 400 leads = environ 20$ de tokens Anthropic.

---

## Prerequisites

Before you start, you need:

- **A Claude Max (or Pro) subscription**
- **A GitHub account** — [create one here](https://github.com/signup) if you don't have one
- **A Lemlist account** with an active subscription
- **~20$ of Anthropic API credits** — [add credits here](https://console.anthropic.com/billing)
- **A deliverability infrastructure ready** (see the dedicated section below)

---

## Before anything: deliverability

C'est l'etape que tout le monde oublie et qui tue les resultats. Envoyer 400 emails depuis des inboxes froides ou mal configurees = blacklist garantie. Avant de lancer une seule campagne, ton infrastructure doit etre en place.

### Checklist delivrabilite obligatoire

- [ ] DNS configures sur tous tes domaines d'envoi : SPF, DKIM, DMARC
- [ ] Minimum 3 inboxes en rotation par campagne (idealement 5)
- [ ] Chaque inbox warmee pendant au minimum 3 semaines avant envoi
- [ ] Volume limite a 30-50 emails/jour/inbox pendant les 30 premiers jours
- [ ] Domaines d'envoi differents de ton domaine principal (ex : buildsales.fr au lieu de buildsales.com)

### Outils de warmup recommandes

- **Lemwarm** (integre a Lemlist) — le plus simple si tu es deja sur Lemlist
- **Instantly.ai Warmup** — efficace pour les volumes importants
- **Mailreach** — bon pour verifier la reputation de tes inboxes

> Avant de lancer, verifie ton score de delivrabilite sur [mail-tester.com](https://www.mail-tester.com). Objectif : 9/10 minimum.

---

## Installation

### Step 1 — Install Claude Code CLI

Open your Terminal (Mac: CMD + Space -> "Terminal" -> Enter) and run:

```bash
curl -fsSL https://claude.ai/install.sh | sh
```

Then configure your PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

Launch Claude Code:

```bash
claude
```

Select "Claude account with subscription" and log in.

### Step 2 — Fork and clone the repo

1. Go to [github.com/enzo-bys/bys_claude_outbound_engine](https://github.com/enzo-bys/bys_claude_outbound_engine)
2. Click **"Fork"** in the top right corner, then **"Create fork"**
3. Clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/bys_claude_outbound_engine.git
cd bys_claude_outbound_engine
```

4. Install Python dependencies:

```bash
pip install -r requirements.txt
```

> **Don't have git?** Download the ZIP from GitHub and unzip it.
>
> **Don't have Python?** Download it from [python.org/downloads](https://www.python.org/downloads/). Mac: `brew install python`.
>
> **Don't have Node.js?** You'll need it for the Lemlist MCP. Download from [nodejs.org](https://nodejs.org) (LTS version).

### Step 3 — Get your 3 enrichment API keys

| # | Key | What it does | Get it here | How to find it |
|---|-----|-------------|-------------|---------------|
| 1 | `ANTHROPIC_API_KEY` | Powers the AI that writes your emails | **[console.anthropic.com/account/keys](https://console.anthropic.com/account/keys)** | Click "Create Key" -> copy it. Then go to Billing and add minimum 20$ of credits. |
| 2 | `SCRAPINGDOG_API_KEY` | Finds Google news about leads | **[api.scrapingdog.com/dashboard](https://api.scrapingdog.com/dashboard)** | Create a free account -> API key is at the top of the dashboard |
| 3 | `RAPIDAPI_KEY` | Enriches LinkedIn profiles | **[rapidapi.com/.../professional-network-data](https://rapidapi.com/pnd-team-pnd-team/api/professional-network-data/playground)** | Subscribe (free plan) -> copy `X-RapidAPI-Key` from the right panel |

> Without Anthropic credits, lead enrichment will not work.

### Step 4 — Save your API keys

```bash
cp .env.example .env.local
```

Then open `.env.local` and paste your keys:

```
ANTHROPIC_API_KEY=sk-ant-...
SCRAPINGDOG_API_KEY=...
RAPIDAPI_KEY=...
```

> You can also tell Claude Code directly: `Add my API keys to .env.local: ANTHROPIC_API_KEY=... SCRAPINGDOG_API_KEY=... RAPIDAPI_KEY=...`

### Step 5 — Connect the Lemlist MCP

This is how Claude Code talks directly to Lemlist — creating campaigns, sourcing leads, pulling stats, everything.

In your terminal (inside Claude Code or outside):

```bash
claude mcp add --transport http lemlist https://app.lemlist.com/mcp
```

Your browser will open a consent page. Authorize your Lemlist team and you're connected.

> **If OAuth fails** (browser doesn't open), use your API key instead:
> ```bash
> claude mcp add --transport http lemlist https://app.lemlist.com/mcp --header "X-API-Key:YOUR_LEMLIST_API_KEY"
> ```
> Get your API key at: **Settings -> Integrations -> API -> Copy Key** in Lemlist.

### Step 6 — Install the plugin

You have two options:

**Option A — Install as a Claude Code plugin (recommended)**

```bash
claude plugin add --from https://github.com/enzo-bys/bys_claude_outbound_engine
```

This installs the plugin globally. You can then use it from any directory — just run `claude` and the skills are available.

**Option B — Run locally from the project folder**

```bash
claude --plugin-dir .
```

This loads the plugin only for the current session, from the local folder.

Either way, accept the trust prompt when Claude asks.

---

## Usage

### Step 1 — Set up your account

```
/outbound-engine:setup
```

Claude checks your API keys, asks for your company info, and creates your client folder.

### Step 2 — Build your strategy

```
/outbound-engine:strategy
```

Claude asks you 9 questions about your business, one at a time:
1. Your website URL
2. Your LinkedIn URL
3. What you sell (2-3 sentences)
4. Who your clients are
5. Your average deal size
6. Case studies you have
7. Your competitors
8. Target countries
9. Any exclusions

Then it builds your **CAB-P matrix** and proposes **up to 10 targeted campaigns**, each with a specific signal, persona, geography, and language.

### Step 3 — Get your leads and launch

You have 3 ways to get leads into a campaign:

**Option A — Source from Lemlist (recommended)**

Just tell Claude what you're looking for:
```
Find 40 CROs at SaaS companies in France with 50-200 employees
```

**Option B — Import a CSV or Excel file**

If you already have a lead list:
```
Here's my lead list: /path/to/leads.csv
```

**Option C — Manual JSON (power users)**

Drop a `leads.json` file in the campaign folder with `firstName`, `lastName`, `companyName` (minimum). Add `email` and `linkedinUrl` for better results.

**Then launch:**

```
/outbound-engine:campaign
```

Claude validates your leads, enriches them (LinkedIn + Google news), writes personalized emails, and injects everything into Lemlist.

### Step 4 — Track and optimize

```
/outbound-engine:monitor
```

Claude pulls your Lemlist stats and tells you which campaigns need adjustment.

---

## The key to success: a quality brief

L'Outbound Engine est aussi bon que le brief que tu lui donnes. Un brief pauvre = des campagnes generiques. Un brief precis = de la personnalisation chirurgicale.

### Brief pauvre vs. brief precis

| Brief pauvre (resultats mediocres) | Brief precis (resultats reels) |
|---|---|
| Je fais du conseil en prospection B2B. | Je delivre de l'outbound B2B 100% externalise pour des PME tech francaises 10-50 salaries. Deal size 2-3k euros/mois. |
| Mes clients sont des dirigeants. | CEO/DG qui n'ont pas de commercial interne et qui ont rate leurs objectifs Q1 faute de pipe. |
| J'ai de bons resultats. | 957 RDV pour IT Link en 6 mois, 117 pour Orisha, 63 pour Les Erudits. |
| Mes concurrents font pareil. | Concurrents : agences outbound classiques (Lalaleads, Akimbo) et freelances prospection — je me differencie par l'installation de l'infra interne. |
| Je vise la France. | France et Belgique. Exclure les boites de moins de 10 salaries et le secteur public. |

### Les 9 elements d'un brief beton

1. Ton URL de site web
2. Ton URL LinkedIn
3. Ton offre en 2-3 phrases : ce que tu fais, pour qui, avec quel resultat
4. Tes clients ideaux : secteur, taille, titre du decideur, probleme principal
5. Ton deal size moyen (pour calibrer le niveau d'effort du prospect)
6. Tes case studies avec chiffres precis
7. Tes concurrents directs et ce qui te differencie
8. Pays cibles et langue de preference
9. Exclusions : secteurs, tailles ou profils a eviter

---

## Getting the best results

### Les 3 leviers qui font la difference

| Levier | Comment l'activer |
|--------|------------------|
| Personnalisation a l'echelle | Laisser l'enrichissement LinkedIn + news tourner sur chaque lead. Ne pas sauter cette etape pour gagner du temps. |
| Signaux d'intention | Cibler des leads avec un signal recent : levee de fonds, nouveau poste, recrutement commercial, publication LinkedIn sur la prospection. |
| Copywriting humain | Combiner l'Outbound Engine pour la structure + ton expertise pour reecrire les emails dans ton style avant d'envoyer. |

### Attentes realistes

- Taux de reponse moyen du marche outbound : **1-3%**
- Taux de reponse avec personnalisation avancee (enrichissement + signal) : **5-9%**
- Premiere reponse attendue : **3-7 jours** apres le debut d'envoi
- Volume recommande pour tester une campagne : **50-100 leads minimum**

> Les resultats dependent directement de la qualite du brief, de la delivrabilite, et du copywriting. L'outil genere la machine — toi tu fournis la matiere premiere.

---

## Post-launch: finalize in Lemlist

After Claude injects your campaigns:

1. Go to Lemlist — your campaigns are created
2. **Pause them immediately** (they are "running" by default)
3. Paste your copywriting into each step
4. Configure A/B tests
5. Activate inbox rotation (minimum 3 accounts)
6. Import your leads (CSV or Lemlist database)
7. Launch and limit to 30-50 emails/day/inbox for the first 30 days

---

## Limitations

What the Outbound Engine does NOT handle:

- Advanced Lemlist conditions (if opened -> LinkedIn) — configure manually
- Clickable images and personalized image variables
- Dynamic landing pages
- Complex multi-channel branches with conditional logic

### Optimal workflow by context

| Context | Recommended approach |
|---------|---------------------|
| Urgent campaign (webinar, event) | Outbound Engine for structure + injection, manual copywriting in Lemlist |
| Long-term campaign | Outbound Engine for enrichment + leads, manual copywriting in your style, then manual injection |
| Scale (10+ campaigns) | Outbound Engine end-to-end with detailed brief |

---

## Summary

| Step | What you type | What happens |
|------|--------------|-------------|
| 1 | `/outbound-engine:setup` | API keys check + Lemlist MCP check + client folder |
| 2 | `/outbound-engine:strategy` | 9 questions + CAB-P + 10 campaigns |
| 3 | "Find 40 CROs in France" or drop a CSV | Leads sourced via Lemlist, CSV import, or manual JSON |
| 4 | `/outbound-engine:campaign` | Enrich leads + write emails + inject Lemlist |
| 5 | `/outbound-engine:monitor` | Stats + recommendations |

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
