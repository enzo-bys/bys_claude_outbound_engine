# BYS Outbound Engine — Redesign Spec

> Date: 2026-03-24
> Status: Approved
> Scope: Refonte complete du systeme agentique pour le rendre scalable, pro, et novice-friendly

---

## 1. Objectif

Transformer le prototype actuel (pipeline Python monolithique + prompts hardcodes) en un systeme Claude-native ou :
- L'utilisateur interagit uniquement via le chat (Claude Code / Claude Co-work)
- Le pipeline Python est un engine silencieux appele par Claude
- Les prompts des agents copywriting sont composes dynamiquement depuis le contexte client
- Le systeme supporte le batch multi-campagne avec budget et reprise sur erreur
- Un mode CLI avance reste disponible pour les power users

---

## 2. Decisions de design

| Question | Decision |
|----------|----------|
| Profil utilisateur | Mode conversation guidee (novice) + CLI avance (power user) |
| Methodologie | BYS-first — la methodo est le coeur, non-negociable |
| Canaux | Email + LinkedIn + Call |
| Source leads | Fichier JSON uniquement |
| Multi-campagne | Batch avec priorisation, budget API, et reprise sur erreur |
| Onboarding | Setup wizard conversationnel guide par Claude |
| Prompts | Dynamiques — composes par le Python engine depuis client.yaml + campaign.yaml + docs client |

---

## 3. Architecture

### 3.1 Vue d'ensemble

```
COUCHE CONVERSATION (4 agents .md, < 150 lignes chacun)
  bys-setup.md      — Onboarding, API keys, config
  bys-strategy.md   — Discovery, CAB-P, 10 ciblages
  bys-campaign.md   — Run pipeline (enrich → write → inject)
  bys-monitor.md    — Status, rapports, optimisation
        │
        │ appelle via Bash
        ▼
COUCHE ENGINE (Python CLI)
  python -m pipeline {enrich|write|inject|status|run}
  Entree : chemins fichiers + flags
  Sortie : JSON structure sur stdout, logs sur stderr
        │
        ▼
COUCHE SERVICES
  enricher.py    — Scrapingdog + RapidAPI LinkedIn
  copywriter.py  — Orchestre 4 agents Claude (analyst → strategist → copywriter → reviewer)
  injector.py    — Lemlist REST API
  scheduler.py   — Batch multi-campagne + budget tracking
        │
        ▼
COUCHE DATA
  clients/{name}_{date}/
    client.yaml · discovery.md · cab-p.md
    campaigns/C{01-10}_{signal}_{persona}_{geo}/
      campaign.yaml · ciblage.md · leads.json
      leads_enriched.json · emails.json · report.json
```

### 3.2 Separation des responsabilites

- **Agents .md** : UX conversationnelle, generation de fichiers config (YAML, MD), lancement de commandes
- **Python engine** : Execution lourde (API calls, concurrence, retry, post-processing). Zero logique UX.
- **Fichiers YAML/MD** : Contrat entre les deux couches. Source de verite.

---

## 4. Les 4 agents Claude Code

### 4.1 `bys-setup.md` (~100 lignes)

**Responsabilite** : Onboarding nouvel utilisateur.

**Flow** :
1. Verifie `.env.local` — API keys presentes (SCRAPINGDOG, RAPIDAPI, ANTHROPIC, LEMLIST)
2. Guide l'utilisateur pour configurer les keys manquantes
3. Cree le dossier client : `clients/{name}_{date}/`
4. Genere `client.yaml` depuis la conversation (nom, sender, email, budget)
5. Confirme setup complet, oriente vers `bys-strategy`

**Entrees** : Conversation utilisateur
**Sorties** : `.env.local` verifie, `clients/{name}_{date}/client.yaml`

### 4.2 `bys-strategy.md` (~120 lignes)

**Responsabilite** : Methodologie BYS — Discovery, CAB-P, 10 ciblages.

**Flow** :
1. Lit `client.yaml` et `templates/methodo/` pour contexte
2. Guide l'utilisateur pour ecrire `discovery.md` (questions conversationnelles)
3. Genere `cab-p.md` depuis le discovery
4. Propose 10 ciblages (signal x persona x geo), l'utilisateur valide/ajuste
5. Pour chaque campagne validee, genere :
   - `campaign.yaml` (tone, custom_rules, banned_words deduits automatiquement)
   - `ciblage.md` (brief detaille du ciblage)

**Entrees** : `client.yaml`, conversation utilisateur
**Sorties** : `discovery.md`, `cab-p.md`, `recap.md`, N x (`campaign.yaml` + `ciblage.md`)

**Deduction automatique du tone et des rules** :
- Claude analyse discovery + cab-p + ciblage pour deduire le ton adapte
- Les `custom_rules` sont specifiques au croisement signal/persona/geo
- Les `banned_words` combinent la liste BYS par defaut + mots specifiques au secteur

### 4.3 `bys-campaign.md` (~100 lignes)

**Responsabilite** : Lancer et superviser le pipeline.

**Flow** :
1. Lit `client.yaml` + liste les `campaign.yaml` disponibles
2. Propose les options : batch all, selection, ou une seule campagne
3. Lance `python -m pipeline run --client {name} --campaigns {list}`
4. Lit `report.json` pour afficher la progression
5. En cas d'erreur : diagnostique, propose solution, relance si besoin
6. En cas de succes : confirme l'injection Lemlist

**Entrees** : `client.yaml`, `campaign.yaml` (status != live)
**Sorties** : Commandes CLI, lecture des reports

### 4.4 `bys-monitor.md` (~80 lignes)

**Responsabilite** : Suivi post-lancement et optimisation.

**Flow** :
1. Lit les `report.json` de toutes les campagnes
2. Recupere stats Lemlist via MCP (`get_campaign_stats`)
3. Identifie les campagnes sous-performantes (open rate < 30%, reply rate < 3%)
4. Propose des ajustements : tone, ciblage, relance, A/B test
5. Peut relancer le pipeline `write` + `inject` sur une campagne avec rules ajustees

**Entrees** : `report.json`, stats Lemlist MCP
**Sorties** : Recommandations, modifications `campaign.yaml`, relance pipeline

---

## 5. Prompts dynamiques

### 5.1 Principe

Les prompts des 4 agents copywriting (analyst, strategist, copywriter, reviewer) ne sont plus hardcodes. Ils sont composes de :

1. **Socle BYS** (non-modifiable) — Le framework, les regles de ton, les interdits universels
2. **Contexte client** (injecte depuis les fichiers) — discovery.md, cab-p.md
3. **Contexte campagne** (injecte depuis campaign.yaml) — signal, persona, geo, tone, custom_rules, banned_words
4. **Donnees lead** (injectees a l'execution) — profil enrichi du lead

### 5.2 Implementation

```python
# pipeline/prompts.py

COPYWRITER_BASE = """..."""  # Socle BYS ~ 60 lignes

def build_copywriter_prompt(context: CampaignContext) -> str:
    return f"""{COPYWRITER_BASE}

## CONTEXTE CLIENT
{context.discovery}

## MATRICE CAB-P
{context.cab_p}

## CIBLAGE
Signal: {context.campaign.signal}
Persona: {context.campaign.persona}
Geo: {context.campaign.geo}

## TON
{context.campaign.tone}

## REGLES SPECIFIQUES
{chr(10).join(f'- {r}' for r in context.campaign.custom_rules)}

## MOTS INTERDITS
{chr(10).join(f'- {w}' for w in context.campaign.banned_words)}

## CANAUX ACTIFS
{', '.join(context.campaign.channels)}
"""
```

Meme pattern pour `build_analyst_prompt()`, `build_strategist_prompt()`, `build_reviewer_prompt()`.

### 5.3 Socles BYS (invariants)

Les socles contiennent les regles non-negociables de la methodo BYS :
- **Analyst** : Extraire les angles de personnalisation depuis le profil enrichi
- **Strategist** : Choisir l'angle, le hook, la sequence
- **Copywriter** : Ton conversationnel, email 1 = 100% sur eux, email 2 = look-a-like subtil, email 3 = au revoir humain, linkedin invite decontractee, DM = question, call script naturel
- **Reviewer** : Score 1-10, red flags (jargon, CTA email 1, chiffres generiques), green flags (specifique, look-a-like credible)

---

## 6. Flow de donnees JSON

### 6.1 leads.json (input utilisateur)

```json
[
  {
    "firstName": "Marie",
    "lastName": "Dupont",
    "email": "marie@acme.fr",
    "companyName": "Acme SAS",
    "linkedinUrl": "https://linkedin.com/in/mariedupont"
  }
]
```

Champs obligatoires : `firstName`, `lastName`, `companyName`.
Champs optionnels : `email`, `linkedinUrl`, `phone`, `jobTitle`, tout champ custom.

**Note** : `email` est optionnel. Si absent, l'injector utilise le flag `findEmail=true` de Lemlist pour trouver l'email automatiquement. Si `linkedinUrl` est absent, le canal LinkedIn est desactive pour ce lead.

### 6.2 leads_enriched.json (sortie enrich)

```json
[
  {
    "firstName": "Marie",
    "lastName": "Dupont",
    "email": "marie@acme.fr",
    "companyName": "Acme SAS",
    "linkedinUrl": "https://linkedin.com/in/mariedupont",
    "headline": "CRO @ Acme SAS",
    "summary": "10 ans d'experience en revenue ops...",
    "experience": [...],
    "company_description": "Acme SAS est un editeur SaaS...",
    "enrichment_source": "rapidapi",
    "enrichment_date": "2026-03-24T14:00:00Z"
  }
]
```

### 6.3 emails.json (sortie write)

```json
[
  {
    "leadEmail": "marie@acme.fr",
    "email1Subject": "...",
    "email1Body": "...",
    "email2Subject": "...",
    "email2Body": "...",
    "email3Subject": "...",
    "email3Body": "...",
    "linkedinInvite": "...",
    "linkedinDm": "...",
    "callScript": "...",
    "reviewScore": 8,
    "reviewNotes": "...",
    "model": "claude-sonnet-4-6",
    "cost_usd": 0.07,
    "generated_at": "2026-03-24T14:30:00Z"
  }
]
```

**Nouveau champ** : `callScript` — script d'appel personnalise pour le canal call.
Le call script est genere par l'agent **Copywriter** (pas un 5eme agent). Le tool schema `EMAILS_TOOL` est etendu avec un champ `callScript`. Le script est un texte court (5-8 phrases) avec : accroche, contexte, question ouverte. Meme ton conversationnel que les emails.

### 6.4 report.json (sortie inject + status global)

```json
{
  "campaign_id": "C04_techchange_cro_fr",
  "status": "live",
  "lemlist_campaign_id": "cam_xxx",
  "leads_total": 40,
  "leads_enriched": 40,
  "leads_written": 40,
  "leads_injected": 38,
  "leads_skipped": 2,
  "errors": [],
  "cost_enrich_usd": 2.00,
  "cost_write_usd": 2.80,
  "cost_total_usd": 4.80,
  "started_at": "2026-03-24T14:00:00Z",
  "completed_at": "2026-03-24T14:35:00Z"
}
```

---

## 7. Batch orchestration et budget

### 7.1 Scheduler

```python
# pipeline/scheduler.py

class BatchScheduler:
    """Orchestre plusieurs campagnes avec budget et reprise."""

    def run_batch(self, client_path: str, campaigns: list[str] | None):
        # 1. Lit client.yaml → budget total
        # 2. Liste campaign.yaml avec status != "live"
        # 3. Trie : draft → enriched → written (reprend ou ca s'est arrete)
        # 4. Pour chaque campagne :
        #    - Estime le cout (nb leads x cout moyen par lead)
        #    - Si budget restant suffisant → lance
        #    - Si budget depasse → skip avec raison
        # 5. Genere report_batch.json
```

### 7.2 Reprise sur erreur

Chaque etape met a jour le `status` dans `campaign.yaml` :
- `draft` → pret a enrichir
- `enriched` → leads enrichis, pret a ecrire
- `written` → emails generes, pret a injecter
- `injected` → leads injectes dans Lemlist
- `live` → campagne active
- `error` → erreur a une etape, details dans `report.json`

La reprise est automatique : si status = `enriched`, le pipeline saute l'enrichissement et passe directement au write.

### 7.3 report_batch.json

```json
{
  "client": "acme_2026-03-24",
  "campaigns_completed": ["C01", "C04"],
  "campaigns_failed": ["C02"],
  "campaigns_skipped": ["C03", "C05"],
  "budget_total": 50.00,
  "budget_used": 34.20,
  "budget_remaining": 15.80,
  "started_at": "2026-03-24T14:00:00Z",
  "completed_at": "2026-03-24T15:20:00Z"
}
```

---

## 8. Post-processing

### 8.1 Pipeline de validation

Apres chaque generation copywriting, avant injection :

```python
# pipeline/postprocess.py

def postprocess(emails: list[dict], campaign: CampaignConfig) -> list[dict]:
    for email in emails:
        for field in TEXT_FIELDS:
            # 1. Banned words replacement
            text = replace_banned_words(email[field], campaign.banned_words)
            # 2. Dash removal (em dash, en dash)
            text = remove_dashes(text)
            # 3. Variable resolution (prenom, nom, entreprise)
            text = resolve_variables(text, email)
            # 4. Validation (longueur, encodage, chars speciaux)
            validate_field(text, field)
            email[field] = text
    return emails
```

### 8.2 Banned words par defaut (socle BYS)

```python
BYS_BANNED_WORDS = {
    "outbound": "prospection",
    "pipe": "flux de prospects",
    "pipeline": "processus",
    "stack": "outils",
    "SDR": "commercial",
    "scale-up": "croissance",
    "growth": "developpement",
    "structurer": "organiser",
}
```

Fusionnes avec les `banned_words` du `campaign.yaml`.

---

## 8b. Schema YAML

### client.yaml (complet)

```yaml
name: "Acme Corp"                    # Nom du client
date: "2026-03-24"                   # Date de creation
sender_name: "Jean Dupont"          # Nom de l'expediteur
sender_email: "jean@acme.com"       # Email expediteur
sender_title: "CEO"                  # Titre expediteur

lemlist_campaign_prefix: "acme"     # Prefixe des campagnes Lemlist

model: "claude-sonnet-4-6"          # Modele Claude par defaut
total_budget_usd: 50.00             # Budget max pour toutes les campagnes

enrichment:
  providers: ["scrapingdog", "rapidapi_linkedin"]
  concurrency: 10                   # Appels paralleles par provider
```

### campaign.yaml (complet)

```yaml
campaign_id: "C01"
signal: "techchange"                # Signal de ciblage
persona: "cro"                      # Persona cible
geo: "fr"                           # Zone geographique
status: "draft"                     # draft|enriched|written|injected|live|error

channels:
  - email                           # 3 emails sequence
  - linkedin                        # invite + DM
  - call                            # script d'appel

tone: "conversationnel, pair-a-pair, curieux"

custom_rules:
  - "Pas de jargon technique cloud/infra"
  - "Mentionner le secteur retail du prospect"
  - "Look-a-like email 2 : secteur e-commerce"

banned_words:                       # Fusionnes avec BYS_BANNED_WORDS
  - "digitalisation"
  - "transformation"

model: "claude-sonnet-4-6"          # Override le client.yaml si besoin
concurrency: 10                     # Parallisme copywriting

# Rempli automatiquement apres chaque etape
last_step_at: null
error_message: null
```

---

## 8c. Cout par lead et budget

### Formule de cout

```
Cout enrichissement par lead :
  - Scrapingdog Google SERP : 5 credits = ~$0.005
  - RapidAPI LinkedIn :       1 credit  = ~$0.01
  Total enrich : ~$0.015 / lead

Cout copywriting par lead :
  - Analyst (sonnet)    : ~800 input + 300 output tokens  = ~$0.004
  - Strategist (sonnet) : ~1200 input + 400 output tokens = ~$0.006
  - Copywriter (sonnet) : ~1500 input + 800 output tokens = ~$0.010
  - Reviewer (sonnet)   : ~2000 input + 400 output tokens = ~$0.008
  - Rewrite (si score < 7, ~20% des cas) :                = ~$0.004
  Total write : ~$0.030 / lead (sonnet), ~$0.30 / lead (opus)

Cout injection : gratuit (API Lemlist incluse dans l'abonnement)

TOTAL ESTIME :
  - Sonnet : ~$0.05 / lead
  - Opus   : ~$0.35 / lead
```

### Budget check dans le scheduler

```python
COST_PER_LEAD = {
    "claude-sonnet-4-6": 0.05,
    "claude-opus-4-6": 0.35,
}

def estimate_campaign_cost(campaign_path: str) -> float:
    leads = load_json(campaign_path / "leads.json")
    model = load_yaml(campaign_path / "campaign.yaml")["model"]
    return len(leads) * COST_PER_LEAD[model]
```

---

## 8d. Strategie de split des prompts

Les prompts actuels dans `agents.py` sont monolithiques (~45-120 lignes chacun). Voici le decoupage :

### Ce qui reste dans le socle BYS (immutable, dans `prompts.py`)

| Agent | Contenu du socle | ~Lignes |
|-------|-----------------|---------|
| Analyst | Role, methode d'analyse (profil, entreprise, actualite), format de sortie brief | 30 |
| Strategist | Role, criteres de choix d'angle, format de sortie strategie | 25 |
| Copywriter | Role, regles de ton BYS (email 1 = sur eux, email 2 = look-a-like, email 3 = au revoir, linkedin = decontracte, call = naturel), format INTERDIT universel | 60 |
| Reviewer | Role, grille de scoring, red flags, green flags, format de sortie review | 35 |

### Ce qui est injecte dynamiquement (depuis les fichiers client)

| Section | Source |
|---------|--------|
| Contexte client | `discovery.md` (texte brut) |
| Matrice CAB-P | `cab-p.md` (texte brut) |
| Signal / Persona / Geo | `campaign.yaml` |
| Ton specifique | `campaign.yaml → tone` |
| Regles custom | `campaign.yaml → custom_rules` |
| Mots interdits | `campaign.yaml → banned_words` + `BYS_BANNED_WORDS` |
| Canaux actifs | `campaign.yaml → channels` |

Le socle ne change JAMAIS entre clients. Seul le contexte injecte varie.

---

## 9. Structure dossiers

```
connect_lemlist_claude_for_outbound/
├── README.md
├── CLAUDE.md
├── requirements.txt
├── .env.example
│
├── agents/
│   ├── bys-setup.md
│   ├── bys-strategy.md
│   ├── bys-campaign.md
│   └── bys-monitor.md
│
├── pipeline/
│   ├── __init__.py
│   ├── __main__.py          # CLI Typer
│   ├── config.py            # Lit client.yaml + campaign.yaml
│   ├── models.py            # Pydantic models
│   ├── prompts.py           # Socle BYS + composition dynamique
│   ├── enricher.py          # Scrapingdog + RapidAPI
│   ├── copywriter.py        # Orchestration 4 agents
│   ├── agents.py            # Run analyst/strategist/copywriter/reviewer
│   ├── injector.py          # Lemlist REST API
│   ├── scheduler.py         # Batch multi-campagne + budget
│   ├── postprocess.py       # Banned words, dashes, validation
│   └── utils.py             # RateLimiter, ProgressTracker, log()
│
├── templates/
│   ├── client.yaml.example
│   ├── campaign.yaml.example
│   ├── leads.json.example
│   └── methodo/
│       ├── discovery-guide.md
│       ├── cab-p-guide.md
│       └── ciblage-guide.md
│
└── clients/                 # .gitignore
    └── {name}_{date}/
        ├── client.yaml
        ├── discovery.md
        ├── cab-p.md
        ├── recap.md
        └── campaigns/
            └── C{01-10}_{signal}_{persona}_{geo}/
                ├── campaign.yaml
                ├── ciblage.md
                ├── leads.json
                ├── leads_enriched.json
                ├── emails.json
                └── report.json
```

---

## 10. CLI Python (mode power user)

```bash
# Commandes atomiques
python -m pipeline enrich --campaign clients/acme_2026-03-24/campaigns/C01_techchange_cro_fr
python -m pipeline write  --campaign clients/acme_2026-03-24/campaigns/C01_techchange_cro_fr
python -m pipeline inject --campaign clients/acme_2026-03-24/campaigns/C01_techchange_cro_fr
python -m pipeline status --client clients/acme_2026-03-24

# Batch
python -m pipeline run --client clients/acme_2026-03-24 --campaigns all
python -m pipeline run --client clients/acme_2026-03-24 --campaigns C01,C04,C07

# Reprise
python -m pipeline run --client clients/acme_2026-03-24 --campaigns C02  # reprend au bon status
```

**Sortie CLI** : JSON sur stdout (pour que Claude puisse parser), logs sur stderr (pour que l'humain puisse lire).

---

## 11. Migration depuis l'existant

### Ce qui est conserve (refactorise)
- `pipeline/enricher.py` — refactorise pour lire `campaign.yaml` au lieu de `config.py`
- `pipeline/copywriter.py` — refactorise pour recevoir les prompts depuis `prompts.py`
- `pipeline/injector.py` — refactorise pour lire `campaign.yaml`, post-processing extrait dans `postprocess.py`
- `pipeline/utils.py` — conserve tel quel
- `pipeline/models.py` — enrichi avec Pydantic models pour YAML configs + champ `email` optionnel sur Lead
- `pipeline/agents.py` — refactorise : les system prompts sont supprimes (migres dans `prompts.py`), les fonctions `run_analyst()` etc. restent mais appellent `prompts.build_*_prompt()` pour obtenir le prompt

### Ce qui est cree
- `pipeline/prompts.py` — socle BYS + composition dynamique
- `pipeline/postprocess.py` — extrait de l'injector actuel (`_resolve_content()` + banned words)
- `pipeline/scheduler.py` — nouveau, batch + budget
- `agents/bys-setup.md` — nouveau
- `agents/bys-strategy.md` — nouveau
- `agents/bys-campaign.md` — nouveau
- `agents/bys-monitor.md` — nouveau
- `templates/` — nouveau, guides methodo + exemples

### Ce qui est supprime
- `pipeline/orchestrator.py` — remplace par `scheduler.py` + nouveau `__main__.py`
- `Mandatory_to_read_before_anything.md` — eclate dans agents/ + templates/methodo/
- `agents/bys-copywriter.md` (ancien) — remplace par le systeme dynamique dans `prompts.py`
- `agents/bys-enricher-firecrawl.md` — obsolete (le pipeline utilise Scrapingdog, jamais Firecrawl)
- `agents/bys-enricher-rapidapi.md` — absorbe dans le pipeline `enricher.py`
- `agents/bys-launcher.md` — remplace par `bys-campaign.md`
- `agents/bys-targeting.md` — remplace par `bys-strategy.md`
- Prompts hardcodes dans `agents.py` — migres dans `prompts.py`

### Renommages de fichiers (breaking changes)
- `emails_personalized.json` → `emails.json`
- `injection_report.json` → `report.json`
- CLI flag `--campaign-dir` → `--campaign` (chemin) ou `--client` + `--campaigns` (batch)

### Nouvelles dependances
- `pyyaml` — parsing des fichiers `client.yaml` et `campaign.yaml`
- `pydantic` — validation schemas (deja implicitement utilise via dataclasses, on formalise)

---

## 12. Phase C (futur) — Plugin Claude Code

Une fois l'approche B stabilisee, le systeme sera empaquete en plugin Claude Code :
- Skills : `/bys-setup`, `/bys-discovery`, `/bys-run`, `/bys-status`
- Installation : `claude plugins install bys-outbound`
- Les agents .md deviennent des skills .md
- Le pipeline Python est embarque comme dependance

Cette phase n'est pas dans le scope actuel.

---

## 13. Notes d'implementation

### email2Subject et thread trick

Le `email2Subject` utilise le format `Re: {email1Subject}` pour simuler un thread (trick Lemlist). L'injector doit injecter `email2Subject` comme variable Lemlist custom. Actuellement le code ne l'injecte pas — a corriger dans le refactoring.

### recap.md

Le fichier `recap.md` (resume du discovery) est conserve dans la structure client. Il est genere par `bys-strategy.md` apres le discovery comme synthese courte. Il est injecte dans les prompts des agents copywriting comme complement du discovery (version condensee).

### Fallback monitoring sans MCP

Si le MCP Lemlist n'est pas disponible (CLI mode, MCP down), `bys-monitor.md` peut utiliser l'API REST Lemlist directement via le Python engine : `python -m pipeline status --client {name} --stats`. Le scheduler lit les stats via l'API REST comme fallback.
