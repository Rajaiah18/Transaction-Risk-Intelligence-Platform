
from src.db import get_connection


def main():
    with get_connection() as conn:
        tables = [
            "customers",
            "accounts",
            "merchants",
            "devices",
            "transactions",
        ]

        print("\n--- Record Counts ---")
        for table in tables:
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            print(f"{table:15} {count:>8,}")

        foreign_key_errors = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        arithmetic_errors = conn.execute("""
            SELECT COUNT(*)
            FROM transactions
            WHERE ABS(
                balance_after -
                CASE
                    WHEN transaction_type = 'CREDIT'
                        THEN balance_before + amount
                    ELSE balance_before - amount
                END
            ) >= 0.011
        """).fetchone()[0]

        print("\n--- Integrity Checks ---")
        print(f"Foreign-key violations: {len(foreign_key_errors)}")
        print(f"Balance arithmetic errors: {arithmetic_errors}")

        if foreign_key_errors or arithmetic_errors:
            raise SystemExit("Validation failed!")

        print("Basic validation passed!")


if __name__ == "__main__":
    main()
