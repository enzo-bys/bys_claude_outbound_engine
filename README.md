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

Tu decris ton business. Claude construit ton pipeline de prospection. Jusqu'a 10 campagnes, 400 leads, emails personnalises — injectes dans Lemlist en une seule session.

> **Necessite [Claude Code CLI](https://claude.ai/code)** — installe-le, clone ce repo, et colle ce README dans Claude Code. Il te guide etape par etape.
>
> **Video walkthrough (3 min) :** https://youtu.be/Foou3pCHXIM

---

## Vue d'ensemble

| Etape | Action | Resultat |
|-------|--------|----------|
| 1 | Installer Claude Code CLI | Terminal pret |
| 2 | Fork + clone le repo GitHub | Projet en local |
| 3 | Creer les 3 cles API (Anthropic + Scrapingdog + RapidAPI) | Enrichissement active |
| 4 | Sauvegarder les cles dans `.env.local` | Config prete |
| 5 | Connecter le Lemlist MCP | Claude parle directement a Lemlist |
| 6 | Installer le plugin | Moteur charge |
| 7 | `/outbound-engine:setup` | Dossier client cree |
| 8 | `/outbound-engine:strategy` | Matrice CAB-P + 10 campagnes |
| 9 | Sourcer ou importer les leads | Leads prets |
| 10 | `/outbound-engine:campaign` | Enrichissement + emails + injection Lemlist |
| 11 | Finaliser dans Lemlist | Campagnes pretes a envoyer |
| 12 | `/outbound-engine:monitor` | Stats + optimisations |

> **Temps reel :** 45-60 min la premiere fois (installation), 15 min les fois suivantes.
>
> **Cout estime :** ~0,05$/lead avec Claude Sonnet. 400 leads = environ 20$ de tokens Anthropic.

---

## Ce que l'outil fait automatiquement

L'Outbound Engine est un plugin Claude Code developpe par Enzo Luciano-Marty (Build Your Sales) qui connecte Claude directement a Lemlist. Tu decris ton business, il genere des campagnes de prospection B2B completes.

1. Pose 9 questions sur ton offre, tes clients, tes concurrents
2. Construit une matrice CAB-P (Caracteristiques, Avantages, Benefices, Douleurs)
3. Propose jusqu'a 10 campagnes ciblees (persona + signal + geo + langue)
4. Enrichit chaque lead (profil LinkedIn + news Google recentes)
5. Redige un email personnalise par personne — pas un template, un vrai message
6. Score chaque email avec l'IA avant envoi
7. Injecte tout dans Lemlist, pret a envoyer

Chaque campagne recoit 30-50 leads. Les emails sont rediges dans la langue de ton choix (francais, anglais, allemand, espagnol...).

---

## Prerequis

Avant de commencer, tu as besoin de :

- **Un abonnement Claude Max (ou Pro)**
- **Un compte GitHub** — [creer un compte ici](https://github.com/signup) si tu n'en as pas
- **Un compte Lemlist** avec un abonnement actif
- **~20$ de credits API Anthropic** — [ajouter des credits](https://console.anthropic.com/billing)
- **Une infrastructure de delivrabilite prete** (voir la section dediee ci-dessous)

---

## Avant tout : la delivrabilite

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

### Etape 1 — Installer Claude Code CLI

Ouvre ton Terminal (Mac : CMD + Espace -> "Terminal" -> Entree) et lance :

```bash
curl -fsSL https://claude.ai/install.sh | sh
```

Configure le PATH :

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

Lance Claude Code :

```bash
claude
```

Selectionne "Claude account with subscription" et connecte-toi.

### Etape 2 — Fork et clone le repo

1. Va sur [github.com/enzo-bys/bys_claude_outbound_engine](https://github.com/enzo-bys/bys_claude_outbound_engine)
2. Clique sur **"Fork"** en haut a droite, puis **"Create fork"**
3. Clone ton fork :

```bash
git clone https://github.com/TON_USERNAME/bys_claude_outbound_engine.git
cd bys_claude_outbound_engine
```

4. Installe les dependances Python :

```bash
pip install -r requirements.txt
```

> **Pas de git ?** Telecharge le ZIP depuis GitHub et dezippe-le.
>
> **Pas de Python ?** Telecharge-le depuis [python.org/downloads](https://www.python.org/downloads/). Mac : `brew install python`.
>
> **Pas de Node.js ?** Tu en auras besoin pour le Lemlist MCP. Telecharge depuis [nodejs.org](https://nodejs.org) (version LTS).

### Etape 3 — Obtenir tes 3 cles API d'enrichissement

| # | Cle | A quoi elle sert | Ou la trouver | Comment faire |
|---|-----|-----------------|---------------|---------------|
| 1 | `ANTHROPIC_API_KEY` | Alimente l'IA qui ecrit tes emails | **[console.anthropic.com/account/keys](https://console.anthropic.com/account/keys)** | Clique "Create Key" -> copie-la. Va dans Billing et ajoute minimum 20$ de credits. |
| 2 | `SCRAPINGDOG_API_KEY` | Trouve les news Google sur tes leads | **[api.scrapingdog.com/dashboard](https://api.scrapingdog.com/dashboard)** | Cree un compte gratuit -> la cle API est en haut du dashboard |
| 3 | `RAPIDAPI_KEY` | Enrichit les profils LinkedIn | **[rapidapi.com/.../professional-network-data](https://rapidapi.com/pnd-team-pnd-team/api/professional-network-data/playground)** | Clique "Subscribe to Test" (plan gratuit) -> copie `X-RapidAPI-Key` dans le panneau de droite |

> Sans credits Anthropic, l'enrichissement des leads ne fonctionnera pas.

### Etape 4 — Sauvegarder tes cles API

```bash
cp .env.example .env.local
```

Ouvre `.env.local` et colle tes cles :

```
ANTHROPIC_API_KEY=sk-ant-...
SCRAPINGDOG_API_KEY=...
RAPIDAPI_KEY=...
```

> Tu peux aussi dire directement a Claude Code : `Add my API keys to .env.local: ANTHROPIC_API_KEY=... SCRAPINGDOG_API_KEY=... RAPIDAPI_KEY=...`

### Etape 5 — Connecter le Lemlist MCP

C'est comme ca que Claude Code parle directement a Lemlist — creation de campagnes, sourcing de leads, stats, tout.

Dans ton terminal (dans Claude Code ou en dehors) :

```bash
claude mcp add --transport http lemlist https://app.lemlist.com/mcp
```

Ton navigateur va s'ouvrir sur une page de consentement. Autorise ton equipe Lemlist et c'est connecte.

> **Si OAuth echoue** (le navigateur ne s'ouvre pas), utilise ta cle API :
> ```bash
> claude mcp add --transport http lemlist https://app.lemlist.com/mcp --header "X-API-Key:TA_CLE_API_LEMLIST"
> ```
> Trouve ta cle API dans Lemlist : **Settings -> Integrations -> API -> Copy Key**.

### Etape 6 — Installer le plugin

Deux options :

**Option A — Installer comme plugin Claude Code (recommande)**

```bash
claude plugin add --from https://github.com/enzo-bys/bys_claude_outbound_engine
```

Installe le plugin globalement. Tu peux l'utiliser depuis n'importe quel dossier — lance `claude` et les skills sont disponibles.

**Option B — Lancer localement depuis le dossier du projet**

```bash
claude --plugin-dir .
```

Charge le plugin uniquement pour la session en cours.

Dans les deux cas, accepte le prompt de confiance quand Claude le demande.

---

## Utilisation

### Etape 7 — Configurer ton compte

```
/outbound-engine:setup
```

Claude verifie tes cles API, te demande les infos de ta boite (nom, expediteur, budget), et cree ton dossier client.

### Etape 8 — Construire ta strategie

```
/outbound-engine:strategy
```

Claude te pose 9 questions sur ton business, une a la fois :
1. Ton URL de site web
2. Ton URL LinkedIn
3. Ce que tu vends (2-3 phrases)
4. Qui sont tes clients
5. Ton deal size moyen
6. Tes case studies
7. Tes concurrents
8. Pays cibles
9. Exclusions

Puis il construit ta **matrice CAB-P** (quelles douleurs ton offre resout) et propose **jusqu'a 10 campagnes ciblees**, chacune avec un signal, un persona, une geographie et une langue specifiques.

### Etape 9 — Obtenir tes leads

Tu as 3 facons d'alimenter une campagne en leads :

**Option A — Sourcer depuis Lemlist (recommande)**

Dis simplement a Claude ce que tu cherches :
```
Find 40 CROs at SaaS companies in France with 50-200 employees
```

Claude utilise la base de leads Lemlist pour chercher, filtrer et ajouter les leads directement a ta campagne. Aucun fichier necessaire.

**Option B — Importer un CSV ou Excel**

Si tu as deja une liste de leads (exportee de LinkedIn, d'un CRM ou d'un tableur) :
```
Here's my lead list: /path/to/leads.csv
```

Claude lit le fichier, mappe les colonnes automatiquement, convertit au bon format et pousse les leads dans la campagne. Colonnes minimum : prenom, nom, entreprise. Email et URL LinkedIn ameliorent les resultats.

**Option C — JSON manuel (power users)**

Depose un fichier `leads.json` dans le dossier de la campagne :

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

### Etape 10 — Lancer les campagnes

Une fois tes leads prets, lance :

```
/outbound-engine:campaign
```

Claude valide tes leads, les enrichit (LinkedIn + news Google), redige des emails personnalises pour chacun, et injecte tout dans Lemlist.

**Exemple de prompt pour creer les structures de campagnes :**

```
Create my 3 Lemlist campaigns.
Campaign 1 — [Persona]: [X emails + LinkedIn], delays [J0/J+2/J+5].
Leave email bodies empty. Use {{firstName}} and {{companyName}}.
Confirm each campaign ID.
```

> **Astuce :** Appuie sur **2** (Yes, and don't ask again) a chaque confirmation pour eviter les interruptions repetees.

### Etape 11 — Finaliser dans Lemlist

Apres que Claude a injecte tes campagnes :

1. Va dans Lemlist — tes campagnes sont creees
2. **Mets-les en pause immediatement** (elles sont en "running" par defaut)
3. Colle ton copywriting dans chaque etape
4. Configure les A/B tests
5. Active la rotation d'inboxes (minimum 3 comptes)
6. Importe tes leads si pas deja fait (CSV ou Lemlist database)
7. Lance en limitant a **30-50 emails/jour/inbox** les 30 premiers jours

### Etape 12 — Suivre et optimiser

```
/outbound-engine:monitor
```

Claude tire tes stats Lemlist (taux d'ouverture, taux de reponse, taux de bounce) et te dit quelles campagnes ajuster et quoi changer.

---

## La cle du succes : un brief de qualite

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

## Obtenir les meilleurs resultats

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

## Limites a connaitre

Ce que l'Outbound Engine ne gere **pas** :

- Conditions avancees Lemlist (si ouvert -> LinkedIn) — a configurer manuellement
- Images cliquables et variables d'image personnalisees
- Landing pages dynamiques
- Branches multi-canales complexes avec logique conditionnelle

### Workflow optimal selon le contexte

| Contexte | Approche recommandee |
|----------|---------------------|
| Campagne urgente (webinar, evenement) | Outbound Engine pour la structure + injection, copywriting manuel dans Lemlist |
| Campagne long terme | Outbound Engine pour enrichissement + leads, copywriting dans ton style, puis injection manuelle |
| Scale (10+ campagnes) | Outbound Engine bout en bout avec brief detaille |

---

## Resume

| Etape | Ce que tu tapes | Ce qui se passe |
|-------|----------------|-----------------|
| 1-6 | Installation (voir ci-dessus) | CLI + repo + cles + MCP + plugin |
| 7 | `/outbound-engine:setup` | Verification cles + dossier client |
| 8 | `/outbound-engine:strategy` | 9 questions + CAB-P + 10 campagnes |
| 9 | "Find 40 CROs in France" ou CSV | Leads sources via Lemlist, CSV, ou JSON |
| 10 | `/outbound-engine:campaign` | Enrichir + ecrire emails + injecter Lemlist |
| 11 | Finaliser dans Lemlist | Pause, copywriting, rotation inboxes, A/B tests |
| 12 | `/outbound-engine:monitor` | Stats + recommandations |

---

## FAQ

**Est-ce que je dois ecrire des prompts ?**
Non. Le moteur a des prompts integres bases sur une methodologie de cold email eprouvee. Claude les adapte a ton business automatiquement.

**Quelles langues sont supportees ?**
Francais, anglais, allemand, espagnol, neerlandais, italien, et toute autre langue que tu specifies. Chaque campagne peut avoir sa propre langue.

**Combien ca coute par lead ?**
Environ 0,05$/lead avec Claude Sonnet, 0,35$/lead avec Claude Opus. Un batch de 10 campagnes avec 40 leads chacune coute environ 20$.

**Est-ce que je peux l'utiliser sans Lemlist ?**
Oui. Lance avec `--dry-run` et le moteur genere les emails sans les injecter. Tu les trouveras dans `emails.json` dans chaque dossier de campagne.

**Quel format pour mes leads ?**
Tu peux sourcer les leads directement depuis Lemlist (aucun fichier necessaire), importer un CSV/Excel, ou fournir un fichier JSON. Champs minimum : prenom, nom, entreprise. Ajoute email et URL LinkedIn pour de meilleurs resultats.

**Je ne suis pas technique. Est-ce que je peux quand meme l'utiliser ?**
Oui. Si tu sais installer Claude Code, connecter Lemlist, et coller 3 cles API, c'est bon. Claude gere tout le reste de maniere conversationnelle.

---

## Mode CLI (power users)

Si tu preferes les commandes a la conversation :

```bash
# Lancer une seule campagne
python -m pipeline run --campaign clients/acme/campaigns/C01_techchange_cro_fr

# Lancer toutes les campagnes d'un client
python -m pipeline run --client clients/acme --campaigns all

# Lancer des campagnes specifiques
python -m pipeline run --client clients/acme --campaigns C01,C04,C07

# Verifier le statut
python -m pipeline status --client clients/acme

# Etapes individuelles
python -m pipeline enrich --campaign path/to/C04
python -m pipeline write  --campaign path/to/C04
python -m pipeline inject --campaign path/to/C04 --lemlist-id cam_xxx
```

---

## Architecture (pour les devs)

```
.claude-plugin/  Manifeste du plugin
skills/          4 skills (SKILL.md) — invocables via /outbound-engine:*
agents/          4 agents Claude Code (.md) — UX conversationnelle
pipeline/        Moteur Python — execution silencieuse
templates/       Guides methodologiques + exemples YAML/JSON
clients/         Donnees client (gitignored)
```

**Stack** : Python 3.11+ / Claude API / Lemlist MCP / Scrapingdog / RapidAPI LinkedIn

---

Built by [BuildYourSales.tech](https://buildyoursales.tech)
