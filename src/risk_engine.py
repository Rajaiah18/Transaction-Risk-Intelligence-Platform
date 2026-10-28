

"""Evaluate transactions against transparent, reproducible risk rules."""

from datetime import datetime

from src.db import get_connection

WINDOW_SECONDS = 24 * 60 * 60
VELOCITY_THRESHOLD = 6


def priority_for_score(score):
    if score >= 80:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def evaluate_transactions():
    alerts_created = 0

    with get_connection() as conn:
        # Load device metadata once instead of querying for every transaction.
        device_first_seen = dict(
            conn.execute(
                "SELECT device_id, first_seen_at FROM devices"
            ).fetchall()
        )

        existing = {
            (transaction_id, rule_id)
            for transaction_id, rule_id in conn.execute(
                "SELECT transaction_id, rule_id FROM alerts "
                "WHERE transaction_id IS NOT NULL"
            )
        }

        transactions = conn.execute("""
            SELECT
                t.transaction_id,
                t.account_id,
                t.amount,
                t.transaction_at,
                t.device_id,
                a.account_status,
                k.risk_category
            FROM transactions t
            JOIN accounts a ON a.account_id = t.account_id
            LEFT JOIN kyc_profiles k ON k.customer_id = a.customer_id
            ORDER BY t.account_id, t.transaction_at, t.transaction_id
        """).fetchall()

        # Store timestamps per account for efficient velocity checks.
        account_events = {}
        for txn in transactions:
            account_events.setdefault(txn[1], []).append(
                (datetime.fromisoformat(txn[3]), txn[0])
            )

        for (
            transaction_id,
            account_id,
            amount,
            transaction_at,
            device_id,
            account_status,
            risk_category,
        ) in transactions:
            timestamp = datetime.fromisoformat(transaction_at)
            matches = []

            if amount > 1000:
                matches.append((
                    "RULE-001",
                    30,
                    "Transaction amount exceeds 1000",
                ))

            # Count transactions within the preceding 24 hours.
            recent_count = sum(
                0 <= (timestamp - event_time).total_seconds()
                <= WINDOW_SECONDS
                for event_time, _ in account_events[account_id]
            )

            if recent_count >= VELOCITY_THRESHOLD:
                matches.append((
                    "RULE-002",
                    25,
                    "At least six transactions within a 24-hour window",
                ))

            if risk_category == "HIGH":
                matches.append((
                    "RULE-003",
                    20,
                    "Customer KYC risk category is HIGH",
                ))

            if account_status == "DORMANT":
                matches.append((
                    "RULE-004",
                    35,
                    "Transaction associated with dormant account",
                ))

            first_seen = device_first_seen.get(device_id)
            if (
                first_seen
                and timestamp.date()
                == datetime.fromisoformat(first_seen).date()
            ):
                matches.append((
                    "RULE-005",
                    15,
                    "Transaction occurred on the device's first-seen date",
                ))

            # Preserve one alert per transaction and matching rule.
            for rule_id, points, reason in matches:
                if (transaction_id, rule_id) in existing:
                    continue

                score = min(100, points)
                alert_id = f"ALT-{transaction_id}-{rule_id}"

                conn.execute("""
                    INSERT INTO alerts (
                        alert_id, transaction_id, rule_id, risk_score,
                        priority, reason, created_at, alert_status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
                """, (
                    alert_id,
                    transaction_id,
                    rule_id,
                    score,
                    priority_for_score(score),
                    reason,
                    transaction_at,
                ))

                existing.add((transaction_id, rule_id))
                alerts_created += 1

    print(f"New alerts created: {alerts_created}")


if __name__ == "__main__":
    evaluate_transactions()
