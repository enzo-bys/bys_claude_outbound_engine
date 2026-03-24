---
name: campaign
description: Launch the outbound pipeline — verify leads, enrich, write emails, inject into Lemlist. Use when leads are ready and campaigns are set up.
---

# Campaign — Outbound Engine by BuildYourSales.tech

You launch the prospecting pipeline and supervise execution.

## Prerequisites
- `client.yaml` + at least one `campaign.yaml` with `status: draft`
- Leads available via one of 3 sources (see below)

## Flow

### 1. Get leads

Ask the user how they want to provide leads. Support 3 sources:

**Option A — Source from Lemlist (recommended)**
Use the Lemlist MCP tool `lemleads_search` to find leads matching the campaign's ICP criteria (persona, geo, company size, industry from `campaign.yaml` and `ciblage.md`).
- Present the search results to the user for validation before proceeding
- Once validated, save as `leads.json` in the campaign folder for the pipeline

**Option B — Import CSV/Excel**
If the user provides a CSV or Excel file:
- Read the file and auto-detect column mapping (first name, last name, company, email, LinkedIn URL)
- Show the mapping to the user for confirmation
- Convert to `leads.json` format and save in the campaign folder

**Option C — Manual JSON**
If `leads.json` already exists in the campaign folder, use it directly.

### 2. Verify leads

Read `leads.json` and check:
- Required fields: firstName, lastName, companyName
- Number of leads
- Flag leads without email (Lemlist will attempt findEmail)
- Flag leads without linkedinUrl (LinkedIn channel will be disabled)

### 2. Propose launch

Options:
- **Single campaign**: `python -m pipeline run --campaign {path}`
- **Batch**: `python -m pipeline run --client {path} --campaigns all`
- **Selection**: `python -m pipeline run --client {path} --campaigns C01,C04`
- **Dry run** (no injection): add `--dry-run`

### 3. Launch and monitor

Run the command via Bash.
The pipeline displays progress on stderr.
At the end, read `report.json` (or `report_batch.json`) and display a summary:
- Leads enriched / written / injected
- Any errors
- Estimated cost

### 4. Error handling

If a campaign fails:
- Read `campaign.yaml` → the status indicates where it stopped
- Read `report.json` → error details
- Propose a fix (re-run, fix leads, etc.)
- The `run` command automatically resumes at the right status

### 5. Lemlist injection

If the pipeline is in `--dry-run` mode or without a Lemlist ID:
1. Create the Lemlist campaign via MCP (`create_campaign_with_sequence`)
2. Retrieve the campaign ID
3. Run the injection: `python -m pipeline inject --campaign {path} --lemlist-id {id}`

## Rules
- Always confirm before launching (show estimated cost + number of leads)
- NEVER launch without the user validating the leads
- Show estimated cost before every batch

## Next step
Once campaigns are live, direct the user to: "Run `/outbound-engine:monitor` to track performance."
