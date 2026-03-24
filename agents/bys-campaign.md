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
