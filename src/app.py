import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

from src.db import get_connection, initialize_database
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
import streamlit as st
import pandas as pd

from src.db import get_connection
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

st.set_page_config(
    page_title="Transaction Risk Intelligence",
    page_icon="🛡️",
    layout="wide",
)
initialize_database()

st.title("🛡️ Transaction Risk Intelligence Platform")
st.caption("Synthetic transaction monitoring, risk alerts, and data-quality validation")

@st.cache_data(ttl=30)
def load_data():
    with get_connection() as conn:
        counts = {}
        for table in [
            "customers",
            "accounts",
            "transactions",
            "alerts",
            "cases",
            "transfer_links",
        ]:
            counts[table] = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

        priorities = pd.read_sql_query(
            """
            SELECT priority, COUNT(*) AS alert_count
            FROM alerts
            GROUP BY priority
            ORDER BY CASE priority
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                ELSE 4
            END
            """,
            conn,
        )

        recent_alerts = pd.read_sql_query(
            """
            SELECT
                alert_id,
                transaction_id,
                rule_id,
                risk_score,
                priority,
                reason,
                created_at,
                alert_status
            FROM alerts
            ORDER BY created_at DESC, alert_id DESC
            LIMIT 100
            """,
            conn,
        )

        cases_by_status = pd.read_sql_query(
            """
            SELECT case_status, COUNT(*) AS case_count
            FROM cases
            GROUP BY case_status
            """,
            conn,
        )

        anomalies = pd.read_sql_query(
            """
            SELECT 'Closed-account transaction' AS anomaly,
                   COUNT(*) AS detected
            FROM transactions
            WHERE issue_type = 'CLOSED_ACCOUNT_TRANSACTION'

            UNION ALL

            SELECT 'Overdraft violation', COUNT(*)
            FROM transactions
            WHERE issue_type = 'OVERDRAFT_VIOLATION'

            UNION ALL

            SELECT 'Transfer amount mismatch', COUNT(*)
            FROM transfer_links
            WHERE issue_type = 'TRANSFER_AMOUNT_MISMATCH'

            UNION ALL

            SELECT 'Orphan alert', COUNT(*)
            FROM alerts
            WHERE alert_id = 'ALT-ANOM-004'
              AND transaction_id IS NULL

            UNION ALL

            SELECT 'Disposition before alert', COUNT(*)
            FROM analyst_actions aa
            JOIN case_alerts ca ON ca.case_id = aa.case_id
            JOIN alerts a ON a.alert_id = ca.alert_id
            WHERE aa.action_id = 'ACT-ANOM-005'
              AND aa.action_at < a.created_at
            """,
            conn,
        )

    return counts, priorities, recent_alerts, cases_by_status, anomalies


try:
    counts, priorities, recent_alerts, cases_by_status, anomalies = load_data()

    col1, col2, col3 = st.columns(3)
    col1.metric("Customers", f"{counts['customers']:,}")
    col2.metric("Accounts", f"{counts['accounts']:,}")
    col3.metric("Transactions", f"{counts['transactions']:,}")

    col4, col5, col6 = st.columns(3)
    col4.metric("Risk Alerts", f"{counts['alerts']:,}")
    col5.metric("Investigation Cases", f"{counts['cases']:,}")
    col6.metric("Transfer Links", f"{counts['transfer_links']:,}")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Alerts by Priority")
        if not priorities.empty:
            st.bar_chart(
                priorities.set_index("priority")["alert_count"]
            )
        else:
            st.info("No alerts are available.")

    with right:
        st.subheader("Cases by Status")
        if not cases_by_status.empty:
            st.bar_chart(
                cases_by_status.set_index("case_status")["case_count"]
            )
        else:
            st.info("No cases are available.")

    st.subheader("Intentional Data-Quality Anomalies")
    st.caption(
        "These are seeded test anomalies, not necessarily real-world fraud."
    )
    st.dataframe(anomalies, use_container_width=True, hide_index=True)

    st.subheader("Recent Risk Alerts")

    search = st.text_input(
        "Search by alert ID, transaction ID, rule, or reason"
    )

    priority_options = ["All"] + sorted(
        recent_alerts["priority"].dropna().unique().tolist()
    )
    selected_priority = st.selectbox("Filter by priority", priority_options)

    filtered = recent_alerts.copy()

    if selected_priority != "All":
        filtered = filtered[
            filtered["priority"] == selected_priority
        ]

    if search:
        searchable = filtered.fillna("").astype(str)
        mask = searchable.apply(
            lambda column: column.str.contains(
                search, case=False, regex=False
            )
        ).any(axis=1)
        filtered = filtered[mask]

    st.dataframe(filtered, use_container_width=True, hide_index=True)

    if st.button("Refresh dashboard"):
        st.cache_data.clear()
        st.rerun()

except Exception as exc:
    st.error("The dashboard could not load the database.")
    st.exception(exc)
    st.info(
        "Run the dashboard from the main project folder and check that "
        "the database has been generated."
    )
