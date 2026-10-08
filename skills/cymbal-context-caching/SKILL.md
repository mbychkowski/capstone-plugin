---
name: cymbal-context-caching
description: >-
  Use this skill when executing Milestone 4.1 (creating explicit Google GenAI CachedContent resources in
  global and us-central1 on the approved current-generation Gemini 3.x model for Cymbal Bank policy
  documents, and verifying >=30% warm-cache latency reduction or <1.2s response time on DISP-99201).
---

# Cymbal Bank — Google GenAI Context Caching & Latency Optimization (Milestone 4.1)

## Overview

Milestone 4.1 evaluates two complementary criteria:
1. **Deterministic `CachedContent` Check:** An explicit Google GenAI `CachedContent` resource exists in `global` (where current-generation Gemini 3.x models are served) or `us-central1`, created on the **exact approved current-generation Gemini 3.x model** used by `cymbal_agent` (never deprecated Gemini 1.x, 2.x, 3.0, or bison).
2. **Empirical Warm-Hit Latency Check:** Executing the complex multi-hop query for `DISP-99201` on `ACCT-88301` twice against `:streamQuery` achieves at least a **30% latency reduction** on Run 2 compared to Run 1 (or completes in `<1.2s`), while returning accurate facts.

---

## Step 1: Provision Explicit `CachedContent` Resource

```bash
python3 /workspace/.gemini/skills/cymbal-context-caching/scripts/create_context_cache.py
```

---

## Step 2: Run Official Milestone 4.1 Cold vs. Warm Test

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REASONING_ENGINE_ID=$(cat /workspace/deployment_metadata.json 2>/dev/null | jq -r '.reasoning_engine_id | split("/") | .[-1]')

echo "--- Run 1 (Cold / Initial Ingestion) ---"
time curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d '{
    "class_method": "stream_query",
    "input": {
      "message": "Dispute DISP-99201 on account ACCT-88301 was reported 15 days after statement transmittal. Which Reg E § 1005.6(b) tier applies, what is the consumer liability cap, and what provisional credit was allocated? Be succinct in your answer.",
      "user_id": "test-user"
    }
  }' \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery"

echo -e "\n--- Run 2 (Warm / Cached Hit) ---"
time curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d '{
    "class_method": "stream_query",
    "input": {
      "message": "Dispute DISP-99201 on account ACCT-88301 was reported 15 days after statement transmittal. Which Reg E § 1005.6(b) tier applies, what is the consumer liability cap, and what provisional credit was allocated? Be succinct in your answer.",
      "user_id": "test-user"
    }
  }' \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery"
```
*Pause at `[CHECKPOINT 4.1]` for user verification.*
