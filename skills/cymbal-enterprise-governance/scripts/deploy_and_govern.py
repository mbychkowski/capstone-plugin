#!/usr/bin/env python3
"""Atomic deployment and governance execution for Milestones 3.1, 5.1, 5.2, 5.3, and 5.4."""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

METADATA_PATH = "/workspace/deployment_metadata.json"


def run_cmd(cmd: list[str], check: bool = True) -> str:
  res = subprocess.run(cmd, capture_output=True, text=True, check=check)
  return res.stdout.strip()


def get_project_id() -> str:
  return run_cmd(["gcloud", "config", "get-value", "project"])


def get_token() -> str:
  return run_cmd(["gcloud", "auth", "print-access-token"])


def load_metadata() -> dict:
  if os.path.exists(METADATA_PATH):
    try:
      with open(METADATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      pass
  return {}


def save_metadata(updates: dict) -> dict:
  data = load_metadata()
  data.update(updates)
  os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
  with open(METADATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
  print(f"Updated {METADATA_PATH}: {json.dumps(data)}")
  return data


def api_request(
    method: str, url: str, project_id: str, body: dict | None = None
) -> dict:
  headers = {
      "Authorization": f"Bearer {get_token()}",
      "X-Goog-User-Project": project_id,
      "Content-Type": "application/json",
  }
  data = json.dumps(body).encode("utf-8") if body is not None else None
  req = urllib.request.Request(url, data=data, headers=headers, method=method)
  try:
    with urllib.request.urlopen(req, timeout=90) as resp:
      raw = resp.read().decode("utf-8")
      return json.loads(raw) if raw else {}
  except urllib.error.HTTPError as e:
    err_body = e.read().decode("utf-8", errors="replace")
    print(f"[HTTP {e.code}] {method} {url}: {err_body}")
    raise


def run_step_3_1(project_id: str) -> str:
  """Deploys /workspace/cymbal_agent to Vertex AI Agent Runtime in us-central1 (Milestone 3.1)."""
  sys.path.insert(0, "/workspace")
  import vertexai
  from vertexai import agent_engines
  from cymbal_agent.agent import root_agent

  staging_bucket = f"gs://cymbal-regulations-{project_id}"
  vertexai.init(
      project=project_id,
      location="us-central1",
      staging_bucket=staging_bucket,
  )

  print("[3.1] Deploying cymbal_agent to Vertex AI Agent Runtime (us-central1)...")
  remote_app = agent_engines.create(
      agent_engine=root_agent,
      display_name="cymbal-agent",
      description=(
          "Autonomous regulatory compliance and financial dispute resolution"
          " agent for Cymbal Bank."
      ),
      requirements=[
          "google-cloud-aiplatform[adk,agent_engines]",
          "google-adk",
          "google-genai",
          "google-cloud-bigquery",
          "google-cloud-discoveryengine",
      ],
      extra_packages=["/workspace/cymbal_agent"],
  )
  resource_name = remote_app.resource_name
  print(f"[3.1] Deployed Reasoning Engine: {resource_name}")
  meta = load_metadata()
  save_metadata({
      "reasoning_engine_id": resource_name,
      "deployment_target": "agent_runtime",
      "gemini_enterprise_app": meta.get(
          "gemini_enterprise_app", "cymbal_enterprise_app"
      ),
  })
  return resource_name


def run_step_5_1(project_id: str) -> str:
  """Creates or verifies cymbal_enterprise_app in Gemini Enterprise (Milestone 5.1)."""
  engines_url = (
      f"https://discoveryengine.googleapis.com/v1/projects/{project_id}"
      "/locations/global/collections/default_collection/engines"
  )
  resp = api_request("GET", engines_url, project_id)
  for eng in resp.get("engines", []):
    eng_id = eng["name"].split("/")[-1]
    cfg = eng.get("searchEngineConfig", {})
    if (
        cfg.get("searchTier") == "SEARCH_TIER_ENTERPRISE"
        or cfg.get("requiredSubscriptionTier")
        == "SUBSCRIPTION_TIER_SEARCH_AND_ASSISTANT"
    ):
      print(f"[5.1] Found existing Gemini Enterprise app: {eng_id}")
      save_metadata({"gemini_enterprise_app": eng_id})
      return eng_id

  app_id = "cymbal_enterprise_app"
  create_url = f"{engines_url}?engineId={app_id}"
  body = {
      "displayName": "cymbal_enterprise_app",
      "solutionType": "SOLUTION_TYPE_SEARCH",
      "industryVertical": "GENERIC",
      "appType": "APP_TYPE_INTRANET",
      "dataStoreIds": ["cymbal-regulations-store"],
      "searchEngineConfig": {
          "searchTier": "SEARCH_TIER_ENTERPRISE",
          "requiredSubscriptionTier": "SUBSCRIPTION_TIER_SEARCH_AND_ASSISTANT",
          "searchAddOns": ["SEARCH_ADD_ON_LLM"],
      },
  }
  try:
    api_request("POST", create_url, project_id, body)
    print(f"[5.1] Created Gemini Enterprise app: {app_id}")
    time.sleep(10)
  except Exception as exc:
    print(f"[5.1] Engine creation note: {exc}")
  save_metadata({"gemini_enterprise_app": app_id})
  return app_id


def run_step_5_2(project_id: str) -> None:
  """Registers the deployed ADK agent with Gemini Enterprise (Milestone 5.2)."""
  meta = load_metadata()
  app_id = meta.get("gemini_enterprise_app", "cymbal_enterprise_app")
  re_resource = meta["reasoning_engine_id"]
  app_resource = (
      f"projects/{project_id}/locations/global/collections/default_collection"
      f"/engines/{app_id}"
  )
  cmd = [
      "uvx",
      "--from",
      "google-agents-cli",
      "agents-cli",
      "publish",
      "gemini-enterprise",
      "--gemini-enterprise-app-id",
      app_resource,
      "--reasoning-engine-id",
      re_resource,
      "--registration-type",
      "adk",
      "--display-name",
      "Cymbal Bank Assistant",
      "--description",
      "Autonomous regulatory compliance and dispute resolution assistant",
  ]
  res = subprocess.run(cmd, capture_output=True, text=True, check=False)
  print(f"[5.2] agents-cli publish stdout: {res.stdout} stderr: {res.stderr}")

  agents_url = (
      f"https://discoveryengine.googleapis.com/v1alpha/{app_resource}"
      "/assistants/default_assistant/agents"
  )
  check_resp = api_request("GET", agents_url, project_id)
  if not check_resp.get("agents"):
    body = {
        "displayName": "Cymbal Bank Assistant",
        "description": (
            "Autonomous regulatory compliance and dispute resolution assistant"
        ),
        "adkAgentDefinition": {
            "toolSettings": {
                "toolDescription": (
                    "Adjudicates Cymbal Bank disputes and answers regulatory"
                    " compliance questions using BigQuery and Agent Search."
                )
            },
            "provisionedReasoningEngine": {
                "reasoningEngine": re_resource
            },
        },
    }
    api_request("POST", agents_url, project_id, body)
    print("[5.2] Registered ADK agent via v1alpha assistants/default_assistant/agents.")


def run_step_5_3(project_id: str) -> None:
  """Registers cymbal-agent in Agent Registry (Milestone 5.3)."""
  meta = load_metadata()
  re_resource = meta["reasoning_engine_id"]
  reg_base = (
      f"https://agentregistry.googleapis.com/v1/projects/{project_id}"
      "/locations/us-central1/agents"
  )
  agent_url = f"{reg_base}/cymbal-agent"
  agent_body = {
      "displayName": "Cymbal Bank Regulatory Compliance Agent",
      "description": "Autonomous compliance and financial dispute resolution agent.",
      "reasoningEngine": re_resource,
  }
  try:
    api_request("POST", f"{reg_base}?agentId=cymbal-agent", project_id, agent_body)
    print("[5.3] Created cymbal-agent in Agent Registry.")
  except urllib.error.HTTPError as e:
    if e.code == 409:
      api_request(
          "PATCH",
          f"{agent_url}?updateMask=displayName,description,reasoningEngine",
          project_id,
          agent_body,
      )
      print("[5.3] Updated existing cymbal-agent in Agent Registry.")
    else:
      raise
  save_metadata({"agent_registry_id": "cymbal-agent"})


def run_step_5_4(project_id: str) -> None:
  """Creates cymbal-gateway in Network Services and binds to cymbal-agent (Milestone 5.4)."""
  reg_base = (
      f"https://agentregistry.googleapis.com/v1/projects/{project_id}"
      "/locations/us-central1/agents"
  )
  agent_url = f"{reg_base}/cymbal-agent"
  gw_base = (
      f"https://networkservices.googleapis.com/v1/projects/{project_id}"
      "/locations/us-central1/agentGateways"
  )
  gw_body = {
      "description": (
          "Enterprise Agent Gateway for Cymbal Bank autonomous compliance"
          " operations"
      )
  }
  try:
    api_request(
        "POST", f"{gw_base}?agentGatewayId=cymbal-gateway", project_id, gw_body
    )
    print("[5.4] Created cymbal-gateway in Network Services.")
    time.sleep(5)
  except urllib.error.HTTPError as e:
    if e.code == 409:
      print("[5.4] cymbal-gateway already exists in Network Services.")
    else:
      raise

  gateway_resource = (
      f"projects/{project_id}/locations/us-central1/agentGateways/cymbal-gateway"
  )
  api_request(
      "PATCH",
      f"{agent_url}?updateMask=agentGateway",
      project_id,
      {"agentGateway": gateway_resource},
  )
  print("[5.4] Bound cymbal-gateway to cymbal-agent in Agent Registry.")
  save_metadata({"agent_gateway_id": "cymbal-gateway"})


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument(
      "--step",
      choices=["3.1", "5.1", "5.2", "5.3", "5.4", "all"],
      default="3.1",
      help="Execute atomic milestone 3.1, 5.1, 5.2, 5.3, 5.4, or all.",
  )
  args = parser.parse_args()
  project_id = get_project_id()

  if args.step in ("3.1", "all"):
    run_step_3_1(project_id)
  if args.step in ("5.1", "all"):
    run_step_5_1(project_id)
  if args.step in ("5.2", "all"):
    run_step_5_2(project_id)
  if args.step in ("5.3", "all"):
    run_step_5_3(project_id)
  if args.step in ("5.4", "all"):
    run_step_5_4(project_id)


if __name__ == "__main__":
  main()
