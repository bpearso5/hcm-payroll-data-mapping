"""
Generate synthetic HCM (source) and Payroll (target) employee data.

All people, IDs, and values are invented. National IDs use the NID- prefix
so they can never be mistaken for real identifiers.

Defects are seeded on purpose so the SQL checks in sql/ have something to
find. The seeded list is written to data/_seeded_defects.csv as an answer key.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(2024)
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

FIRST = ["Avery", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn", "Reese",
         "Harper", "Rowan", "Emerson", "Parker", "Sawyer", "Hayden", "Finley", "Blair",
         "Dakota", "Ellis", "Kendall", "Lennon", "Marlowe", "Noel", "Oakley", "Peyton"]
LAST = ["Abbott", "Barlow", "Calder", "Dempsey", "Ellison", "Fairfax", "Garrison",
        "Holloway", "Ingram", "Jessup", "Kingsley", "Langford", "Mercer", "Norwood",
        "Oakes", "Prescott", "Quimby", "Radcliffe", "Sterling", "Thornton", "Underwood",
        "Vance", "Whitaker", "Yardley"]
US_STATES = ["TN", "GA", "TX", "IL", "NY", "CA", "NC", "OH"]
FOREIGN = [("IN", "Karnataka", "560001"), ("IN", "Telangana", "500081"),
           ("MX", "Jalisco", "44100"), ("GB", "", "EC1A 1BB")]
DEPTS = ["Audit", "Tax", "Consulting", "Advisory", "Internal Services"]

N = 220
GO_LIVE = date(2024, 6, 16)


def rand_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))


hcm, payroll, seeded = [], [], []

for i in range(1, N + 1):
    person_id = f"P{100000 + i}"
    nid = f"NID-{random.randint(100000, 999999)}"
    first, last = random.choice(FIRST), random.choice(LAST)
    hire = rand_date(date(2012, 1, 1), date(2024, 8, 30))
    pay_basis = "HOURLY" if random.random() < 0.18 else "SALARIED"
    if pay_basis == "HOURLY":
        amount = round(random.uniform(22, 68), 2)
    else:
        amount = round(random.uniform(52000, 210000), 2)
    fte = random.choice([1.0, 1.0, 1.0, 1.0, 0.9, 0.8])
    status = "ACTIVE" if random.random() < 0.9 else "TERMINATED"
    if random.random() < 0.1:
        country, region, postal = random.choice(FOREIGN)
    else:
        country, region, postal = "US", random.choice(US_STATES), f"{random.randint(10000, 99999)}"
    action = "REHIRE" if random.random() < 0.08 else "HIRE"
    bank = f"ACCT-{random.randint(1000, 9999)}"

    src = dict(person_id=person_id, national_id=nid, first_name=first, last_name=last,
               hire_date=hire.isoformat(), hire_action=action, employment_status=status,
               pay_basis=pay_basis, comp_amount=f"{amount:.2f}", fte=f"{fte:.2f}",
               department=random.choice(DEPTS), country=country, region=region,
               postal_code=postal, bank_ref=bank)
    hcm.append(src)

    # Target record is a clean transform of the source unless a defect is seeded.
    tgt = dict(payroll_id=f"{500000 + i}", source_person_id=person_id, national_id=nid,
               full_name=f"{last}, {first}", hire_date=hire.isoformat(),
               emp_status="A" if status == "ACTIVE" else "W",
               pay_basis="H" if pay_basis == "HOURLY" else "S",
               annual_salary=f"{(amount * 2080 * fte if pay_basis == 'HOURLY' else amount):.2f}",
               hourly_rate=f"{amount:.2f}" if pay_basis == "HOURLY" else "",
               fte=f"{fte:.2f}", country=country, state=region if country == "US" else "",
               province=region if country != "US" else "", postal_code=postal, bank_ref=bank)
    payroll.append(tgt)


def seed(defect, idx, note):
    seeded.append(dict(defect_type=defect, person_id=hcm[idx]["person_id"], note=note))


pool = list(range(N))
random.shuffle(pool)
take = lambda k: [pool.pop() for _ in range(k)]

# 1. Not replicated: source record has no target record.
for idx in take(4):
    seed("MISSING_IN_TARGET", idx, "Record never replicated to payroll")
missing_ids = {s["person_id"] for s in seeded if s["defect_type"] == "MISSING_IN_TARGET"}

# 2. Rehire processed as new hire: extra payroll ID for the same national ID.
for idx in take(3):
    hcm[idx]["hire_action"] = "REHIRE"
    dup = dict(payroll[idx])
    dup["payroll_id"] = f"{900000 + idx}"
    payroll.append(dup)
    seed("DUPLICATE_PERSON", idx, "Rehire created a second payroll ID")

# 3. Hourly worker with an annual amount keyed as the hourly rate.
for idx in take(3):
    hcm[idx]["pay_basis"] = "HOURLY"
    hcm[idx]["comp_amount"] = f"{random.choice([57000, 66000, 79000]):.2f}"
    payroll[idx]["pay_basis"] = "H"
    payroll[idx]["hourly_rate"] = hcm[idx]["comp_amount"]
    payroll[idx]["annual_salary"] = f"{float(hcm[idx]['comp_amount']) * 2080:.2f}"
    seed("COMP_OUT_OF_RANGE", idx, "Annual figure entered as hourly rate")

# 4. Foreign address mapped to the wrong target fields.
foreign_idx = [i for i in pool if hcm[i]["country"] != "US" and hcm[i]["region"]][:3]
for idx in foreign_idx:
    pool.remove(idx)
    payroll[idx]["state"] = hcm[idx]["region"]
    payroll[idx]["province"] = ""
    seed("ADDRESS_MAPPING", idx, "Foreign region mapped to US state field")

# 5. Bank details missing in target.
for idx in take(4):
    payroll[idx]["bank_ref"] = ""
    seed("MISSING_BANK", idx, "Bank reference blank in payroll")

# 6. Hire date changed in source after replication.
for idx in take(3):
    d = date.fromisoformat(hcm[idx]["hire_date"]) + timedelta(days=random.choice([7, 14, -3]))
    hcm[idx]["hire_date"] = d.isoformat()
    seed("HIRE_DATE_MISMATCH", idx, "Source date corrected; target not updated")

# 7. Name missing in target.
for idx in take(2):
    payroll[idx]["full_name"] = ""
    seed("MISSING_NAME", idx, "Name dropped during replication")

# 8. FTE changed without a matching compensation change (salaried).
sal = [i for i in pool if hcm[i]["pay_basis"] == "SALARIED" and hcm[i]["fte"] == "1.00"][:3]
for idx in sal:
    pool.remove(idx)
    hcm[idx]["fte"] = "0.90"
    payroll[idx]["fte"] = "0.90"
    hcm[idx]["comp_amount"] = f"{float(hcm[idx]['comp_amount']) * 0.9:.2f}"
    seed("FTE_COMP_MISMATCH", idx, "FTE changed; target salary not prorated")

# 9. Status out of sync.
act = [i for i in pool if hcm[i]["employment_status"] == "ACTIVE"][:3]
for idx in act:
    pool.remove(idx)
    payroll[idx]["emp_status"] = "W"
    seed("STATUS_MISMATCH", idx, "Active in HCM, withdrawn in payroll")

payroll = [p for p in payroll if p["source_person_id"] not in missing_ids]


def write(name, rows):
    with open(DATA / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


write("hcm_employees.csv", hcm)
write("payroll_employees.csv", payroll)
write("_seeded_defects.csv", seeded)
print(f"HCM rows: {len(hcm)}  Payroll rows: {len(payroll)}  Seeded defects: {len(seeded)}")
