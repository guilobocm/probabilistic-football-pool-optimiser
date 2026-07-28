#!/usr/bin/env bash
set -e

echo "=== Running Validation Checks ==="

echo "[1/4] Running Ruff Check (Linting)..."
uv run ruff check .

echo "[2/4] Running Ruff Format (Formatting)..."
uv run ruff format --check .

echo "[3/4] Running Pytest (Unit Tests)..."
uv run pytest

echo "[4/4] Running Mypy (Type Checking)..."
uv run mypy src

echo "=== All Checks Passed! ==="
