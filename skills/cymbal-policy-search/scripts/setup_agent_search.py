#!/usr/bin/env python3
"""Atomic Agent Search execution for Milestone 1.2 (--step 1.2) and Milestone 1.4 (--step 1.4)."""

import argparse
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request


def run_cmd(cmd: list[str], check: bool = True) -> str:
  res = subprocess.run(cmd, capture_output=True, text=True, check=check)
  return res.stdout.strip()


def get_project_id() -> str:
  return run_cmd(["gcloud", "config", "get-value", "project"])


def get_token() -> str:
  return run_cmd(["gcloud", "auth", "print-access-token"])


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
    with urllib.request.urlopen(req, timeout=60) as resp:
      raw = resp.read().decode("utf-8")
      return json.loads(raw) if raw else {}
  except urllib.error.HTTPError as e:
    err_body = e.read().decode("utf-8", errors="replace")
    print(f"[HTTP {e.code}] {method} {url}: {err_body}")
    raise


def classify_description(filename_or_id: str) -> str:
  lower = filename_or_id.lower()
  if "1005" in lower or "reg_e" in lower or "rege" in lower or "electronic" in lower:
    return (
        "Regulation E (12 CFR Part 1005) — Electronic Fund Transfers: defines"
        " statutory consumer liability tiers under 12 CFR 1005.6(b)(1)-(3)"
        " ($50 cap within 2 business days, $500 cap within 60 calendar days,"
        " and unlimited consumer liability / DENIED_STATUTORY_EXPIRED beyond"
        " 60 days after statement transmittal) and error resolution timelines"
        " under 12 CFR 1005.11 (10 business days investigation, 45 calendar"
        " days with provisional credit)."
    )
  if "ffiec" in lower or "bsa" in lower or "cdd" in lower or "beneficial" in lower:
    return (
        "FFIEC BSA/AML Examination Manual — Customer Due Diligence (CDD) and"
        " Beneficial Ownership Requirements (31 CFR 1010.230): mandates"
        " identification and verification of beneficial owners holding 25% or"
        " more equity interest plus a control-prong individual for legal"
        " entity customers, and ongoing customer risk profiling."
    )
  if "2023-03" in lower or "2023_03" in lower or "cfpb" in lower or "circular" in lower:
    return (
        "CFPB Consumer Financial Protection Circular 2023-03 — Adverse Action"
        " Notification Requirements under Regulation B (ECOA, 12 CFR Part"
        " 1002): requires specific and accurate principal reasons for adverse"
        " credit actions within 30 days, even when complex algorithms or AI"
        " models are used."
    )
  if "2019-a005" in lower or "2019_a005" in lower or "fincen" in lower or "advisory" in lower:
    return (
        "FinCEN Advisory FIN-2019-A005 — Bank Secrecy Act (BSA) obligations"
        " regarding Business Email Compromise (BEC), funnel/mule accounts,"
        " Currency Transaction Reports (CTR over $10,000 under 31 CFR"
        " 1010.311), Suspicious Activity Reports (SAR within 30 days under 31"
        " CFR 1020.320), USA PATRIOT Act due diligence, and federal felony"
        " prohibitions against structuring (31 U.S.C. 5324)."
    )
  return (
      "Cymbal Bank Supervisory and Internal Governance Manual — covers"
      " Regulation Z (12 CFR Part 1026, Truth in Lending Act, including the"
      " standard 3 business days right of rescission under 12 CFR 1026.15/23"
      " and billing error resolution rules) and Federal Reserve SR 11-7"
      " Supervisory Guidance on Model Risk Management."
  )


def wait_for_lro(op_name: str, project_id: str, max_wait_s: int = 180) -> None:
  url = f"https://discoveryengine.googleapis.com/v1/{op_name}"
  deadline = time.time() + max_wait_s
  while time.time() < deadline:
    try:
      op = api_request("GET", url, project_id)
      if op.get("done"):
        print(f"LRO completed: {op_name}")
        return
    except Exception:
      pass
    time.sleep(5)
  print(f"LRO still in progress after {max_wait_s}s: {op_name}")


def run_step_1_2(project_id: str) -> None:
  bucket_name = f"cymbal-regulations-{project_id}"
  src_prefix = f"gs://{project_id}-static-assets-bucket/data/policies/*"
  dst_bucket = f"gs://{bucket_name}"

  buckets = run_cmd(
      ["gcloud", "storage", "buckets", "list", f"--project={project_id}"],
      check=False,
  )
  if bucket_name not in buckets:
    run_cmd([
        "gcloud",
        "storage",
        "buckets",
        "create",
        dst_bucket,
        "--location=us-central1",
        f"--project={project_id}",
    ])
    print(f"[1.2] Created bucket {dst_bucket} in us-central1.")
  else:
    print(f"[1.2] Bucket {dst_bucket} already exists.")

  run_cmd(["gcloud", "storage", "cp", src_prefix, f"{dst_bucket}/"])
  ls_out = run_cmd(["gcloud", "storage", "ls", dst_bucket])
  uris = [
      line.strip()
      for line in ls_out.splitlines()
      if line.strip().startswith("gs://") and not line.strip().endswith("/")
  ]
  print(f"[1.2] Copied {len(uris)} policy files: {uris}")

  base_ds_url = (
      f"https://discoveryengine.googleapis.com/v1/projects/{project_id}"
      "/locations/global/collections/default_collection/dataStores"
  )
  ds_url = f"{base_ds_url}/cymbal-regulations-store"
  try:
    api_request("GET", ds_url, project_id)
    print("[1.2] Datastore cymbal-regulations-store already exists.")
  except urllib.error.HTTPError as e:
    if e.code == 404:
      create_url = f"{base_ds_url}?dataStoreId=cymbal-regulations-store"
      body = {
          "displayName": "cymbal-regulations-store",
          "industryVertical": "GENERIC",
          "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
          "contentConfig": "CONTENT_REQUIRED",
      }
      api_request("POST", create_url, project_id, body)
      print("[1.2] Created datastore cymbal-regulations-store.")
      time.sleep(5)
    else:
      raise

  import_url = f"{ds_url}/branches/default_branch/documents:import"
  import_body = {
      "gcsSource": {
          "inputUris": [f"{dst_bucket}/*"],
          "dataSchema": "content",
      },
      "reconciliationMode": "INCREMENTAL",
  }
  try:
    op = api_request("POST", import_url, project_id, import_body)
    if "name" in op:
      wait_for_lro(op["name"], project_id, max_wait_s=120)
  except Exception as ex:
    print(f"[1.2] Import note: {ex}")


def run_step_1_4(project_id: str) -> None:
  dst_bucket = f"gs://cymbal-regulations-{project_id}"
  ds_url = (
      f"https://discoveryengine.googleapis.com/v1/projects/{project_id}"
      "/locations/global/collections/default_collection/dataStores/cymbal-regulations-store"
  )
  schema_url = f"{ds_url}/schemas/default_schema"
  schema_body = {
      "structSchema": {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "properties": {
              "description": {
                  "type": "string",
                  "retrievable": True,
                  "indexable": True,
                  "searchable": True,
              },
              "title": {
                  "type": "string",
                  "retrievable": True,
                  "indexable": True,
                  "searchable": True,
              },
          },
      }
  }
  try:
    op = api_request("PATCH", schema_url, project_id, schema_body)
    if "name" in op and "operations/" in op["name"]:
      wait_for_lro(op["name"], project_id, max_wait_s=90)
    print("[1.4] Registered 'description' in datastore default_schema.")
  except Exception as ex:
    print(f"[1.4] Schema update note: {ex}")

  ls_out = run_cmd(["gcloud", "storage", "ls", dst_bucket])
  uris = [
      line.strip()
      for line in ls_out.splitlines()
      if line.strip().startswith("gs://") and not line.strip().endswith("/")
  ]

  docs_url = f"{ds_url}/branches/default_branch/documents"
  docs_resp = api_request("GET", docs_url, project_id)
  existing_docs = docs_resp.get("documents", [])

  if existing_docs:
    for doc in existing_docs:
      doc_id = doc["id"]
      uri = doc.get("content", {}).get("uri", doc_id)
      mime = doc.get("content", {}).get(
          "mimeType",
          "text/markdown" if uri.endswith(".md") else "application/pdf",
      )
      desc = classify_description(uri)
      patch_url = f"{docs_url}/{doc_id}"
      patch_body = {
          "id": doc_id,
          "structData": {
              "description": desc,
              "title": os.path.basename(uri),
          },
          "content": {
              "uri": uri,
              "mimeType": mime,
          },
      }
      api_request("PATCH", patch_url, project_id, patch_body)
      print(f"[1.4] Patched structData.description on doc id={doc_id} ({uri})")
  else:
    for uri in uris:
      base = os.path.basename(uri)
      doc_id = re.sub(r"[^a-zA-Z0-9_-]", "_", os.path.splitext(base)[0])
      mime = "text/markdown" if uri.endswith(".md") else "application/pdf"
      desc = classify_description(base)
      put_url = f"{docs_url}?documentId={doc_id}"
      doc_body = {
          "id": doc_id,
          "structData": {
              "description": desc,
              "title": base,
          },
          "content": {
              "uri": uri,
              "mimeType": mime,
          },
      }
      api_request("POST", put_url, project_id, doc_body)
      print(f"[1.4] Created document id={doc_id} with structData.description")


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument(
      "--step",
      choices=["1.2", "1.4", "all"],
      default="all",
      help="Run atomic milestone 1.2, 1.4, or both.",
  )
  args = parser.parse_args()
  project_id = get_project_id()

  if args.step in ("1.2", "all"):
    run_step_1_2(project_id)
  if args.step in ("1.4", "all"):
    run_step_1_4(project_id)


if __name__ == "__main__":
  main()
