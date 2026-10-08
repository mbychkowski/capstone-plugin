---
name: cymbal-enterprise-governance
description: >-
  Use this skill when executing Milestones 3.1 through 3.5 (deploying cymbal_agent to Vertex AI Agent Runtime
  in us-central1, writing /workspace/deployment_metadata.json, and running remote streamQuery checks)
  and Milestones 5.1 through 5.4 (creating cymbal_enterprise_app in Gemini Enterprise, publishing via
  agents-cli, registering cymbal-agent in Agent Registry, and creating/binding cymbal-gateway in
  Network Services). Execute each milestone as an isolated step and pause for user verification after each test.
---

# Cymbal Bank — Agent Runtime Deployment & Enterprise Governance Runbook (Phases 3 & 5)

## Overview

Uses `/workspace/.gemini/skills/cymbal-enterprise-governance/scripts/deploy_and_govern.py` with `--step <milestone>` so each milestone in Phase 3 (`3.1`–`3.5`) and Phase 5 (`5.1`–`5.4`) runs atomically and pauses for user verification.

---

## Phase 3: Deploy to Agent Runtime & Verify (`3.1` – `3.5`)

### Milestone `3.1` — Deploy to Vertex AI Agent Runtime
```bash
python3 /workspace/.gemini/skills/cymbal-enterprise-governance/scripts/deploy_and_govern.py --step 3.1
```
**Test:**
```bash
cat /workspace/deployment_metadata.json | jq .reasoning_engine_id
export PROJECT_ID=$(gcloud config get-value project)
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/reasoningEngines" \
  | jq '.reasoningEngines[]? | {name: .name, displayName: .displayName, createTime: .createTime}'
```
*Pause at `[CHECKPOINT 3.1]` for user verification.*

### Milestone `3.2` — Verify Deployed Conversational Greeting
```bash
export PROJECT_ID=$(gcloud config get-value project)
export REASONING_ENGINE_ID=$(cat /workspace/deployment_metadata.json | jq -r '.reasoning_engine_id | split("/") | .[-1]')

curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d '{"class_method":"stream_query","input":{"message":"Hello, can you help me with my Cymbal Bank dispute claim? Be succinct in your answer.","user_id":"test-user"}}' \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery"
```
*Pause at `[CHECKPOINT 3.2]` for user verification.*

### Milestone `3.3` — Verify Deployed Unstructured Policy Query (Reg Z)
```bash
export PROJECT_ID=$(gcloud config get-value project)
export REASONING_ENGINE_ID=$(cat /workspace/deployment_metadata.json | jq -r '.reasoning_engine_id | split("/") | .[-1]')

curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d '{"class_method":"stream_query","input":{"message":"Under Reg Z, how many business days is the standard rescission period? Be succinct in your answer.","user_id":"test-user"}}' \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery"
```
*Pause at `[CHECKPOINT 3.3]` for user verification.*

### Milestone `3.4` — Verify Deployed Structured Data Query (`DISP-99203`)
```bash
export PROJECT_ID=$(gcloud config get-value project)
export REASONING_ENGINE_ID=$(cat /workspace/deployment_metadata.json | jq -r '.reasoning_engine_id | split("/") | .[-1]')

curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d '{"class_method":"stream_query","input":{"message":"What is the account ID, customer tier, claim type, and disputed amount for dispute ticket DISP-99203? Be succinct in your answer.","user_id":"test-user"}}' \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery"
```
*Pause at `[CHECKPOINT 3.4]` for user verification.*

### Milestone `3.5` — Verify Deployed Multi-Hop Synthesis (`DISP-99205`)
```bash
export PROJECT_ID=$(gcloud config get-value project)
export REASONING_ENGINE_ID=$(cat /workspace/deployment_metadata.json | jq -r '.reasoning_engine_id | split("/") | .[-1]')

curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d '{"class_method":"stream_query","input":{"message":"Dispute DISP-99205 on ACCT-33109 was reported 70 days after statement. Why was provisional credit denied under Reg E, and what is the credit status in the dispute record? Be succinct in your answer.","user_id":"test-user"}}' \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery"
```
*Pause at `[CHECKPOINT 3.5]` for user verification.*

---

## Phase 5: Enterprise Readiness & Governance (`5.1` – `5.4`)

### Milestone `5.1` — Create Gemini Enterprise Application
```bash
python3 /workspace/.gemini/skills/cymbal-enterprise-governance/scripts/deploy_and_govern.py --step 5.1
```
**Test:**
```bash
export PROJECT_ID=$(gcloud config get-value project)
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://discoveryengine.googleapis.com/v1/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines" \
  | jq -r '.engines[]? | {id: (.name | split("/") | .[-1]), displayName: .displayName, tier: .searchEngineConfig.searchTier, subscriptionTier: .searchEngineConfig.requiredSubscriptionTier}'
```
*Pause at `[CHECKPOINT 5.1]` for user verification.*

### Milestone `5.2` — Register Agent with Gemini Enterprise
```bash
python3 /workspace/.gemini/skills/cymbal-enterprise-governance/scripts/deploy_and_govern.py --step 5.2
```
**Test:**
```bash
export PROJECT_ID=$(gcloud config get-value project)
export GEMINI_APP_ID=$(cat /workspace/deployment_metadata.json 2>/dev/null | jq -r '.gemini_enterprise_app // "cymbal_enterprise_app"')
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${GEMINI_APP_ID}/assistants/default_assistant/agents" \
  | jq -r '.agents[]? | {name: .name, displayName: .displayName, state: .state, target: (.adkAgentDefinition.provisionedReasoningEngine.reasoningEngine // .a2aAgentDefinition.jsonAgentCard // "custom")}'
```
*Pause at `[CHECKPOINT 5.2]` for user verification.*

### Milestone `5.3` — Register Agent in Google Cloud Agent Registry
```bash
python3 /workspace/.gemini/skills/cymbal-enterprise-governance/scripts/deploy_and_govern.py --step 5.3
```
**Test:**
```bash
export PROJECT_ID=$(gcloud config get-value project)
curl -s -X GET \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://agentregistry.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/agents/cymbal-agent" | jq .
```
*Pause at `[CHECKPOINT 5.3]` for user verification.*

### Milestone `5.4` — Create Agent Gateway and Bind to Agent Registry
```bash
python3 /workspace/.gemini/skills/cymbal-enterprise-governance/scripts/deploy_and_govern.py --step 5.4
```
**Test:**
```bash
export PROJECT_ID=$(gcloud config get-value project)
curl -s -X GET \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://networkservices.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/agentGateways/cymbal-gateway" | jq .
curl -s -X GET \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://agentregistry.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/agents/cymbal-agent" | jq '{name: .name, agentGateway: .agentGateway}'
```
*Pause at `[CHECKPOINT 5.4]` for final user verification.*
