"""
Name Normalisation — Maps team aliases to canonical names.

Uses the teams_aliases.yaml config to resolve different
name formats (Brazil, BRA, Brasil → Brazil).
"""

from __future__ import annotations

import pandas as pd

from src.config_loader import load_team_aliases


def normalise_team_column(
    df: pd.DataFrame,
    column: str,
    alias_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Normalise team names in a DataFrame column.

    Args:
        df: DataFrame with team names
        column: column name to normalise
        alias_map: optional pre-loaded alias map

    Returns:
        DataFrame with normalised team names
    """
    if alias_map is None:
        alias_map = load_team_aliases()

    df = df.copy()
    normalised = []
    unknown = set()

    for name in df[column]:
        key = str(name).lower().strip()
        if key in alias_map:
            normalised.append(alias_map[key])
        else:
            normalised.append(str(name))
            unknown.add(str(name))

    df[column] = normalised

    if unknown:
        print(f"⚠ Unknown team names in '{column}': {unknown}")

    return df


def normalise_all_team_columns(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    alias_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Normalise multiple team name columns at once."""
    if alias_map is None:
        alias_map = load_team_aliases()

    if columns is None:
        # Auto-detect team columns
        columns = [c for c in df.columns if "team" in c.lower()]

    for col in columns:
        if col in df.columns:
            df = normalise_team_column(df, col, alias_map)

    return df
