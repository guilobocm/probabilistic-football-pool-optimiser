"""
Scoring Rules — parametric implementation of the prediction-pool scoring model.

Implements the neutral-venue tournament rule:
- Correct winning team: 2 points
- Correct winning margin: 3 points
- Correct exact winning scoreline: 4 points
- Correct draw, incorrect scoreline: 3 points
- Correct exact draw scoreline: 4 points

A correct non-exact draw is worth three points, compared with two points for a
correct non-exact win. That asymmetry can make a draw the expected-points-
maximising selection in sufficiently balanced matches.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ScoringRule:
    """Parametric scoring rule for the prediction pool."""

    trend_win: int = 2
    diff_win: int = 3
    exact_win: int = 4
    trend_draw: int = 3
    exact_draw: int = 4

    def to_dict(self) -> dict[str, int]:
        return {
            "trend_win": self.trend_win,
            "diff_win": self.diff_win,
            "exact_win": self.exact_win,
            "trend_draw": self.trend_draw,
            "exact_draw": self.exact_draw,
        }


def load_active_rule(config_path: Path | None = None) -> ScoringRule:
    """Load the active scoring rule configured in YAML."""
    if config_path is None:
        config_path = (
            Path(__file__).resolve().parent.parent.parent
            / "config"
            / "scoring_rules.yaml"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    active_rule_name = config.get("active_rule", "tournament_neutral_3_draw")
    rule_data = config.get(active_rule_name, {})

    return ScoringRule(
        trend_win=rule_data.get("trend_win", 2),
        diff_win=rule_data.get("diff_win", 3),
        exact_win=rule_data.get("exact_win", 4),
        trend_draw=rule_data.get("trend_draw", 3),
        exact_draw=rule_data.get("exact_draw", 4),
    )


TOURNAMENT_RULE = load_active_rule()


def get_trend(goals_a: int, goals_b: int) -> str:
    """Return A for a Team A win, B for a Team B win, or D for a draw."""
    if goals_a > goals_b:
        return "A"
    if goals_a < goals_b:
        return "B"
    return "D"


def calculate_points(
    pred: tuple[int, int],
    actual: tuple[int, int],
    rule: ScoringRule | None = None,
) -> int:
    """Calculate prediction-pool points for one predicted and actual scoreline."""
    if rule is None:
        rule = TOURNAMENT_RULE

    pa, pb = pred
    aa, ab = actual

    if pred == actual:
        if pa == pb:
            return rule.exact_draw
        return rule.exact_win

    pred_trend = get_trend(pa, pb)
    actual_trend = get_trend(aa, ab)
    if pred_trend != actual_trend:
        return 0

    if aa == ab:
        return rule.trend_draw

    if (pa - pb) == (aa - ab):
        return rule.diff_win

    return rule.trend_win
