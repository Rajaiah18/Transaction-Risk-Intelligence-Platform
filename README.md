# Transaction Risk Intelligence Platform

A reproducible transaction-risk analytics platform that generates synthetic financial data, evaluates transactions using transparent risk rules, creates risk alerts and investigation cases, and validates intentionally injected data-quality anomalies.

## Features

- Generates synthetic customers, accounts, merchants, devices, and transactions.
- Maintains KYC profiles and configurable risk rules.
- Detects transaction risks using rule-based evaluation.
- Creates alerts and links them to investigation cases.
- Injects known data-quality anomalies for testing.
- Validates database integrity and transaction balances.
- Exports database tables to CSV, JSON, and SQL formats.
- Provides a Streamlit dashboard for exploring risk data and alerts.
- Includes automated unit tests.

## Technology Stack

- Python
- SQLite and SQL
- Streamlit
- Pandas
- CSV and JSON

## Project Structure

```text
Transaction-Risk-Intelligence-Platform/
├── src/                  # Application and data pipeline
├── schema/               # Database schema
├── tests/                # Automated tests
├── docs/                 # Data dictionary and validation summary
├── data/output/          # Generated CSV, JSON, and SQL exports
├── requirements.txt      # Python dependencies
├── .gitignore
└── README.md
```

The local SQLite database and Python virtual environment are excluded from Git.

## Prerequisites

- Python 3.11 or a compatible Python version
- Git
- pip

## Installation

Clone the repository:

```bash
git clone https://github.com/Rajaiah18/Transaction-Risk-Intelligence-Platform.git
cd Transaction-Risk-Intelligence-Platform
```

Create and activate a virtual environment on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Dashboard

Start the Streamlit application:

```bash
streamlit run src/app.py
```

Open the local URL displayed in the terminal, usually `http://localhost:8501`.

## Data Generation and Pipeline

The generator uses a fixed random seed (`20261022`) to support reproducible synthetic datasets.

**Warning:** The `--reset` option rebuilds the database and removes existing generated data. Use it only when you intend to start a fresh dataset.

To rebuild the dataset and run the pipeline from the beginning, execute these commands separately and in order:

```bash
python -m src.generator --customers 5000 --accounts 7000 --transactions 100000 --reset
python -m src.add_reference_data
python -m src.inject_anomalies
python -m src.risk_engine
python -m src.case_manager
python -m src.validate_data
python -m src.export_data
```

Run each command only after the preceding command completes successfully. The anomaly-injection script is intended to run once per fresh baseline dataset; do not rerun it against a database that already contains the injected anomalies.

## Automated Tests

Run the tests from the project root:

```bash
python -m unittest discover -s tests -v
```

The current test suite contains three tests covering:

- Presence of the five intentional anomalies.
- Foreign-key integrity.
- Transaction balance consistency.

**Latest recorded result:** All three tests passed.

## Validation Results

The current generated dataset contains:

| Metric | Count |
|---|---:|
| Customers | 5,000 |
| Accounts | 7,000 |
| Transactions | 100,003 |
| Alerts | 33,588 |
| Cases | 33,589 |

The validator checks:

- Foreign-key violations
- Transaction balance mismatches
- Transactions occurring after account closure
- Negative balances beyond overdraft limits
- Mismatched transfer legs
- Alerts without triggering transactions
- Case actions occurring before linked alerts
- Cases without linked alerts

The current dataset contains five deliberately injected anomalies, with one occurrence in each of the five anomaly categories. Foreign-key violations, transaction balance mismatches, and cases without linked alerts are zero.

See [`docs/validation_summary.md`](docs/validation_summary.md) for the validation details and [`docs/data_dictionary.md`](docs/data_dictionary.md) for the dataset and field descriptions.

## Reproducibility and Data Safety

- The synthetic data generator uses seed `20261022`.
- The dataset includes deliberately injected anomalies for validation and demonstration.
- Generated CSV, JSON, and SQL exports are stored under `data/output/`.
- The local database is not committed to the repository.

## Disclaimer

This project uses synthetic data for educational and demonstration purposes. It does not contain real customer financial information.
