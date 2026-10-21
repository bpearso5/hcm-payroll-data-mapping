# HCM-to-Payroll Data Mapping & Integrity Checks

A rebuilt case study of the data work I did during an enterprise HR system go-live: mapping fields between two systems, writing checks that catch where the data didn't line up, and tracking each defect to resolution.

> **All data here is synthetic.** People, IDs, and values are invented, and national IDs use an `NID-` prefix so they can't be mistaken for real ones. No client data, files, or screenshots are included. The defect types are modeled on the kinds of issues I tracked in practice.

## The problem

When an organization moves employee records into a new HR system, that system becomes the source of truth, and payroll receives its data through replication. If the field mapping is wrong, or a record is keyed incorrectly, the error lands in payroll: someone isn't paid, is paid twice, or gets a check mailed to an unformatted address.

On the go-live I supported, I kept the payroll issues log: 115 items over the hypercare period, most of them replication and data defects between the HR system and payroll. I logged ServiceNow incidents, followed them through resolution, and flagged recurring patterns so they could be fixed at the rule level instead of one record at a time.

This repo rebuilds that work at small scale so it can be shown.

## What's in here

| Path | What it is |
|---|---|
| `mapping/source_to_target_mapping.csv` | Field-level mapping spec: 16 mappings, each with its transformation rule and validation check |
| `mapping/HCM_to_Payroll_Mapping_and_Defect_Log.xlsx` | The mapping spec, defect log, and summary in one workbook, with filters and a status dropdown |
| `sql/01_schema.sql` | Table definitions for the source (`hcm_employees`) and target (`payroll_employees`) |
| `sql/02_integrity_checks.sql` | Nine SQL checks, one per validation rule |
| `results/defect_log.csv` | Output of the checks: every flagged record with source and target values |
| `results/check_summary.csv` | Rows flagged per check, with severity |
| `docs/ticket_workflow.md` | How a defect moves from detection to ticket to closure |
| `scripts/` | `generate_data.py` builds the synthetic data; `run_checks.py` loads it and runs the SQL |
| `data/` | The two synthetic tables, plus `_seeded_defects.csv`, the answer key used to test the checks |

## The checks

| Check | Catches | Severity | Example of real-world impact |
|---|---|---|---|
| C01 | Record never replicated to payroll | High | New hire not paid |
| C02 | Same person holds two payroll IDs | High | Rehire set up as a new hire; wages split across two records |
| C03 | Hourly rate outside a plausible range | High | An annual salary keyed as an hourly rate |
| C04 | Non-US region mapped to the US state field | Medium | Checks mailed with unusable addresses |
| C05 | Bank details missing for an active employee | High | Payroll rejects the direct deposit |
| C06 | Hire date differs between systems | Medium | Correction in the HR system never re-replicated |
| C07 | Name missing in payroll | Low | Staff can't tell whose record they're in |
| C08 | Salary doesn't match after applying the mapping rule | High | FTE changed but pay wasn't prorated |
| C09 | Employment status out of sync | High | Active employee withdrawn in payroll |

## Results

The synthetic data contains 220 source records with 28 seeded defects. The checks flag all 28 and nothing else (31 rows, because each duplicate person shows up on both payroll records).

| Check | Rows flagged |
|---|---|
| C01 Missing in target | 4 |
| C02 Duplicate person | 6 (3 people) |
| C03 Hourly rate out of range | 3 |
| C04 Address mapping | 3 |
| C05 Missing bank | 4 |
| C06 Hire date mismatch | 3 |
| C07 Missing name | 2 |
| C08 Salary mismatch | 3 |
| C09 Status mismatch | 3 |

## Run it yourself

```bash
python3 scripts/generate_data.py   # rebuilds data/ (seeded, so output is the same each time)
python3 scripts/run_checks.py      # loads into SQLite, runs every check, writes results/
```

The SQL is written to run unchanged in **MySQL 8** and **SQLite 3**. For MySQL, run `sql/01_schema.sql`, import the two CSVs from `data/`, then run `sql/02_integrity_checks.sql`.

## What this demonstrates

| Skill | Where it shows |
|---|---|
| Source-to-target data mapping | `mapping/source_to_target_mapping.csv` — value maps, derived fields, conditional routing (M13) |
| SQL data profiling and validation | `sql/02_integrity_checks.sql` — joins, anti-joins, grouping, conditional logic |
| Data integrity assessment | Each check tied to a mapping rule and a business impact |
| Defect tracking and escalation | `results/defect_log.csv`, `docs/ticket_workflow.md` |
| Excel | Workbook with filters, frozen headers, a status dropdown, and COUNTIF summaries |
| Testing my own work | `data/_seeded_defects.csv` is an answer key; the checks are verified against it |


## How this was built

The problem, the defect types, and the workflow come from my own experience tracking data issues on an HR system go-live. I used Claude (Anthropic’s AI assistant) to help generate the synthetic data, draft the SQL, and structure the documentation. I reviewed, ran, and tested everything here, and I can walk through any query and the reasoning behind each check.


## About me

I'm Brystal Pearson, CAPM. I work at the intersection of data and delivery: implementation support, data governance, and the reporting that keeps leadership informed. I'm completing a BBA in Management Information Systems at the University of Memphis.

[LinkedIn](https://www.linkedin.com/in/brystal-pearson-capm) · [More projects](https://github.com/bpearso5)
