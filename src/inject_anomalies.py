
"""Inject deterministic, labeled anomalies into the synthetic database."""

import csv
import random
from pathlib import Path

from src.db import get_connection

SEED = 20261022
ROOT = Path(__file__).resolve().parent.parent
GROUND_TRUTH = ROOT / "data" / "output" / "ground_truth.csv"

FIELDS = [
    "anomaly_id", "entity_type", "entity_id", "anomaly_type",
    "description", "expected_detection", "seed",
]


def record_truth(writer, anomaly_id, entity_type, entity_id,
                 anomaly_type, description, expected_detection):
    writer.writerow({
        "anomaly_id": anomaly_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "anomaly_type": anomaly_type,
        "description": description,
        "expected_detection": expected_detection,
        "seed": SEED,
    })


def inject():
    rng = random.Random(SEED)
    GROUND_TRUTH.parent.mkdir(parents=True, exist_ok=True)

    # This module is designed to run once on a freshly generated prototype.
    # Do not rerun it on the same database.
    with get_connection() as conn:
        already_injected = conn.execute("""
            SELECT COUNT(*)
            FROM transactions
            WHERE issue_type IS NOT NULL
        """).fetchone()[0]

        if already_injected:
            raise RuntimeError(
                "Anomalies already exist. Reset and regenerate the database "
                "before running this module again."
            )

        with GROUND_TRUTH.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()

            
            # 1. Transaction references a closed account.
            # Create a dedicated transaction so existing balance history
            # remains unchanged.
            closed = conn.execute("""
                SELECT account_id, opening_balance
                FROM accounts
                WHERE account_status = 'CLOSED'
                ORDER BY account_id LIMIT 1
            """).fetchone()

            if closed:
                account_id, opening_balance = closed

                conn.execute("""
                    UPDATE accounts
                    SET closed_at = '2026-03-01T00:00:00'
                    WHERE account_id = ?
                """, (account_id,))

                txn_id = "TXN-ANOM-001"
                amount = 50.00
                before = float(opening_balance)
                after = round(before - amount, 2)

                conn.execute("""
                    INSERT INTO transactions (
                        transaction_id, account_id, merchant_id, device_id,
                        transaction_type, amount, transaction_at,
                        balance_before, balance_after, issue_type
                    )
                    VALUES (?, ?, NULL, NULL, 'DEBIT', ?, ?, ?, ?, ?)
                """, (
                    txn_id,
                    account_id,
                    amount,
                    "2026-03-02T00:00:00",
                    before,
                    after,
                    "CLOSED_ACCOUNT_TRANSACTION",
                ))

                record_truth(
                    writer, "ANOM-001", "transaction", txn_id,
                    "CLOSED_ACCOUNT_TRANSACTION",
                    "Transaction occurred after the account closure time.",
                    "Transaction time is later than account closed_at.",
                )
            else:
                raise RuntimeError(
                    "No closed account available for anomaly testing."
                )


            # 2. Negative balance beyond the account's overdraft limit.
            account = conn.execute("""
                SELECT account_id
                FROM accounts
                WHERE account_status = 'ACTIVE'
                ORDER BY account_id LIMIT 1
            """).fetchone()

            if account:
                account_id = account[0]
                txn = conn.execute("""
                    SELECT transaction_id
                    FROM transactions
                    WHERE account_id = ?
                    ORDER BY transaction_id LIMIT 1
                """, (account_id,)).fetchone()

                if txn:
                    txn_id = txn[0]
                    conn.execute("""
                        UPDATE transactions
                        SET transaction_type = 'DEBIT',
                            amount = 5000,
                            balance_before = 100,
                            balance_after = -4900,
                            issue_type = 'OVERDRAFT_VIOLATION'
                        WHERE transaction_id = ?
                    """, (txn_id,))

                    record_truth(
                        writer, "ANOM-002", "transaction", txn_id,
                        "OVERDRAFT_VIOLATION",
                        "Balance falls below the configured overdraft limit.",
                        "balance_after is less than negative overdraft_limit.",
                    )

            
            
            # 3. Create two valid transactions with mismatched transfer amounts.
            accounts = conn.execute("""
                SELECT account_id, opening_balance
                FROM accounts
                WHERE account_status = 'ACTIVE'
                ORDER BY account_id
                LIMIT 2
            """).fetchall()

            if len(accounts) == 2:
                source_account, destination_account = accounts
                source_id = "TXN-ANOM-003-SRC"
                destination_id = "TXN-ANOM-003-DST"

                # Use different amounts, while maintaining balance arithmetic.
                source_amount = 111.00
                destination_amount = 222.00
                source_before = float(source_account[1])
                destination_before = float(destination_account[1])

                source_after = round(source_before - source_amount, 2)
                destination_after = round(
                    destination_before + destination_amount, 2
                )

                # Keep the source balance nonnegative for this test.
                if source_after >= 0:
                    conn.execute("""
                        INSERT INTO transactions (
                            transaction_id, account_id, merchant_id, device_id,
                            transaction_type, amount, transaction_at,
                            balance_before, balance_after, issue_type
                        )
                        VALUES (?, ?, NULL, NULL, 'DEBIT', ?, ?, ?, ?, ?)
                    """, (
                        source_id, source_account[0], source_amount,
                        "2026-03-10T12:00:00", source_before, source_after,
                        "TRANSFER_AMOUNT_MISMATCH",
                    ))

                    conn.execute("""
                        INSERT INTO transactions (
                            transaction_id, account_id, merchant_id, device_id,
                            transaction_type, amount, transaction_at,
                            balance_before, balance_after, issue_type
                        )
                        VALUES (?, ?, NULL, NULL, 'CREDIT', ?, ?, ?, ?, ?)
                    """, (
                        destination_id, destination_account[0],
                        destination_amount, "2026-03-10T12:00:00",
                        destination_before, destination_after,
                        "TRANSFER_AMOUNT_MISMATCH",
                    ))

                    conn.execute("""
                        INSERT INTO transfer_links (
                            transfer_id, source_transaction_id,
                            destination_transaction_id, created_at, issue_type
                        )
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        "TRF-ANOM-003", source_id, destination_id,
                        "2026-03-10T12:00:00", "TRANSFER_AMOUNT_MISMATCH",
                    ))

                    record_truth(
                        writer, "ANOM-003", "transfer", "TRF-ANOM-003",
                        "TRANSFER_AMOUNT_MISMATCH",
                        "Transfer source amount is 111.00; destination is 222.00.",
                        "Source and destination amounts should match.",
                    )
                else:
                    raise RuntimeError(
                        "Could not create test transfer: source balance too low."
                    )
            else:
                raise RuntimeError(
                    "At least two active accounts are required for transfer testing."
                )



            # 4. Alert with no triggering transaction.
            rule = conn.execute("""
                SELECT rule_id FROM risk_rules ORDER BY rule_id LIMIT 1
            """).fetchone()

            if rule:
                conn.execute("""
                    INSERT OR IGNORE INTO alerts
                    (alert_id, transaction_id, rule_id, risk_score,
                     priority, reason, created_at, alert_status)
                    VALUES (?, NULL, ?, 40, 'MEDIUM', ?, ?, 'OPEN')
                """, (
                    "ALT-ANOM-004", rule[0],
                    "Planted alert without a triggering transaction.",
                    "2026-03-05T12:00:00",
                ))

                record_truth(
                    writer, "ANOM-004", "alert", "ALT-ANOM-004",
                    "ORPHAN_ALERT",
                    "Alert intentionally has no transaction reference.",
                    "Alert transaction_id is NULL.",
                )

            # 5. Case disposition occurs before its linked alert.
            alert = conn.execute("""
                SELECT alert_id, created_at
                FROM alerts
                WHERE transaction_id IS NOT NULL
                ORDER BY alert_id LIMIT 1
            """).fetchone()

            if alert:
                alert_id, alert_time = alert
                case_id = "CASE-ANOM-005"
                earlier = "2025-12-31T00:00:00"

                conn.execute("""
                    INSERT INTO cases
                    (case_id, created_at, case_status, disposition, issue_type)
                    VALUES (?, ?, 'RESOLVED', 'CONFIRMED_FRAUD',
                            'DISPOSITION_BEFORE_ALERT')
                """, (case_id, earlier))

                conn.execute("""
                    INSERT INTO case_alerts
                    (case_id, alert_id, linked_at)
                    VALUES (?, ?, ?)
                """, (case_id, alert_id, alert_time))

                conn.execute("""
                    INSERT INTO analyst_actions
                    (action_id, case_id, analyst_id, action_type,
                     action_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "ACT-ANOM-005", case_id, "ANALYST-SYNTH-01",
                    "CONFIRMED", earlier,
                    "Planted chronology anomaly for validation testing.",
                ))

                record_truth(
                    writer, "ANOM-005", "case", case_id,
                    "DISPOSITION_BEFORE_ALERT",
                    "Case disposition action predates the linked alert.",
                    "Analyst action time is earlier than alert creation time.",
                )

    print("Anomaly injection complete.")
    print(f"Ground truth written to: {GROUND_TRUTH}")


if __name__ == "__main__":
    inject()
