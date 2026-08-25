"""Monthly NYC TLC ingestion with Airflow catchup and safe reruns."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = PROJECT_ROOT / "data" / "incoming"
MANIFEST = PROJECT_ROOT / "data" / "state" / "manifest.json"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"

with DAG(
    dag_id="nyc_taxi_monthly_lakehouse",
    start_date=datetime(2024, 1, 1),
    schedule="0 3 1 * *",
    catchup=True,
    max_active_runs=1,
    default_args={"owner": "fatma", "retries": 2},
    tags=["nyc-taxi", "lakehouse", "batch"],
    doc_md="""
    ### Monthly NYC Taxi Lakehouse

    Before triggering this DAG, put the target TLC Parquet files in
    `data/incoming/`. The incremental command fingerprints each file and
    skips a file that has already completed successfully.

    Airflow catchup creates one scheduled run per missed month. Manual
    backfills can use `airflow dags backfill` for a bounded date range.
    """,
) as dag:
    run_incremental = BashOperator(
        task_id="incremental_ingestion_and_transform",
        bash_command=(
            "cd '{{ params.project_root }}' && "
            "python -m src.incremental "
            "--input-dir '{{ params.input_dir }}' "
            "--manifest '{{ params.manifest }}' "
            "--silver-dir '{{ params.silver_dir }}' "
            "--gold-dir '{{ params.gold_dir }}'"
        ),
        params={
            "project_root": str(PROJECT_ROOT),
            "input_dir": str(INPUT_DIR),
            "manifest": str(MANIFEST),
            "silver_dir": str(SILVER_DIR),
            "gold_dir": str(GOLD_DIR),
        },
    )

    run_incremental
