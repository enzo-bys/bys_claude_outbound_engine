# BYS Outbound Engine

10 micro-campagnes outbound ultra-ciblees depuis un brief humain, via Claude.

## Quick Start

1. Clone le repo et installe les dependances :
   ```bash
   pip install -r requirements.txt
   ```

2. Copie `.env.example` vers `.env.local` et remplis tes API keys.

3. Ouvre Claude Code dans ce dossier et dis :
   > "Je veux creer ma premiere campagne de prospection"

   Claude te guidera a travers tout le process.

## Agents disponibles

| Agent | Ce qu'il fait |
|-------|--------------|
| bys-setup | Configure tes API keys et cree ton dossier client |
| bys-strategy | Cree ta strategie : discovery, CAB-P, 10 ciblages |
| bys-campaign | Lance le pipeline et injecte dans Lemlist |
| bys-monitor | Suit les performances et optimise |

## Mode CLI (power users)

```bash
# Campagne unique
python -m pipeline run --campaign clients/acme_2026-03-24/campaigns/C01_techchange_cro_fr

# Batch (toutes les campagnes)
python -m pipeline run --client clients/acme_2026-03-24 --campaigns all

# Selection
python -m pipeline run --client clients/acme_2026-03-24 --campaigns C01,C04,C07

# Status
python -m pipeline status --client clients/acme_2026-03-24

# Etapes individuelles
python -m pipeline enrich --campaign path/to/C04
python -m pipeline write  --campaign path/to/C04
python -m pipeline inject --campaign path/to/C04 --lemlist-id cam_xxx
```

## Stack

- Python 3.11+ (anthropic, aiohttp, typer, pyyaml, pydantic)
- Claude API (Sonnet par defaut, Opus optionnel)
- Scrapingdog (Google SERP) + RapidAPI (LinkedIn)
- Lemlist (injection + sequences)

## Architecture

```
agents/          4 agents Claude Code (.md) — UX conversationnelle
pipeline/        Engine Python — execution silencieuse
templates/       Guides methodo + exemples YAML/JSON
clients/         Donnees clients (gitignore)
```
