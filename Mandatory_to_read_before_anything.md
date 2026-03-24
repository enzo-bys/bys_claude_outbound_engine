# BYS Outbound Engine

> **buildyoursystem.tech** -- 10 micro-campagnes outbound ultra-ciblees depuis un brief humain via Claude.

---

## WORKFLOW OBLIGATOIRE

L'agent DOIT suivre ce flow dans l'ordre. Aucune etape ne peut etre sautee.

### Etape 1 -- Discovery (OBLIGATOIRE avant tout ciblage)

Poser ces questions au client et ne pas avancer tant qu'on n'a pas les reponses :

```
1. URL du site web de la boite
2. URL LinkedIn de la boite
3. Autres URLs utiles (Crunchbase, blog, cas clients, landing pages)
4. Description de l'offre en 2-3 phrases
5. Qui sont vos clients aujourd'hui ? (secteurs, tailles, geos)
6. Quel est votre panier moyen / ACV ?
7. Avez-vous des cas clients / temoignages a utiliser ?
8. Quels sont vos concurrents directs ?
9. Quels pays cibler ? (obligatoire -- conditionne la langue, le ton et les regles legales)
10. Y a-t-il des exclusions ? (clients existants, concurrents, secteurs)
```

Scraper le site web et le LinkedIn pour completer les infos manquantes.

### Etape 2 -- CAB-P

A partir du discovery, remplir le tableau :

```
| Offre | Caracteristiques | Avantages | Benefices | Pains cibles |
|-------|------------------|-----------|-----------|--------------|
| ...   | ...              | ...       | ...       | ...          |
```

Flow : Offre -> Benefices -> Pains -> Types d'entreprises cibles

Valider le CAB-P avec le client avant de continuer.

### Etape 3 -- 10 ciblages

Construire 10 campagnes ciblees en appliquant :
- Tiers ABM (T1/T2/T3)
- Relevance data > intent data
- Sweet spot contextuel (niveaux 3-4)
- Look-alike si clients existants
- Regles culturelles et linguistiques du pays cible (cf section "Regles par pays")

Chaque ciblage doit etre documente avec : persona, secteur, taille, geo, signal, pain, angle.

### Etape 4 -- Copywriting

3 emails par campagne + LinkedIn invite/DM.
Appliquer les regles de la section "Regles email" ET "Regles par pays".

### Etape 5 -- Lancement Lemlist

Creer, injecter en batch, configurer senders, review humain, start.
Cf section "Operations Lemlist" pour le detail technique.

---

## ARCHITECTURE FICHIERS

Tout le travail est organise par client, puis par campagne. Nomenclature stricte et datee.

```
clients/
  {nom_client}_{date}/                    # Ex: octopus_2026-03-23/
    |
    |-- discovery.md                       # Etape 1 : infos client, URLs, offre
    |-- cab-p.md                           # Etape 2 : tableau CAB-P valide
    |
    |-- campaigns/
    |   |-- C01_{signal}_{persona}_{geo}/  # Ex: C01_funding_vp-sales_fr/
    |   |   |-- ciblage.md                 # Criteres de ciblage (tier, filtres, angle)
    |   |   |-- leads.json                 # Liste de leads bruts (output targeting)
    |   |   |-- enrichment.json            # Enrichissement Firecrawl (contexte entreprise)
    |   |   |-- linkedin_enrichment.json   # Enrichissement RapidAPI (profil LinkedIn)
    |   |   |-- leads_enriched.json        # Leads fusionnes avec enrichissements + icebreakers
    |   |   |-- emails.json                # 3 emails + LinkedIn msgs
    |   |   +-- batch_lemlist.json         # Config Lemlist (campaign_id, sequence, webhooks)
    |   |
    |   +-- ... (C02 a C10)
    |
    +-- recap.md                           # Tableau recap des 10 campagnes
```

### Nomenclature

- **Client** : `{nom_client}_{YYYY-MM-DD}` (date de lancement)
- **Campagne** : `C{01-10}_{signal}_{persona}_{geo}`
  - signal : `funding`, `hiring`, `growth`, `newleader`, `techchange`, `lookalike`...
  - persona : `vp-sales`, `cto`, `head-marketing`, `ceo`...
  - geo : `fr`, `uk`, `dach`, `us`, `eu`, `be`, `ch`...
- **Fichiers** : toujours les memes 4 fichiers par campagne

### Contenu des fichiers

**ciblage.md :**
```markdown
# C01 -- Funding / VP Sales / France

- Date : 2026-03-23
- Tier : 1
- Persona : VP Sales, Head of Sales, CRO
- Seniority : ATL (VP/C-Level)
- Secteur : SaaS B2B
- Taille : 51-500
- Geo : France
- Langue : Francais
- Signal : Levee de fonds < 3 mois
- Pain : Scaler l'outbound sans recruter de SDR
- Angle : Post-funding, besoin de pipeline rapide
- Hook type : Lite
- Filtres Lemlist People DB :
  - currentTitle: ["VP Sales", "Head of Sales", "CRO"]
  - currentCompanyHeadcount: ["51-200", "201-500"]
  - currentCompanySubIndustry: ["Software Development"]
  - country: ["France"]
  - currentCompanyLastFundingRoundAt: ["Less than 1 month", "1 month to 3 months"]
```

**leads.json :**
```json
[
  {
    "email": "john@company.com",
    "firstName": "John",
    "lastName": "Doe",
    "companyName": "Acme SaaS",
    "jobTitle": "VP Sales",
    "linkedinUrl": "https://linkedin.com/in/johndoe",
    "companyDomain": "acme.com",
    "signal": "Series B -- 15M EUR -- Jan 2026",
    "icebreaker": "..."
  }
]
```

**emails.json :**
```json
{
  "campaign": "C01_funding_vp-sales_fr",
  "framework": "Avant/Apres",
  "country": "fr",
  "language": "francais",
  "emails": [
    { "step": 1, "delay": 0, "subject": "...", "body": "...", "word_count": 72 },
    { "step": 2, "delay": 3, "subject": "Re: ...", "body": "...", "word_count": 65 },
    { "step": 3, "delay": 17, "subject": "...", "body": "...", "word_count": 48 }
  ],
  "linkedin_invite": "...",
  "linkedin_dm": "..."
}
```

**batch_lemlist.json :**
```json
{
  "campaign_id": "cam_xxx",
  "campaign_name": "2026-03-23-C01-funding-vp-sales-fr",
  "sequence_id": "seq_xxx",
  "leads_count": 42,
  "leads_excluded": [],
  "senders": ["enzo@bys1.com", "enzo@bys2.com"],
  "steps": ["email", "linkedinVisit", "linkedinInvite", "email", "conditional", "email"],
  "webhooks": ["emailsReplied", "interested", "emailsBounced"],
  "status": "paused",
  "started_at": null
}
```

---

## Agents

| Agent | Role |
|-------|------|
| `bys-targeting` | Discovery + CAB-P + 10 ciblages + leads |
| `bys-copywriter` | 3 emails x 10 campagnes + LinkedIn msgs |
| `bys-launcher` | Cree + lance + monitore dans Lemlist |
| `bys-enricher-firecrawl` | Enrichissement web : scrape sites, news, technos, contexte entreprise |
| `bys-enricher-rapidapi` | Enrichissement LinkedIn : profils, posts, activite, intent scoring |

### Workflow enrichissement (entre targeting et copywriting)

```
bys-targeting (leads.json)
    |
    v
bys-enricher-firecrawl (contexte entreprise, news, technos)
    +
bys-enricher-rapidapi (profil LinkedIn, posts, activite, intent)
    |
    v
leads_enriched.json (leads + enrichment + icebreakers personnalises + intent score)
    |
    v
bys-copywriter (emails personnalises a partir des enrichissements)
    |
    v
bys-launcher (creation + injection + lancement)
```

### Combinaison enrichissement

| Donnee | Firecrawl | RapidAPI LinkedIn |
|--------|-----------|-------------------|
| Site web entreprise | Primaire | Non |
| Actualites presse | Primaire | Non |
| Stack techno | Primaire | Non |
| Profil personnel | Non | Primaire |
| Posts LinkedIn | Non | Primaire |
| Activite recente | Non | Primaire |
| Jobs entreprise | Secondaire (site carrieres) | Primaire (LinkedIn) |
| Description entreprise | Primaire | Secondaire |

## Setup

```bash
claude mcp add --transport http lemlist https://app.lemlist.com/mcp
# .env.local :
# LEMLIST_API_KEY=xxx
# FIRECRAWL_API_KEY=fc-xxx
# RAPIDAPI_KEY=xxx
```

---

## Methodologie BYS

### Relevance Data > Intent Data

L'intent seul c'est du bruit dans 90% des cas. On cherche la **relevance data** : donnees contextuelles qui rendent le message pertinent. Micro-campagnes de 30-50 leads.

### Tiers ABM

| Tier | Definition | Leads | Personnalisation |
|------|-----------|-------|------------------|
| 1 | Pain fort + relevance forte | < 50 | 1:1, strong hooks |
| 2 | Pain modere + signaux | 50-150 | Segmentee, lite hooks |
| 3 | Profil match, signal faible | 150+ | Templates auto |

### Sweet Spot

| Niveau | Precision | Verdict |
|--------|-----------|---------|
| 1 | Industrie seule | Trop vague |
| 2 | + anciennete | Insuffisant |
| 3 | + stack techno | **Sweet spot** |
| 4 | + trafic/croissance | **Ideal** |
| 5 | + recrutement recent | Tier 1 only |

---

## Lemlist People DB -- Filtres

### Lead

| Filtre | Type | Valeurs |
|--------|------|---------|
| `currentTitle` | autocomplete | Job title |
| `seniority` | select | Owner/Partner, CxO, VP, Director, Manager, Senior, Entry level... |
| `department` | select | Sales, Marketing, Engineering, IT, Finance, HR, Operations... (27) |
| `country` | autocomplete | Pays |
| `region` | select | Europe, Western Europe, DACH, North America, Asia... (25) |
| `keyword` | text | Mot-cle dans le profil |
| `currentPositionTenure` | select | < 6 mois, 6m-1an, 1-3ans, 3-5ans, 5+ |
| `yearsOfExperience` | select | < 1an, 1-2, 2-5, 5-10, 10+ |
| `pastTitle` | autocomplete | Ancien poste |
| `skill` | autocomplete | Competences |
| `location` | autocomplete | Ville / Etat |

### Company

| Filtre | Type | Valeurs |
|--------|------|---------|
| `currentCompanyHeadcount` | select | 1-10, 11-50, 51-200, 201-500, 501-1K, 1K-5K, 5K-10K, 10K+ |
| `currentCompanySubIndustry` | level | 20 industries + sous-industries |
| `currentCompanySizeGrowth` | slider | -100% a +200% (croissance 6 mois) |
| `currentCompanyLastFundingRoundAt` | select | < 1 mois, 1-3 mois, 3-6 mois, 6+ mois |
| `currentCompanyRevenue` | select | $0-500K a 30M+ (8 tranches) |
| `currentCompanyTechnologies` | autocomplete | Stack techno |
| `currentCompanyFounded` | slider | Annee creation |
| `currentCompanyType` | select | Public, Private, Nonprofit... (10) |
| `currentCompanyMarket` | select | B2B, B2C, B2G |
| `currentCompanyCountry` | autocomplete | Pays siege |
| `keywordInCompany` | text | Mot-cle dans l'entreprise |

**IMPORTANT : People DB search via MCP uniquement (API REST retourne 405).**

---

## Regles email -- FONDAMENTALES

### Ton et style

- **Humain a humain** -- ecrire comme un collegue, pas comme un robot
- **JAMAIS de tiret long (---)** dans les emails envoyes -- utiliser des virgules, points, parentheses
- **JAMAIS de formules AI** : "I hope this finds you well", "I wanted to reach out", "I came across your profile", "leverage", "streamline", "synergy", "game-changer", "cutting-edge"
- **JAMAIS de listes a puces** dans un cold email
- **Phrases courtes**, conversationnelles, comme un SMS pro
- Le ton doit sonner comme si on l'avait tape vite entre deux meetings

### Structure

- 60-90 mots max, plain text, 1 seul CTA soft
- Subject : 2 mots, lowercase, zero mots sales
- Pas de "Bonjour {{firstName}}," ou "Hi {{firstName}}" -- hook direct
- 6-8 phrases max (donnees Belkins 2025 : 42% open rate, 6.9% reply)
- Moins de 200 mots absolument

### Sequence

```
Email 1 (J0)  : reduire les couts / le gaspillage
Email 2 (J+3) : augmenter les revenus / les resultats
Email 3 (J+17): gagner du temps / breakup soft
```

- Email 2 subject = "Re: {{subject_email_1}}" (thread trick obligatoire)
- Email 3 = breakup email, court, pas de pression

### ATL vs BTL

- **ATL** (VP/C-Level) : 2-3 phrases, outcomes business, "15 min pour en discuter ?"
- **BTL** (Managers/ICs) : 3-4 phrases, workflow/pain quotidien, "Je te montre ?"

### Hooks

- **Strong** (Tier 1, <50 leads) : reference specifique au prospect (post, actu, recrutement)
- **Lite** (Tier 2-3, >50 leads) : observation firmographique ("vous utilisez X", "votre equipe a grandi de Y%")

### 8 Frameworks

1. **Avant/Apres** -- douleur -> resultat
2. **Pattern Break** -- surprise -> fait inattendu -> pitch
3. **Question d'abord** -- question -> proposition si oui
4. **Valeur d'emblee** -- observation -> tactic gratuite
5. **Calcul du cout** -- X heures x cout = montant gaspille
6. **Defi commun** -- probleme recurrent -> case study
7. **Insight neutre** -- tendance marche -> question ouverte
8. **3 problemes du role** -- P1, P2, P3 -> on resout PX

### Donnees benchmark (Belkins/Martal 2025-2026)

- Reply rate moyen : 5.8% (bon = >7%, excellent = >10%)
- 1-2 contacts par entreprise max (7.8% reply vs 3.8% pour 10+)
- Campagnes < 100 leads = meilleur reply rate
- Jeudi = meilleur jour (6.87% reply)
- Envoi soir 20h-23h = meilleur reply rate (6.52%)
- One-touch ou 2 follow-ups max, au-dela le reply rate chute

---

## Regles par pays -- OBLIGATOIRE

Le pays cible conditionne la langue, le ton, le niveau de formalisme et les regles legales. Demander le pays au discovery (question 9).

### France (fr)

| Regle | Detail |
|-------|--------|
| Langue | Francais obligatoire |
| Anglicismes | INTERDITS ou rarissimes. Pas de "pipeline", "scale", "growth hack". Dire "portefeuille", "passer a l'echelle", "croissance rapide" |
| Ton | Vouvoiement obligatoire. Formel mais pas rigide. Direct sans etre familier |
| Formalisme | Moyen-haut. Eviter le tutoiement sauf indication contraire |
| Saturation outbound | TRES HAUTE. Les decision makers FR recoivent 10-20 cold emails/jour. Se demarquer par la pertinence, pas le volume |
| Subject line | 2 mots francais, lowercase. "croissance rapide", "equipe commerciale", "nouveau pipeline" |
| Legal | RGPD + interet legitime B2B. Droit d'opposition obligatoire. Bloctel pour le tel |
| Accents | GARDER les accents dans les noms (Melina -> Melina, Stephane -> Stephane). Attention : les accents passent dans les variables Lemlist |

### DACH (dach) -- Allemagne, Autriche, Suisse alemanique

| Regle | Detail |
|-------|--------|
| Langue | Allemand obligatoire (sauf Suisse international) |
| Ton | TRES formel. "Sie" obligatoire. "Sehr geehrte/r Herr/Frau X" ou "Guten Tag Herr/Frau X" |
| Anglicismes | Toleres dans la tech mais a doser. Pas de franglais |
| Formalisme | HAUT. Precision et clarte valorisees. Pas de flou ni de promesses vagues |
| Saturation outbound | MOYENNE. Moins de cold email qu'en FR/US, mais filtres anti-spam avances |
| Subject line | Allemand, precis, factuel. "Vertriebsteam", "Pipeline-Aufbau" |
| Legal | RGPD strict + BDSG. Interet legitime OK en B2B mais source de donnees doit etre justifiable |
| Domaine | Acheter des domaines en .de/.at/.ch pour les campagnes locales augmente la confiance |

### UK (uk) -- Royaume-Uni

| Regle | Detail |
|-------|--------|
| Langue | Anglais |
| Ton | Semi-formel, pragmatique, droit au but. British understatement apprecie |
| Formalisme | MOYEN. Prenom OK rapidement. "Hi John" acceptable |
| Saturation outbound | HAUTE. Marche mature, beaucoup de cold email |
| Subject line | 2 mots anglais, lowercase. "sales pipeline", "outbound results" |
| Legal | UK GDPR post-Brexit. Interet legitime OK en B2B. ICO supervise |

### US (us)

| Regle | Detail |
|-------|--------|
| Langue | Anglais US |
| Ton | Decontracte mais professionnel. "Hey John" OK pour BTL |
| Formalisme | BAS. Direct, action-oriented, time-conscious |
| Saturation outbound | LA PLUS HAUTE au monde. Se demarquer est critique |
| Subject line | Ultra court, casual. "quick question", "saw this" |
| Legal | CAN-SPAM. Opt-out obligatoire. Pas de consentement prealable necessaire |

### Belgique (be)

| Regle | Detail |
|-------|--------|
| Langue | Adapter a la region : FR (Wallonie/Bruxelles) ou NL (Flandre). JAMAIS melanger |
| Ton | Similaire a la France pour le FR, plus decontracte pour le NL |

### Suisse (ch)

| Regle | Detail |
|-------|--------|
| Langue | Adapter : FR (Romandie), DE (Suisse alemanique), IT (Tessin). Anglais OK si profil international |
| Ton | Plus decontracte que DE. "Du" parfois OK en startup |

---

## Variables Lemlist -- REGLES CRITIQUES

### Syntaxe des variables

```
{{firstName}}     = OK
{{ firstName }}   = ERREUR -- LE LEAD RECOIT LA VARIABLE BRUTE
{{first Name}}    = ERREUR -- pas d'espace dans le nom
```

**JAMAIS d'espace entre les accolades et le nom de variable.**

### Nommage

- **camelCase** : `{{jobTitle}}`, `{{companyName}}`, `{{painPoint}}`
- **snake_case** : `{{job_title}}`, `{{company_name}}`
- **PascalCase** : `{{JobTitle}}`
- Case-sensitive : `{{firstname}}` != `{{firstName}}`

### Fallback obligatoire

Toujours utiliser un fallback pour eviter les "Bonjour ," si la donnee manque :

```
{% if firstName %}{{firstName}},{% else %}Bonjour,{% endif %}
```

Ou en Liquid inline :
```
{{firstName | default: "Bonjour"}}
```

### Variables par defaut Lemlist

| Variable | Contenu |
|----------|---------|
| `{{email}}` | Email du lead |
| `{{firstName}}` | Prenom |
| `{{lastName}}` | Nom |
| `{{companyName}}` | Entreprise |
| `{{phone}}` | Telephone |
| `{{linkedinUrl}}` | URL LinkedIn |
| `{{icebreaker}}` | Icebreaker genere |
| `{{sender.name}}` | Nom de l'expediteur |

### Variables custom (a creer par campagne)

| Variable | Format | Usage |
|----------|--------|-------|
| `{{jobTitle}}` | Titre du poste | Personnalisation |
| `{{signal}}` | Signal detecte | Icebreaker |
| `{{painPoint}}` | Douleur cible | Angle email |
| `{{companyDomain}}` | Domaine site | Enrichment |

### Spin syntax (variations anti-spam)

```
{Bonjour|Salut|Hey} {{firstName}},
{On aide|On accompagne|On travaille avec} des {boites|entreprises|equipes} comme {{companyName}}
```

Chaque envoi pioche une variation aleatoire.

### Checklist variables avant envoi

- [ ] Aucun espace dans les `{{ }}` -> `{{var}}` pas `{{ var }}`
- [ ] Tous les noms de variables matchent les colonnes CSV / custom vars
- [ ] Fallback sur `{{firstName}}` et `{{companyName}}` minimum
- [ ] Preview dans Lemlist avec des vrais leads AVANT lancement
- [ ] Pas de variable orpheline (utilisee dans l'email mais pas dans les leads)

---

## Operations Lemlist -- Guide technique

### Sequence multichannel (ordre obligatoire)

**TOUJOURS commencer par un email, JAMAIS par une etape LinkedIn.**

```
J0  : Email 1 (premier contact)
J+2 : LinkedIn Visit (warm up profil)
J+3 : LinkedIn Invite (avec message court)
J+5 : Email 2 (follow-up, "Re:" thread trick)
J+8 : Conditional (LinkedIn accepted? -> DM)
J+22: Email 3 (breakup, branche NO du conditional)
```

Pourquoi email d'abord : delivrabilite, tracking, pas de dependance a l'acceptation LinkedIn.

### Senders / Inbox Rotation

- **Toujours** configurer 2-5 senders par campagne (inbox rotation)
- Lemlist fait du round-robin automatique : chaque lead garde le meme sender tout au long de la sequence
- Max 30 emails/inbox/jour
- Configurer les senders AVANT d'ajouter les leads
- Via MCP : utiliser `get_user_channels` pour lister les senders disponibles
- Checker la sante du domaine : `check_domain_health`

### Injection leads -- Bulk & Batch

**MCP (prioritaire)** :
- `add_lead_to_campaign` : 1 lead a la fois
- Batcher par groupes de 15, pas de pause necessaire (le MCP gere)
- Flags obligatoires : `findEmail=true`, `verifyEmail=true`, `deduplicate=true`

**API REST (fallback)** :
- `POST /campaigns/{id}/leads/?deduplicate=true&verifyEmail=true`
- Rate limit : 20 requetes / 2 secondes
- Batcher par groupes de 15, pause 2s entre les batches
- Import CSV via l'UI Lemlist si > 100 leads (plus fiable)

**Limites d'import** :
- API : 40 000 leads/campagne (1 call par lead)
- CSV : 40 000 leads, batches de 10 000/campagne
- Chrome extension : 999 (LinkedIn) / 2 500 (Sales Navigator)

### Creation de campagne

**Via MCP** :
1. `create_campaign_with_sequence` -- cree la campagne + premier email
   - ATTENTION : la campagne peut demarrer en "running" automatiquement
   - Verifier le statut apres creation avec `get_campaign_details`
   - Si running sans leads, pas de probleme (rien ne s'envoie)
2. `add_sequence_step` pour chaque step supplementaire (dans l'ordre)
3. Configurer les senders via l'UI ou `get_user_channels`
4. Injecter les leads en batch
5. `get_campaign_details` pour verifier le statut et le nombre de leads
6. `set_campaign_state` action="start" avec `userConfirmed=true`

**Via API REST** :
1. `POST /campaigns` -- creer
2. `PATCH /campaigns/{id}` -- configurer (stopOnEmailReplied, etc.)
3. `POST /sequences/{id}/steps` -- ajouter steps
4. `POST /campaigns/{id}/leads/` -- injecter leads
5. `POST /hooks` -- webhooks
6. `PUT /campaigns/{id}/start` -- demarrer (confirmation humaine)

### Webhooks Slack

Configurer pour chaque campagne :
- `emailsReplied` -- reponse recue
- `interested` -- marque comme interesse
- `emailsBounced` -- bounce detecte
- `meetingBooked` -- meeting book

### Checklist pre-lancement

- [ ] Senders configures (2-5, inbox rotation)
- [ ] Sequence complete (email first, jamais LinkedIn first)
- [ ] Variables verifiees (pas d'espace, fallbacks)
- [ ] Preview email avec vrais leads dans Lemlist
- [ ] Leads injectes avec dedup + email verification
- [ ] Webhooks Slack actifs
- [ ] Credits suffisants (`get_team_info`)
- [ ] Domaine sain (`check_domain_health`)
- [ ] Confirmation humaine obtenue
- [ ] Statut = running verifie apres start

---

## Lemlist API

```
Base: https://api.lemlist.com/api  |  Auth: Basic (:API_KEY)  |  Rate: 20/2s
MCP:  https://app.lemlist.com/mcp  |  Auth: OAuth auto

POST   /campaigns                    Creer campagne
PATCH  /campaigns/{id}               Configurer settings
POST   /sequences/{id}/steps         Ajouter step
POST   /campaigns/{id}/leads/        Ajouter lead (?deduplicate=true&verifyEmail=true)
PUT    /campaigns/{id}/start         DEMARRER (confirmation humaine obligatoire)
GET    /v2/campaigns/{id}/stats      Stats campagne
POST   /enrich?findEmail=true&verifyEmail=true  Enrichir (flags obligatoires)
POST   /hooks                        Webhooks
GET    /team/credits                 Credits restants
```

### MCP Tools principaux

| Tool MCP | Usage | Quand |
|----------|-------|-------|
| `lemleads_search` | Chercher dans People DB (450M+ contacts) | Etape 3 targeting |
| `get_lemleads_filters` | Lister les filtres disponibles | AVANT tout lemleads_search |
| `create_campaign_with_sequence` | Creer campagne + 1er email | Etape 5 |
| `add_sequence_step` | Ajouter steps a la sequence | Etape 5 |
| `add_lead_to_campaign` | Injecter 1 lead (batch de 15) | Etape 5 |
| `set_campaign_state` | Start/pause campagne | Etape 5 |
| `get_campaign_details` | Verifier statut + leads | Monitoring |
| `get_campaign_stats` | Stats (open, reply, bounce) | Monitoring |
| `check_domain_health` | Sante du domaine d'envoi | Pre-lancement |
| `get_user_channels` | Lister senders disponibles | Config senders |
| `enrich_lead` | Enrichir 1 lead | Enrichment |
| `search_campaign_leads` | Chercher leads dans une campagne | Debug |

---

## Garde-fous

| Regle | Valeur |
|-------|--------|
| Leads/campagne | 30-50 |
| Contacts/entreprise | 1-2 max |
| Emails/inbox/jour | 30 max |
| Domains | 3-5 rotation |
| Bounce max | 2% (auto-pause > 5%) |
| Email size | 60-90 mots |
| Verification | 100% |
| Dedup | Toujours |
| Review humain | Obligatoire avant START |
| Meilleur jour | Jeudi |
| Meilleure heure | 20h-23h |
| Sequence | Email first, jamais LinkedIn first |
| Variables | `{{var}}` jamais `{{ var }}` |

## Limites API (testees 2026-03-23)

| Endpoint | API REST | MCP |
|----------|----------|-----|
| `/people-database/search` | 405 (bloque) | OK |
| `/senders` | 405 (bloque) | OK |
| `/enrich` | OK (flags obligatoires) | OK |
| `DELETE /campaigns` | 405 (pause only) | - |
| `create_campaign_with_sequence` | - | OK (attention : peut demarrer en "running") |

## Roadmap

- [x] RapidAPI LinkedIn (headcount, posts, decision makers) -- agent `bys-enricher-rapidapi` cree
- [x] Firecrawl (scraping sites, stack techno, relevance data) -- agent `bys-enricher-firecrawl` cree
- [ ] BuiltWith / Semrush (sweet spot niveau 4)
- [ ] Domaines locaux par pays (.de, .at, .ch, .co.uk)
- [ ] A/B testing sequences via MCP
- [ ] Webhooks Slack automatises par campagne
