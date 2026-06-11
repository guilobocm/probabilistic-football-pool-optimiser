"""
Team Strength Model — Elo-based ratings with offensive/defensive split.

Provides prior strength estimates for each team, used as input to the
Poisson goal model. Includes Elo ratings, FIFA rankings, xG data,
and allows manual overrides and external model calibration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class TeamStrength:
    """Snapshot of a team's estimated strength."""
    name: str
    elo: float = 1500.0
    fifa_rank: int = 50
    attack_rating: float = 1.0   # multiplicative, >1 = strong attack
    defense_rating: float = 1.0  # multiplicative, >1 = strong defense
    xg_for_90: float = 1.2      # expected goals scored per 90 min
    xg_against_90: float = 1.0  # expected goals conceded per 90 min
    form: float = 0.0           # recent form adjustment (-0.3 to +0.3)
    squad_quality: float = 1.0  # 0.5 (weak) to 1.5 (elite)
    confederation: str = ""


# ============================================================
# Default Elo ratings for all 48 World Cup 2026 teams
# Based on approximate eloratings.net values as of June 2026
# These are starting priors — will be calibrated with odds
# ============================================================

DEFAULT_TEAM_DATA: dict[str, dict] = {
    # Tier 1: Elite (Elo ~2000+)
    "Argentina":    {"elo": 2072, "fifa_rank": 1,  "attack": 1.45, "defense": 1.30, "xg_f": 1.85, "xg_a": 0.65, "conf": "CONMEBOL"},
    "France":       {"elo": 2045, "fifa_rank": 2,  "attack": 1.50, "defense": 1.25, "xg_f": 1.90, "xg_a": 0.75, "conf": "UEFA"},
    "Spain":        {"elo": 2040, "fifa_rank": 3,  "attack": 1.40, "defense": 1.35, "xg_f": 1.80, "xg_a": 0.60, "conf": "UEFA"},
    "England":      {"elo": 2015, "fifa_rank": 4,  "attack": 1.35, "defense": 1.25, "xg_f": 1.75, "xg_a": 0.70, "conf": "UEFA"},
    "Brazil":       {"elo": 1990, "fifa_rank": 5,  "attack": 1.35, "defense": 1.15, "xg_f": 1.65, "xg_a": 0.80, "conf": "CONMEBOL"},
    "Portugal":     {"elo": 1985, "fifa_rank": 6,  "attack": 1.40, "defense": 1.20, "xg_f": 1.70, "xg_a": 0.75, "conf": "UEFA"},
    "Germany":      {"elo": 1970, "fifa_rank": 7,  "attack": 1.35, "defense": 1.20, "xg_f": 1.70, "xg_a": 0.80, "conf": "UEFA"},
    "Netherlands":  {"elo": 1965, "fifa_rank": 8,  "attack": 1.30, "defense": 1.25, "xg_f": 1.65, "xg_a": 0.75, "conf": "UEFA"},

    # Tier 2: Strong (Elo ~1850-1960)
    "Colombia":     {"elo": 1955, "fifa_rank": 9,  "attack": 1.25, "defense": 1.15, "xg_f": 1.50, "xg_a": 0.80, "conf": "CONMEBOL"},
    "Belgium":      {"elo": 1940, "fifa_rank": 10, "attack": 1.25, "defense": 1.15, "xg_f": 1.55, "xg_a": 0.85, "conf": "UEFA"},
    "Italy":        {"elo": 1935, "fifa_rank": 11, "attack": 1.20, "defense": 1.30, "xg_f": 1.45, "xg_a": 0.65, "conf": "UEFA"},  # Not qualified but kept for reference
    "Uruguay":      {"elo": 1925, "fifa_rank": 12, "attack": 1.25, "defense": 1.20, "xg_f": 1.50, "xg_a": 0.75, "conf": "CONMEBOL"},
    "Croatia":      {"elo": 1910, "fifa_rank": 13, "attack": 1.20, "defense": 1.20, "xg_f": 1.45, "xg_a": 0.80, "conf": "UEFA"},
    "Japan":        {"elo": 1895, "fifa_rank": 14, "attack": 1.20, "defense": 1.15, "xg_f": 1.45, "xg_a": 0.85, "conf": "AFC"},
    "Morocco":      {"elo": 1885, "fifa_rank": 15, "attack": 1.15, "defense": 1.20, "xg_f": 1.35, "xg_a": 0.75, "conf": "CAF"},
    "United States":{"elo": 1880, "fifa_rank": 16, "attack": 1.15, "defense": 1.10, "xg_f": 1.40, "xg_a": 0.90, "conf": "CONCACAF"},
    "Mexico":       {"elo": 1870, "fifa_rank": 17, "attack": 1.15, "defense": 1.10, "xg_f": 1.35, "xg_a": 0.90, "conf": "CONCACAF"},
    "Switzerland":  {"elo": 1865, "fifa_rank": 18, "attack": 1.10, "defense": 1.20, "xg_f": 1.30, "xg_a": 0.75, "conf": "UEFA"},
    "Norway":       {"elo": 1860, "fifa_rank": 19, "attack": 1.25, "defense": 1.05, "xg_f": 1.55, "xg_a": 0.95, "conf": "UEFA"},
    "Denmark":      {"elo": 1855, "fifa_rank": 20, "attack": 1.15, "defense": 1.15, "xg_f": 1.35, "xg_a": 0.80, "conf": "UEFA"},  # not qualified ref
    "Austria":      {"elo": 1845, "fifa_rank": 21, "attack": 1.15, "defense": 1.10, "xg_f": 1.40, "xg_a": 0.90, "conf": "UEFA"},
    "Türkiye":      {"elo": 1840, "fifa_rank": 22, "attack": 1.15, "defense": 1.05, "xg_f": 1.40, "xg_a": 0.95, "conf": "UEFA"},
    "Ecuador":      {"elo": 1830, "fifa_rank": 23, "attack": 1.10, "defense": 1.10, "xg_f": 1.30, "xg_a": 0.85, "conf": "CONMEBOL"},
    "South Korea":  {"elo": 1825, "fifa_rank": 24, "attack": 1.10, "defense": 1.10, "xg_f": 1.30, "xg_a": 0.90, "conf": "AFC"},
    "Senegal":      {"elo": 1820, "fifa_rank": 25, "attack": 1.10, "defense": 1.10, "xg_f": 1.30, "xg_a": 0.85, "conf": "CAF"},
    "Sweden":       {"elo": 1815, "fifa_rank": 26, "attack": 1.10, "defense": 1.10, "xg_f": 1.30, "xg_a": 0.85, "conf": "UEFA"},

    # Tier 3: Competitive (Elo ~1700-1849)
    "Australia":    {"elo": 1800, "fifa_rank": 27, "attack": 1.05, "defense": 1.05, "xg_f": 1.20, "xg_a": 0.95, "conf": "AFC"},
    "Paraguay":     {"elo": 1790, "fifa_rank": 28, "attack": 1.05, "defense": 1.10, "xg_f": 1.15, "xg_a": 0.90, "conf": "CONMEBOL"},
    "Ivory Coast":  {"elo": 1785, "fifa_rank": 29, "attack": 1.10, "defense": 1.00, "xg_f": 1.25, "xg_a": 1.00, "conf": "CAF"},
    "Egypt":        {"elo": 1780, "fifa_rank": 30, "attack": 1.05, "defense": 1.10, "xg_f": 1.20, "xg_a": 0.85, "conf": "CAF"},
    "Algeria":      {"elo": 1775, "fifa_rank": 31, "attack": 1.05, "defense": 1.05, "xg_f": 1.20, "xg_a": 0.90, "conf": "CAF"},
    "Iran":         {"elo": 1770, "fifa_rank": 32, "attack": 1.00, "defense": 1.10, "xg_f": 1.15, "xg_a": 0.85, "conf": "AFC"},
    "Canada":       {"elo": 1760, "fifa_rank": 33, "attack": 1.05, "defense": 1.00, "xg_f": 1.20, "xg_a": 1.00, "conf": "CONCACAF"},
    "Uzbekistan":   {"elo": 1750, "fifa_rank": 34, "attack": 1.00, "defense": 1.05, "xg_f": 1.15, "xg_a": 0.90, "conf": "AFC"},
    "Nigeria":      {"elo": 1745, "fifa_rank": 35, "attack": 1.05, "defense": 1.00, "xg_f": 1.20, "xg_a": 1.00, "conf": "CAF"},  # not qualified ref
    "Czechia":      {"elo": 1740, "fifa_rank": 36, "attack": 1.05, "defense": 1.05, "xg_f": 1.20, "xg_a": 0.90, "conf": "UEFA"},
    "Tunisia":      {"elo": 1735, "fifa_rank": 37, "attack": 1.00, "defense": 1.05, "xg_f": 1.10, "xg_a": 0.90, "conf": "CAF"},
    "Scotland":     {"elo": 1730, "fifa_rank": 38, "attack": 1.00, "defense": 1.05, "xg_f": 1.10, "xg_a": 0.90, "conf": "UEFA"},
    "Ghana":        {"elo": 1720, "fifa_rank": 39, "attack": 1.00, "defense": 1.00, "xg_f": 1.15, "xg_a": 1.00, "conf": "CAF"},
    "Panama":       {"elo": 1710, "fifa_rank": 40, "attack": 0.95, "defense": 1.00, "xg_f": 1.05, "xg_a": 1.00, "conf": "CONCACAF"},
    "Iraq":         {"elo": 1700, "fifa_rank": 41, "attack": 0.95, "defense": 1.00, "xg_f": 1.05, "xg_a": 1.00, "conf": "AFC"},
    "Saudi Arabia": {"elo": 1695, "fifa_rank": 42, "attack": 0.95, "defense": 1.00, "xg_f": 1.05, "xg_a": 1.00, "conf": "AFC"},
    "Jordan":       {"elo": 1690, "fifa_rank": 43, "attack": 0.95, "defense": 1.00, "xg_f": 1.00, "xg_a": 1.00, "conf": "AFC"},
    "South Africa": {"elo": 1680, "fifa_rank": 44, "attack": 0.95, "defense": 0.95, "xg_f": 1.05, "xg_a": 1.05, "conf": "CAF"},
    "Qatar":        {"elo": 1670, "fifa_rank": 45, "attack": 0.90, "defense": 1.00, "xg_f": 1.00, "xg_a": 1.05, "conf": "AFC"},
    "Bosnia and Herzegovina": {"elo": 1735, "fifa_rank": 46, "attack": 1.05, "defense": 1.00, "xg_f": 1.20, "xg_a": 0.95, "conf": "UEFA"},
    "DR Congo":     {"elo": 1660, "fifa_rank": 47, "attack": 0.95, "defense": 0.95, "xg_f": 1.05, "xg_a": 1.10, "conf": "CAF"},

    # Tier 4: Underdogs (Elo ~1400-1650)
    "Cape Verde":   {"elo": 1620, "fifa_rank": 50, "attack": 0.90, "defense": 0.95, "xg_f": 0.95, "xg_a": 1.10, "conf": "CAF"},
    "New Zealand":  {"elo": 1550, "fifa_rank": 55, "attack": 0.80, "defense": 0.90, "xg_f": 0.85, "xg_a": 1.20, "conf": "OFC"},
    "Curaçao":      {"elo": 1480, "fifa_rank": 65, "attack": 0.75, "defense": 0.85, "xg_f": 0.80, "xg_a": 1.35, "conf": "CONCACAF"},
    "Haiti":        {"elo": 1450, "fifa_rank": 70, "attack": 0.75, "defense": 0.80, "xg_f": 0.75, "xg_a": 1.40, "conf": "CONCACAF"},
}


def build_default_strengths() -> dict[str, TeamStrength]:
    """Build TeamStrength objects from default data."""
    strengths: dict[str, TeamStrength] = {}

    for name, data in DEFAULT_TEAM_DATA.items():
        strengths[name] = TeamStrength(
            name=name,
            elo=data["elo"],
            fifa_rank=data["fifa_rank"],
            attack_rating=data["attack"],
            defense_rating=data["defense"],
            xg_for_90=data["xg_f"],
            xg_against_90=data["xg_a"],
            confederation=data["conf"],
        )

    return strengths


def elo_expected_score(elo_a: float, elo_b: float) -> float:
    """Calculate expected score for team A based on Elo ratings."""
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400.0))


def elo_to_win_draw_loss(elo_a: float, elo_b: float) -> tuple[float, float, float]:
    """
    Convert Elo ratings to win/draw/loss probabilities.

    Uses the empirical relationship from international football:
    - Expected score gives P(win) + 0.5 * P(draw)
    - Draw probability is estimated from the Elo gap

    Returns (p_win_a, p_draw, p_win_b)
    """
    exp_a = elo_expected_score(elo_a, elo_b)

    # Draw probability decreases with Elo gap
    # Empirical formula calibrated on international football
    elo_diff = abs(elo_a - elo_b)
    p_draw = max(0.15, 0.32 - 0.0005 * elo_diff)

    # Distribute remaining probability
    p_win_a = exp_a * (1.0 - p_draw)
    p_win_b = (1.0 - exp_a) * (1.0 - p_draw)

    # Ensure valid probabilities
    total = p_win_a + p_draw + p_win_b
    return p_win_a / total, p_draw / total, p_win_b / total


def estimate_lambdas(
    team_a: TeamStrength,
    team_b: TeamStrength,
    avg_goals: float = 2.65,
) -> tuple[float, float]:
    """
    Estimate Poisson λ parameters for goals scored by each team.

    λ_A = (avg_goals / 2) * attack_A * (1 / defense_B) * elo_adjustment * form
    λ_B = (avg_goals / 2) * attack_B * (1 / defense_A) * elo_adjustment * form

    avg_goals: average total goals per World Cup match (~2.65 historically)
    """
    base = avg_goals / 2.0

    # Elo-based multiplicative adjustment
    elo_diff = team_a.elo - team_b.elo
    # Smooth adjustment: ~10% per 100 Elo points
    elo_factor_a = 1.0 + 0.001 * elo_diff
    elo_factor_b = 1.0 - 0.001 * elo_diff

    # Combine factors
    lambda_a = (
        base
        * team_a.attack_rating
        * (1.0 / team_b.defense_rating)
        * elo_factor_a
        * (1.0 + team_a.form)
    )

    lambda_b = (
        base
        * team_b.attack_rating
        * (1.0 / team_a.defense_rating)
        * elo_factor_b
        * (1.0 + team_b.form)
    )

    # Clamp to reasonable range
    lambda_a = max(0.20, min(4.0, lambda_a))
    lambda_b = max(0.20, min(4.0, lambda_b))

    return lambda_a, lambda_b
