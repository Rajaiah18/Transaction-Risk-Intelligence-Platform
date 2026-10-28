
# Transaction Risk Intelligence Platform

A reproducible transaction-risk analytics project that generates synthetic financial data, evaluates transactions using transparent risk rules, creates alerts and investigation cases, and validates intentionally injected data-quality anomalies.

## Features

- Synthetic customers, accounts, merchants, devices, and transactions
- KYC profiles and configurable risk rules
- Rule-based transaction risk alerts
- Case creation and alert-to-case relationships
- Intentional anomaly injection and ground-truth tracking
- Database integrity and transaction balance validation
- CSV, JSON, and SQL data exports
- Automated tests

## Technology Stack

- Python
- SQLite
- SQL
- Streamlit (dashboard)
- CSV and JSON

## Project Structure

- `src/` — data generation, risk evaluation, case management, validation, and exports
- `schema/` — database schema
- `tests/` — automated tests
- `data/` — generated database and exported datasets

## Setup

Create and activate a Python virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required packages after creating `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Generate Data

The generator uses a fixed seed for reproducibility.

```bash
python -m src.generator --customers 5000 --accounts 7000 --transactions 100000 --reset
```

**Warning:** The `--reset` option regenerates the database and removes existing generated data. Do not use it on your current dataset unless you intend to rebuild the full pipeline.

## Run the Pipeline

```bash
python -m src.add_reference_data
python -m src.check_data
python -m src.risk_engine
python -m src.case_manager
python -m src.validate_data
python -m src.export_data
```

For the complete anomaly-injection workflow, run `python -m src.inject_anomalies` only once after generating a fresh baseline dataset. Do not rerun it on an already-injected database.

## Run Automated Tests

```bash
python -m unittest discover -s tests -v
```

## Validation

The validation process checks foreign-key integrity, transaction balance arithmetic, closed-account transactions, overdraft violations, transfer mismatches, orphan alerts, and case actions that precede linked alerts.

## Reproducibility

The data-generation seed is `20261022`. Generated data and intentional anomalies are designed to support repeatable validation and analysis.

## Disclaimer

This project uses synthetic data for educational and demonstration purposes. It does not contain real customer financial information.
