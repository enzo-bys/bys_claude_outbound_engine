# BYS Outbound Engine Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the monolithic Python pipeline into a Claude-native system with 4 conversation agents, dynamic prompts, batch orchestration, and YAML-based configuration.

**Architecture:** 4 Claude Code agents (.md) handle UX conversation. Python engine handles execution (enrich/write/inject). YAML files (client.yaml, campaign.yaml) are the contract between the two layers. Prompts are composed dynamically from BYS base + client context.

**Tech Stack:** Python 3.11+, anthropic SDK, aiohttp, typer, pyyaml, pydantic, Claude Code agents (.md)

**Spec:** `docs/superpowers/specs/2026-03-24-outbound-engine-redesign.md`

---

## File Map

### New files to create
| File | Responsibility |
|------|---------------|
| `pipeline/prompts.py` | BYS base prompts (immutable) + `build_*_prompt()` dynamic composition |
| `pipeline/postprocess.py` | Banned words replacement, dash removal, variable resolution, validation |
| `pipeline/scheduler.py` | Batch multi-campaign orchestration, budget tracking, resume-on-error |
| `templates/client.yaml.example` | Template for client configuration |
| `templates/campaign.yaml.example` | Template for campaign configuration |
| `templates/leads.json.example` | Template for leads input format |
| `templates/methodo/discovery-guide.md` | Guide for running discovery phase |
| `templates/methodo/cab-p-guide.md` | Guide for CAB-P matrix |
| `templates/methodo/ciblage-guide.md` | Guide for creating targeted campaigns |
| `agents/bys-setup.md` | Onboarding agent — API keys, client folder, client.yaml |
| `agents/bys-strategy.md` | Strategy agent — discovery, CAB-P, 10 ciblages |
| `agents/bys-campaign.md` | Campaign agent — launch pipeline, monitor progress |
| `agents/bys-monitor.md` | Monitor agent — stats, optimization, relaunch |
| `.env.example` | Template for environment variables |
| `README.md` | Quick start guide for novice users |

### Existing files to modify
| File | Changes |
|------|---------|
| `pipeline/models.py` | Add Pydantic models for YAML configs, `email` optional on Lead, `callScript` on PersonalizedSections, new `CampaignConfig`/`ClientConfig` |
| `pipeline/agents.py` | Remove hardcoded system prompts, import from `prompts.py`, add `callScript` to tool schema |
| `pipeline/config.py` | Add YAML loading helpers, keep .env.local for API keys only |
| `pipeline/__main__.py` | New CLI: `--campaign` for single, `--client` + `--campaigns` for batch, add `status` command |
| `pipeline/copywriter.py` | Use new output filename `emails.json`, pass `CampaignConfig` to agents |
| `pipeline/injector.py` | Move `_resolve_content()` to `postprocess.py`, add `email2Subject` injection, rename output to `report.json` |
| `pipeline/enricher.py` | Accept `CampaignConfig` for provider/concurrency settings |
| `requirements.txt` | Add `pyyaml`, `pydantic` |

### Files to delete
| File | Reason |
|------|--------|
| `pipeline/orchestrator.py` | Replaced by `scheduler.py` + new `__main__.py` |
| `agents/bys-copywriter.md` | Replaced by dynamic prompts in `prompts.py` |
| `agents/bys-enricher-firecrawl.md` | Obsolete (pipeline uses Scrapingdog) |
| `agents/bys-enricher-rapidapi.md` | Absorbed into `enricher.py` |
| `agents/bys-launcher.md` | Replaced by `bys-campaign.md` |
| `agents/bys-targeting.md` | Replaced by `bys-strategy.md` |

---

## Task 1: Add dependencies and YAML config models

**Files:**
- Modify: `requirements.txt`
- Modify: `pipeline/models.py`

- [ ] **Step 1: Add pyyaml and pydantic to requirements.txt**

```
anthropic>=0.40.0
aiohttp>=3.9.0
typer>=0.12.0
python-dotenv>=1.0.0
pyyaml>=6.0
pydantic>=2.0
```

- [ ] **Step 2: Install new dependencies**

Run: `pip install pyyaml pydantic`

- [ ] **Step 3: Add Pydantic models to `pipeline/models.py`**

Add these imports at the top:

```python
import yaml
from pydantic import BaseModel, Field
```

Add these Pydantic models after the existing dataclasses:

```python
class ClientConfig(BaseModel):
    """Client-level configuration from client.yaml."""
    name: str
    date: str
    sender_name: str = ""
    sender_email: str = ""
    sender_title: str = ""
    lemlist_campaign_prefix: str = ""
    model: str = "claude-sonnet-4-6"
    total_budget_usd: float = 50.0
    enrichment: dict = Field(default_factory=lambda: {
        "providers": ["scrapingdog", "rapidapi_linkedin"],
        "concurrency": 10,
    })

    @classmethod
    def load(cls, client_dir: str | Path) -> ClientConfig:
        path = Path(client_dir) / "client.yaml"
        if not path.exists():
            raise FileNotFoundError(f"client.yaml not found in {client_dir}")
        with open(path) as f:
            return cls(**yaml.safe_load(f))


class CampaignConfig(BaseModel):
    """Campaign-level configuration from campaign.yaml."""
    campaign_id: str
    signal: str = ""
    persona: str = ""
    geo: str = ""
    status: str = "draft"  # draft|enriched|written|injected|live|error
    channels: list[str] = Field(default_factory=lambda: ["email", "linkedin"])
    tone: str = "conversationnel, pair-a-pair, curieux"
    custom_rules: list[str] = Field(default_factory=list)
    banned_words: list[str] = Field(default_factory=list)
    model: str = "claude-sonnet-4-6"
    concurrency: int = 10
    last_step_at: str | None = None
    error_message: str | None = None

    @classmethod
    def load(cls, campaign_dir: str | Path) -> CampaignConfig:
        path = Path(campaign_dir) / "campaign.yaml"
        if not path.exists():
            raise FileNotFoundError(f"campaign.yaml not found in {campaign_dir}")
        with open(path) as f:
            return cls(**yaml.safe_load(f))

    def save(self, campaign_dir: str | Path) -> None:
        path = Path(campaign_dir) / "campaign.yaml"
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, allow_unicode=True)
```

- [ ] **Step 4: Add `email` field to Lead and `callScript` to PersonalizedSections**

In the `Lead` dataclass, add after `linkedinUrl`:
```python
    email: str = ""
```

In the `PersonalizedSections` dataclass, add after `linkedinDm`:
```python
    callScript: str = ""          # script d'appel personnalise
```

- [ ] **Step 5: Update CampaignContext to load YAML configs**

Add `campaign_config` and `client_config` fields to `CampaignContext`:

```python
    campaign_config: CampaignConfig | None = None
    client_config: ClientConfig | None = None
```

In `CampaignContext.load()`, after loading existing files, add:

```python
        # Load YAML configs (optional — backward compatible)
        campaign_config = None
        campaign_yaml = cdir / "campaign.yaml"
        if campaign_yaml.exists():
            campaign_config = CampaignConfig.load(cdir)

        client_config = None
        client_yaml = client_dir / "client.yaml"
        if client_yaml.exists():
            client_config = ClientConfig.load(client_dir)
```

And add them to the return `cls(...)`.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt pipeline/models.py
git commit -m "feat: add YAML config models (ClientConfig, CampaignConfig) and new fields"
```

---

## Task 2: Create `pipeline/prompts.py` — dynamic prompt composition

**Files:**
- Create: `pipeline/prompts.py`

- [ ] **Step 1: Create prompts.py with BYS base prompts**

Extract the 4 system prompts from `pipeline/agents.py` into `pipeline/prompts.py` as base constants, then add `build_*_prompt()` functions that compose them dynamically.

```python
"""BYS base prompts (immutable) + dynamic composition from client context."""

from __future__ import annotations
from pipeline.models import CampaignContext


# ---------------------------------------------------------------------------
# BYS Base Prompts (immutable — these never change between clients)
# ---------------------------------------------------------------------------

ANALYST_BASE = """Tu es un analyste de leads B2B. Ton role est de comprendre QUI est cette personne et CE QUE VIT sa boite.

Tu recois des donnees brutes (profil LinkedIn, actualites Google, contexte campagne) et tu produis une analyse structuree.

Regles :
- Identifie le VRAI secteur de l'entreprise (pas juste "SaaS B2B" mais le metier concret)
- Comprends le MOMENT que vit l'entreprise (fusion, levee, recrutement, expansion...)
- Raconte l'HISTOIRE de la personne (transitions, promotions, ce qui la rend unique)
- Trouve le SWEET SPOT : l'intersection personne x moment
- Decris le QUOTIDIEN reel de cette personne dans son role actuel

Sois factuel. Utilise uniquement les donnees fournies. Ne fabrique pas d'informations."""


STRATEGIST_BASE = """Tu es un stratege de communication B2B. Tu decides de l'angle, du pain a adresser, et du gap de curiosite a creer.

Tu connais la psychologie de la curiosite (Loewenstein, 1994) :
- Information gap : le cerveau detecte un ecart entre ce qu'il sait et ce qu'il voudrait savoir
- Effet Zeigarnik : les boucles ouvertes creent une tension cognitive
- Pattern break : l'inattendu capte l'attention

HIERARCHIE DES ANGLES (du plus fort au plus faible) :
1. PARCOURS + MOMENTUM : transition/promo du lead RELIEE a un moment de l'entreprise
2. ROLE + NEWS : ce que vit cette personne dans son poste vu l'actualite
3. PARCOURS SEUL : transition de role, changement secteur, promotion
4. COMPETENCES + CONTEXTE : skill specifique + contexte actuel
5. NEWS SEULE : actualite entreprise sans lien personnel (dernier recours)

Choisis TOUJOURS l'angle le plus haut possible dans la hierarchie.
La question cle doit etre OUVERTE (pas oui/non), SPECIFIQUE (pas generique), et liee au QUOTIDIEN du lead."""


COPYWRITER_BASE = """Tu es un humain qui ecrit a un autre humain. Pas un commercial. Pas un consultant. Pas une IA.

Tu recois un brief (qui est cette personne) et une strategie (quel angle, quel gap de curiosite). Tu ecris les emails et messages LinkedIn.

STYLE = MESSAGE ENTRE HUMAINS
Ecris comme si tu envoyais un message a quelqu'un que tu as croise a une conference. Decontracte mais respectueux.
Phrases courtes. Paragraphes de 1-2 phrases. Retours a la ligne comme dans un iMessage.
JAMAIS de tiret (ni \u2014 ni \u2013 ni -). Pas de liste a puces.

TON = CONVERSATION ENTRE PAIRS
Tu parles comme quelqu'un du metier qui echange avec un pair. Pas un vendeur, pas un consultant.
L'email 1 = curiosite sincere, pas de pitch.
L'email 2 = tu glisses subtilement de la preuve sociale et des chiffres. Exemples :
  - "un CRO dans la cyber avec qui j'echangeais recemment avait le meme constat"
  - "une boite dans l'evenementiel a peu pres de votre taille a regle ca en 6 semaines"
  - des chiffres CREDIBLES et SPECIFIQUES (pas "+30%" generique mais "il est passe de 4% a 11% de taux de reponse")
  - du LOOK-A-LIKE : toujours citer un cas dans le MEME secteur ou une situation SIMILAIRE
L'email 3 = au revoir humain.
Le DM LinkedIn = decontracte, une question, rien d'autre.

La preuve sociale doit sonner comme une anecdote naturelle, pas comme un pitch marketing.
JAMAIS de "nos clients", "on accompagne", "on a aide". Plutot "quelqu'un dans une situation proche", "un CRO que je connais dans le meme secteur".

STRUCTURE :
Email 1 : 100% sur EUX. Tu montres que tu as compris quelque chose de specifique sur leur situation. Tu finis par une question ouverte qui montre ta curiosite reelle. Pas de presentation, pas de pitch. 50-80 mots.
Email 2 : Tu glisses un look-a-like (cas similaire dans leur secteur ou situation) avec un chiffre credible et specifique. Ca doit sonner comme "tiens je repensais a votre truc, ca me rappelle un cas..." pas comme un pitch. 50-70 mots.
Email 3 : 2-3 phrases. Humain. Pas de "je ne vais pas insister". Juste un mot sympa et c'est tout. 20-40 mots.
LinkedIn invite : Max 12 mots, comme un texto.
LinkedIn DM : Le message le plus decontracte. Une question sincere, rien d'autre. 20-40 mots.

INTERDIT :
- "On aide des..." / "Nous accompagnons..." / "On a construit..."
- "Ca vaut X minutes ?" / "Un echange ?" / "Un call ?" dans l'email 1
- "+30%", "2x" generiques sans contexte. MAIS un chiffre precis dans un look-a-like email 2 est OK (ex: "il est passe de 4% a 11%")
- "Question directe :", "Curiosite sincere :", "Vraie question :"
- Toute forme de pitch deguise en question dans l'email 1

Chaque lead est unique. Pense chaque email en silo.
Les emails commencent par le PRENOM REEL du lead (ex: "Julien,"), suivi d'une virgule et retour a la ligne.
JAMAIS de variable type {{firstName}} ou {{companyName}}. Ecris le vrai prenom, le vrai nom de boite.
JAMAIS de signature (pas de prenom de l'expediteur). La signature est geree automatiquement.
JAMAIS de tiret long ou court. Utilise des virgules, points, parentheses.
Pas de formule de politesse."""


REVIEWER_BASE = """Tu es un expert en psychologie de la persuasion et en cold email B2B.

Tu evalues des emails selon 4 criteres neuroscientifiques :

1. PERTINENCE PERSONNELLE (0-3) : Est-ce que ca parle de CETTE personne specifiquement ?
   0 = generique, pourrait etre envoye a n'importe qui
   1 = mentionne le nom/l'entreprise mais rien de specifique
   2 = reference au role ou au secteur
   3 = reference au parcours, a une transition, a un moment precis de cette personne

2. INFORMATION GAP (0-3) : Est-ce que ca cree une question non resolue ?
   0 = aucune tension cognitive
   1 = question fermee (oui/non) sans profondeur
   2 = question ouverte mais generique
   3 = question specifique au quotidien du lead qui force a reflechir

3. PATTERN BREAK (0-2) : Est-ce que ca sort du bruit ?
   0 = ressemble a un cold email classique
   1 = un element inattendu
   2 = le lead ne peut pas penser "encore un email de prospection"

4. NATUREL (0-2) : Est-ce que ca sonne comme un humain qui s'interesse sincerement ?
   0 = ton vendeur, pushy, "ca vaut 15 min ?", chiffres marketing, pitch deguise
   1 = correct mais encore un peu "commercial"
   2 = on dirait un vrai message d'un pair curieux, zero pression

RED FLAGS (score naturel = 0 automatiquement) :
- "On aide des..." / "Nos clients..." / "on accompagne..."
- CTA dans l'email 1 ("ca vaut X min ?", "un echange ?")
- Chiffres GENERIQUES (+30%, 2x) sans contexte sectoriel. Les chiffres SPECIFIQUES dans un look-a-like sont OK (ex: "passe de 4% a 11%")
- Mots : "outbound", "pipe", "pipeline", "stack", "SDR", "structurer"
- "Question directe :", "Curiosite sincere :"
- Preuve sociale qui sonne comme un pitch marketing. MAIS un look-a-like subtil dans l'email 2 est ATTENDU et positif.

Sois exigeant. Un 7/10 = correct. Un 9/10 = exceptionnel.
Si le total est < 7, donne un feedback PRECIS et ACTIONNABLE pour ameliorer."""


# ---------------------------------------------------------------------------
# BYS Banned Words (immutable defaults)
# ---------------------------------------------------------------------------

BYS_BANNED_WORDS: dict[str, str] = {
    "outbound": "prospection",
    "pipe": "flux de prospects",
    "pipeline": "processus",
    "stack": "outils",
    "SDR": "commercial",
    "scale-up": "croissance",
    "growth": "developpement",
    "structurer": "organiser",
}


# ---------------------------------------------------------------------------
# Dynamic prompt composition
# ---------------------------------------------------------------------------

def _inject_context(base: str, ctx: CampaignContext) -> str:
    """Append dynamic context from client files and campaign.yaml to a base prompt."""
    parts = [base]

    if ctx.discovery:
        parts.append(f"\n\n## CONTEXTE CLIENT\n{ctx.discovery[:1500]}")

    if ctx.cab_p:
        parts.append(f"\n\n## MATRICE CAB-P\n{ctx.cab_p[:1000]}")

    cfg = ctx.campaign_config
    if cfg:
        parts.append(f"\n\n## CIBLAGE\nSignal: {cfg.signal}\nPersona: {cfg.persona}\nGeo: {cfg.geo}")
        parts.append(f"\n\n## TON\n{cfg.tone}")

        if cfg.custom_rules:
            rules = "\n".join(f"- {r}" for r in cfg.custom_rules)
            parts.append(f"\n\n## REGLES SPECIFIQUES\n{rules}")

        # Merge BYS banned words + campaign banned words
        all_banned = list(BYS_BANNED_WORDS.keys()) + cfg.banned_words
        if all_banned:
            words = "\n".join(f"- {w}" for w in all_banned)
            parts.append(f"\n\n## MOTS INTERDITS\n{words}")

        if cfg.channels:
            parts.append(f"\n\n## CANAUX ACTIFS\n{', '.join(cfg.channels)}")

        # Add call script instruction if call channel is active
        if "call" in cfg.channels:
            parts.append("\n\nSi le canal 'call' est actif, genere aussi un callScript : texte court (5-8 phrases) avec accroche, contexte, question ouverte. Meme ton conversationnel.")

    # Add geo-specific rules
    if cfg and cfg.geo:
        geo = cfg.geo.lower()
        if geo in ("fr", "france"):
            parts.append("\n\nFrancais naturel. Vouvoiement.")
        elif geo in ("be", "belgique"):
            parts.append("\n\nFrancais naturel. Vouvoiement. Pas de references franco-francaises.")
        elif geo in ("us", "uk", "en"):
            parts.append("\n\nEnglish. Professional but casual.")

    return "\n".join(parts)


def build_analyst_prompt(ctx: CampaignContext) -> str:
    """Compose analyst system prompt from BYS base + client context."""
    return _inject_context(ANALYST_BASE, ctx)


def build_strategist_prompt(ctx: CampaignContext) -> str:
    """Compose strategist system prompt from BYS base + client context."""
    return _inject_context(STRATEGIST_BASE, ctx)


def build_copywriter_prompt(ctx: CampaignContext) -> str:
    """Compose copywriter system prompt from BYS base + client context."""
    return _inject_context(COPYWRITER_BASE, ctx)


def build_reviewer_prompt(ctx: CampaignContext) -> str:
    """Compose reviewer system prompt from BYS base + client context."""
    return _inject_context(REVIEWER_BASE, ctx)
```

- [ ] **Step 2: Commit**

```bash
git add pipeline/prompts.py
git commit -m "feat: add prompts.py with BYS base prompts and dynamic composition"
```

---

## Task 3: Create `pipeline/postprocess.py` — post-processing pipeline

**Files:**
- Create: `pipeline/postprocess.py`

- [ ] **Step 1: Create postprocess.py**

Extract `_resolve_content()` from `injector.py` and add banned words replacement + validation:

```python
"""Post-processing pipeline: banned words, dash removal, variable resolution, validation."""

from __future__ import annotations
import re

from pipeline.models import CampaignConfig
from pipeline.prompts import BYS_BANNED_WORDS
from pipeline.utils import log


TEXT_FIELDS = [
    "email1Subject", "email1Body",
    "email2Subject", "email2Body",
    "email3Subject", "email3Body",
    "linkedinInvite", "linkedinDm",
    "callScript",
]


def replace_banned_words(text: str, campaign_banned: list[str] | None = None) -> str:
    """Replace BYS banned words + campaign-specific banned words."""
    result = text
    for word, replacement in BYS_BANNED_WORDS.items():
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        result = pattern.sub(replacement, result)
    # Campaign-specific banned words (no replacement, just flag)
    if campaign_banned:
        for word in campaign_banned:
            if word.lower() in result.lower():
                log(f"Warning: banned word '{word}' found in content", "warn")
    return result


def remove_dashes(text: str) -> str:
    """Remove em dashes and en dashes, replace with commas."""
    result = text
    result = result.replace(" \u2014 ", ", ")
    result = result.replace(" \u2013 ", ", ")
    result = result.replace("\u2014", ",")
    result = result.replace("\u2013", ",")
    return result


def resolve_variables(text: str, lead_data: dict) -> str:
    """Replace {{variable}} placeholders with actual values."""
    result = text
    result = result.replace("{{firstName}}", lead_data.get("firstName", ""))
    result = result.replace("{{lastName}}", lead_data.get("lastName", ""))
    result = result.replace("{{companyName}}", lead_data.get("companyName", ""))
    return result


def validate_field(text: str, field_name: str) -> None:
    """Validate a text field (log warnings, don't block)."""
    if not text:
        return
    if len(text) > 5000:
        log(f"Field '{field_name}' exceeds 5000 chars ({len(text)})", "warn")
    if "{{" in text:
        log(f"Field '{field_name}' still contains unresolved variables", "warn")


def postprocess_emails(
    emails: list[dict],
    campaign_config: CampaignConfig | None = None,
) -> list[dict]:
    """Run full post-processing pipeline on generated emails."""
    banned = campaign_config.banned_words if campaign_config else []

    for email in emails:
        for field in TEXT_FIELDS:
            text = email.get(field, "")
            if not text:
                continue
            text = replace_banned_words(text, banned)
            text = remove_dashes(text)
            text = resolve_variables(text, email)
            validate_field(text, field)
            email[field] = text

    return emails
```

- [ ] **Step 2: Commit**

```bash
git add pipeline/postprocess.py
git commit -m "feat: add postprocess.py — banned words, dash removal, variable resolution"
```

---

## Task 4: Refactor `pipeline/agents.py` — use dynamic prompts + add callScript

**Files:**
- Modify: `pipeline/agents.py`

- [ ] **Step 1: Remove hardcoded system prompts**

Delete the 4 constants `ANALYST_SYSTEM`, `STRATEGIST_SYSTEM`, `COPYWRITER_SYSTEM`, `REVIEWER_SYSTEM` from `agents.py`.

Add import at top:
```python
from pipeline.prompts import build_analyst_prompt, build_strategist_prompt, build_copywriter_prompt, build_reviewer_prompt
```

- [ ] **Step 2: Add `callScript` to EMAILS_TOOL schema**

In the `EMAILS_TOOL` dict, add this property after `linkedinDm`:
```python
            "callScript": {"type": "string", "description": "Script d'appel personnalise (5-8 phrases). Accroche, contexte, question ouverte. Ton conversationnel."},
```

Update the `required` list to conditionally include `callScript` — but since tool schemas are static, make it optional by NOT adding it to required. The copywriter prompt will instruct to include it when the call channel is active.

- [ ] **Step 3: Update `run_analyst()` to use dynamic prompt**

Change:
```python
        system=ANALYST_SYSTEM,
```
To:
```python
        system=build_analyst_prompt(ctx),
```

- [ ] **Step 4: Update `run_strategist()` to use dynamic prompt**

Change:
```python
        system=STRATEGIST_SYSTEM,
```
To:
```python
        system=build_strategist_prompt(ctx),
```

- [ ] **Step 5: Update `run_copywriter()` to use dynamic prompt**

Change:
```python
        system=COPYWRITER_SYSTEM,
```
To:
```python
        system=build_copywriter_prompt(ctx),
```

Also update the return to include `callScript`:
```python
        callScript=data.get("callScript", ""),
```

- [ ] **Step 6: Update `run_reviewer()` to use dynamic prompt**

Change:
```python
        system=REVIEWER_SYSTEM,
```
To:
```python
        system=build_reviewer_prompt(ctx),
```

Note: `run_reviewer` currently doesn't receive `ctx`. Add it to the signature:
```python
async def run_reviewer(
    client: anthropic.AsyncAnthropic,
    sections: PersonalizedSections,
    brief: LeadBrief,
    strategy: Strategy,
    ctx: CampaignContext,
) -> tuple[int, str]:
```

- [ ] **Step 7: Update `run_rewrite()` similarly**

Add `ctx: CampaignContext` parameter and use `build_copywriter_prompt(ctx)`.

- [ ] **Step 8: Remove `CLAUDE_MODEL` import, use campaign config model**

Replace:
```python
from pipeline.config import CLAUDE_MODEL
```
With:
```python
from pipeline.config import CLAUDE_MODEL as DEFAULT_MODEL
```

In each `run_*` function, use the campaign config model if available:
```python
        model = ctx.campaign_config.model if ctx.campaign_config else DEFAULT_MODEL,
```

- [ ] **Step 9: Commit**

```bash
git add pipeline/agents.py
git commit -m "refactor: agents.py uses dynamic prompts from prompts.py, adds callScript"
```

---

## Task 5: Update `pipeline/copywriter.py` — new output filename + post-processing

**Files:**
- Modify: `pipeline/copywriter.py`

- [ ] **Step 1: Update save_personalized output filename**

Change `emails_personalized.json` to `emails.json`:
```python
    output_path = campaign_dir / "emails.json"
```

- [ ] **Step 2: Add post-processing after generation**

Add import:
```python
from pipeline.postprocess import postprocess_emails
from dataclasses import asdict
```

In `write_personalized()`, after `sections = await asyncio.gather(*tasks)`, add:

```python
    # Post-process: banned words, dashes, variable resolution
    emails_data = [asdict(s) for s in sections if not s.generation_error]
    campaign_config = ctx.campaign_config
    postprocess_emails(emails_data, campaign_config)
    # Update sections from post-processed data
    for s, d in zip([s for s in sections if not s.generation_error], emails_data):
        for field in ("email1Subject", "email1Body", "email2Subject", "email2Body",
                       "email3Subject", "email3Body", "linkedinInvite", "linkedinDm", "callScript"):
            setattr(s, field, d.get(field, getattr(s, field)))
```

- [ ] **Step 3: Pass `ctx` to `run_reviewer` calls**

In `_write_one_lead()`, update the reviewer calls:
```python
            score, feedback = await run_reviewer(client, sections, brief, strategy, ctx)
```
And:
```python
                score, _ = await run_reviewer(client, sections, brief, strategy, ctx)
```

- [ ] **Step 4: Commit**

```bash
git add pipeline/copywriter.py
git commit -m "refactor: copywriter uses emails.json, adds post-processing, passes ctx to reviewer"
```

---

## Task 6: Update `pipeline/injector.py` — use postprocess, add email2Subject, rename output

**Files:**
- Modify: `pipeline/injector.py`

- [ ] **Step 1: Remove `_resolve_content()` function**

Delete the `_resolve_content()` function — it's now in `postprocess.py`.

- [ ] **Step 2: Add `email2Subject` to `_build_lead_payload()`**

Add this line after `email1Body`:
```python
        custom_vars["email2Subject"] = sections.email2Subject
```

Also add `callScript` if present:
```python
        if sections.callScript:
            custom_vars["callScript"] = sections.callScript
```

- [ ] **Step 3: Rename output file in `save_report()`**

Change:
```python
    output_path = campaign_dir / "injection_report.json"
```
To:
```python
    output_path = campaign_dir / "report.json"
```

- [ ] **Step 4: Commit**

```bash
git add pipeline/injector.py
git commit -m "refactor: injector adds email2Subject, callScript, renames output to report.json"
```

---

## Task 7: Create `pipeline/scheduler.py` — batch orchestration + budget

**Files:**
- Create: `pipeline/scheduler.py`

- [ ] **Step 1: Create scheduler.py**

```python
"""Batch multi-campaign orchestration with budget tracking and resume-on-error."""

from __future__ import annotations
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import yaml

from pipeline.models import (
    CampaignContext, ClientConfig, CampaignConfig,
    EnrichedLead, PersonalizedSections,
)
from pipeline.enricher import enrich_leads, save_enriched
from pipeline.copywriter import write_personalized, save_personalized
from pipeline.injector import inject_leads, save_report
from pipeline.utils import log

import asyncio


COST_PER_LEAD: dict[str, float] = {
    "claude-sonnet-4-6": 0.05,
    "claude-opus-4-6": 0.35,
}

STATUS_ORDER = ["draft", "enriched", "written", "injected", "live"]


def _estimate_cost(campaign_dir: Path, model: str) -> float:
    """Estimate campaign cost based on lead count and model."""
    leads_file = campaign_dir / "leads.json"
    if not leads_file.exists():
        return 0.0
    leads = json.loads(leads_file.read_text())
    return len(leads) * COST_PER_LEAD.get(model, 0.05)


def _update_status(campaign_dir: Path, status: str, error: str | None = None) -> None:
    """Update campaign.yaml status field."""
    yaml_path = campaign_dir / "campaign.yaml"
    if not yaml_path.exists():
        return
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    data["status"] = status
    data["last_step_at"] = datetime.now(timezone.utc).isoformat()
    data["error_message"] = error
    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def _list_campaigns(client_dir: Path, filter_ids: list[str] | None = None) -> list[Path]:
    """List campaign directories, optionally filtered by ID."""
    campaigns_dir = client_dir / "campaigns"
    if not campaigns_dir.exists():
        return []
    dirs = sorted(d for d in campaigns_dir.iterdir() if d.is_dir())
    if filter_ids:
        dirs = [d for d in dirs if any(d.name.startswith(fid) for fid in filter_ids)]
    return dirs


async def run_single_campaign(
    campaign_dir: Path,
    campaign_id_lemlist: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Run pipeline for a single campaign with status-based resume."""
    ctx = CampaignContext.load(campaign_dir)
    cfg = ctx.campaign_config or CampaignConfig(campaign_id=campaign_dir.name)
    status = cfg.status
    result = {
        "campaign": campaign_dir.name,
        "status_before": status,
        "status_after": status,
        "error": None,
        "cost_usd": 0.0,
    }

    try:
        # Step 1: Enrich (if draft)
        if status in ("draft",):
            log(f"[{campaign_dir.name}] Step 1/3: Enrichment")
            enriched = await enrich_leads(ctx)
            save_enriched(enriched, campaign_dir)
            _update_status(campaign_dir, "enriched")
            status = "enriched"

        # Step 2: Write (if enriched)
        if status in ("enriched",):
            log(f"[{campaign_dir.name}] Step 2/3: Copywriting")
            enriched_path = campaign_dir / "leads_enriched.json"
            raw = json.loads(enriched_path.read_text())
            enriched = []
            for data in raw:
                lead = EnrichedLead(
                    firstName=data.get("firstName", ""),
                    lastName=data.get("lastName", ""),
                    companyName=data.get("companyName", ""),
                    linkedinUrl=data.get("linkedinUrl", ""),
                    headline=data.get("headline", ""),
                    seniority=data.get("seniority", ""),
                    industry=data.get("industry", ""),
                    techStack=data.get("techStack", ""),
                    icebreaker=data.get("icebreaker", ""),
                    email=data.get("email", ""),
                    firecrawl_context=data.get("firecrawl_context", {}),
                    linkedin_profile=data.get("linkedin_profile", {}),
                    intent_score=data.get("intent_score", 0),
                    enrichment_errors=data.get("enrichment_errors", []),
                )
                enriched.append(lead)

            sections = await write_personalized(enriched, ctx)
            save_personalized(sections, campaign_dir)
            model = cfg.model
            result["cost_usd"] = len(enriched) * COST_PER_LEAD.get(model, 0.05)
            _update_status(campaign_dir, "written")
            status = "written"

        # Step 3: Inject (if written and not dry_run)
        if status in ("written",) and not dry_run:
            if not campaign_id_lemlist:
                log(f"[{campaign_dir.name}] No Lemlist campaign ID, skipping injection", "warn")
            else:
                log(f"[{campaign_dir.name}] Step 3/3: Injection")
                enriched_path = campaign_dir / "leads_enriched.json"
                raw = json.loads(enriched_path.read_text())
                enriched = [EnrichedLead(
                    firstName=d.get("firstName", ""),
                    lastName=d.get("lastName", ""),
                    companyName=d.get("companyName", ""),
                    linkedinUrl=d.get("linkedinUrl", ""),
                    headline=d.get("headline", ""),
                    email=d.get("email", ""),
                    firecrawl_context=d.get("firecrawl_context", {}),
                    linkedin_profile=d.get("linkedin_profile", {}),
                    intent_score=d.get("intent_score", 0),
                ) for d in raw]

                perso_path = campaign_dir / "emails.json"
                personalized = None
                if perso_path.exists():
                    perso_raw = json.loads(perso_path.read_text())
                    personalized = [
                        PersonalizedSections(**{k: v for k, v in s.items()
                                                if k in PersonalizedSections.__dataclass_fields__})
                        for s in perso_raw
                    ]

                report = await inject_leads(campaign_id_lemlist, enriched, personalized)
                save_report(report, campaign_dir)
                _update_status(campaign_dir, "live")
                status = "live"

        result["status_after"] = status

    except Exception as e:
        result["error"] = str(e)
        result["status_after"] = "error"
        _update_status(campaign_dir, "error", str(e))
        log(f"[{campaign_dir.name}] Pipeline error: {e}", "error")

    return result


async def run_batch(
    client_dir: str | Path,
    campaign_ids: list[str] | None = None,
    dry_run: bool = False,
) -> dict:
    """Run pipeline for multiple campaigns with budget tracking."""
    client_path = Path(client_dir)
    client_config = ClientConfig.load(client_path)
    started_at = datetime.now(timezone.utc).isoformat()

    # List campaigns to process
    filter_ids = campaign_ids if campaign_ids and campaign_ids != ["all"] else None
    campaign_dirs = _list_campaigns(client_path, filter_ids)

    if not campaign_dirs:
        log("No campaigns found", "warn")
        return {"error": "no campaigns"}

    # Sort by status (most advanced first for resume)
    def sort_key(d: Path) -> int:
        cfg_path = d / "campaign.yaml"
        if cfg_path.exists():
            with open(cfg_path) as f:
                status = yaml.safe_load(f).get("status", "draft")
            return STATUS_ORDER.index(status) if status in STATUS_ORDER else 99
        return 0
    campaign_dirs.sort(key=sort_key)

    budget_total = client_config.total_budget_usd
    budget_used = 0.0
    results = {
        "client": client_path.name,
        "campaigns_completed": [],
        "campaigns_failed": [],
        "campaigns_skipped": [],
        "budget_total": budget_total,
        "budget_used": 0.0,
        "budget_remaining": budget_total,
        "started_at": started_at,
        "completed_at": None,
    }

    for cdir in campaign_dirs:
        cfg_path = cdir / "campaign.yaml"
        if cfg_path.exists():
            with open(cfg_path) as f:
                cfg_data = yaml.safe_load(f)
            status = cfg_data.get("status", "draft")
            if status in ("live", "injected"):
                log(f"[{cdir.name}] Already {status}, skipping")
                continue

        # Budget check
        model = cfg_data.get("model", client_config.model) if cfg_path.exists() else client_config.model
        estimated_cost = _estimate_cost(cdir, model)
        if budget_used + estimated_cost > budget_total:
            log(f"[{cdir.name}] Budget exceeded (need ${estimated_cost:.2f}, "
                f"remaining ${budget_total - budget_used:.2f}), skipping", "warn")
            results["campaigns_skipped"].append(cdir.name)
            continue

        log(f"=== Campaign: {cdir.name} (est. ${estimated_cost:.2f}) ===")
        result = await run_single_campaign(cdir, dry_run=dry_run)

        if result["error"]:
            results["campaigns_failed"].append(cdir.name)
        else:
            results["campaigns_completed"].append(cdir.name)
            budget_used += result["cost_usd"]

    results["budget_used"] = round(budget_used, 2)
    results["budget_remaining"] = round(budget_total - budget_used, 2)
    results["completed_at"] = datetime.now(timezone.utc).isoformat()

    # Save batch report
    report_path = client_path / "report_batch.json"
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    log(f"Batch done: {len(results['campaigns_completed'])} completed, "
        f"{len(results['campaigns_failed'])} failed, "
        f"{len(results['campaigns_skipped'])} skipped. "
        f"Budget: ${budget_used:.2f}/{budget_total:.2f}", "success")

    return results
```

- [ ] **Step 2: Commit**

```bash
git add pipeline/scheduler.py
git commit -m "feat: add scheduler.py — batch orchestration with budget tracking and resume"
```

---

## Task 8: Rewrite `pipeline/__main__.py` — new CLI interface

**Files:**
- Modify: `pipeline/__main__.py`

- [ ] **Step 1: Rewrite CLI with new commands**

```python
"""BYS Outbound Pipeline CLI.

Usage:
    python -m pipeline enrich --campaign path/to/C04
    python -m pipeline write  --campaign path/to/C04
    python -m pipeline inject --campaign path/to/C04 --lemlist-id cam_xxx
    python -m pipeline run    --client path/to/client --campaigns all
    python -m pipeline run    --client path/to/client --campaigns C01,C04
    python -m pipeline status --client path/to/client
"""

from __future__ import annotations
import asyncio
import json
import sys
from typing import Optional

import typer

app = typer.Typer(
    name="bys-pipeline",
    help="BYS Outbound Pipeline: enrich, write, inject, batch run.",
    no_args_is_help=True,
)


@app.command()
def enrich(
    campaign: str = typer.Option(..., help="Path to campaign directory"),
) -> None:
    """Step 1: Enrich leads with Scrapingdog + RapidAPI LinkedIn."""
    from pipeline.scheduler import run_single_campaign
    result = asyncio.run(run_single_campaign(
        campaign_dir=campaign,
        dry_run=True,  # Only enrich, don't continue
    ))
    # Output JSON to stdout for Claude to parse
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


@app.command()
def write(
    campaign: str = typer.Option(..., help="Path to campaign directory"),
) -> None:
    """Step 2: Write personalized emails with Claude API."""
    from pipeline.models import CampaignContext
    from pipeline.copywriter import write_personalized, save_personalized
    from pipeline.models import EnrichedLead
    import json as json_mod
    from pathlib import Path

    ctx = CampaignContext.load(campaign)
    enriched_path = Path(campaign) / "leads_enriched.json"
    if not enriched_path.exists():
        typer.echo("Error: leads_enriched.json not found. Run 'enrich' first.", err=True)
        raise typer.Exit(1)

    raw = json_mod.loads(enriched_path.read_text())
    enriched = [EnrichedLead(**{k: v for k, v in d.items()
                                if k in EnrichedLead.__dataclass_fields__}) for d in raw]
    sections = asyncio.run(write_personalized(enriched, ctx))
    save_personalized(sections, Path(campaign))

    result = {"leads": len(sections), "errors": sum(1 for s in sections if s.generation_error)}
    json.dump(result, sys.stdout, indent=2)
    print()


@app.command()
def inject(
    campaign: str = typer.Option(..., help="Path to campaign directory"),
    lemlist_id: str = typer.Option(..., help="Lemlist campaign ID (cam_xxx)"),
) -> None:
    """Step 3: Inject leads into Lemlist campaign."""
    from pipeline.scheduler import run_single_campaign
    result = asyncio.run(run_single_campaign(
        campaign_dir=campaign,
        campaign_id_lemlist=lemlist_id,
    ))
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


@app.command()
def run(
    client: Optional[str] = typer.Option(None, help="Path to client directory"),
    campaign: Optional[str] = typer.Option(None, help="Path to single campaign directory"),
    campaigns: str = typer.Option("all", help="Campaign IDs: all, or C01,C04,C07"),
    dry_run: bool = typer.Option(False, help="Skip injection step"),
) -> None:
    """Run full pipeline: enrich -> write -> inject (single or batch)."""
    if campaign:
        # Single campaign mode
        from pipeline.scheduler import run_single_campaign
        result = asyncio.run(run_single_campaign(
            campaign_dir=campaign,
            dry_run=dry_run,
        ))
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    elif client:
        # Batch mode
        from pipeline.scheduler import run_batch
        campaign_ids = None if campaigns == "all" else campaigns.split(",")
        result = asyncio.run(run_batch(
            client_dir=client,
            campaign_ids=campaign_ids,
            dry_run=dry_run,
        ))
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    else:
        typer.echo("Error: provide --client (batch) or --campaign (single)", err=True)
        raise typer.Exit(1)
    print()


@app.command()
def status(
    client: str = typer.Option(..., help="Path to client directory"),
) -> None:
    """Show status of all campaigns for a client."""
    from pathlib import Path
    import yaml

    client_path = Path(client)
    campaigns_dir = client_path / "campaigns"
    if not campaigns_dir.exists():
        typer.echo("No campaigns directory found", err=True)
        raise typer.Exit(1)

    statuses = []
    for cdir in sorted(campaigns_dir.iterdir()):
        if not cdir.is_dir():
            continue
        cfg_path = cdir / "campaign.yaml"
        leads_path = cdir / "leads.json"
        info = {"campaign": cdir.name, "status": "unknown", "leads": 0}
        if cfg_path.exists():
            with open(cfg_path) as f:
                cfg = yaml.safe_load(f)
            info["status"] = cfg.get("status", "draft")
            info["model"] = cfg.get("model", "")
            info["error"] = cfg.get("error_message")
        if leads_path.exists():
            leads = json.loads(leads_path.read_text())
            info["leads"] = len(leads)
        statuses.append(info)

    json.dump(statuses, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: Commit**

```bash
git add pipeline/__main__.py
git commit -m "refactor: new CLI with --campaign/--client flags, status command, JSON stdout"
```

---

## Task 9: Delete obsolete files

**Files:**
- Delete: `pipeline/orchestrator.py`
- Delete: `agents/bys-copywriter.md`, `agents/bys-enricher-firecrawl.md`, `agents/bys-enricher-rapidapi.md`, `agents/bys-launcher.md`, `agents/bys-targeting.md`

- [ ] **Step 1: Remove orchestrator.py**

```bash
rm pipeline/orchestrator.py
```

- [ ] **Step 2: Remove old agent files**

```bash
rm agents/bys-copywriter.md agents/bys-enricher-firecrawl.md agents/bys-enricher-rapidapi.md agents/bys-launcher.md agents/bys-targeting.md
```

- [ ] **Step 3: Commit**

```bash
git add -u
git commit -m "chore: remove orchestrator.py and old agent .md files"
```

---

## Task 10: Create templates

**Files:**
- Create: `templates/client.yaml.example`
- Create: `templates/campaign.yaml.example`
- Create: `templates/leads.json.example`
- Create: `.env.example`

- [ ] **Step 1: Create client.yaml.example**

```yaml
# Client configuration — generated by bys-setup agent
name: "Acme Corp"
date: "2026-01-01"
sender_name: "Jean Dupont"
sender_email: "jean@acme.com"
sender_title: "CEO"

lemlist_campaign_prefix: "acme"

model: "claude-sonnet-4-6"
total_budget_usd: 50.00

enrichment:
  providers:
    - scrapingdog
    - rapidapi_linkedin
  concurrency: 10
```

- [ ] **Step 2: Create campaign.yaml.example**

```yaml
# Campaign configuration — generated by bys-strategy agent
campaign_id: "C01"
signal: "techchange"
persona: "cro"
geo: "fr"
status: "draft"

channels:
  - email
  - linkedin
  - call

tone: "conversationnel, pair-a-pair, curieux"

custom_rules:
  - "Mentionner le secteur du prospect"

banned_words: []

model: "claude-sonnet-4-6"
concurrency: 10

last_step_at: null
error_message: null
```

- [ ] **Step 3: Create leads.json.example**

```json
[
  {
    "firstName": "Marie",
    "lastName": "Dupont",
    "companyName": "Acme SAS",
    "email": "marie@acme.fr",
    "linkedinUrl": "https://linkedin.com/in/mariedupont"
  }
]
```

- [ ] **Step 4: Create .env.example**

```bash
# API Keys — copy to .env.local and fill in
SCRAPINGDOG_API_KEY=
RAPIDAPI_KEY=
ANTHROPIC_API_KEY=
LEMLIST_API_KEY=
```

- [ ] **Step 5: Commit**

```bash
git add templates/ .env.example
git commit -m "feat: add templates (client.yaml, campaign.yaml, leads.json, .env)"
```

---

## Task 11: Create methodo guides

**Files:**
- Create: `templates/methodo/discovery-guide.md`
- Create: `templates/methodo/cab-p-guide.md`
- Create: `templates/methodo/ciblage-guide.md`

- [ ] **Step 1: Create discovery-guide.md**

Extract the discovery section from `Mandatory_to_read_before_anything.md` (lines 11-28) into a standalone guide.

- [ ] **Step 2: Create cab-p-guide.md**

Extract the CAB-P section (lines 30-42) into a standalone guide.

- [ ] **Step 3: Create ciblage-guide.md**

Extract the ciblage section (lines 44+) into a standalone guide.

- [ ] **Step 4: Commit**

```bash
git add templates/methodo/
git commit -m "feat: add methodo guides (discovery, cab-p, ciblage)"
```

---

## Task 12: Create the 4 Claude Code agents

**Files:**
- Create: `agents/bys-setup.md`
- Create: `agents/bys-strategy.md`
- Create: `agents/bys-campaign.md`
- Create: `agents/bys-monitor.md`

- [ ] **Step 1: Create bys-setup.md**

```markdown
---
name: bys-setup
description: Onboarding nouvel utilisateur BYS Outbound Engine
---

# BYS Setup Agent

Tu guides un nouvel utilisateur pour configurer le BYS Outbound Engine.

## Flow

### 1. Verifier les API keys

Lis `.env.local` et verifie que ces 4 cles sont presentes :
- `SCRAPINGDOG_API_KEY`
- `RAPIDAPI_KEY`
- `ANTHROPIC_API_KEY`
- `LEMLIST_API_KEY`

Si des cles manquent, guide l'utilisateur :
- Scrapingdog : https://www.scrapingdog.com (Google SERP API)
- RapidAPI : https://rapidapi.com/rockapis-rockapis-default/api/linkedin-data-api (LinkedIn profiles)
- Anthropic : https://console.anthropic.com (Claude API)
- Lemlist : Settings > Integrations > API dans Lemlist

### 2. Creer le dossier client

Demande a l'utilisateur :
- Nom de la boite
- Nom de l'expediteur (qui signe les emails)
- Email de l'expediteur
- Titre de l'expediteur
- Budget max en USD pour les campagnes

Cree le dossier : `clients/{nom}_{date_du_jour}/`

### 3. Generer client.yaml

Utilise les infos pour generer `client.yaml` dans le dossier client.
Reference : `templates/client.yaml.example`

### 4. Confirmer

Affiche un resume et confirme que tout est pret.
Oriente vers : "Maintenant, lance l'agent bys-strategy pour creer ta strategie de prospection."

## Regles
- Ne JAMAIS ecraser `.env.local` sans confirmation
- Ne JAMAIS hardcoder de secrets dans les fichiers
- Toujours verifier que le dossier n'existe pas deja avant de le creer
```

- [ ] **Step 2: Create bys-strategy.md**

```markdown
---
name: bys-strategy
description: Strategie BYS — Discovery, CAB-P, 10 ciblages
---

# BYS Strategy Agent

Tu guides l'utilisateur a travers la methodologie BYS pour creer sa strategie de prospection.

## Prerequis
- `client.yaml` existe dans le dossier client
- Lis `templates/methodo/discovery-guide.md` pour le format attendu

## Flow

### 1. Discovery

Pose ces questions UNE PAR UNE (ne pas tout envoyer d'un coup) :
1. URL du site web
2. URL LinkedIn de la boite
3. Description de l'offre en 2-3 phrases
4. Qui sont vos clients aujourd'hui ?
5. Quel est votre panier moyen ?
6. Avez-vous des cas clients ?
7. Quels sont vos concurrents ?
8. Quels pays cibler ?
9. Y a-t-il des exclusions ?

Scrape le site web et LinkedIn (via Firecrawl MCP) pour completer.
Sauvegarde le resultat dans `discovery.md` dans le dossier client.

### 2. CAB-P

A partir du discovery, genere la matrice CAB-P :
| Offre | Caracteristiques | Avantages | Benefices | Pains cibles |

Presente au client pour validation. Sauvegarde dans `cab-p.md`.

### 3. Recap

Genere un resume court (5-10 lignes) du discovery + CAB-P.
Sauvegarde dans `recap.md`.

### 4. 10 Ciblages

Propose 10 campagnes ciblees en croisant :
- Signal (techchange, hiring, funding, newrole...)
- Persona (cro, cto, ceo, vp_sales...)
- Geo (fr, be, us...)

Pour chaque campagne :
1. Cree le dossier `campaigns/C{01-10}_{signal}_{persona}_{geo}/`
2. Genere `campaign.yaml` avec tone, custom_rules, banned_words deduits du contexte
3. Genere `ciblage.md` avec le brief detaille

Presente les 10 ciblages au client pour validation.

## Regles
- UNE question a la fois pendant le discovery
- Toujours valider le CAB-P avec le client avant de passer aux ciblages
- Les banned_words incluent automatiquement les defaults BYS + mots specifiques au secteur
- Le tone est deduit du croisement persona x geo (vouvoiement FR, tutoiement startup, etc.)
```

- [ ] **Step 3: Create bys-campaign.md**

```markdown
---
name: bys-campaign
description: Lancer et superviser le pipeline BYS
---

# BYS Campaign Agent

Tu lances le pipeline de prospection et supervises l'execution.

## Prerequis
- `client.yaml` + au moins un `campaign.yaml` avec `status: draft`
- `leads.json` present dans le dossier campagne (l'utilisateur les fournit)

## Flow

### 1. Verifier les leads

Lis `leads.json` et verifie :
- Champs obligatoires : firstName, lastName, companyName
- Nombre de leads
- Signale les leads sans email (Lemlist tentera findEmail)
- Signale les leads sans linkedinUrl (canal LinkedIn desactive)

### 2. Proposer le lancement

Options :
- **Une campagne** : `python -m pipeline run --campaign {path}`
- **Batch** : `python -m pipeline run --client {path} --campaigns all`
- **Selection** : `python -m pipeline run --client {path} --campaigns C01,C04`
- **Dry run** (sans injection) : ajouter `--dry-run`

### 3. Lancer et monitorer

Lance la commande via Bash.
Le pipeline affiche la progression sur stderr.
A la fin, lis `report.json` (ou `report_batch.json`) et affiche un resume :
- Leads enrichis / ecrits / injectes
- Erreurs eventuelles
- Cout estime

### 4. Gestion des erreurs

Si une campagne echoue :
- Lis `campaign.yaml` → le status indique ou ca s'est arrete
- Lis `report.json` → details de l'erreur
- Propose une solution (relancer, corriger les leads, etc.)
- La commande `run` reprend automatiquement au bon status

### 5. Injection Lemlist

Si le pipeline est en mode `--dry-run` ou sans Lemlist ID :
1. Cree la campagne Lemlist via MCP (`create_campaign_with_sequence`)
2. Recupere le campaign ID
3. Lance l'injection : `python -m pipeline inject --campaign {path} --lemlist-id {id}`

## Regles
- Toujours confirmer avant de lancer (afficher cout estime + nombre de leads)
- Ne JAMAIS lancer sans que l'utilisateur ait valide les leads
- Afficher le cout estime avant chaque batch
```

- [ ] **Step 4: Create bys-monitor.md**

```markdown
---
name: bys-monitor
description: Suivi et optimisation des campagnes BYS
---

# BYS Monitor Agent

Tu suis les performances des campagnes et proposes des optimisations.

## Flow

### 1. Status global

Lis tous les `report.json` et `campaign.yaml` du client :
```bash
python -m pipeline status --client {path}
```

Affiche un tableau :
| Campagne | Status | Leads | Injectes | Erreurs | Cout |

### 2. Stats Lemlist

Recupere les stats via MCP :
- `get_campaign_stats` pour chaque campagne live
- Open rate, click rate, reply rate, bounce rate

Seuils d'alerte :
- Open rate < 30% → probleme de delivrabilite ou de subject line
- Reply rate < 3% → probleme de contenu ou de ciblage
- Bounce rate > 5% → probleme de qualite des emails

### 3. Recommandations

Si une campagne sous-performe :
- Analyse le ciblage et le tone
- Propose des ajustements dans `campaign.yaml`
- Peut relancer le pipeline `write` + `inject` avec les nouvelles rules

### 4. Fallback sans MCP

Si le MCP Lemlist n'est pas disponible :
- Utilise `python -m pipeline status --client {path}` pour les donnees locales
- Demande a l'utilisateur de copier les stats depuis le dashboard Lemlist

## Regles
- Ne jamais modifier les campagnes live sans confirmation
- Toujours montrer les donnees avant de recommander
```

- [ ] **Step 5: Commit**

```bash
git add agents/
git commit -m "feat: add 4 Claude Code agents (setup, strategy, campaign, monitor)"
```

---

## Task 13: Delete `Mandatory_to_read_before_anything.md`

**Files:**
- Delete: `Mandatory_to_read_before_anything.md`

- [ ] **Step 1: Verify content is captured elsewhere**

The content has been split into:
- Discovery flow → `agents/bys-strategy.md` + `templates/methodo/discovery-guide.md`
- CAB-P → `agents/bys-strategy.md` + `templates/methodo/cab-p-guide.md`
- Ciblage → `agents/bys-strategy.md` + `templates/methodo/ciblage-guide.md`
- Email rules → `pipeline/prompts.py` (BYS base prompts)
- Lemlist API → `agents/bys-campaign.md`
- Pipeline flow → `agents/bys-campaign.md`

- [ ] **Step 2: Remove the file**

```bash
rm Mandatory_to_read_before_anything.md
```

- [ ] **Step 3: Commit**

```bash
git add -u
git commit -m "chore: remove Mandatory_to_read_before_anything.md (content split into agents + templates)"
```

---

## Task 14: Create README.md for novice users

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

Short, action-oriented README that a novice can follow in Claude Code:

```markdown
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
python -m pipeline run --campaign clients/acme_2026-03-24/campaigns/C01_techchange_cro_fr
python -m pipeline run --client clients/acme_2026-03-24 --campaigns all
python -m pipeline status --client clients/acme_2026-03-24
```

## Stack

- Python 3.11+ (anthropic, aiohttp, typer, pyyaml, pydantic)
- Claude API (Sonnet par defaut)
- Scrapingdog (Google SERP) + RapidAPI (LinkedIn)
- Lemlist (injection + sequences)
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "feat: add README.md quick start guide"
```

---

## Task 15: Smoke test the full pipeline

- [ ] **Step 1: Generate a campaign.yaml for existing test data**

Create `clients/buildyoursales_2026-03-23/client.yaml` and `clients/buildyoursales_2026-03-23/campaigns/C04_techchange_cro_fr/campaign.yaml` from the existing data so the new system is backward-compatible.

- [ ] **Step 2: Run status command**

```bash
python -m pipeline status --client clients/buildyoursales_2026-03-23
```

Expected: JSON output listing all campaigns with their status.

- [ ] **Step 3: Verify imports**

```bash
python -c "from pipeline.models import ClientConfig, CampaignConfig; print('OK')"
python -c "from pipeline.prompts import build_copywriter_prompt; print('OK')"
python -c "from pipeline.postprocess import postprocess_emails; print('OK')"
python -c "from pipeline.scheduler import run_batch; print('OK')"
```

Expected: All print "OK".

- [ ] **Step 4: Commit smoke test configs**

```bash
git add clients/buildyoursales_2026-03-23/client.yaml clients/buildyoursales_2026-03-23/campaigns/C04_techchange_cro_fr/campaign.yaml
git commit -m "feat: add YAML configs for existing test client (backward compat)"
```
