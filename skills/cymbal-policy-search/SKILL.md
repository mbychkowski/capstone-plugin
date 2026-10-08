---
name: cymbal-policy-search
description: >-
  Use this skill when executing Milestone 1.2 (creating gs://cymbal-regulations-${PROJECT_ID} in us-central1,
  copying the 5 regulatory policy manuals, and creating/importing the cymbal-regulations-store datastore
  in Agent Search) or Milestone 1.4 (registering the description metadata field in the datastore schema and
  populating structData.description on all 5 policy documents). Execute 1.2 and 1.4 as separate atomic steps with a user verification checkpoint after each.
---

# Cymbal Bank — Agent Search Unstructured Policy & Metadata Runbook (Milestones 1.2 & 1.4)

## Overview

This skill separates unstructured policy work into two strictly isolated milestones using `./scripts/setup_agent_search.py` (installed at `/workspace/.gemini/skills/cymbal-policy-search/scripts/setup_agent_search.py`):
- **Milestone 1.2 (`--step 1.2`):** Creates `gs://cymbal-regulations-${PROJECT_ID}` (`us-central1`), copies the 5 policy files from `gs://${PROJECT_ID}-static-assets-bucket/data/policies/*`, creates Discovery Engine datastore `cymbal-regulations-store` (`global`), and imports the documents.
- **Milestone 1.4 (`--step 1.4`):** Registers `description` in the `cymbal-regulations-store` schema and populates `structData.description` on all 5 documents (Reg E `12 CFR 1005`, FFIEC BSA/AML `CDD and beneficial ownership`, CFPB Circular `2023-03`, FinCEN Advisory `FIN-2019-A005`, and Cymbal Bank manual covering `Regulation Z and SR 11-7`).

---

## Milestone 1.2 Execution & Verification

### 1. Run Atomic Step 1.2
```bash
python3 /workspace/.gemini/skills/cymbal-policy-search/scripts/setup_agent_search.py --step 1.2
```

### 2. Run Official Milestone 1.2 Test
```bash
curl -s -X GET \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "X-Goog-User-Project: $(gcloud config get-value project)" \
  "https://discoveryengine.googleapis.com/v1/projects/$(gcloud config get-value project)/locations/global/collections/default_collection/dataStores/cymbal-regulations-store" \
  | jq -r '{name: .name, displayName: .displayName, contentConfig: .contentConfig}'
```

### 3. Pause for User Verification (`[CHECKPOINT 1.2]`)
Present the test output and **wait for the user to verify Milestone 1.2 on their end** before running Milestone 1.4.

---

## Milestone 1.4 Execution & Verification

### 1. Run Atomic Step 1.4
```bash
python3 /workspace/.gemini/skills/cymbal-policy-search/scripts/setup_agent_search.py --step 1.4
```

### 2. Run Official Milestone 1.4 Test
```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://discoveryengine.googleapis.com/v1/projects/$(gcloud config get-value project)/locations/global/collections/default_collection/dataStores/cymbal-regulations-store/branches/default_branch/documents" \
  | jq '.documents[]? | {id: .id, description: .structData.description}'
```

### 3. Pause for User Verification (`[CHECKPOINT 1.4]`)
Present the output showing `.id` and `.structData.description` for all 5 documents, and **wait for the user to verify Milestone 1.4 on their end**.
