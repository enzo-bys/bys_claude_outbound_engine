# Guide Ciblage

> Etape 3 du workflow BYS. Construire 10 campagnes ciblees a partir du CAB-P.

---

## Objectif

Creer 10 micro-campagnes ultra-ciblees (30-50 leads chacune) en combinant les pains du CAB-P avec des signaux de relevance.

---

## Principes fondamentaux

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

## Construction des 10 ciblages

Pour chaque ciblage, appliquer :
- Tiers ABM (T1/T2/T3)
- Relevance data > intent data
- Sweet spot contextuel (niveaux 3-4)
- Look-alike si clients existants
- Regles culturelles et linguistiques du pays cible

### Documentation obligatoire par ciblage

Chaque ciblage doit etre documente dans un fichier `ciblage.md` avec :

```
- Date
- Tier (1/2/3)
- Persona (titres cibles)
- Seniority (ATL ou BTL)
- Secteur
- Taille (headcount)
- Geo (pays)
- Langue
- Signal (evenement declencheur)
- Pain (douleur ciblee, issu du CAB-P)
- Angle (approche de l'email)
- Hook type (Strong pour T1, Lite pour T2-T3)
- Filtres Lemlist People DB
```

---

## Filtres Lemlist People DB

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

## Nomenclature campagne

`C{01-10}_{signal}_{persona}_{geo}`

- signal : `funding`, `hiring`, `growth`, `newleader`, `techchange`, `lookalike`...
- persona : `vp-sales`, `cto`, `head-marketing`, `ceo`...
- geo : `fr`, `uk`, `dach`, `us`, `eu`, `be`, `ch`...

---

## Exemple

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

---

## Regles

- 30-50 leads par campagne max
- 1-2 contacts par entreprise max
- Toujours viser le sweet spot niveau 3-4 minimum
- Diversifier les signaux entre les 10 campagnes
- Ne JAMAIS creer de campagne sans pain identifie dans le CAB-P
