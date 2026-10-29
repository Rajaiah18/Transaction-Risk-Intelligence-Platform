# AI Prompt History

## 1. Purpose

This document records AI assistance used during development of the Transaction Risk Intelligence Platform for the YottaFlex AI recruitment challenge.

**Important:** The entries below summarize the main prompt topics reconstructed from the available development history. They are not claimed to be a complete, verbatim transcript of every prompt. Where original wording is available, it should be preserved separately.

## 2. AI Tools Used

- **ChatGPT:** Used for project planning, implementation guidance, debugging support, documentation, and interpreting test and validation results.

Add any other AI tools used during development and document their prompts as well.

## 3. Reconstructed Prompt Record

The following topics summarize the main areas where AI assistance was requested:

1. Help plan a transaction-risk analytics project using Python and SQLite.
2. Help design a relational database schema for customers, accounts, transactions, alerts, cases, and related entities.
3. Help generate reproducible synthetic financial data with customers, accounts, and transactions.
4. Help implement configurable risk rules and transaction-risk alert generation.
5. Help implement investigation-case creation and alert-to-case relationships.
6. Help inject intentional data-quality anomalies and track them with ground-truth records.
7. Help validate foreign keys, transaction balances, account closures, overdraft limits, transfer legs, alerts, and case actions.
8. Help export database tables to CSV, JSON, and SQL.
9. Help create and run a Streamlit dashboard for exploring transaction risk and alerts.
10. Help run automated tests and understand their results.
11. Help document project setup, execution, validation, and limitations.
12. Help initialize Git, configure `.gitignore`, publish the project to a public GitHub repository, and update its README.

These entries are reconstructed summaries, not exact historical prompt text.

## 4. How AI Assistance Was Used

AI assistance helped break tasks into smaller steps, explain implementation concepts, troubleshoot commands, improve documentation, and interpret validation results.

The project was executed in a local development environment. The recorded validation and test results were reviewed after running the relevant commands.

## 5. Personal Review and Validation

The following checks were performed in the local environment:

- Ran the database validation script.
- Ran the automated test suite; all three recorded tests passed.
- Checked that the Streamlit dashboard ran locally.
- Reviewed entity counts and the five intentionally injected anomaly categories.
- Verified that the project files were pushed to a public GitHub repository.

Do not interpret these checks as proof that every possible input or production scenario has been tested.

## 6. Limitations and Assumptions

- The platform uses synthetic financial data, not real customer records.
- Risk evaluation is rule-based and does not use a trained machine-learning model.
- The injected anomalies are test scenarios, not evidence of actual fraud.
- Rules may miss risks outside their defined conditions or generate false positives.
- The project is a demonstration and has not been established as production-ready.

## 7. Prompt History Completeness

This document is a reconstructed summary based on the development history available for review. It must not be treated as a complete verbatim record.

Before final submission, recover and include the original prompts from available ChatGPT conversations and any other AI tools used. If some prompts cannot be recovered, state that limitation clearly rather than inventing exact wording.
