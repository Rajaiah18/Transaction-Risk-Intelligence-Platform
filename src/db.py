
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
        raise FileNotFoundError(f"Missing schema file: {SCHEMA_PATH}")

    if not SEED_SQL_PATH.exists():
        raise FileNotFoundError(f"Missing seed file: {SEED_SQL_PATH}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    seed_sql = SEED_SQL_PATH.read_text(encoding="utf-8")

    # Extract INSERT statements, ignoring CREATE TABLE and transaction commands.
    insert_statements = []
    for statement in seed_sql.split(";"):
        statement = statement.strip()
        if statement.upper().startswith("INSERT INTO"):
            insert_statements.append(statement + ";")

    with get_connection() as connection:
        connection.executescript(schema_sql)

        customer_count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

        if customer_count == 0:
            if not insert_statements:
                raise ValueError("No INSERT statements found in seed SQL.")

            connection.executescript(
                "BEGIN TRANSACTION;\n"
                + "\n".join(insert_statements)
                + "\nCOMMIT;"
            )

    print(f"Database initialized: {DATABASE_PATH}")


if __name__ == "__main__":
    initialize_database()

