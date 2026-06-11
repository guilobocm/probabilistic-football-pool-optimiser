"""
Config loader for the World Cup 2026 Pool Optimizer.
Loads YAML configs and provides typed access to tournament data.
"""

from pathlib import Path
from typing import Any

import yaml


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load a YAML config file from the config directory."""
    path = CONFIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_tournament() -> dict[str, Any]:
    """Load tournament structure (groups, venues, knockout bracket)."""
    return _load_yaml("tournament.yaml")


def load_scoring_rules() -> dict[str, Any]:
    """Load bolão scoring rules."""
    return _load_yaml("scoring_rules.yaml")


def load_sources() -> dict[str, Any]:
    """Load data source definitions and ensemble weights."""
    return _load_yaml("sources.yaml")


def load_team_aliases() -> dict[str, str]:
    """
    Load team aliases and return a mapping: alias (lowercase) -> canonical name.
    """
    raw = _load_yaml("teams_aliases.yaml")
    alias_map: dict[str, str] = {}

    for canonical_name, data in raw.get("teams", {}).items():
        for alias in data.get("aliases", []):
            alias_map[alias.lower().strip()] = canonical_name
        # Also map canonical name itself
        alias_map[canonical_name.lower().strip()] = canonical_name
        # And the code
        code = data.get("code", "")
        if code:
            alias_map[code.lower().strip()] = canonical_name

    return alias_map


def get_groups() -> dict[str, list[str]]:
    """Return groups as {group_letter: [team1, team2, team3, team4]}."""
    tournament = load_tournament()
    return tournament.get("groups", {})


def get_all_teams() -> list[str]:
    """Return flat list of all 48 teams."""
    groups = get_groups()
    teams = []
    for group_teams in groups.values():
        teams.extend(group_teams)
    return teams


def get_scoring_rule() -> dict[str, int]:
    """
    Return the scoring rule dict compatible with algorithm.py.

    Returns dict with keys:
        trend_win, diff_win, exact_win, trend_draw, exact_draw
    """
    rules = load_scoring_rules()
    match_scoring = rules.get("match_scoring", {})
    return {
        "trend_win": match_scoring.get("trend_win", 2),
        "diff_win": match_scoring.get("diff_win", 3),
        "exact_win": match_scoring.get("exact_win", 4),
        "trend_draw": match_scoring.get("trend_draw", 3),
        "exact_draw": match_scoring.get("exact_draw", 4),
    }


def normalise_team_name(name: str, alias_map: dict[str, str] | None = None) -> str:
    """Normalise a team name to its canonical form."""
    if alias_map is None:
        alias_map = load_team_aliases()

    key = name.lower().strip()
    if key in alias_map:
        return alias_map[key]

    raise ValueError(f"Unknown team name/alias: '{name}'")
