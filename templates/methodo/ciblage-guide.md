# Ciblage Guide

> Step 3 of the workflow. Build 10 targeted campaigns from the CAB-P.

---

## Objective

Create 10 ultra-targeted micro-campaigns (30-50 leads each) by combining CAB-P pains with relevance signals.

---

## Core principles

### Relevance Data > Intent Data

Intent alone is noise in 90% of cases. We look for **relevance data**: contextual data that makes the message relevant. Micro-campaigns of 30-50 leads.

### ABM Tiers

| Tier | Definition | Leads | Personalization |
|------|-----------|-------|----------------|
| 1 | Strong pain + strong relevance | < 50 | 1:1, strong hooks |
| 2 | Moderate pain + signals | 50-150 | Segmented, lite hooks |
| 3 | Profile match, weak signal | 150+ | Auto templates |

### Sweet Spot

| Level | Precision | Verdict |
|-------|-----------|---------|
| 1 | Industry only | Too vague |
| 2 | + tenure | Insufficient |
| 3 | + tech stack | **Sweet spot** |
| 4 | + traffic/growth | **Ideal** |
| 5 | + recent hiring | Tier 1 only |

---

## Building the 10 ciblages

For each ciblage, apply:
- ABM Tier (T1/T2/T3)
- Relevance data > intent data
- Contextual sweet spot (levels 3-4)
- Look-alike if existing clients
- Cultural and linguistic rules for the target country

### Mandatory documentation per ciblage

Each ciblage must be documented in a `ciblage.md` file with:

```
- Date
- Tier (1/2/3)
- Persona (target titles)
- Seniority (ATL or BTL)
- Industry
- Size (headcount)
- Geo (country)
- Language
- Signal (trigger event)
- Pain (targeted pain, from CAB-P)
- Angle (email approach)
- Hook type (Strong for T1, Lite for T2-T3)
- Lemlist People DB filters
```

---

## Lemlist People DB Filters

### Lead

| Filter | Type | Values |
|--------|------|--------|
| `currentTitle` | autocomplete | Job title |
| `seniority` | select | Owner/Partner, CxO, VP, Director, Manager, Senior, Entry level... |
| `department` | select | Sales, Marketing, Engineering, IT, Finance, HR, Operations... (27) |
| `country` | autocomplete | Country |
| `region` | select | Europe, Western Europe, DACH, North America, Asia... (25) |
| `keyword` | text | Keyword in profile |
| `currentPositionTenure` | select | < 6 months, 6m-1yr, 1-3yrs, 3-5yrs, 5+ |
| `yearsOfExperience` | select | < 1yr, 1-2, 2-5, 5-10, 10+ |
| `pastTitle` | autocomplete | Previous title |
| `skill` | autocomplete | Skills |
| `location` | autocomplete | City / State |

### Company

| Filter | Type | Values |
|--------|------|--------|
| `currentCompanyHeadcount` | select | 1-10, 11-50, 51-200, 201-500, 501-1K, 1K-5K, 5K-10K, 10K+ |
| `currentCompanySubIndustry` | level | 20 industries + sub-industries |
| `currentCompanySizeGrowth` | slider | -100% to +200% (6-month growth) |
| `currentCompanyLastFundingRoundAt` | select | < 1 month, 1-3 months, 3-6 months, 6+ months |
| `currentCompanyRevenue` | select | $0-500K to 30M+ (8 ranges) |
| `currentCompanyTechnologies` | autocomplete | Tech stack |
| `currentCompanyFounded` | slider | Founding year |
| `currentCompanyType` | select | Public, Private, Nonprofit... (10) |
| `currentCompanyMarket` | select | B2B, B2C, B2G |
| `currentCompanyCountry` | autocomplete | HQ country |
| `keywordInCompany` | text | Keyword in company |

**IMPORTANT: People DB search via MCP only (REST API returns 405).**

---

## Campaign naming convention

`C{01-10}_{signal}_{persona}_{geo}`

- signal: `funding`, `hiring`, `growth`, `newleader`, `techchange`, `lookalike`...
- persona: `vp-sales`, `cto`, `head-marketing`, `ceo`...
- geo: `fr`, `uk`, `dach`, `us`, `eu`, `be`, `ch`...

---

## Example

```markdown
# C01 -- Funding / VP Sales / France

- Date: 2026-03-23
- Tier: 1
- Persona: VP Sales, Head of Sales, CRO
- Seniority: ATL (VP/C-Level)
- Industry: SaaS B2B
- Size: 51-500
- Geo: France
- Language: French
- Signal: Funding round < 3 months
- Pain: Scale outbound without hiring SDRs
- Angle: Post-funding, need for fast pipeline
- Hook type: Lite
- Lemlist People DB filters:
  - currentTitle: ["VP Sales", "Head of Sales", "CRO"]
  - currentCompanyHeadcount: ["51-200", "201-500"]
  - currentCompanySubIndustry: ["Software Development"]
  - country: ["France"]
  - currentCompanyLastFundingRoundAt: ["Less than 1 month", "1 month to 3 months"]
```

---

## Rules

- 30-50 leads per campaign max
- 1-2 contacts per company max
- Always target sweet spot level 3-4 minimum
- Diversify signals across the 10 campaigns
- NEVER create a campaign without a pain identified in the CAB-P
