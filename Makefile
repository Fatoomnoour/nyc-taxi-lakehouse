.PHONY: install run test lint check clean

install:
	python -m pip install -e '.[dev]'

run:
	python -m src.pipeline --sample-rows 5000

test:
	pytest -q

lint:
	ruff check .

check: lint test

clean:
	rm -rf data/bronze/* data/silver/* data/gold/* .pytest_cache .ruff_cache
