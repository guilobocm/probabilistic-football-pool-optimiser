#!/usr/bin/env bash
set -euo pipefail

echo "=== Installing locked dependencies ==="
uv sync --locked --all-groups

echo "=== Running Ruff lint ==="
uv run --frozen ruff check .

echo "=== Running Ruff format check ==="
uv run --frozen ruff format --check .

echo "=== Enforcing public-language standard ==="
uv run --frozen python scripts/check_public_language.py

echo "=== Verifying public package manifest ==="
uv run --frozen python scripts/verify_public_package_manifest.py

echo "=== Running tests ==="
uv run --frozen pytest

echo "=== Running mypy ==="
uv run --frozen mypy src

echo "=== Running synthetic demo ==="
uv run --frozen python -m examples.synthetic_four_team_tournament

echo "=== Verifying clean working tree ==="
git diff --exit-code

echo "=== All validation checks passed ==="
