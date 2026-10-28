
# Data Dictionary
## Transaction Risk Intelligence Platform

This document describes the database tables, key fields, relationships, and validation rules used by the platform.

## 1. Entity Tables

### customers
Stores the synthetic customer records.

| Column | Description |
|---|---|
| customer_id | Unique customer identifier (primary key) |
| full_name | Synthetic customer name |
| created_at | Customer creation timestamp |
| customer_status | ACTIVE, INACTIVE, or BLOCKED |

### kyc_profiles
Stores customer identity-verification and risk information.

| Column | Description |
|---|---|
| kyc_id | Unique KYC profile identifier |
| customer_id | Customer reference |
| verification_status | PENDING, VERIFIED, or REJECTED |
| risk_category | LOW, MEDIUM, or HIGH |
| effective_from | Start of profile validity |
| effective_to | Optional end of profile validity |

### accounts
Stores customer financial-account metadata.

| Column | Description |
|---|---|
| account_id | Unique account identifier |
| customer_id | Account owner |
| opened_at | Account opening timestamp |
| closed_at | Optional account closure timestamp |
| account_status | ACTIVE, DORMANT, CLOSED, or FROZEN |
| opening_balance | Initial account balance |
| overdraft_limit | Permitted overdraft amount |

### merchants
Stores synthetic merchant information.

| Column | Description |
|---|---|
| merchant_id | Unique merchant identifier |
| merchant_name | Merchant display name |
| merchant_category | Merchant business category |
| country_code | Merchant country code |

### devices
Stores device metadata associated with transaction activity.

| Column | Description |
|---|---|
| device_id | Unique device identifier |
| device_type | Device classification |
| first_seen_at | First-seen timestamp |

## 2. Transaction and Transfer Tables

### transactions
Stores debit and credit events.

| Column | Description |
|---|---|
| transaction_id | Unique transaction identifier |
| account_id | Account involved in the transaction |
| merchant_id | Optional merchant reference |
| device_id | Optional device reference |
| transaction_type | DEBIT or CREDIT |
| amount | Positive transaction amount |
| transaction_at | Transaction timestamp |
| balance_before | Balance before the transaction |
| balance_after | Balance after the transaction |
| issue_type | Optional intentional anomaly label |

**Balance rule:** For a credit, `balance_after = balance_before + amount`. For a debit, `balance_after = balance_before - amount`.

### transfer_links
Connects the two transaction legs of a transfer.

| Column | Description |
|---|---|
| transfer_id | Unique transfer identifier |
| source_transaction_id | Debit transaction reference |
| destination_transaction_id | Credit transaction reference |
| created_at | Transfer-link creation timestamp |
| issue_type | Optional transfer anomaly label |

Expected behavior: source and destination amounts should match, and the source and destination transactions should be distinct.

## 3. Risk and Investigation Tables

### risk_rules
Stores the configurable rules used to identify risky activity.

| Column | Description |
|---|---|
| rule_id | Unique rule identifier |
| rule_name | Rule display name |
| description | Rule purpose |
| threshold | Optional numeric threshold |
| risk_points | Rule risk score contribution |
| is_active | Whether the rule is enabled |
| effective_from | Rule start timestamp |
| effective_to | Optional rule end timestamp |

### alerts
Stores rule-generated risk alerts.

| Column | Description |
|---|---|
| alert_id | Unique alert identifier |
| transaction_id | Optional triggering transaction |
| rule_id | Rule that generated the alert |
| risk_score | Alert risk score from 0 to 100 |
| priority | LOW, MEDIUM, HIGH, or CRITICAL |
| reason | Explanation for the alert |
| created_at | Alert creation timestamp |
| alert_status | OPEN, IN_REVIEW, RESOLVED, or CLOSED |

An alert with a null transaction reference is treated as an intentional data-quality anomaly in this dataset.

### cases
Stores investigation cases.

| Column | Description |
|---|---|
| case_id | Unique case identifier |
| created_at | Case creation timestamp |
| case_status | OPEN, IN_REVIEW, RESOLVED, or CLOSED |
| disposition | Optional investigation outcome |
| issue_type | Optional intentional anomaly label |

### case_alerts
Associates investigation cases with alerts.

| Column | Description |
|---|---|
| case_id | Case reference |
| alert_id | Alert reference |
| linked_at | Timestamp when the association was created |

The combination of `case_id` and `alert_id` is the primary key.

### analyst_actions
Records actions taken during an investigation.

| Column | Description |
|---|---|
| action_id | Unique action identifier |
| case_id | Case reference |
| analyst_id | Analyst identifier |
| action_type | ASSIGNED, COMMENTED, ESCALATED, CONFIRMED, FALSE_POSITIVE, or CLOSED |
| action_at | Action timestamp |
| notes | Action details |

## 4. Audit and Event Table

### entity_events
Stores events associated with entities.

| Column | Description |
|---|---|
| event_id | Unique event identifier |
| entity_type | Type of entity involved |
| entity_id | Identifier of the entity |
| event_type | Event classification |
| event_at | Event timestamp |
| details_json | Additional event details encoded as JSON |

## 5. Entity Relationships

- One customer can own multiple accounts.
- A customer can have multiple KYC profiles over time.
- An account can have many transactions.
- A transaction can reference a merchant and a device.
- A transfer connects a source transaction and a destination transaction.
- A risk rule can generate many alerts.
- An alert can be associated with a case through `case_alerts`.
- A case can contain multiple linked alerts.
- A case can have multiple analyst actions.

## 6. Validation Rules

The validation process checks:

1. Foreign-key integrity.
2. Transaction balance arithmetic.
3. Transactions occurring after account closure.
4. Negative balances beyond the permitted overdraft limit.
5. Transfer legs with mismatched amounts.
6. Alerts without triggering transactions.
7. Analyst disposition actions occurring before linked alerts.
8. Cases without linked alerts.

## 7. Synthetic Data and Anomalies

The generator uses seed `20261022` for reproducibility.

Five intentional anomaly types are included:

- `CLOSED_ACCOUNT_TRANSACTION`
- `OVERDRAFT_VIOLATION`
- `TRANSFER_AMOUNT_MISMATCH`
- `ORPHAN_ALERT`
- `DISPOSITION_BEFORE_ALERT`

These records are controlled test cases, not claims of actual fraud. The `ground_truth.csv` file records the expected anomaly types and detection conditions.
