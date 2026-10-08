---
name: cymbal-bq-grounding
description: >-
  Use this skill when executing Milestone 1.1 (creating the cymbal_compliance BigQuery dataset in US and loading
  the 5 operational CSV tables from Cloud Storage) or Milestone 1.3 (populating table and column descriptions
  for all 5 tables in cymbal_compliance). Execute 1.1 and 1.3 as separate atomic steps with a user verification checkpoint after each.
---

# Cymbal Bank — BigQuery Structured Ingestion & Metadata Runbook (Milestones 1.1 & 1.3)

## Overview

This skill separates structured BigQuery work into two strictly isolated milestones using `./scripts/ingest_and_describe_bq.py` (installed at `/workspace/.gemini/skills/cymbal-bq-grounding/scripts/ingest_and_describe_bq.py`):
- **Milestone 1.1 (`--step 1.1`):** Creates BigQuery dataset `cymbal_compliance` in `US` and loads the 5 CSVs from `gs://${PROJECT_ID}-static-assets-bucket/data/structured/`.
- **Milestone 1.3 (`--step 1.3`):** Populates table descriptions and 100% of column descriptions across all 5 tables (`dispute_tickets`, `transaction_ledger`, `analyst_user_mapping`, `regulatory_metadata_registry`, `compliance_qa_audit`).

---

## Milestone 1.1 Execution & Verification

### 1. Run Atomic Step 1.1
```bash
python3 /workspace/.gemini/skills/cymbal-bq-grounding/scripts/ingest_and_describe_bq.py --step 1.1
```

### 2. Run Official Milestone 1.1 Test
```bash
bq ls cymbal_compliance
bq query --nouse_legacy_sql 'SELECT count(*) FROM `cymbal_compliance.dispute_tickets`'
```

### 3. Pause for User Verification (`[CHECKPOINT 1.1]`)
Report the output of `bq ls` and `SELECT count(*)` to the orchestrator/user and **wait for the user to verify Milestone 1.1 on their end** before running Milestone 1.3.

---

## Milestone 1.3 Execution & Verification

### 1. Run Atomic Step 1.3
```bash
python3 /workspace/.gemini/skills/cymbal-bq-grounding/scripts/ingest_and_describe_bq.py --step 1.3
```

### 2. Run Official Milestone 1.3 Test
```bash
bq show --format=prettyjson cymbal_compliance.dispute_tickets
```

### 3. Pause for User Verification (`[CHECKPOINT 1.3]`)
Report the JSON schema output confirming table and column descriptions are populated, and **wait for the user to verify Milestone 1.3 on their end**.
