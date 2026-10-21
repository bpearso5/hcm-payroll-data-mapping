# From defect to ticket to closure

How a row in `results/defect_log.csv` moves to resolution. This mirrors the workflow I used during a go-live hypercare period, where data defects were logged as ServiceNow incidents and tracked daily until payroll confirmed the fix.

## Lifecycle

| Stage | Who | What happens | Log field updated |
|---|---|---|---|
| 1. Detect | Analyst | Integrity check flags the record | `defect_id`, `check_id`, `severity` |
| 2. Triage | Analyst | Confirm it's a real defect, not expected behavior (for example, a field that is intentionally not replicated) | `status` → Open or Closed (not a defect) |
| 3. Log | Analyst | Open an incident with the record IDs, field, source value, target value, and the mapping rule it breaks | `ticket`, `status` → Ticket Logged |
| 4. Assign | Service desk | Ticket routed to the owning team (data management, integration, payroll) | `owner` |
| 5. Fix | Owning team | Correct the source record and re-replicate, or fix the integration rule | `status` → In Progress |
| 6. Verify | Analyst | Re-run the same check; the row must no longer appear | `status` → Resolved |
| 7. Close | Analyst + business | Business confirms downstream impact (for example, the next payroll run) is clean | `status` → Closed, `resolution` |

## What goes in the ticket

- **Record IDs:** source `person_id` and target `payroll_id`
- **Field and values:** the field name, the source value, and the target value
- **Rule broken:** the mapping ID from `mapping/source_to_target_mapping.csv` (for example, M13)
- **Business impact:** what fails if it isn't fixed (missed paycheck, wrong tax, returned mail)
- **Deadline:** the next run that depends on the data

## Patterns worth escalating

A single defect is a ticket. The same defect type showing up again is a root-cause problem: a mapping rule, an integration setting, or a data-entry process. During go-live, recurring issues were numbered in the log ("fourth occurrence") so the pattern was visible and could be escalated as a change request instead of fixed one record at a time.
