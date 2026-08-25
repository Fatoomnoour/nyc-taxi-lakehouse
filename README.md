# NYC Taxi Lakehouse

This repository contains a small but complete batch pipeline for NYC taxi trip records. I built it as a local project first: it can run offline with a deterministic fixture, and it can also process a real TLC Parquet file when one is available.

The point of the project is not to pretend that a laptop is a distributed cluster. It is to keep the transformation rules, data checks, and output contract easy to inspect before moving the same ideas to Spark, Airflow, and a warehouse.

## Pipeline

```mermaid
flowchart LR
    A[NYC TLC Parquet] --> B[Bronze raw file]
    B --> C[Silver normalized trips]
    C --> D{Quality checks}
    D -->|valid| E[Gold daily metrics]
    D -->|invalid| X[Fail with a report]
    E --> F[DuckDB or BI client]
```

## What is implemented

The command reads taxi records, normalizes timestamps, calculates trip duration, maps payment codes, rejects records that violate basic business rules, and writes two Parquet outputs. The gold table is grouped by trip date and payment method and contains trip count, revenue, average fare, average distance, average duration, total tips, and tip rate.

| Layer | Meaning | Local output |
| --- | --- | --- |
| Bronze | A copy of the input used for repeatable processing | `data/bronze/*.parquet` |
| Silver | Clean rows with a stable set of names and types | `data/silver/trips.parquet` |
| Gold | Aggregated data intended for analysis | `data/gold/daily_metrics.parquet` |

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m src.pipeline --sample-rows 5000
pytest -q
ruff check .
```

The offline command is useful for tests and code review. To process a real file downloaded from the [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), run:

```bash
python -m src.pipeline --input data/incoming/yellow_tripdata_2024-01.parquet
```

The input file is intentionally not committed to the repository. Real TLC files are large, and the source page is the correct place to select the month required for an analysis.

## Data checks

Rows are rejected when a required timestamp is missing, drop-off occurs before pickup, duration is longer than one day, distance is not positive, or total amount is smaller than fare amount. The test suite also checks that the aggregate trip count and revenue reconcile with the silver layer.

The current test run covers four cases and includes an end-to-end smoke run on 250 rows. It does not claim distributed performance; that is the next step once a real sample has been profiled.

## Repository layout

```text
src/
  generate_sample.py  # deterministic fixture for local tests
  pipeline.py         # command-line entry point
  quality.py          # quality report and fail-fast gate
  transform.py        # bronze -> silver -> gold
architecture/
  pipeline.mmd        # editable Mermaid diagram
tests/
  test_pipeline.py
```

## Next engineering steps

The natural next increments are incremental partition loading, a small DuckDB SQL layer, an Airflow DAG with retries and backfills, and a Spark implementation benchmarked against the local version. Those pieces should be added only after profiling a real TLC file, so the repository does not make performance claims without measurements.

## License

MIT
