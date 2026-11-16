"""
load_to_bigquery.py
Loads one day's clean claims file into BigQuery.
Safe to rerun: it REPLACES that day's partition instead of adding to it.

Usage:  python scripts/load_to_bigquery.py 2026-11-10
"""

import sys
from pathlib import Path
from google.cloud import bigquery

PROJECT_ID = "hospital-pipeline"
TABLE_ID = f"{PROJECT_ID}.raw.claims_daily"

SCHEMA = [
    bigquery.SchemaField("claim_id", "STRING"),
    bigquery.SchemaField("encounter_id", "STRING"),
    bigquery.SchemaField("patient_id", "STRING"),
    bigquery.SchemaField("payer_id", "STRING"),
    bigquery.SchemaField("member_id", "STRING"),
    bigquery.SchemaField("service_date", "DATE"),
    bigquery.SchemaField("amount", "NUMERIC"),
    bigquery.SchemaField("status", "STRING"),
]

# 1. Read the date and find the clean file
if len(sys.argv) != 2:
    print("Usage: python scripts/load_to_bigquery.py YYYY-MM-DD")
    sys.exit(1)

day = sys.argv[1]
ready_file = Path("data/ready") / f"claims_{day}.csv"

if not ready_file.exists():
    print(f"ERROR: {ready_file} not found. Run the cleaner first.")
    sys.exit(1)

client = bigquery.Client(project=PROJECT_ID)

# 2. Make sure the table exists, partitioned by service_date
table = bigquery.Table(TABLE_ID, schema=SCHEMA)
table.time_partitioning = bigquery.TimePartitioning(field="service_date")
client.create_table(table, exists_ok=True)

# 3. Load into ONLY this day's partition, replacing whatever was there
partition = f"{TABLE_ID}${day.replace('-', '')}"   # e.g. ...claims_daily$20261110

job_config = bigquery.LoadJobConfig(
    schema=SCHEMA,
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
)

with open(ready_file, "rb") as f:
    job = client.load_table_from_file(f, partition, job_config=job_config)

job.result()   # wait until BigQuery finishes; raises an error if the load failed

# 4. Verify: count what's in BigQuery for this day
query = f"SELECT COUNT(*) AS n FROM `{TABLE_ID}` WHERE service_date = '{day}'"
n = list(client.query(query).result())[0].n

print(f"Loaded {n} rows into {partition}")