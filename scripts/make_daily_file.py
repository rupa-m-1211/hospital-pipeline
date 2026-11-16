"""
make_daily_file.py
Pretends to be the hospital's billing system.
Creates one day's claims file, with some problems planted on purpose.

Usage:  python3 scripts/make_daily_file.py 2026-11-10
"""

import csv
import random
import sys
from pathlib import Path

# 1. Read the date from the command line
if len(sys.argv) != 2:
    print("Usage: python3 scripts/make_daily_file.py YYYY-MM-DD")
    sys.exit(1)

day = sys.argv[1]   # e.g. "2026-11-10"

# 2. Same date -> same random choices -> same file every time
rng = random.Random(day)

# 3. Read real encounters from Synthea so our claims link to real visits
with open("output/csv/encounters.csv", newline="") as f:
    encounters = list(csv.DictReader(f))

todays_visits = rng.sample(encounters, 200)

# 4. Build one claim row per visit
rows = []
for i, enc in enumerate(todays_visits, start=1):
    rows.append({
        "claim_id": f"CLM-{day}-{i:04d}",
        "encounter_id": enc["Id"],
        "patient_id": enc["PATIENT"],
        "payer_id": enc["PAYER"],
        "member_id": f"{rng.randint(1, 999999):06d}",
        "service_date": day,
        "amount": enc["TOTAL_CLAIM_COST"],
        "status": rng.choice(["PAID", "PAID", "PAID", "DENIED", "PENDING"]),
    })

# 5. Plant problems on purpose
rows += rng.sample(rows, 6)      # 5a. 6 duplicate claims (resent by the source)
rows[10]["amount"] = "N/A"       # 5b. one amount that isn't a number
rng.shuffle(rows)

# 6. Write the file into data/landing/
out_path = Path("data/landing") / f"claims_{day}.csv"
columns = ["claim_id", "encounter_id", "patient_id", "payer_id",
           "member_id", "service_date", "amount", "status"]

with open(out_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    f.write("CLM-BROKEN-ROW,abc123\n")   # 5c. a broken row, missing most columns

print(f"Wrote {len(rows) + 1} claim rows to {out_path}")