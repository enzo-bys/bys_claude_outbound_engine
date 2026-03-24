# Guide Discovery

> Etape 1 du workflow BYS. OBLIGATOIRE avant tout ciblage.

---

## Objectif

Collecter toutes les informations necessaires sur le client pour construire une strategie de prospection pertinente. Aucune etape suivante ne peut commencer sans discovery complete.

---

## Questions a poser

Poser ces questions au client et ne pas avancer tant qu'on n'a pas les reponses :

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

---

## Enrichissement automatique

Apres les reponses du client, scraper :
- Le site web (Firecrawl / Scrapingdog) pour completer les infos manquantes
- Le LinkedIn de la boite (RapidAPI) pour le headcount, les posts recents, les decision makers

---

## Output

Fichier `discovery.md` dans le dossier client, contenant :
- Toutes les reponses aux 10 questions
- Les donnees enrichies depuis le scraping
- Les URLs sources

---

## Regles

- Ne JAMAIS inventer de reponses -- si l'info manque, la demander
- Ne JAMAIS avancer a l'etape CAB-P sans discovery complete
- Le pays cible (question 9) est critique : il conditionne la langue, le ton et les regles legales de toute la campagne
