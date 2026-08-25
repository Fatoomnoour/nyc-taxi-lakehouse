from __future__ import annotations

import argparse
from pathlib import Path

from .generate_sample import write_sample
from .quality import assert_quality
from .transform import read_trips, run_transform, to_silver

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the NYC Taxi local lakehouse pipeline")
    parser.add_argument("--input", type=Path, help="Input TLC Parquet file")
    parser.add_argument(
        "--sample-rows", type=int, default=5000,
        help="Rows to generate when --input is omitted",
    )
    args = parser.parse_args()

    input_path = args.input or ROOT / "data" / "bronze" / "sample_trips.parquet"
    if args.input is None:
        write_sample(input_path, rows=args.sample_rows)
    silver_path = ROOT / "data" / "silver" / "trips.parquet"
    gold_path = ROOT / "data" / "gold" / "daily_metrics.parquet"
    stats = run_transform(input_path, silver_path, gold_path)
    silver, _ = to_silver(read_trips(input_path))
    report = assert_quality(silver)
    print({"pipeline": stats, "quality": report})


if __name__ == "__main__":
    main()
