set shell := ["bash", "-cu"]

default:
    @just --list

install:
    uv sync

install-all:
    uv sync --all-groups

lint:
    uv run ruff check .

format:
    uv run ruff format .

format-check:
    uv run ruff format --check .

type-check:
    uv run pyright

test:
    uv run pytest -q

coverage:
    uv run pytest --cov --cov-report=term-missing

docs-build:
    uv run --group docs mkdocs build --strict

docs-serve:
    uv run --group docs mkdocs serve -a localhost:8000

ui-install:
    npm --prefix ui ci

ui-lint:
    npm --prefix ui run lint

ui-build:
    npm --prefix ui run build

check: format-check lint type-check test ui-lint ui-build docs-build

clean:
    rm -rf .pytest_cache .ruff_cache .pyright dist build site htmlcov

package-smoke-test:
    uv run --no-sync python scripts/package_smoke_test.py
