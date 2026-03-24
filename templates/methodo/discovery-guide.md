# Discovery Guide

> Step 1 of the workflow. MANDATORY before any targeting.

---

## Objective

Collect all necessary information about the client to build a relevant prospecting strategy. No subsequent step can begin without a complete discovery.

---

## Questions to ask

Ask these questions to the client and do not proceed until all answers are received:

1. Company website URL
2. Company LinkedIn URL
3. Other useful URLs (Crunchbase, blog, case studies, landing pages)
4. Offer description in 2-3 sentences
5. Who are your current clients? (industries, sizes, geos)
6. What is your average deal size / ACV?
7. Do you have any client case studies / testimonials to use?
8. Who are your direct competitors?
9. Which countries to target? (mandatory -- determines language, tone, and legal rules)
10. Are there any exclusions? (existing clients, competitors, industries)

---

## Automatic enrichment

After the client's answers, scrape:
- The website (Firecrawl / Scrapingdog) to fill in any missing information
- The company LinkedIn (RapidAPI) for headcount, recent posts, and decision makers

---

## Output

File `discovery.md` in the client folder, containing:
- All answers to the 10 questions
- Enriched data from scraping
- Source URLs

---

## Rules

- NEVER invent answers -- if information is missing, ask for it
- NEVER proceed to the CAB-P step without a complete discovery
- The target country (question 9) is critical: it determines the language, tone, and legal rules for the entire campaign
