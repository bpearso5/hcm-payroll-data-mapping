"""
Load the CSVs into SQLite, run every check in sql/02_integrity_checks.sql,
and write results/defect_log.csv plus a per-check summary. Then compare the
flagged records to the answer key in data/_seeded_defects.csv and exit non-zero
if any seeded defect was missed or any unseeded record was flagged.

The SQL is portable; to run it in MySQL instead, execute sql/01_schema.sql,
load the two CSVs with LOAD DATA (or the MySQL Workbench import wizard),
then run sql/02_integrity_checks.sql.
"""
import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

CHECK_NAMES = {
    "C01": "Missing in target", "C02": "Duplicate person", "C03": "Hourly rate out of range",
    "C04": "Address mapping", "C05": "Missing bank", "C06": "Hire date mismatch",
    "C07": "Missing name", "C08": "Salary mismatch", "C09": "Status mismatch",
    "C10": "Orphan in target", "C11": "Copied field mismatch",
}
SEVERITY = {"C01": "High", "C02": "High", "C03": "High", "C05": "High",
            "C08": "High", "C09": "High", "C10": "High",
            "C04": "Medium", "C06": "Medium", "C11": "Medium", "C07": "Low"}
# Which check is expected to catch each seeded defect type in data/_seeded_defects.csv.
EXPECTED_CHECK = {
    "MISSING_IN_TARGET": "C01", "DUPLICATE_PERSON": "C02", "COMP_OUT_OF_RANGE": "C03",
    "ADDRESS_MAPPING": "C04", "MISSING_BANK": "C05", "HIRE_DATE_MISMATCH": "C06",
    "MISSING_NAME": "C07", "FTE_COMP_MISMATCH": "C08", "STATUS_MISMATCH": "C09",
}
NUMERIC = {"comp_amount", "fte", "annual_salary", "hourly_rate"}

con = sqlite3.connect(":memory:")
con.executescript((ROOT / "sql/01_schema.sql").read_text())

for table in ("hcm_employees", "payroll_employees"):
    with open(ROOT / f"data/{table}.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    vals = [[(float(r[c]) if r[c] != "" else None) if c in NUMERIC else r[c] for c in cols]
            for r in rows]
    con.executemany(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", vals)

sql = (ROOT / "sql/02_integrity_checks.sql").read_text()
blocks = re.split(r"^-- @check ", sql, flags=re.M)[1:]

log, summary = [], []
for block in blocks:
    check_id = block.split()[0]
    query = "\n".join(l for l in block.splitlines()[1:] if not l.strip().startswith("--"))
    rows = con.execute(query).fetchall()
    summary.append((check_id, CHECK_NAMES[check_id], SEVERITY[check_id], len(rows)))
    for r in rows:
        src = r[4] if not isinstance(r[4], float) else f"{r[4]:.2f}"
        tgt = r[5] if not isinstance(r[5], float) else f"{r[5]:.2f}"
        log.append(dict(defect_id=f"D{len(log) + 1:03d}", check_id=r[0],
                        check_name=CHECK_NAMES[r[0]], severity=SEVERITY[r[0]],
                        person_id=r[1], payroll_id=r[2] or "", field=r[3],
                        source_value="" if src is None else src,
                        target_value="" if tgt is None else tgt,
                        status="Open", ticket="", owner="", resolution=""))

with open(RESULTS / "defect_log.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(log[0].keys()))
    w.writeheader()
    w.writerows(log)

with open(RESULTS / "check_summary.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["check_id", "check_name", "severity", "rows_flagged"])
    w.writerows(summary)

for s in summary:
    print(f"{s[0]}  {s[1]:<26} {s[2]:<7} {s[3]}")
print(f"Total defect rows: {len(log)}")

# Verify against the answer key: every seeded defect caught by its check, nothing else flagged.
with open(ROOT / "data/_seeded_defects.csv", newline="") as f:
    expected = {(EXPECTED_CHECK[r["defect_type"]], r["person_id"]) for r in csv.DictReader(f)}
found = {(d["check_id"], d["person_id"]) for d in log}
missed, unexpected = sorted(expected - found), sorted(found - expected)
for check_id, person_id in missed:
    print(f"MISSED      {check_id} {person_id}: seeded defect was not flagged")
for check_id, person_id in unexpected:
    print(f"UNEXPECTED  {check_id} {person_id}: flagged but not in the answer key")
if missed or unexpected:
    sys.exit("Answer-key verification FAILED")
print(f"Answer-key verification passed: {len(expected)} seeded defects found, nothing else flagged")
