from __future__ import annotations

from pathlib import Path

from src.generate_sample import write_sample
from src.incremental import run_incremental


def test_incremental_loader_skips_completed_file(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    source = write_sample(incoming / "yellow_tripdata_2024-01.parquet", rows=20)
    manifest = tmp_path / "state" / "manifest.json"
    silver = tmp_path / "silver"
    gold = tmp_path / "gold"

    first = run_incremental(incoming, manifest, silver, gold)
    second = run_incremental(incoming, manifest, silver, gold)

    assert source.exists()
    assert first["files_processed"] == 1
    assert first["files_skipped"] == 0
    assert second["files_processed"] == 0
    assert second["files_skipped"] == 1
    assert len(list(silver.glob("*.parquet"))) == 1
    assert len(list(gold.glob("*.parquet"))) == 1


def test_incremental_loader_processes_new_file(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    manifest = tmp_path / "state" / "manifest.json"
    silver = tmp_path / "silver"
    gold = tmp_path / "gold"
    write_sample(incoming / "yellow_tripdata_2024-01.parquet", rows=10)
    write_sample(incoming / "yellow_tripdata_2024-02.parquet", rows=12)

    result = run_incremental(incoming, manifest, silver, gold)

    assert result["files_seen"] == 2
    assert result["files_processed"] == 2
    assert result["silver_rows"] == 22
