
"""Validate database integrity and detect planted risk anomalies."""

from src.db import get_connection


CHECKS = {
    "Foreign-key violations": """
        SELECT COUNT(*) FROM pragma_foreign_key_check
    """,
    "Transaction balance mismatches": """
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
    """,
    "Transactions after account closure": """
        SELECT COUNT(*)
        FROM transactions t
        JOIN accounts a ON a.account_id = t.account_id
        WHERE a.account_status = 'CLOSED'
          AND a.closed_at IS NOT NULL
          AND t.transaction_at >= a.closed_at
    """,
    "Negative balances beyond overdraft limits": """
        SELECT COUNT(*)
        FROM transactions t
        JOIN accounts a ON a.account_id = t.account_id
        WHERE t.balance_after < -a.overdraft_limit
    """,
    "Mismatched transfer legs": """
        SELECT COUNT(*)
        FROM transfer_links l
        JOIN transactions s
          ON s.transaction_id = l.source_transaction_id
        JOIN transactions d
          ON d.transaction_id = l.destination_transaction_id
        WHERE ABS(s.amount - d.amount) >= 0.011
    """,
    "Alerts without triggering transactions": """
        SELECT COUNT(*)
        FROM alerts a
        LEFT JOIN transactions t
          ON t.transaction_id = a.transaction_id
        WHERE a.transaction_id IS NULL
           OR t.transaction_id IS NULL
    """,
    "Case actions before linked alerts": """
        SELECT COUNT(DISTINCT aa.action_id)
        FROM analyst_actions aa
        JOIN case_alerts ca ON ca.case_id = aa.case_id
        JOIN alerts a ON a.alert_id = ca.alert_id
        WHERE aa.action_type IN ('CONFIRMED', 'FALSE_POSITIVE', 'CLOSED')
          AND aa.action_at < a.created_at
    """,
    "Cases without linked alerts": """
        SELECT COUNT(*)
        FROM cases c
        WHERE NOT EXISTS (
            SELECT 1 FROM case_alerts ca WHERE ca.case_id = c.case_id
        )
    """,
}


def main():
    with get_connection() as conn:
        print("--- Database Validation Report ---")
        for label, query in CHECKS.items():
            count = conn.execute(query).fetchone()[0]
            print(f"{label}: {count}")

        print("\n--- Entity Counts ---")
        tables = (
            "customers", "accounts", "transactions", "transfer_links",
            "alerts", "cases", "case_alerts", "analyst_actions",
        )
        for table in tables:
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            print(f"{table}: {count}")


if __name__ == "__main__":
    main()
