# Cymbal Bank Capstone — Antigravity Agents & Skills Bundle

This bundle packages **1 Main Orchestrator Agent**, **6 Specialized Sub-Agents**, **7 Modular Skills** (with executable automation scripts), and **1 Global Rule File** designed to execute every milestone (`1.0` through `5.4`) of the Cymbal Bank Autonomous Regulatory Compliance & Dispute Resolution lab.

## Installation

### Option A: Install as an Antigravity Plugin (Recommended)
Copy or symlink this directory into your global Antigravity plugins folder:

```bash
mkdir -p ~/.gemini/config/plugins
cp -r /path/to/cymbal-capstone-plugin ~/.gemini/config/plugins/cymbal-capstone
```

### Option B: Install Directly into `/workspace` on the Lab VM
Copy the skills, agents, and rules into `/workspace/.gemini/` (or `/workspace/_agents/`):

```bash
mkdir -p /workspace/.gemini
cp -r /path/to/cymbal-capstone-plugin/{agents,skills,rules} /workspace/.gemini/
cp /path/to/cymbal-capstone-plugin/rules/AGENTS.md /workspace/AGENTS.md
```

## Included Agents & Skills

| Agent (`agents/*.md`) | Paired Skill (`skills/*/SKILL.md`) | Milestones Handled |
|---|---|---|
| `cymbal-orchestrator` | `cymbal-dag-orchestration` | End-to-end 5-Wave DAG coordinator, gate verifier, and `/workspace/deployment_metadata.json` owner |
| `bq-data-agent` | `cymbal-bq-grounding` | **1.1** (BigQuery dataset + 5 CSV loads) & **1.3** (Table + column descriptions) |
| `policy-search-agent` | `cymbal-policy-search` | **1.2** (GCS bucket + Discovery Engine datastore `cymbal-regulations-store`) & **1.4** (`description` schema + `structData.description` metadata) |
| `adk-core-agent` | `cymbal-adk-agent` | **1.0** (`agents-cli`), **2.1–2.5** (Local ADK server on `:8080`, BQ SQL tool, Agent Search RAG tool, multi-hop synthesis), **4.4–4.6** (Competitor deflection, persona lock, anti-structuring guardrails) |
| `secops-hardening-agent` | `cymbal-secops-hardening` | **4.3a** (Semgrep 8-rule SAST scan = 0 findings) & **4.2** (Least-privilege IAM on Reasoning Engine SA + `DISP-SANITY-998` canary probe) |
| `perf-caching-agent` | `cymbal-context-caching` | **4.1** (Google GenAI `CachedContent` in `global` + warm multi-hop caching achieving $\ge 30\%$ latency drop or `<1.2s`) |
| `runtime-governance-agent` | `cymbal-enterprise-governance` | **3.1–3.5** (Reasoning Engine deploy in `us-central1` + remote `:streamQuery` tests) & **5.1–5.4** (`cymbal_enterprise_app`, `agents-cli publish`, `cymbal-agent` in Agent Registry, `cymbal-gateway` in Network Services) |
