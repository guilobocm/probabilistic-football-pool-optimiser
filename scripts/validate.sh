#!/usr/bin/env bash
set -euo pipefail

echo "=== Installing locked dependencies ==="
uv sync --locked --all-groups

echo "=== Running Ruff lint ==="
uv run --frozen ruff check .

echo "=== Running Ruff format check ==="
uv run --frozen ruff format --check .

echo "=== Running tests ==="
uv run --frozen pytest

echo "=== Running mypy ==="
uv run --frozen mypy src

echo "=== Running synthetic demo ==="
uv run --frozen python -m examples.synthetic_four_team_tournament

echo "=== Verifying clean working tree ==="
git diff --exit-code

echo "=== All validation checks passed ==="
