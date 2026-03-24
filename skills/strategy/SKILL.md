---
name: strategy
description: Build prospecting strategy — Discovery questions, CAB-P matrix, 10 targeted campaigns. Use after setup to create the full outbound strategy.
---

# Strategy — Outbound Engine by BuildYourSales.tech

You guide the user through the methodology to build their prospecting strategy.

## Prerequisites
- `client.yaml` exists in the client folder (created by `/outbound-engine:setup`)
- Read `templates/methodo/discovery-guide.md` for the expected format

## Flow

### 1. Discovery

Ask these questions ONE AT A TIME (do not send them all at once):
1. Company website URL
2. Company LinkedIn URL
3. Offer description in 2-3 sentences
4. Who are your current clients?
5. What is your average deal size?
6. Do you have any client case studies?
7. Who are your competitors?
8. Which countries to target?
9. Are there any exclusions?

Scrape the website and LinkedIn (via Firecrawl MCP) to fill in missing information.
Save the result in `discovery.md` in the client folder.

Reference: `templates/methodo/discovery-guide.md`

### 2. CAB-P

From the discovery, generate the CAB-P matrix:
| Offer | Characteristics | Advantages | Benefits | Target Pains |

Present to the client for validation. Save in `cab-p.md`.

Reference: `templates/methodo/cab-p-guide.md`

### 3. Recap

Generate a short summary (5-10 lines) of the discovery + CAB-P.
Save in `recap.md`.

### 4. 10 Ciblages

Propose 10 targeted campaigns by combining:
- Signal (techchange, hiring, funding, newrole...)
- Persona (cro, cto, ceo, vp_sales...)
- Geo (fr, be, us...)

For each campaign:
1. Create the folder `campaigns/C{01-10}_{signal}_{persona}_{geo}/`
2. Ask the user what language this campaign should be written in (e.g. fr, en, de) and save it as `language` in `campaign.yaml`
3. Generate `campaign.yaml` with tone, custom_rules, banned_words inferred from context, and the `language` field
4. Generate `ciblage.md` with the detailed brief

Present the 10 ciblages to the client for validation.

Reference: `templates/methodo/ciblage-guide.md`

## Rules
- ONE question at a time during discovery
- Always validate CAB-P with the client before moving to ciblages
- banned_words automatically includes the defaults + industry-specific words
- The tone is inferred from the persona x geo combination (formal FR, startup casual, etc.)

## Next step
Once validated, direct the user to: "Add your leads.json files and run `/outbound-engine:campaign` to launch."
