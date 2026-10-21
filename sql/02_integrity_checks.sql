-- Integrity checks: one query per check ID in mapping/source_to_target_mapping.csv.
-- Each returns: check_id, person_id, payroll_id, field, source_value, target_value.
-- Portable SQL: runs unchanged in MySQL 8 and SQLite 3.
-- scripts/run_checks.py runs each block (separated by "-- @check") and writes results/defect_log.csv.

-- @check C01 Record missing in target (never replicated)
SELECT 'C01' AS check_id, h.person_id, NULL AS payroll_id,
       'source_person_id' AS field, h.person_id AS source_value, NULL AS target_value
FROM hcm_employees h
LEFT JOIN payroll_employees p ON p.source_person_id = h.person_id
WHERE p.payroll_id IS NULL;

-- @check C02 Same person holds more than one payroll ID (rehire processed as new hire)
SELECT 'C02' AS check_id, p.source_person_id AS person_id, p.payroll_id,
       'payroll_id' AS field, p.national_id AS source_value, p.payroll_id AS target_value
FROM payroll_employees p
WHERE p.national_id IN (
    SELECT national_id
    FROM payroll_employees
    GROUP BY national_id
    HAVING COUNT(DISTINCT payroll_id) > 1
);

-- @check C03 Hourly rate outside plausible range (annual figure keyed as hourly)
SELECT 'C03' AS check_id, p.source_person_id AS person_id, p.payroll_id,
       'hourly_rate' AS field, h.comp_amount AS source_value, p.hourly_rate AS target_value
FROM payroll_employees p
JOIN hcm_employees h ON h.person_id = p.source_person_id
WHERE p.pay_basis = 'H'
  AND (p.hourly_rate < 10 OR p.hourly_rate > 150);

-- @check C04 Non-US region mapped to the US state field
SELECT 'C04' AS check_id, p.source_person_id AS person_id, p.payroll_id,
       'state/province' AS field, h.region AS source_value, p.state AS target_value
FROM payroll_employees p
JOIN hcm_employees h ON h.person_id = p.source_person_id
WHERE h.country <> 'US'
  AND COALESCE(h.region, '') <> ''
  AND (COALESCE(p.state, '') <> '' OR COALESCE(p.province, '') <> h.region);

-- @check C05 Bank reference missing for an active employee
SELECT 'C05' AS check_id, p.source_person_id AS person_id, p.payroll_id,
       'bank_ref' AS field, h.bank_ref AS source_value, p.bank_ref AS target_value
FROM payroll_employees p
JOIN hcm_employees h ON h.person_id = p.source_person_id
WHERE p.emp_status = 'A'
  AND COALESCE(p.bank_ref, '') = '';

-- @check C06 Hire date differs between systems
SELECT 'C06' AS check_id, p.source_person_id AS person_id, p.payroll_id,
       'hire_date' AS field, h.hire_date AS source_value, p.hire_date AS target_value
FROM payroll_employees p
JOIN hcm_employees h ON h.person_id = p.source_person_id
WHERE h.hire_date <> p.hire_date;

-- @check C07 Name missing in target
SELECT 'C07' AS check_id, p.source_person_id AS person_id, p.payroll_id,
       'full_name' AS field, h.last_name AS source_value, p.full_name AS target_value
FROM payroll_employees p
JOIN hcm_employees h ON h.person_id = p.source_person_id
WHERE COALESCE(p.full_name, '') = '';

-- @check C08 Annual salary does not match the source after applying the mapping rule
-- (rows already flagged by C03 are excluded so one defect is logged once)
SELECT 'C08' AS check_id, p.source_person_id AS person_id, p.payroll_id,
       'annual_salary' AS field,
       CASE WHEN h.pay_basis = 'HOURLY' THEN h.comp_amount * 2080 * h.fte
            ELSE h.comp_amount END AS source_value,
       p.annual_salary AS target_value
FROM payroll_employees p
JOIN hcm_employees h ON h.person_id = p.source_person_id
WHERE NOT (p.pay_basis = 'H' AND p.hourly_rate > 150)
  AND ABS(p.annual_salary -
          CASE WHEN h.pay_basis = 'HOURLY' THEN h.comp_amount * 2080 * h.fte
               ELSE h.comp_amount END) > 1.00;

-- @check C09 Employment status out of sync
SELECT 'C09' AS check_id, p.source_person_id AS person_id, p.payroll_id,
       'emp_status' AS field, h.employment_status AS source_value, p.emp_status AS target_value
FROM payroll_employees p
JOIN hcm_employees h ON h.person_id = p.source_person_id
WHERE p.emp_status <> CASE h.employment_status WHEN 'ACTIVE' THEN 'A' ELSE 'W' END;
