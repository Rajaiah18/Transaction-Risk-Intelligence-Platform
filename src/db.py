
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "transaction_risk.db"
SCHEMA_PATH = PROJECT_ROOT / "schema" / "schema.sql"
SEED_SQL_PATH = (
    PROJECT_ROOT / "data" / "output" / "transaction_risk_seed.sql"
)


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}"
        )

    with get_connection() as connection:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema_sql)

        # Load sample data only if the customers table is empty.
        customer_count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

        if customer_count == 0:
            if not SEED_SQL_PATH.exists():
                raise FileNotFoundError(
                    f"Seed SQL file not found: {SEED_SQL_PATH}"
                )

            seed_sql = SEED_SQL_PATH.read_text(encoding="utf-8")
            connection.executescript(seed_sql)

    print(f"Database initialized: {DATABASE_PATH}")


if __name__ == "__main__":
    initialize_database()

