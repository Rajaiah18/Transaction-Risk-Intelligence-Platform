
"""Utilities for recording planted synthetic anomalies."""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GROUND_TRUTH_PATH = PROJECT_ROOT / "data" / "output" / "ground_truth.csv"

FIELDS = [
    "anomaly_id",
    "entity_type",
    "entity_id",
    "anomaly_type",
    "description",
    "expected_detection",
    "seed",
]


def record_anomaly(
    anomaly_id,
    entity_type,
    entity_id,
    anomaly_type,
    description,
    expected_detection,
    seed=20261022,
):
    """Append one planted anomaly to the ground-truth CSV."""

    GROUND_TRUTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = GROUND_TRUTH_PATH.exists()

    with GROUND_TRUTH_PATH.open(
        "a", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "anomaly_id": anomaly_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "anomaly_type": anomaly_type,
            "description": description,
            "expected_detection": expected_detection,
            "seed": seed,
        })

    print(f"Recorded ground truth: {anomaly_id}")


if __name__ == "__main__":
    record_anomaly(
        anomaly_id="TEST-001",
        entity_type="transaction",
        entity_id="SYNTHETIC-TEST-TRANSACTION",
        anomaly_type="TEST_RECORD",
        description="Test record for checking ground-truth CSV creation.",
        expected_detection="Ground-truth file contains the test record.",
    )
