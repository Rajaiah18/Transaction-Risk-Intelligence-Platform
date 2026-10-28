
import unittest

from src.db import get_connection


class TestTransactionRiskData(unittest.TestCase):

    def test_foreign_keys_are_valid(self):
        with get_connection() as conn:
            violations = conn.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()

        self.assertEqual(violations, [])

    def test_transaction_balances_are_consistent(self):
        with get_connection() as conn:
            mismatches = conn.execute("""
                SELECT transaction_id
                FROM transactions
                WHERE ABS(
                    balance_after -
                    (balance_before +
                     CASE
                         WHEN transaction_type = 'CREDIT' THEN amount
                         ELSE -amount
                     END)
                ) > 0.011
            """).fetchall()

        self.assertEqual(mismatches, [])

    def test_five_intentional_anomalies_exist(self):
        with get_connection() as conn:
            checks = [
                (
                    "Closed account transaction",
                    """
                    SELECT COUNT(*) FROM transactions
                    WHERE transaction_id = 'TXN-ANOM-001'
                      AND issue_type = 'CLOSED_ACCOUNT_TRANSACTION'
                    """,
                ),
                (
                    "Overdraft violation",
                    """
                    SELECT COUNT(*) FROM transactions
                    WHERE issue_type = 'OVERDRAFT_VIOLATION'
                    """,
                ),
                (
                    "Transfer amount mismatch",
                    """
                    SELECT COUNT(*) FROM transfer_links
                    WHERE transfer_id = 'TRF-ANOM-003'
                      AND issue_type = 'TRANSFER_AMOUNT_MISMATCH'
                    """,
                ),
                (
                    "Orphan alert",
                    """
                    SELECT COUNT(*) FROM alerts
                    WHERE alert_id = 'ALT-ANOM-004'
                      AND transaction_id IS NULL
                    """,
                ),
                
(
    "Disposition before alert",
    """
    SELECT COUNT(*)
    FROM analyst_actions aa
    JOIN case_alerts ca ON ca.case_id = aa.case_id
    JOIN alerts a ON a.alert_id = ca.alert_id
    WHERE aa.action_id = 'ACT-ANOM-005'
      AND ca.case_id = 'CASE-ANOM-005'
      AND aa.action_at < a.created_at
    """,
),

            ]

            for description, query in checks:
                with self.subTest(anomaly=description):
                    count = conn.execute(query).fetchone()[0]
                    self.assertEqual(
                        count,
                        1,
                        f"{description}: expected 1 record, found {count}",
                    )


if __name__ == "__main__":
    unittest.main()
