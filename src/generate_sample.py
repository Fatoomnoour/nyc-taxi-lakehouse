from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "fare_amount",
    "tip_amount",
    "total_amount",
    "payment_type",
]


def generate_sample(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Generate deterministic taxi-like records for offline development."""
    if rows < 1:
        raise ValueError("rows must be positive")
    rng = np.random.default_rng(seed)
    start = datetime(2024, 1, 1)
    pickup = pd.Series(
        [start + timedelta(minutes=int(x)) for x in rng.integers(0, 60 * 24 * 31, rows)],
        dtype="datetime64[ns]",
    )
    duration = rng.integers(3, 70, rows)
    distance = np.round(rng.gamma(shape=2.2, scale=2.5, size=rows), 2)
    fare = np.round(3.5 + distance * 2.75 + rng.normal(0, 1.5, rows), 2)
    fare = np.maximum(fare, 2.5)
    tip = np.where(rng.random(rows) > 0.35, np.round(fare * rng.uniform(0.05, 0.25, rows), 2), 0)
    payment = rng.choice([1, 2, 3, 4], size=rows, p=[0.52, 0.42, 0.04, 0.02])
    return pd.DataFrame(
        {
            "tpep_pickup_datetime": pickup,
            "tpep_dropoff_datetime": pickup + pd.to_timedelta(duration, unit="m"),
            "passenger_count": rng.integers(1, 5, rows),
            "trip_distance": distance,
            "fare_amount": fare,
            "tip_amount": tip,
            "total_amount": np.round(fare + tip + 2.5, 2),
            "payment_type": payment,
        }
    )[REQUIRED_COLUMNS]


def write_sample(path: Path, rows: int = 5000, seed: int = 42) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    generate_sample(rows, seed).to_parquet(path, index=False)
    return path
