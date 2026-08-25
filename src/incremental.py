from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .quality import assert_quality
from .transform import read_trips, to_gold, to_silver

ROOT = Path(__file__).resolve().parents[1]


def file_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, dict[str, str | int]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, manifest: dict[str, dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def process_file(path: Path, silver_dir: Path, gold_dir: Path) -> dict[str, int]:
    raw = read_trips(path)
    silver, rejected = to_silver(raw)
    quality = assert_quality(silver)
    gold = to_gold(silver)
    stem = path.stem.replace("-", "_")
    silver_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(silver_dir / f"{stem}.parquet", index=False)
    gold.to_parquet(gold_dir / f"daily_metrics_{stem}.parquet", index=False)
    return {
        "raw_rows": len(raw),
        "silver_rows": len(silver),
        "rejected_rows": rejected,
        "gold_rows": len(gold),
        "quality_rows": int(quality["row_count"]),
    }


def run_incremental(
    input_dir: Path,
    manifest_path: Path,
    silver_dir: Path,
    gold_dir: Path,
) -> dict[str, int]:
    manifest = load_manifest(manifest_path)
    files = sorted(input_dir.glob("*.parquet"))
    processed = 0
    skipped = 0
    rows = 0

    for path in files:
        fingerprint = file_fingerprint(path)
        key = str(path.resolve())
        if manifest.get(key, {}).get("fingerprint") == fingerprint:
            skipped += 1
            continue
        stats = process_file(path, silver_dir, gold_dir)
        manifest[key] = {
            "fingerprint": fingerprint,
            "raw_rows": stats["raw_rows"],
            "silver_rows": stats["silver_rows"],
            "rejected_rows": stats["rejected_rows"],
        }
        processed += 1
        rows += stats["silver_rows"]
        save_manifest(manifest_path, manifest)

    return {
        "files_seen": len(files),
        "files_processed": processed,
        "files_skipped": skipped,
        "silver_rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Process new TLC Parquet files exactly once")
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data" / "incoming")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data" / "state" / "manifest.json")
    parser.add_argument("--silver-dir", type=Path, default=ROOT / "data" / "silver")
    parser.add_argument("--gold-dir", type=Path, default=ROOT / "data" / "gold")
    args = parser.parse_args()
    print(run_incremental(args.input_dir, args.manifest, args.silver_dir, args.gold_dir))


if __name__ == "__main__":
    main()
