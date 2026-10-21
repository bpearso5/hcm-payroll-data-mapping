-- Schema for the mock HCM (source) and Payroll (target) tables.
-- Written to run unchanged in MySQL 8 and SQLite 3.

DROP TABLE IF EXISTS hcm_employees;
DROP TABLE IF EXISTS payroll_employees;

CREATE TABLE hcm_employees (
    person_id          VARCHAR(10)    NOT NULL PRIMARY KEY,
    national_id        VARCHAR(12)    NOT NULL,
    first_name         VARCHAR(40)    NOT NULL,
    last_name          VARCHAR(40)    NOT NULL,
    hire_date          DATE           NOT NULL,
    hire_action        VARCHAR(10)    NOT NULL,   -- HIRE | REHIRE
    employment_status  VARCHAR(12)    NOT NULL,   -- ACTIVE | TERMINATED
    pay_basis          VARCHAR(10)    NOT NULL,   -- HOURLY | SALARIED
    comp_amount        DECIMAL(12,2)  NOT NULL,   -- hourly rate or annual salary
    fte                DECIMAL(3,2)   NOT NULL,
    department         VARCHAR(30),
    country            CHAR(2)        NOT NULL,
    region             VARCHAR(30),
    postal_code        VARCHAR(10),
    bank_ref           VARCHAR(12)
);

CREATE TABLE payroll_employees (
    payroll_id         VARCHAR(10)    NOT NULL PRIMARY KEY,
    source_person_id   VARCHAR(10)    NOT NULL,
    national_id        VARCHAR(12)    NOT NULL,
    full_name          VARCHAR(90),
    hire_date          DATE,
    emp_status         CHAR(1),                   -- A | W
    pay_basis          CHAR(1),                   -- H | S
    annual_salary      DECIMAL(12,2),
    hourly_rate        DECIMAL(12,2),
    fte                DECIMAL(3,2),
    country            CHAR(2),
    state              VARCHAR(30),
    province           VARCHAR(30),
    postal_code        VARCHAR(10),
    bank_ref           VARCHAR(12)
);

CREATE INDEX ix_payroll_source ON payroll_employees (source_person_id);
CREATE INDEX ix_payroll_nid    ON payroll_employees (national_id);
