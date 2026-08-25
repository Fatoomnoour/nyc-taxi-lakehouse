from __future__ import annotations

from pathlib import Path

import pandas as pd

PAYMENT_LABELS = {1: "credit_card", 2: "cash", 3: "no_charge", 4: "dispute"}


def read_trips(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def to_silver(raw: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Normalize records and return (valid_rows, rejected_row_count)."""
    frame = raw.copy()
    frame["pickup_at"] = pd.to_datetime(frame["tpep_pickup_datetime"], errors="coerce", utc=True)
    frame["dropoff_at"] = pd.to_datetime(frame["tpep_dropoff_datetime"], errors="coerce", utc=True)
    frame["duration_minutes"] = (frame["dropoff_at"] - frame["pickup_at"]).dt.total_seconds() / 60
    frame["payment_method"] = frame["payment_type"].map(PAYMENT_LABELS).fillna("unknown")
    frame["trip_date"] = frame["pickup_at"].dt.date.astype("string")
    valid = (
        frame["pickup_at"].notna()
        & frame["dropoff_at"].notna()
        & (frame["dropoff_at"] >= frame["pickup_at"])
        & (frame["duration_minutes"] <= 24 * 60)
        & (frame["trip_distance"] > 0)
        & (frame["fare_amount"] >= 0)
        & (frame["total_amount"] >= frame["fare_amount"])
    )
    columns = [
        "pickup_at", "dropoff_at", "trip_date", "passenger_count", "trip_distance",
        "duration_minutes", "fare_amount", "tip_amount", "total_amount", "payment_method",
    ]
    silver = frame.loc[valid, columns].reset_index(drop=True)
    return silver, int((~valid).sum())


def to_gold(silver: pd.DataFrame) -> pd.DataFrame:
    """Build a daily analytics mart by date and payment method."""
    gold = (
        silver.groupby(["trip_date", "payment_method"], as_index=False)
        .agg(
            trip_count=("trip_date", "size"),
            total_revenue=("total_amount", "sum"),
            average_fare=("fare_amount", "mean"),
            average_distance=("trip_distance", "mean"),
            average_duration_minutes=("duration_minutes", "mean"),
            total_tips=("tip_amount", "sum"),
        )
        .sort_values(["trip_date", "payment_method"])
        .reset_index(drop=True)
    )
    gold["tip_rate"] = (gold["total_tips"] / gold["total_revenue"]).fillna(0).round(4)
    numeric = [
        "total_revenue",
        "average_fare",
        "average_distance",
        "average_duration_minutes",
        "total_tips",
    ]
    gold[numeric] = gold[numeric].round(2)
    return gold


def run_transform(input_path: Path, silver_path: Path, gold_path: Path) -> dict[str, int]:
    raw = read_trips(input_path)
    silver, rejected = to_silver(raw)
    gold = to_gold(silver)
    silver_path.parent.mkdir(parents=True, exist_ok=True)
    gold_path.parent.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(silver_path, index=False)
    gold.to_parquet(gold_path, index=False)
    return {
        "raw_rows": len(raw),
        "silver_rows": len(silver),
        "rejected_rows": rejected,
        "gold_rows": len(gold),
    }
