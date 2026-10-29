# Design Decisions, Validation, and Limitations

## 1. Problem and Objective

The Transaction Risk Intelligence Platform demonstrates how synthetic financial transactions can be stored, evaluated using configurable risk rules, converted into alerts and investigation cases, and checked for data-quality issues.

The objective is to create a reproducible, locally runnable demonstration of a basic transaction-risk monitoring workflow.

## 2. Technology Choices

- **Python:** Used for data generation, risk evaluation, validation, exports, and application logic.
- **SQLite:** Provides local relational storage without requiring a separate database server.
- **Streamlit:** Provides a browser-based dashboard for reviewing transaction-risk information.
- **CSV, JSON, and SQL exports:** Make generated data easier to inspect and reuse.
- **Python unittest:** Provides automated checks for key integrity and anomaly expectations.

These technologies keep the project relatively simple to install and run locally.

## 3. Database Design

The database separates entities such as customers, accounts, merchants, devices, transactions, alerts, cases, and analyst actions into related tables.

This structure reduces unnecessary duplication and helps represent relationships between financial activity and investigations. Foreign-key constraints and validation queries help identify broken relationships and inconsistent records.

## 4. Risk Evaluation and Case Management

The risk engine applies configured rules to transaction data and creates alerts when the relevant conditions are met. The case-management component associates alerts with investigation cases.

A rule-based approach was chosen because its conditions are explicit and easier to inspect and explain than an opaque model. However, the quality of detection depends on the rules that have been configured.

## 5. Intentional Anomalies

Five deliberate data-quality scenarios were added to exercise the validation logic:

1. A transaction after account closure.
2. A balance below the permitted overdraft limit.
3. Mismatched transfer legs.
4. An alert without a triggering transaction.
5. A case action or disposition preceding its linked alert.

These scenarios test whether the validation process can identify known problems. They are synthetic test cases, not evidence of real financial fraud.

## 6. Reproducibility and Data Handling

The generator uses the fixed seed `20261022` to support reproducibility. The project stores its SQLite database locally and excludes the database and virtual environment from version control.

Generated CSV, JSON, and SQL exports are included in the repository to support inspection of the dataset. The generator's reset option and anomaly-injection step must be used carefully to avoid destroying or duplicating the current test dataset.

## 7. Validation Approach and Results

The recorded validation checks cover:

- Foreign-key violations.
- Transaction balance mismatches.
- Transactions after account closure.
- Negative balances beyond overdraft limits.
- Mismatched transfer legs.
- Alerts without triggering transactions.
- Case actions before linked alerts.
- Cases without linked alerts.

The latest recorded report showed zero foreign-key violations, zero transaction balance mismatches, and zero cases without linked alerts. Each of the five intentional anomaly categories was detected once.

The recorded automated test suite passed all three tests:

- `test_five_intentional_anomalies_exist`
- `test_foreign_keys_are_valid`
- `test_transaction_balances_are_consistent`

These results demonstrate that the recorded checks passed for the current dataset. They do not prove that the platform is free from all defects.

## 8. Trade-offs and Limitations

- SQLite simplifies local setup but is not a substitute for evaluating the concurrency, access control, and operational needs of a production financial system.
- Rule-based detection is explainable but may miss patterns not represented in the configured rules.
- Synthetic data provides a safe test environment but cannot establish real-world detection accuracy.
- The current automated tests cover selected integrity and anomaly conditions, not every feature or edge case.
- The dashboard and pipeline require further testing before any production use.

## 9. Future Improvements

Potential improvements include:

- Adding more unit and integration tests.
- Testing malformed and boundary-case transactions.
- Improving alert prioritization and investigation workflows.
- Adding authentication and role-based access controls if deployed for multiple users.
- Measuring false-positive and false-negative rates against a suitable labelled dataset.
- Adding automated checks to verify the full pipeline from a fresh database.

## 10. Personal Understanding

Before the technical walkthrough, I should be able to explain the database relationships, how a transaction is evaluated, how alerts become cases, how each intentional anomaly is detected, how to run the tests, and what the current validation results do and do not prove.

I should also clearly distinguish AI-assisted implementation from the code and decisions I have personally reviewed and tested.
