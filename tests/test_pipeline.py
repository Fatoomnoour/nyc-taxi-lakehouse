from __future__ import annotations

import pandas as pd

from src.generate_sample import generate_sample
from src.quality import quality_report
from src.transform import to_gold, to_silver


def test_sample_is_deterministic() -> None:
    left = generate_sample(25)
    right = generate_sample(25)
    pd.testing.assert_frame_equal(left, right)


def test_invalid_trips_are_rejected() -> None:
    raw = generate_sample(3)
    raw.loc[0, "trip_distance"] = -1
    raw.loc[1, "tpep_dropoff_datetime"] = (
        raw.loc[1, "tpep_pickup_datetime"] - pd.Timedelta(1, unit="min")
    )
    silver, rejected = to_silver(raw)
    assert rejected == 2
    assert len(silver) == 1


def test_gold_metrics_reconcile_with_silver() -> None:
    silver, rejected = to_silver(generate_sample(100))
    assert rejected == 0
    gold = to_gold(silver)
    assert int(gold["trip_count"].sum()) == len(silver)
    assert round(float(gold["total_revenue"].sum()), 2) == round(
        float(silver["total_amount"].sum()), 2
    )


def test_quality_gate_passes_for_clean_data() -> None:
    silver, _ = to_silver(generate_sample(100))
    report = quality_report(silver)
    assert report["passed"] is True
    assert report["duplicate_count"] == 0
