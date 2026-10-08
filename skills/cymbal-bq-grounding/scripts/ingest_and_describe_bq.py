#!/usr/bin/env python3
"""Atomic BigQuery execution for Milestone 1.1 (--step 1.1) and Milestone 1.3 (--step 1.3)."""

import argparse
import json
import subprocess
from google.cloud import bigquery


def get_project_id() -> str:
  res = subprocess.run(
      ["gcloud", "config", "get-value", "project"],
      capture_output=True,
      text=True,
      check=True,
  )
  return res.stdout.strip()


TABLES = [
    "dispute_tickets",
    "transaction_ledger",
    "analyst_user_mapping",
    "regulatory_metadata_registry",
    "compliance_qa_audit",
]

TABLE_DESCRIPTIONS = {
    "dispute_tickets": (
        "Cymbal Bank operational dispute tickets table tracking customer fraud"
        " claims, billing error disputes, customer tiers, reporting timelines"
        " (days since statement transmittal), disputed amounts, provisional"
        " credit statuses, and Reg E / Reg Z adjudication outcomes."
    ),
    "transaction_ledger": (
        "Cymbal Bank core settlement and transaction ledger containing wire"
        " transfers, ACH debits, card settlements, counterparty routing"
        " details, timestamps, hub codes, and settlement statuses."
    ),
    "analyst_user_mapping": (
        "Cymbal Bank compliance analyst and dispatcher directory mapping"
        " employee user IDs to RBAC role tiers (analyst, senior_counsel,"
        " audit_reviewer, system), assigned regional operations hubs, and"
        " approval authority limits."
    ),
    "regulatory_metadata_registry": (
        "Cymbal Bank regulatory policy metadata registry cataloguing active"
        " statutory frameworks (Reg E 12 CFR 1005, Reg Z 12 CFR 1026, FFIEC"
        " BSA/AML CDD, CFPB Circular 2023-03, FinCEN Advisory FIN-2019-A005,"
        " SR 11-7), statutory deadlines, liability caps, and document versions."
    ),
    "compliance_qa_audit": (
        "Cymbal Bank immutable compliance QA and evidentiary audit trail"
        " recording historical dispute evaluations, analyst overrides, SAR/CTR"
        " escalations, policy citations, and compliance quality review scores."
    ),
}

KNOWN_COLUMN_DESCRIPTIONS = {
    "dispute_id": (
        "Unique primary identifier for the customer dispute ticket (e.g.,"
        " DISP-99203)."
    ),
    "ticket_id": "Unique identifier for the compliance dispute ticket.",
    "account_id": (
        "Customer banking account identifier associated with the dispute (e.g.,"
        " ACCT-10293)."
    ),
    "customer_id": "Unique Cymbal Bank customer relationship identifier.",
    "customer_tier": (
        "Customer account relationship and statutory tier classification (e.g.,"
        " TIER_1_PLATINUM, TIER_2_COMMERCIAL, TIER_3_RETAIL)."
    ),
    "claim_type": (
        "Category of the customer dispute claim (e.g., UNAUTHORIZED_EFT,"
        " BILLING_ERROR, WIRE_FRAUD, BEC_SCAM)."
    ),
    "dispute_type": "Classification of the disputed banking transaction.",
    "disputed_amount": (
        "Monetary amount disputed by the account holder in USD (e.g., 75.00)."
    ),
    "claim_amount": (
        "Monetary value of the customer claim in USD submitted for"
        " adjudication."
    ),
    "amount": "Transaction or dispute monetary amount in USD.",
    "days_since_statement": (
        "Number of calendar days elapsed between periodic statement transmittal"
        " and customer notice to Cymbal Bank (critical for Reg E 12 CFR"
        " 1005.6(b) 2-day and 60-day liability windows)."
    ),
    "days_to_report": (
        "Elapsed days from statement transmittal or transaction date to"
        " customer dispute notification."
    ),
    "reported_days_after_statement": (
        "Calendar days after periodic statement transmittal when the consumer"
        " reported the error or unauthorized transfer."
    ),
    "provisional_credit_status": (
        "Current Reg E / Reg Z provisional credit determination status (e.g.,"
        " ALLOCATED, DENIED_STATUTORY_EXPIRED, PENDING_REVIEW, NOT_REQUIRED)."
    ),
    "credit_status": (
        "Provisional credit allocation status recorded on the dispute ticket"
        " (e.g., ALLOCATED, DENIED_STATUTORY_EXPIRED)."
    ),
    "provisional_credit_amount": (
        "Dollar amount of provisional credit granted to the consumer pending"
        " investigation."
    ),
    "liability_cap": (
        "Applicable statutory consumer liability limit in USD under 12 CFR"
        " 1005.6(b) ($0, $50, $500, or UNLIMITED)."
    ),
    "consumer_liability": (
        "Calculated consumer liability amount in USD under Regulation E or Z."
    ),
    "applicable_regulation": (
        "Primary federal banking regulation governing the dispute (e.g., REG_E,"
        " REG_Z, BSA_AML, UCC_4A)."
    ),
    "status": "Current lifecycle status of the record or dispute case.",
    "dispute_status": "Current investigation status of the dispute ticket.",
    "transaction_id": (
        "Unique transaction identifier linking to the core transaction_ledger"
        " table."
    ),
    "created_at": "Timestamp or date when the record was created.",
    "reported_date": "Date when the customer reported the dispute to the bank.",
    "statement_date": (
        "Date when the periodic account statement reflecting the transaction"
        " was transmitted."
    ),
    "transaction_date": (
        "Date and time when the underlying transaction occurred."
    ),
    "resolution_notes": (
        "Compliance analyst or automated adjudication notes explaining the"
        " statutory basis for the ruling."
    ),
    "denial_reason": (
        "Statutory or operational reason why provisional credit or claim"
        " reimbursement was denied."
    ),
    "sender_account": "Originating account identifier for the transfer.",
    "receiver_account": (
        "Beneficiary or destination account identifier for the transfer."
    ),
    "counterparty_name": "Name of the external counterparty or merchant.",
    "counterparty_bank": (
        "Receiving or correspondent financial institution for the transaction."
    ),
    "channel": (
        "Payment rail or banking channel (e.g., WIRE, ACH, DEBIT_CARD, P2P,"
        " BRANCH_CASH)."
    ),
    "transaction_type": (
        "Type of ledger entry (e.g., DEBIT, CREDIT, WIRE_OUT, ACH_DEBIT)."
    ),
    "currency": "ISO 4217 currency code for the transaction (e.g., USD).",
    "hub_id": (
        "Cymbal Bank regional operations hub code processing the settlement"
        " (e.g., NYC, CLT, LAX, LON)."
    ),
    "risk_score": "Automated fraud and AML risk score assigned to the transfer.",
    "sar_flagged": (
        "Boolean or status indicator showing whether the transaction triggered"
        " a FinCEN Suspicious Activity Report (SAR) review."
    ),
    "analyst_id": "Unique employee identifier for the compliance analyst.",
    "user_id": "Unique internal user identifier for the Cymbal Bank employee.",
    "analyst_name": "Full name of the compliance operations staff member.",
    "email": "Corporate Cymbal Bank email address of the analyst.",
    "role": (
        "RBAC authorization role tier (analyst, senior_counsel, audit_reviewer,"
        " or system)."
    ),
    "rbac_role": "Assigned Role-Based Access Control tier in Compliance Ops.",
    "department": (
        "Internal Cymbal Bank department or cost center (e.g., COC_OPS,"
        " BSA_AML_UNIT, LEGAL_COUNSEL)."
    ),
    "assigned_hub": (
        "Primary regional compliance hub where the analyst is stationed."
    ),
    "approval_limit": (
        "Maximum dollar threshold in USD that the analyst can approve for"
        " provisional credit or fee waivers."
    ),
    "active": "Indicates whether the analyst's compliance credentials are active.",
    "reg_id": "Unique identifier for the regulatory rule or citation entry.",
    "regulation_code": (
        "Short code identifying the regulation (e.g., REG_E, REG_Z, BSA_CDD,"
        " CFPB_2023_03, FINCEN_2019_A005, SR_11_7)."
    ),
    "cfr_citation": (
        "Exact Code of Federal Regulations or statutory citation (e.g., 12 CFR"
        " 1005.6(b)(3), 31 U.S.C. 5324)."
    ),
    "document_name": (
        "Filename of the authoritative policy document in the"
        " cymbal-regulations-store datastore."
    ),
    "statutory_window_days": (
        "Statutory deadline or reporting window in days defined by the"
        " regulation."
    ),
    "summary": "Concise compliance summary of the regulatory requirement.",
    "effective_date": "Effective date of the regulatory policy version.",
    "audit_id": "Unique identifier for the compliance QA audit log entry.",
    "reviewed_by": (
        "Analyst or senior counsel identifier who performed the QA audit."
    ),
    "audit_status": (
        "Outcome of the compliance QA review (e.g., PASSED, OVERRIDDEN,"
        " ESCALATED_SAR, VIOLATION_FLAGGED)."
    ),
    "qa_notes": (
        "Detailed audit findings and evidentiary verification notes from"
        " Compliance QA."
    ),
    "audit_timestamp": "Timestamp when the QA audit evaluation was recorded.",
}


def describe_column(table_name: str, col_name: str, col_type: str) -> str:
  col_lower = col_name.lower()
  if col_lower in KNOWN_COLUMN_DESCRIPTIONS:
    return KNOWN_COLUMN_DESCRIPTIONS[col_lower]
  readable = col_name.replace("_", " ")
  return (
      f"Column '{col_name}' ({col_type}) in Cymbal Bank table '{table_name}'"
      f" recording the {readable} attribute for regulatory compliance and"
      " dispute adjudication analysis."
  )


def run_step_1_1(client: bigquery.Client, project_id: str) -> None:
  dataset_id = f"{project_id}.cymbal_compliance"
  dataset = bigquery.Dataset(dataset_id)
  dataset.location = "US"
  client.create_dataset(dataset, exists_ok=True)
  print(f"[1.1] Created/verified dataset {dataset_id} in US multi-region.")

  for table_name in TABLES:
    gcs_uri = (
        f"gs://{project_id}-static-assets-bucket/data/structured/{table_name}.csv"
    )
    table_ref = f"{dataset_id}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        allow_quoted_newlines=True,
    )
    load_job = client.load_table_from_uri(
        gcs_uri, table_ref, job_config=job_config
    )
    load_job.result()
    table = client.get_table(table_ref)
    print(f"[1.1] Loaded {table_ref}: {table.num_rows} rows.")


def run_step_1_3(client: bigquery.Client, project_id: str) -> None:
  dataset_id = f"{project_id}.cymbal_compliance"
  schema_summary = {}

  for table_name, table_desc in TABLE_DESCRIPTIONS.items():
    table_ref = f"{dataset_id}.{table_name}"
    table = client.get_table(table_ref)
    table.description = table_desc

    new_schema = []
    cols_meta = []
    for field in table.schema:
      desc = describe_column(table_name, field.name, field.field_type)
      new_field = bigquery.SchemaField(
          name=field.name,
          field_type=field.field_type,
          mode=field.mode,
          description=desc,
          fields=field.fields,
      )
      new_schema.append(new_field)
      cols_meta.append(
          {"name": field.name, "type": field.field_type, "description": desc}
      )

    table.schema = new_schema
    client.update_table(table, ["description", "schema"])
    print(
        f"[1.3] Populated table & {len(new_schema)} column descriptions for"
        f" {table_ref}."
    )
    schema_summary[table_name] = {
        "row_count": table.num_rows,
        "description": table_desc,
        "columns": cols_meta,
    }

  try:
    with open("/workspace/bq_schema_summary.json", "w", encoding="utf-8") as f:
      json.dump(schema_summary, f, indent=2)
    print("[1.3] Saved live schema summary to /workspace/bq_schema_summary.json")
  except OSError:
    pass


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument(
      "--step",
      choices=["1.1", "1.3", "all"],
      default="all",
      help="Run atomic milestone 1.1, 1.3, or both.",
  )
  args = parser.parse_args()

  project_id = get_project_id()
  client = bigquery.Client(project=project_id, location="US")

  if args.step in ("1.1", "all"):
    run_step_1_1(client, project_id)
  if args.step in ("1.3", "all"):
    run_step_1_3(client, project_id)


if __name__ == "__main__":
  main()
