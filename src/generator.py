
"""Reproducible synthetic data generator for Transaction Risk Intelligence."""

import argparse
import random
from datetime import datetime, timedelta

from src.db import get_connection

SEED = 20261022
YEAR = 2026
BASE_TIME = datetime(2026, 1, 1, 0, 0, 0)


def generate_data(
    customer_count: int = 5000,
    account_count: int = 7000,
    transaction_count: int = 100000,
    reset: bool = False,
) -> None:
    """Generate deterministic synthetic master data and transactions."""

    if customer_count < 1:
        raise ValueError("customer_count must be at least 1")

    if not customer_count <= account_count <= customer_count * 5:
        raise ValueError(
            "Use at least one and at most five accounts per customer"
        )

    if transaction_count < 1:
        raise ValueError("transaction_count must be at least 1")

    rng = random.Random(SEED)

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

        if existing and not reset:
            raise RuntimeError(
                "Customer data already exists. Use --reset to regenerate "
                "the synthetic dataset."
            )

        if reset:
            # Delete child records before parent records.
            for table in (
                "analyst_actions",
                "case_alerts",
                "cases",
                "alerts",
                "transfer_links",
                "transactions",
                "risk_rules",
                "devices",
                "merchants",
                "accounts",
                "kyc_profiles",
                "entity_events",
                "customers",
            ):
                conn.execute(f"DELETE FROM {table}")

        # 1. Customers
        customers = []

        for i in range(1, customer_count + 1):
            created_at = BASE_TIME - timedelta(
                days=rng.randint(30, 1500)
            )

            status = rng.choices(
                ["ACTIVE", "INACTIVE", "BLOCKED"],
                weights=[90, 7, 3],
            )[0]

            customers.append(
                (
                    f"CUS-{i:06d}",
                    f"Synthetic Customer {i:06d}",
                    created_at.isoformat(),
                    status,
                )
            )

        conn.executemany(
            """
            INSERT INTO customers
                (customer_id, full_name, created_at, customer_status)
            VALUES (?, ?, ?, ?)
            """,
            customers,
        )

        # 2. Accounts
        account_owners = [
            customers[i % customer_count][0]
            for i in range(account_count)
        ]
        rng.shuffle(account_owners)

        accounts = []
        balances = {}
        owner_counts = {}

        for i, owner in enumerate(account_owners, start=1):
            owner_counts[owner] = owner_counts.get(owner, 0) + 1
            account_id = f"ACC-{owner}-{owner_counts[owner]:02d}"

            opened_at = BASE_TIME - timedelta(
                days=rng.randint(10, 1200)
            )

            status = rng.choices(
                ["ACTIVE", "DORMANT", "CLOSED", "FROZEN"],
                weights=[85, 8, 4, 3],
            )[0]

            closed_at = None

            if status == "CLOSED":
                # Ensure closure occurs after opening and no later than
                # the start of the transaction period.
                available_days = max(
                    0, (BASE_TIME - opened_at).days
                )
                closure_days = rng.randint(0, available_days)
                closed_at = (
                    opened_at + timedelta(days=closure_days)
                ).isoformat()

            opening_balance = round(
                rng.uniform(2000, 20000), 2
            )

            accounts.append(
                (
                    account_id,
                    owner,
                    opened_at.isoformat(),
                    closed_at,
                    status,
                    opening_balance,
                    0.0,
                )
            )

            balances[account_id] = opening_balance

        conn.executemany(
            """
            INSERT INTO accounts
                (account_id, customer_id, opened_at, closed_at,
                 account_status, opening_balance, overdraft_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            accounts,
        )

        eligible_accounts = [
            row[0] for row in accounts if row[4] == "ACTIVE"
        ]

        if not eligible_accounts:
            chosen = accounts[0]
            conn.execute(
                """
                UPDATE accounts
                SET account_status = 'ACTIVE', closed_at = NULL
                WHERE account_id = ?
                """,
                (chosen[0],),
            )
            eligible_accounts = [chosen[0]]

        # 3. Merchants
        merchant_count = max(
            10, min(100, customer_count * 2)
        )

        merchants = [
            (
                f"MER-{i:04d}",
                f"Synthetic Merchant {i:04d}",
                rng.choice(
                    [
                        "GROCERY",
                        "RETAIL",
                        "TRAVEL",
                        "FOOD",
                        "UTILITIES",
                        "DIGITAL",
                    ]
                ),
                rng.choice(["IN", "US", "GB", "SG"]),
            )
            for i in range(1, merchant_count + 1)
        ]

        conn.executemany(
            """
            INSERT INTO merchants
                (merchant_id, merchant_name, merchant_category, country_code)
            VALUES (?, ?, ?, ?)
            """,
            merchants,
        )

        # 4. Devices
        device_count = max(
            10, min(100, customer_count * 2)
        )

        devices = [
            (
                f"DEV-{i:05d}",
                rng.choice(["MOBILE", "WEB", "TABLET"]),
                (
                    BASE_TIME
                    - timedelta(days=rng.randint(1, 365))
                ).isoformat(),
            )
            for i in range(1, device_count + 1)
        ]

        conn.executemany(
            """
            INSERT INTO devices
                (device_id, device_type, first_seen_at)
            VALUES (?, ?, ?)
            """,
            devices,
        )

        # 5. Transactions
        # Sort events chronologically before calculating account balances.
        events = []

        for _ in range(transaction_count):
            timestamp = BASE_TIME + timedelta(
                seconds=rng.randint(0, 180 * 24 * 60 * 60)
            )

            events.append(
                (
                    timestamp,
                    rng.choice(eligible_accounts),
                    rng.choice(["DEBIT", "CREDIT"]),
                    round(rng.uniform(10, 1500), 2),
                    rng.choice(merchants)[0],
                    rng.choice(devices)[0],
                )
            )

        events.sort(key=lambda item: item[0])

        transactions = []

        for i, event in enumerate(events, start=1):
            (
                timestamp,
                account_id,
                txn_type,
                amount,
                merchant_id,
                device_id,
            ) = event

            before = balances[account_id]

            # Keep the baseline free of overdraft violations.
            if txn_type == "DEBIT" and before < amount:
                txn_type = "CREDIT"

            if txn_type == "CREDIT":
                after = round(before + amount, 2)
            else:
                after = round(before - amount, 2)

            balances[account_id] = after

            transactions.append(
                (
                    f"TXN-{YEAR}-{i:08d}",
                    account_id,
                    merchant_id,
                    device_id,
                    txn_type,
                    amount,
                    timestamp.isoformat(),
                    before,
                    after,
                    None,
                )
            )

        conn.executemany(
            """
            INSERT INTO transactions
                (transaction_id, account_id, merchant_id, device_id,
                 transaction_type, amount, transaction_at,
                 balance_before, balance_after, issue_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            transactions,
        )

    print("Synthetic baseline dataset generated successfully.")
    print(f"Customers:     {customer_count:,}")
    print(f"Accounts:      {account_count:,}")
    print(f"Merchants:     {merchant_count:,}")
    print(f"Devices:       {device_count:,}")
    print(f"Transactions:  {transaction_count:,}")
    print(f"Seed:          {SEED}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic transaction data."
    )

    parser.add_argument("--customers", type=int, default=5000)
    parser.add_argument("--accounts", type=int, default=7000)
    parser.add_argument("--transactions", type=int, default=100000)

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing project records before regeneration.",
    )

    args = parser.parse_args()

    generate_data(
        customer_count=args.customers,
        account_count=args.accounts,
        transaction_count=args.transactions,
        reset=args.reset,
    )


if __name__ == "__main__":
    main()
