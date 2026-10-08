---
name: cymbal-dag-orchestration
description: >-
  Stable-State Parallel DAG orchestration runbook for the Cymbal Bank Regulatory Compliance & Dispute Resolution Capstone.
  Use this skill to execute Milestones 1.0 through 5.4 with maximum concurrency across 4 monotonic execution waves,
  ensuring every passed test enters a permanent stable state that never regresses as downstream tasks execute.
---

# Cymbal Bank Capstone — Stable-State Parallel DAG Orchestration Runbook

## Architectural Invariant: Tests as Monotonic Stable States

A milestone can be executed in parallel or out of numerical sequence **if and only if**:
1. Its true technical dependencies are satisfied.
2. Its execution is **state-monotonic** — meaning it never overwrites, stops, or invalidates the passing test state of any earlier milestone.

### The 3 State-Mutation Hazards (And How This DAG Eliminates Them)

| Potential Mutation Hazard | What Would Break If Done Naïvely | How the 4-Wave DAG Eliminates It |
|---|---|---|
| **Hazard 1: Editing `agent.py` in Phase 4 after deploying `3.1`** | Redeploying `3.1` changes `REASONING_ENGINE_ID` in `/workspace/deployment_metadata.json`, invalidating `3.1`–`3.5` and breaking `5.2`/`5.3` bindings if already created. | All `agent.py` requirements (`2.1`–`2.5`, `4.3a` SAST, `4.4` Competitor, `4.5` Persona, `4.6` Structuring) are built and verified in **Wave 2** *before* `3.1` deploys in **Wave 3**. `3.1` is deployed **once**; `REASONING_ENGINE_ID` is immutable. |
| **Hazard 2: Locking down BigQuery IAM (`4.2`) before `1.1`, `1.3`, or `3.1`** | Stripping `roles/editor` or `bigquery.admin` too early could block table creation (`1.1`), schema description updates (`1.3`), or staging bucket writes (`3.1`). | `4.2` is strictly gated to **Wave 4** (after `1.1`, `1.3`, and `3.1` are locked in) and only strips write roles while preserving `bigquery.dataViewer` and `bigquery.jobUser` (so `2.3`, `2.5`, `3.4`, `3.5`, and `4.1` continue passing forever). |
| **Hazard 3: Stopping `localhost:8080` (`2.1`) after Phase 2** | If the local ADK server is killed after `2.5`, a later grader check on `2.1` (`http://localhost:8080/docs`) fails. | `adk api_server --host 0.0.0.0 --port 8080` runs as a persistent background daemon (`nohup ... &`) from Wave 2 through the end of the lab. |

---

## Wave 1: Parallel Data Grounding, SAST Discovery & Standalone Gateway (5 Concurrent Sub-Agent Tracks)

All 5 tracks below have **zero upstream dependencies** and operate on completely disjoint resources. Dispatch them in parallel via `invoke_subagent`:

1. **Track 1A — `bq-data-agent` (`1.1` $\rightarrow$ `1.3`):**
   - Run `python3 /workspace/.gemini/skills/cymbal-bq-grounding/scripts/ingest_and_describe_bq.py --step all`
   - Creates `cymbal_compliance` (`US`), loads all 5 CSVs (`1.1`), and populates 100% of table and column descriptions (`1.3`).
   - *Why `1.1` + `1.3` together is safe:* Adding table/column descriptions in `1.3` is purely additive; both `1.1` (`bq ls` & `SELECT count(*)`) and `1.3` (`bq show --format=prettyjson`) pass simultaneously and permanently.
2. **Track 1B — `policy-search-agent` (`1.2` $\rightarrow$ `1.4`):**
   - Run `python3 /workspace/.gemini/skills/cymbal-policy-search/scripts/setup_agent_search.py --step all`
   - Creates `gs://cymbal-regulations-${PROJECT_ID}` (`us-central1`), copies the 5 policy files, creates `cymbal-regulations-store` (`global`), imports docs (`1.2`), registers `description` in `default_schema`, and patches `structData.description` on all 5 docs (`1.4`).
   - *Why `1.2` + `1.4` together is safe:* `1.4` only enriches document metadata; `1.2` (`GET .../dataStores/cymbal-regulations-store`) and `1.4` (`GET .../documents`) pass simultaneously and permanently.
3. **Track 1C — `adk-core-agent` (`1.0`):**
   - Install and verify `uvx google-agents-cli --help`.
4. **Track 1D — `secops-hardening-agent` (`4.3a-pre`):**
   - Read `/opt/security/rules.yaml` to extract all 8 Semgrep SAST rules (including Rule #8's approved Gemini 3.x model regex).
5. **Track 1E — `runtime-governance-agent` (`5.4a`):**
   - Pre-create the standalone Network Services `cymbal-gateway` resource (`POST .../locations/us-central1/agentGateways?agentGatewayId=cymbal-gateway`).

### Wave 1 Stable-State Checkpoint (`[WAVE 1 COMPLETE]`)
- **Milestones Locked in Permanent Passing State:** **`1.0`, `1.1`, `1.2`, `1.3`, `1.4`**
- Present the verification outputs for `1.1`, `1.2`, `1.3`, and `1.4` to the user. The user can verify all of Phase 1 on their end at any time; Wave 2 will never alter Phase 1 state.

---

## Wave 2: Parallel Local Agent Construction, SAST Gate, Context Cache & Enterprise App (4 Concurrent Sub-Agent Tracks)

Depends on Wave 1 (`1.0`–`1.4`, `4.3a-pre`). Dispatch in parallel:

1. **Track 2A — `adk-core-agent` (`2.1`, `2.2`, `2.3`, `2.4`, `2.5`, plus `4.4–4.6` instructions):**
   - Scaffold `/workspace/cymbal_agent/agent.py` (using the approved Gemini 3.x model from `4.3a-pre` and live schema from `1.3`), start `adk api_server --host 0.0.0.0 --port 8080` in background (`2.1`), and execute local verification tests for `2.2` (greeting), `2.3` (`DISP-99203`), `2.4` (Reg Z `3 business days`), and `2.5` (`DISP-99205` $\rightarrow$ `1005.6(b)(3)` 60-day Tier 3 window & `DENIED_STATUTORY_EXPIRED`).
2. **Track 2B — `secops-hardening-agent` (`4.3a`):**
   - Once `agent.py` is written in Track 2A, run:
     ```bash
     semgrep scan --config=/opt/security/rules.yaml --error --exclude="venv" --exclude=".venv" --exclude="__pycache__" /workspace/cymbal_agent/
     ```
   - Verify `Ran 8 rules ... 0 findings` (exit code `0`).
3. **Track 2C — `perf-caching-agent` (`4.1a`):**
   - Run `python3 /workspace/.gemini/skills/cymbal-context-caching/scripts/create_context_cache.py` to provision explicit `CachedContent` in `global` (and `us-central1`) on the approved Gemini 3.x model with a 2-hour TTL.
4. **Track 2D — `runtime-governance-agent` (`5.1`):**
   - Run `python3 /workspace/.gemini/skills/cymbal-enterprise-governance/scripts/deploy_and_govern.py --step 5.1` to create Gemini Enterprise app `cymbal_enterprise_app` (`SEARCH_TIER_ENTERPRISE` / `SUBSCRIPTION_TIER_SEARCH_AND_ASSISTANT`) in `global`.

### Wave 2 Stable-State Checkpoint (`[WAVE 2 COMPLETE]`)
- **Cumulative Milestones Locked in Permanent Passing State:** **`1.0`–`1.4`, `2.1`, `2.2`, `2.3`, `2.4`, `2.5`, `4.3a`, `5.1`**
- Present the verification outputs for `2.1`–`2.5`, `4.3a`, and `5.1`. None of these will ever change in Waves 3 or 4.

---

## Wave 3: Single Immutable Deployment to Vertex AI Agent Runtime (`3.1`)

Depends on Wave 2 (`2.5`, `4.3a`, `4.1a`).

1. **Track 3A — `runtime-governance-agent` (`3.1`):**
   - Run `python3 /workspace/.gemini/skills/cymbal-enterprise-governance/scripts/deploy_and_govern.py --step 3.1`
   - Deploys the fully hardened `/workspace/cymbal_agent` to Vertex AI Agent Runtime (`reasoningEngines` in `us-central1`) **once** and writes `reasoning_engine_id` + `deployment_target: "agent_runtime"` to `/workspace/deployment_metadata.json`.

### Wave 3 Stable-State Checkpoint (`[WAVE 3 COMPLETE]`)
- **Cumulative Milestones Locked in Permanent Passing State:** **`1.0`–`1.4`, `2.1`–`2.5`, `3.1`, `4.3a`, `5.1`**

---

## Wave 4: Parallel Post-Deploy IAM Lockdown, Remote Verification & Governance Binding (3 Concurrent Sub-Agent Tracks)

Depends on Wave 3 (`3.1`). All 3 tracks run concurrently against the immutable `REASONING_ENGINE_ID`:

1. **Track 4A — `secops-hardening-agent` (`4.2`):**
   - Run `bash /workspace/.gemini/skills/cymbal-secops-hardening/scripts/lock_down_iam.sh`
   - Strips BigQuery write roles (`dataEditor`, `admin`, `editor`) from the Reasoning Engine SA while keeping `roles/bigquery.dataViewer` and `roles/bigquery.jobUser`.
   - Dispatches the `DISP-SANITY-998` adversarial write probe and verifies `SELECT count(*) ... WHERE dispute_id = 'DISP-SANITY-998'` returns `0`.
2. **Track 4B — `perf-caching-agent` (`4.1b`):**
   - Runs Cold (Run 1) and Warm (Run 2) `:streamQuery` calls on `DISP-99201` (`ACCT-88301`) and verifies Run 2 is $\ge 30\%$ faster or `<1.2s` alongside the active `CachedContent` resource.
3. **Track 4C — `runtime-governance-agent` (`3.2`–`3.5`, `4.4`–`4.6`, `5.2`, `5.3`, `5.4`):**
   - Runs remote `:streamQuery` verification for `3.2` (greeting), `3.3` (Reg Z), `3.4` (`DISP-99203`), `3.5` (`DISP-99205`), `4.4` (Chase competitor deflection), `4.5` (`ComedianBot` persona defense), and `4.6` (\$47,000 structuring refusal + BSA/FinCEN citations).
   - Runs `deploy_and_govern.py --step 5.2` (publish agent to `cymbal_enterprise_app` & verify on `v1alpha`), `--step 5.3` (register `cymbal-agent` in Agent Registry), and `--step 5.4` (bind `cymbal-gateway` to `cymbal-agent` via `PATCH ?updateMask=agentGateway` and finalize `/workspace/deployment_metadata.json`).

### Wave 4 Stable-State Checkpoint (`[WAVE 4 COMPLETE — ALL 21 MILESTONES STABLE]`)
- **All 21 Milestones (`1.0` through `5.4`) are now simultaneously in their final, permanent passing states.** The user can verify any remaining milestones in the lab UI in any order without any risk of state conflict or regression.
