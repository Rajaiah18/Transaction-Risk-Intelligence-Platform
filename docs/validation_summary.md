# Validation Summary
## Transaction Risk Intelligence Platform

### Dataset Overview

The platform uses reproducible synthetic financial data generated with seed `20261022`.

| Entity | Record Count |
|---|---:|
| Customers | 5,000 |
| KYC Profiles | 5,000 |
| Accounts | 7,000 |
| Merchants | 100 |
| Devices | 100 |
| Transactions | 100,003 |
| Transfer Links | 1 |
| Risk Rules | 5 |
| Alerts | 33,588 |
| Cases | 33,589 |
| Case-Alert Links | 33,589 |
| Analyst Actions | 1 |
| Entity Events | 0 |

### Integrity Checks

The latest validation run reported:

- Foreign-key violations: 0
- Transaction balance mismatches: 0
- Transactions occurring after account closure: 1
- Negative balances beyond overdraft limits: 1
- Mismatched transfer legs: 1
- Alerts without triggering transactions: 1
- Case actions before linked alerts: 1
- Cases without linked alerts: 0

The five detected anomaly types are intentional test records used to verify validation behavior.

### Automated Tests

Command:

`python -m unittest discover -s tests -v`

Result: **3 tests passed.**

The tests check foreign-key integrity, transaction balance arithmetic, and the presence of all five intentional anomaly scenarios.

### Export Artifacts

The export script completed successfully and generated:

- CSV files under `data/output/csv/`
- JSON files under `data/output/json/`
- SQL database dump at `data/output/transaction_risk_seed.sql`

### Interpretation

The integrity checks report no foreign-key violations or transaction balance arithmetic mismatches. The other five anomaly checks intentionally identify seeded data-quality problems.

The alert and case totals differ because the disposition-before-alert test case is associated with an existing alert while retaining a separate investigation case.

### Scope and Limitations

This project uses synthetic data and transparent, rule-based risk detection. Its outputs demonstrate data engineering, validation, and risk-monitoring workflows; they should not be interpreted as proof of real-world fraud or production-grade detection accuracy.