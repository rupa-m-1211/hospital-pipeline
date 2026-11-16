"""
clean_daily_file.py
Cleans one day's claims file safely.

Reads:   data/landing/claims_YYYY-MM-DD.csv   (messy)
Writes:  data/ready/claims_YYYY-MM-DD.csv     (clean)
         data/rejects/claims_YYYY-MM-DD.csv   (bad rows + the reason)

Usage:  python3 scripts/clean_daily_file.py 2026-11-10
"""

import csv
import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

MAX_REJECT_RATE = 0.05   # more than 5% bad rows -> stop, don't publish

# 1. Read the date and build file paths
if len(sys.argv) != 2:
    print("Usage: python3 scripts/clean_daily_file.py YYYY-MM-DD")
    sys.exit(1)

day = sys.argv[1]
landing = Path("data/landing") / f"claims_{day}.csv"
staging = Path("data/staging") / f"claims_{day}.csv.tmp"
ready   = Path("data/ready")   / f"claims_{day}.csv"
rejects = Path("data/rejects") / f"claims_{day}.csv"

if not landing.exists():
    print(f"ERROR: {landing} not found")
    sys.exit(1)

seen_ids = set()
counts = {"read": 0, "good": 0, "duplicate": 0, "rejected": 0}

# 2. Read the messy file one row at a time
with open(landing, newline="") as src, \
     open(staging, "w", newline="") as good_out, \
     open(rejects, "w", newline="") as bad_out:

    reader = csv.reader(src)
    header = next(reader)

    good_writer = csv.writer(good_out)
    bad_writer = csv.writer(bad_out)
    good_writer.writerow(header)
    bad_writer.writerow(["reason"] + header)

    for row in reader:
        counts["read"] += 1

        # Check 1: does the row have the right number of columns?
        if len(row) != len(header):
            bad_writer.writerow([f"expected {len(header)} columns, got {len(row)}"] + row)
            counts["rejected"] += 1
            continue

        record = dict(zip(header, row))

        # Check 2: is the amount a real number?
        try:
            Decimal(record["amount"])
        except InvalidOperation:
            bad_writer.writerow([f"bad amount: {record['amount']}"] + row)
            counts["rejected"] += 1
            continue

        # Check 3: have we already seen this claim_id? keep the first copy
        if record["claim_id"] in seen_ids:
            counts["duplicate"] += 1
            continue
        seen_ids.add(record["claim_id"])

        good_writer.writerow(row)
        counts["good"] += 1

# 3. Report what happened
print(f"Read {counts['read']} rows: {counts['good']} good, "
      f"{counts['duplicate']} duplicates skipped, {counts['rejected']} rejected")

# 4. Decide: publish or stop?
if counts["read"] == 0:
    print("ERROR: file had no data rows. Not publishing.")
    staging.unlink()
    sys.exit(1)

reject_rate = counts["rejected"] / counts["read"]
if reject_rate > MAX_REJECT_RATE:
    print(f"ERROR: {reject_rate:.1%} of rows rejected (limit {MAX_REJECT_RATE:.0%}). Not publishing.")
    staging.unlink()
    sys.exit(1)

os.replace(staging, ready)   # atomic move: staging -> ready
print(f"Published {ready}")