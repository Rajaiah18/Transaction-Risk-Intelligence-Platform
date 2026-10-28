
"""Create investigation cases for alerts that are not yet linked."""

from src.db import get_connection


def create_cases():
    created = 0

    with get_connection() as conn:
        alerts = conn.execute("""
            SELECT a.alert_id, a.created_at
            FROM alerts a
            WHERE NOT EXISTS (
                SELECT 1
                FROM case_alerts ca
                WHERE ca.alert_id = a.alert_id
            )
            ORDER BY a.created_at, a.alert_id
        """).fetchall()

        for alert_id, created_at in alerts:
            case_id = f"CASE-{alert_id}"

            conn.execute(
                """
                INSERT OR IGNORE INTO cases (
                    case_id, created_at, case_status,
                    disposition, issue_type
                )
                VALUES (?, ?, 'OPEN', NULL, NULL)
                """,
                (case_id, created_at),
            )

            conn.execute(
                """
                INSERT OR IGNORE INTO case_alerts (
                    case_id, alert_id, linked_at
                )
                VALUES (?, ?, ?)
                """,
                (case_id, alert_id, created_at),
            )

            created += 1

    print(f"Cases created/linked: {created}")


if __name__ == "__main__":
    create_cases()
