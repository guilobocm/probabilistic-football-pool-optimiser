"""
CSV Ingest — Load odds and probability data from CSV files.

Supports:
- Odds CSVs (with decimal_odd column)
- Probability CSVs (with p_home, p_draw, p_away columns)
- Team rating CSVs (with elo, xg_for, etc.)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.transform.implied_probabilities import (
    decimal_odds_to_clean_probs,
)


REQUIRED_ODDS_COLUMNS = {
    "match_id",
    "source",
    "market",
    "selection",
    "decimal_odd",
}

REQUIRED_PROB_COLUMNS = {
    "match_id",
    "source",
    "p_home",
    "p_draw",
    "p_away",
}


def validate_odds_csv(df: pd.DataFrame) -> list[str]:
    """Validate an odds CSV and return list of issues."""
    issues = []
    missing = REQUIRED_ODDS_COLUMNS - set(df.columns)
    if missing:
        issues.append(f"Missing columns: {missing}")

    if "decimal_odd" in df.columns:
        bad_odds = df[df["decimal_odd"] <= 1.0]
        if len(bad_odds) > 0:
            issues.append(f"{len(bad_odds)} rows with odds <= 1.0")

    return issues


def load_odds_csv(path: str | Path) -> pd.DataFrame:
    """Load and validate an odds CSV file."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_csv(file_path)
    issues = validate_odds_csv(df)
    if issues:
        print(f"⚠ Validation issues in {file_path.name}:")
        for issue in issues:
            print(f"  - {issue}")

    return df


def load_probability_csv(path: str | Path) -> pd.DataFrame:
    """Load a probability CSV (direct probabilities, no odds)."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_csv(file_path)
    missing = REQUIRED_PROB_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Validate probabilities sum to ~1
    df["total"] = df["p_home"] + df["p_draw"] + df["p_away"]
    bad_rows = df[(df["total"] < 0.95) | (df["total"] > 1.05)]
    if len(bad_rows) > 0:
        print(f"⚠ {len(bad_rows)} rows with probabilities not summing to ~1.0")

    return df


def odds_csv_to_probabilities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert an odds dataframe to clean probabilities per match.

    Groups by match_id and source, converts 1X2 odds to probabilities.
    """
    records = []

    for (match_id, source), group in df.groupby(["match_id", "source"]):
        if group["market"].iloc[0] != "1x2":
            continue

        odds = dict(zip(group["selection"], group["decimal_odd"]))

        needed = {"team_a", "draw", "team_b"}
        if not needed.issubset(set(odds.keys())):
            # Try alternative names
            alt_map = {
                "home": "team_a",
                "1": "team_a",
                "draw": "draw",
                "x": "draw",
                "X": "draw",
                "away": "team_b",
                "2": "team_b",
            }
            remapped = {}
            for sel, odd in odds.items():
                mapped = alt_map.get(sel.lower(), sel)
                remapped[mapped] = odd
            odds = remapped

        if not needed.issubset(set(odds.keys())):
            continue

        try:
            clean = decimal_odds_to_clean_probs(odds)
            margin = sum(1.0 / v for v in odds.values())

            records.append(
                {
                    "match_id": match_id,
                    "source": source,
                    "p_home": clean["team_a"],
                    "p_draw": clean["draw"],
                    "p_away": clean["team_b"],
                    "overround": margin,
                }
            )
        except (ValueError, ZeroDivisionError) as e:
            print(f"⚠ Error processing {match_id}/{source}: {e}")

    return pd.DataFrame(records)
