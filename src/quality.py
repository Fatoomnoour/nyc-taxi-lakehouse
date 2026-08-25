from __future__ import annotations

import pandas as pd


def quality_report(silver: pd.DataFrame) -> dict[str, int | float | bool]:
    """Return measurable quality metrics for the normalized trip table."""
    required = ["pickup_at", "dropoff_at", "trip_distance", "fare_amount", "total_amount"]
    missing_required = int(silver[required].isna().any(axis=1).sum())
    invalid_duration = int((silver["duration_minutes"] < 0).sum())
    invalid_distance = int((silver["trip_distance"] <= 0).sum())
    invalid_amounts = int((silver["total_amount"] < silver["fare_amount"]).sum())
    duplicate_count = int(silver.duplicated().sum())
    violations = [
        missing_required,
        invalid_duration,
        invalid_distance,
        invalid_amounts,
        duplicate_count,
    ]
    passed = all(value == 0 for value in violations)
    return {
        "row_count": len(silver),
        "missing_required": missing_required,
        "invalid_duration": invalid_duration,
        "invalid_distance": invalid_distance,
        "invalid_amounts": invalid_amounts,
        "duplicate_count": duplicate_count,
        "passed": passed,
    }


def assert_quality(silver: pd.DataFrame) -> dict[str, int | float | bool]:
    report = quality_report(silver)
    if not report["passed"]:
        raise ValueError(f"Data quality gate failed: {report}")
    return report
