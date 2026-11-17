"""
check_quality.py
Checks one day's claims in BigQuery. Exits with code 1 if anything is wrong.

Usage:  python scripts/check_quality.py 2026-11-11
"""

import sys
from pathlib import Path
from google.cloud import bigquery

PROJECT_ID = "hospital-pipeline"
TABLE_ID = f"{PROJECT_ID}.raw.claims_daily"

if len(sys.argv) != 2:
    print("Usage: python scripts/check_quality.py YYYY-MM-DD")
    sys.exit(1)

day = sys.argv[1]

# 1. How many rows SHOULD be in BigQuery? Count the clean file (minus the header)
ready_file = Path("data/ready") / f"claims_{day}.csv"
with open(ready_file) as f:
    expected = sum(1 for _ in f) - 1

# 2. What's ACTUALLY in BigQuery for this day?
client = bigquery.Client(project=PROJECT_ID)
query = f"""
    SELECT
      COUNT(*)                 AS total_rows,
      COUNT(DISTINCT claim_id) AS unique_claims,
      COUNTIF(amount IS NULL)  AS null_amounts
    FROM `{TABLE_ID}`
    WHERE service_date = '{day}'
"""
row = list(client.query(query).result())[0]

# 3. Compare, and collect every problem found
problems = []
if row.total_rows != expected:
    problems.append(f"row count {row.total_rows} does not match the clean file ({expected})")
if row.unique_claims != row.total_rows:
    problems.append(f"{row.total_rows - row.unique_claims} duplicate claim_ids")
if row.null_amounts > 0:
    problems.append(f"{row.null_amounts} claims with no amount")

# 4. Fail loudly, or pass with a clear message
if problems:
    print(f"QUALITY CHECK FAILED for {day}:")
    for p in problems:
        print(f"  - {p}")
    sys.exit(1)

print(f"Quality check passed for {day}: {row.total_rows} rows, all unique, no missing amounts")