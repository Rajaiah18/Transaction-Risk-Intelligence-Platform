
"""Create KYC profiles and initial risk rules."""

from src.db import get_connection


def add_reference_data():
    with get_connection() as conn:
        # One KYC profile for each customer.
        customers = conn.execute(
            "SELECT customer_id FROM customers ORDER BY customer_id"
        ).fetchall()

        for (customer_id,) in customers:
            exists = conn.execute(
                "SELECT 1 FROM kyc_profiles WHERE customer_id = ?",
                (customer_id,),
            ).fetchone()

            if exists:
                continue

            conn.execute(
                """
                INSERT INTO kyc_profiles (
                    kyc_id, customer_id, verification_status,
                    risk_category, effective_from, effective_to
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    f"KYC-{customer_id}",
                    customer_id,
                    "VERIFIED",
                    "LOW",
                    "2026-01-01T00:00:00",
                    None,
                ),
            )

        # Insert the baseline rules only once.
        rules = [
            (
                "RULE-001",
                "High transaction amount",
                "Flag transactions above a configured amount.",
                1000.0,
                30,
            ),
            (
                "RULE-002",
                "Repeated transaction activity",
                "Flag accounts with unusually frequent transactions.",
                5.0,
                25,
            ),
            (
                "RULE-003",
                "High-risk customer profile",
                "Increase review priority for high-risk KYC profiles.",
                None,
                20,
            ),
            (
                "RULE-004",
                "Dormant account activity",
                "Flag transactions associated with dormant accounts.",
                None,
                35,
            ),
            (
                "RULE-005",
                "New device activity",
                "Flag transactions from recently observed devices.",
                None,
                15,
            ),
        ]

        for rule_id, name, description, threshold, points in rules:
            conn.execute(
                """
                INSERT OR IGNORE INTO risk_rules (
                    rule_id, rule_name, description, threshold,
                    risk_points, is_active, effective_from, effective_to
                )
                VALUES (?, ?, ?, ?, ?, 1, ?, NULL)
                """,
                (
                    rule_id,
                    name,
                    description,
                    threshold,
                    points,
                    "2026-01-01T00:00:00",
                ),
            )

    print(f"KYC profiles created/checked: {len(customers)}")
    print(f"Risk rules created/checked: {len(rules)}")


if __name__ == "__main__":
    add_reference_data()
