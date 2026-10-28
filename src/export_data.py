
"""Export synthetic database tables to CSV, JSON, and SQL."""

import csv
import json
import sqlite3
from pathlib import Path

from src.db import DATABASE_PATH

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "data" / "output"
CSV_DIR = OUTPUT_DIR / "csv"
JSON_DIR = OUTPUT_DIR / "json"

TABLES = [
    "customers",
    "kyc_profiles",
    "accounts",
    "merchants",
    "devices",
    "transactions",
    "transfer_links",
    "risk_rules",
    "alerts",
    "cases",
    "case_alerts",
    "analyst_actions",
    "entity_events",
]


def export_table(conn, table):
    cursor = conn.execute(f'SELECT * FROM "{table}"')
    columns = [item[0] for item in cursor.description]
    rows = cursor.fetchall()

    # CSV export
    csv_path = CSV_DIR / f"{table}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)

    # JSON export
    json_path = JSON_DIR / f"{table}.json"
    json_rows = [
        dict(zip(columns, row))
        for row in rows
    ]

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(json_rows, file, indent=2, ensure_ascii=False)

    print(f"{table}: {len(rows):,} rows exported")


def main():
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    JSON_DIR.mkdir(parents=True, exist_ok=True)

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        for table in TABLES:
            exists = conn.execute(
                """
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type = 'table' AND name = ?
                """,
                (table,),
            ).fetchone()[0]

            if exists:
                export_table(conn, table)

        # Export schema and data as a portable SQL script.
        sql_path = OUTPUT_DIR / "transaction_risk_seed.sql"
        with sql_path.open("w", encoding="utf-8") as file:
            for statement in conn.iterdump():
                file.write(statement + "\n")

    print("\nExport completed.")
    print(f"CSV files:  {CSV_DIR}")
    print(f"JSON files: {JSON_DIR}")
    print(f"SQL dump:   {OUTPUT_DIR / 'transaction_risk_seed.sql'}")


if __name__ == "__main__":
    main()
