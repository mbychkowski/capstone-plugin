# Cymbal Bank Capstone — Global Agent & Sub-Agent Rules

These rules apply across the main orchestrator and all specialized sub-agents executing the Cymbal Bank Regulatory Compliance & Dispute Resolution lab milestones.

## 1. Regional & Resource Naming Invariants

All provisioned Google Cloud resources MUST strictly adhere to these identifiers and regions:

| Resource Component | Exact Identifier / URI | Region / Location |
|---|---|---|
| Raw Structured CSVs (Source) | `gs://${PROJECT_ID}-static-assets-bucket/data/structured/` (`dispute_tickets`, `transaction_ledger`, `analyst_user_mapping`, `regulatory_metadata_registry`, `compliance_qa_audit`) | Cloud Storage (read directly via `gs://`) |
| Raw Policy Manuals (Source) | `gs://${PROJECT_ID}-static-assets-bucket/data/policies/*` (4 PDFs, 1 `.md`) | Cloud Storage |
| BigQuery Operational Dataset | `cymbal_compliance` | `US` (multi-region) |
| Policy Datastore Bucket | `gs://cymbal-regulations-${PROJECT_ID}` | `us-central1` |
| Agent Search Datastore | `cymbal-regulations-store` | `global` (`default_collection`) |
| Local ADK Agent Package | `/workspace/cymbal_agent` (`agent.py` exporting `root_agent`) | Local VM (`0.0.0.0:8080`) |
| Vertex AI Agent Runtime | Reasoning Engine (`cymbal_agent`) | `us-central1` |
| GenAI Context Cache | `CachedContent` on approved Gemini 3.x model | `global` (and `us-central1` if supported) |
| Gemini Enterprise App | `cymbal_enterprise_app` (`SEARCH_TIER_ENTERPRISE` / `SUBSCRIPTION_TIER_SEARCH_AND_ASSISTANT`) | `global` (`default_collection`) |
| Agent Registry Resource | `cymbal-agent` (`agentregistry.googleapis.com`) | `us-central1` |
| Agent Gateway Resource | `cymbal-gateway` (`networkservices.googleapis.com`) | `us-central1` |

## 2. Deployment Metadata Contract (`/workspace/deployment_metadata.json`)

Every deployment and governance step in Phases 3 and 5 MUST read and atomically update `/workspace/deployment_metadata.json` without clobbering existing keys. The completed JSON contract is:

```json
{
  "reasoning_engine_id": "projects/<PROJECT_ID>/locations/us-central1/reasoningEngines/<REASONING_ENGINE_ID>",
  "deployment_target": "agent_runtime",
  "gemini_enterprise_app": "cymbal_enterprise_app",
  "agent_registry_id": "cymbal-agent",
  "agent_gateway_id": "cymbal-gateway"
}
```

## 3. Strict 25-Second SLA & Anti-Hardcoding Policy

- **Request-Time Grounding Mandatory:** Every live evaluation query has a strict **25-second platform timeout**. Answers MUST be retrieved dynamically from BigQuery (`cymbal_compliance`) and Agent Search (`cymbal-regulations-store`) at request time.
- **Zero Hardcoding of Test Fixtures:** Never hardcode specific ticket IDs (`DISP-99203`, `DISP-99205`, `DISP-99201`), account IDs (`ACCT-10293`, `ACCT-33109`, `ACCT-88301`), or canned test answers in `agent.py`. Graded evaluation probes use unseen dispute IDs and accounts.
- **Fast Client Initialization:** Initialize `bigquery.Client`, Discovery Engine `SearchServiceClient`, and `google.genai.Client` lazily as module-level singletons so cold per-turn client instantiation never adds latency.

## 4. Semgrep SAST & Approved Model Standard

- Before authoring `/workspace/cymbal_agent/agent.py` or creating `CachedContent`, ALWAYS read `/opt/security/rules.yaml` to verify all 8 Semgrep rules (including the 8th Cymbal Bank internal engineering standard).
- Never use deprecated models (`gemini-1.x`, `gemini-2.x`, `gemini-3.0`, or `bison`). Use the approved current-generation Gemini 3.x model permitted by `/opt/security/rules.yaml` across both `root_agent` and `CachedContent`.
- Never use Python string interpolation (`f"..."`, `.format()`, `%`) to build SQL strings, never include literal `INSERT`/`UPDATE`/`DELETE`/`DROP` statements in Python source files, never use `eval`/`exec`/`shell=True`, never pass dynamic paths to `open()`, and never log sensitive PII/credential variable names.
