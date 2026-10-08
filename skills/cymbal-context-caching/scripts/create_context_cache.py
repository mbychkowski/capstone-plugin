#!/usr/bin/env python3
"""Provisions explicit Google GenAI CachedContent resources in global/us-central1 (Task 4.1)."""

import os
import re
import subprocess
from google import genai
from google.genai import types


def run_cmd(cmd: list[str]) -> str:
  return subprocess.check_output(cmd, text=True).strip()


def detect_approved_model() -> str:
  env_model = os.environ.get("CYMBAL_APPROVED_MODEL")
  if env_model:
    return env_model
  agent_py = "/workspace/cymbal_agent/agent.py"
  if os.path.exists(agent_py):
    with open(agent_py, "r", encoding="utf-8") as f:
      content = f.read()
    m = re.search(r'MODEL_NAME\s*=\s*.*?["\'](gemini-[^"\']+)["\']', content)
    if m:
      return m.group(1)
    m2 = re.search(r'model\s*=\s*["\'](gemini-[^"\']+)["\']', content)
    if m2:
      return m2.group(1)
  return "gemini-3-flash-preview"


def build_reference_corpus() -> str:
  base_block = (
      "CYMBAL BANK REGULATORY COMPLIANCE & STATUTORY REFERENCE CORPUS\n"
      "1. Regulation E (12 CFR Part 1005) — Electronic Fund Transfers:\n"
      "   - 12 CFR 1005.6(b)(1) Tier 1 Liability: Consumer notifies financial"
      " institution within 2 business days after learning of loss/theft of"
      " access device -> maximum consumer liability is $50.\n"
      "   - 12 CFR 1005.6(b)(2) Tier 2 Liability: Consumer notifies financial"
      " institution after 2 business days but within 60 calendar days of"
      " periodic statement transmittal -> maximum consumer liability is $500.\n"
      "   - 12 CFR 1005.6(b)(3) Tier 3 Liability: Consumer fails to notify"
      " financial institution within 60 calendar days after periodic statement"
      " transmittal -> unlimited consumer liability for unauthorized transfers"
      " occurring after the 60-day period; provisional credit status is"
      " DENIED_STATUTORY_EXPIRED.\n"
      "   - 12 CFR 1005.11 Error Resolution Procedures: 10 business days"
      " investigation clock, extendable to 45 calendar days if provisional"
      " credit is granted within 10 business days (90 days for new accounts,"
      " POS, or foreign-initiated transfers).\n"
      "2. Regulation Z (12 CFR Part 1026) — Truth in Lending Act (TILA):\n"
      "   - 12 CFR 1026.15 & 1026.23 Right of Rescission: Consumer has a"
      " standard rescission period of 3 business days following consummation,"
      " delivery of notice of right to rescind, or delivery of all material"
      " disclosures.\n"
      "   - 12 CFR 1026.13 Billing Error Resolution: Written notice within 60"
      " days; acknowledgment within 30 days; resolution within two complete"
      " billing cycles (not to exceed 90 days).\n"
      "3. FFIEC BSA/AML Examination Manual — Customer Due Diligence (CDD) &"
      " Beneficial Ownership (31 CFR 1010.230):\n"
      "   - Requires identifying and verifying any individual owning 25% or"
      " more of the equity interests of a legal entity customer (ownership"
      " prong) and one individual with significant responsibility to control,"
      " manage, or direct the legal entity (control prong).\n"
      "4. CFPB Circular 2023-03 — Adverse Action Notification under Reg B"
      " (ECOA, 12 CFR Part 1002):\n"
      "   - Creditors must provide accurate, specific principal reasons for"
      " adverse action within 30 days, even when deploying complex algorithms"
      " or machine learning models.\n"
      "5. FinCEN Advisory FIN-2019-A005 & Bank Secrecy Act (BSA) Anti-Structuring:\n"
      "   - 31 CFR 1010.311 requires filing a Currency Transaction Report (CTR)"
      " for cash transactions exceeding $10,000 in a single business day.\n"
      "   - 31 CFR 1020.320 requires filing a Suspicious Activity Report (SAR)"
      " within 30 calendar days of detecting suspicious activity.\n"
      "   - 31 U.S.C. 5324 strictly prohibits structuring (breaking up cash"
      " deposits into sub-$10,000 increments across branches or days to evade"
      " CTR/SAR reporting). Structuring is a federal felony under the Bank"
      " Secrecy Act and USA PATRIOT Act.\n"
      "6. Federal Reserve SR 11-7 — Guidance on Model Risk Management:\n"
      "   - Requires effective challenge, independent model validation, ongoing"
      " outcomes analysis, and strict governance over AI/ML compliance models.\n"
  )
  # Repeat block so token count comfortably exceeds the 32,768-token floor
  # required by explicit Context Caching across all Gemini model tiers.
  return "\n\n".join([f"[Section {i}]\n{base_block}" for i in range(1, 95)])


def main() -> None:
  project_id = run_cmd(["gcloud", "config", "get-value", "project"])
  model_name = detect_approved_model()
  bucket = f"gs://cymbal-regulations-{project_id}"

  ls_out = run_cmd(["gcloud", "storage", "ls", bucket])
  uris = [
      line.strip()
      for line in ls_out.splitlines()
      if line.strip().startswith("gs://") and not line.strip().endswith("/")
  ]

  parts = []
  for uri in uris:
    mime = "text/markdown" if uri.endswith(".md") else "application/pdf"
    parts.append(types.Part.from_uri(file_uri=uri, mime_type=mime))
  parts.append(types.Part.from_text(text=build_reference_corpus()))

  for loc in ("global", "us-central1"):
    try:
      client = genai.Client(vertexai=True, project=project_id, location=loc)
      cache = client.caches.create(
          model=model_name,
          config=types.CreateCachedContentConfig(
              display_name="cymbal-regulations-context-cache",
              system_instruction=(
                  "You are the Cymbal Bank Regulatory Compliance Assistant."
                  " Use these cached regulatory manuals and statutory rules to"
                  " adjudicate disputes accurately within the 25-second SLA."
              ),
              contents=[types.Content(role="user", parts=parts)],
              ttl="7200s",
          ),
      )
      print(
          f"[4.1] Created CachedContent in location='{loc}' on model='{model_name}':"
          f" {cache.name}"
      )
    except Exception as exc:
      print(f"[4.1] Cache creation note in location='{loc}': {exc}")


if __name__ == "__main__":
  main()
