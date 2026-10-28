
PRAGMA foreign_keys = ON;

-- 1. Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    customer_status TEXT NOT NULL
        CHECK (customer_status IN ('ACTIVE', 'INACTIVE', 'BLOCKED'))
);

-- 2. KYC profiles: a customer can have multiple historical profiles
CREATE TABLE IF NOT EXISTS kyc_profiles (
    kyc_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    verification_status TEXT NOT NULL
        CHECK (verification_status IN ('PENDING', 'VERIFIED', 'REJECTED')),
    risk_category TEXT NOT NULL
        CHECK (risk_category IN ('LOW', 'MEDIUM', 'HIGH')),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- 3. Accounts
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    account_status TEXT NOT NULL
        CHECK (account_status IN ('ACTIVE', 'DORMANT', 'CLOSED', 'FROZEN')),
    opening_balance REAL NOT NULL DEFAULT 0,
    overdraft_limit REAL NOT NULL DEFAULT 0
        CHECK (overdraft_limit >= 0),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CHECK (closed_at IS NULL OR closed_at >= opened_at)
);

-- 4. Merchants
CREATE TABLE IF NOT EXISTS merchants (
    merchant_id TEXT PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    merchant_category TEXT NOT NULL,
    country_code TEXT NOT NULL
);

-- 5. Devices
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    device_type TEXT NOT NULL,
    first_seen_at TEXT NOT NULL
);

-- 6. Transactions
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    merchant_id TEXT,
    device_id TEXT,
    transaction_type TEXT NOT NULL
        CHECK (transaction_type IN ('DEBIT', 'CREDIT')),
    amount REAL NOT NULL CHECK (amount > 0),
    transaction_at TEXT NOT NULL,
    balance_before REAL NOT NULL,
    balance_after REAL NOT NULL,
    issue_type TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id),
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    CHECK (
        ABS(
            balance_after -
            CASE
                WHEN transaction_type = 'CREDIT'
                    THEN balance_before + amount
                ELSE balance_before - amount
            END
        ) < 0.011
    )
);

-- 7. Transfers: connect the two transaction legs
CREATE TABLE IF NOT EXISTS transfer_links (
    transfer_id TEXT PRIMARY KEY,
    source_transaction_id TEXT NOT NULL UNIQUE,
    destination_transaction_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    issue_type TEXT,
    FOREIGN KEY (source_transaction_id)
        REFERENCES transactions(transaction_id),
    FOREIGN KEY (destination_transaction_id)
        REFERENCES transactions(transaction_id),
    CHECK (source_transaction_id <> destination_transaction_id)
);

-- 8. Configurable risk rules
CREATE TABLE IF NOT EXISTS risk_rules (
    rule_id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    description TEXT NOT NULL,
    threshold REAL,
    risk_points INTEGER NOT NULL CHECK (risk_points BETWEEN 0 AND 100),
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),
    effective_from TEXT NOT NULL,
    effective_to TEXT
);

-- 9. Alerts: nullable transaction supports testing missing evidence
CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    transaction_id TEXT,
    rule_id TEXT NOT NULL,
    risk_score INTEGER NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    priority TEXT NOT NULL
        CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    alert_status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK (alert_status IN ('OPEN', 'IN_REVIEW', 'RESOLVED', 'CLOSED')),
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    FOREIGN KEY (rule_id) REFERENCES risk_rules(rule_id)
);

-- 10. Cases: multiple alerts can be grouped into one case
CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    case_status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK (case_status IN ('OPEN', 'IN_REVIEW', 'RESOLVED', 'CLOSED')),
    disposition TEXT,
    issue_type TEXT
);

-- Many-to-many relationship between cases and alerts
CREATE TABLE IF NOT EXISTS case_alerts (
    case_id TEXT NOT NULL,
    alert_id TEXT NOT NULL,
    linked_at TEXT NOT NULL,
    PRIMARY KEY (case_id, alert_id),
    FOREIGN KEY (case_id) REFERENCES cases(case_id),
    FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
);

-- 11. Analyst actions: append decisions instead of overwriting history
CREATE TABLE IF NOT EXISTS analyst_actions (
    action_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    analyst_id TEXT NOT NULL,
    action_type TEXT NOT NULL
        CHECK (action_type IN (
            'ASSIGNED', 'COMMENTED', 'ESCALATED',
            'CONFIRMED', 'FALSE_POSITIVE', 'CLOSED'
        )),
    action_at TEXT NOT NULL,
    notes TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

-- Audit history for lifecycle changes and other state transitions
CREATE TABLE IF NOT EXISTS entity_events (
    event_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_at TEXT NOT NULL,
    details_json TEXT NOT NULL
);

-- Indexes for common review queries
CREATE INDEX IF NOT EXISTS idx_txn_account_time
    ON transactions(account_id, transaction_at);

CREATE INDEX IF NOT EXISTS idx_alert_priority_status
    ON alerts(priority, alert_status);

CREATE INDEX IF NOT EXISTS idx_case_status
    ON cases(case_status);

CREATE INDEX IF NOT EXISTS idx_actions_case_time
    ON analyst_actions(case_id, action_at);
