"""
Scoring Rules — Parametric implementation of the bolão scoring function.

Implements the "Exemplo Torneio" rule (neutral venue, no home/away distinction):
  - Win trend correct: 2 pts
  - Win goal diff correct: 3 pts
  - Win exact score: 4 pts
  - Draw trend correct: 3 pts
  - Draw exact score: 4 pts

Key insight: empate na tendência vale 3 pontos vs 2 para vitória,
criando um incentivo para apostar empate em jogos equilibrados.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ScoringRule:
    """Parametric scoring rule for the bolão."""
    trend_win: int = 2      # Correct trend (who won)
    diff_win: int = 3       # Correct goal difference
    exact_win: int = 4      # Exact score (win)
    trend_draw: int = 3     # Correct trend (draw, wrong score)
    exact_draw: int = 4     # Exact draw score

    def to_dict(self) -> dict[str, int]:
        return {
            "trend_win": self.trend_win,
            "diff_win": self.diff_win,
            "exact_win": self.exact_win,
            "trend_draw": self.trend_draw,
            "exact_draw": self.exact_draw,
        }


def load_active_rule(config_path: Path = None) -> ScoringRule:
    """Carrega a regra ativa configurada no YAML."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent.parent / "config" / "scoring_rules.yaml"
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    active_rule_name = config.get("active_rule", "tournament_neutral_3_draw")
    rule_data = config.get(active_rule_name, {})
    
    return ScoringRule(
        trend_win=rule_data.get("trend_win", 2),
        diff_win=rule_data.get("diff_win", 3),
        exact_win=rule_data.get("exact_win", 4),
        trend_draw=rule_data.get("trend_draw", 3),
        exact_draw=rule_data.get("exact_draw", 4)
    )

# Rule loaded dynamically from config
TOURNAMENT_RULE = load_active_rule()


def get_trend(goals_a: int, goals_b: int) -> str:
    """Return match trend: 'A' (win A), 'B' (win B), 'D' (draw)."""
    if goals_a > goals_b:
        return "A"
    elif goals_a < goals_b:
        return "B"
    return "D"


def calculate_points(
    pred: tuple[int, int],
    actual: tuple[int, int],
    rule: ScoringRule | None = None,
) -> int:
    """
    Calculate bolão points for a prediction given the actual result.

    Args:
        pred: (predicted_goals_a, predicted_goals_b)
        actual: (actual_goals_a, actual_goals_b)
        rule: scoring rule to use (default: TOURNAMENT_RULE)

    Returns:
        Points awarded (0, 2, 3, or 4)
    """
    if rule is None:
        rule = TOURNAMENT_RULE

    pa, pb = pred
    aa, ab = actual

    # Exact score match
    if pred == actual:
        if pa == pb:
            return rule.exact_draw
        else:
            return rule.exact_win

    # Wrong trend = 0 points
    pred_trend = get_trend(pa, pb)
    actual_trend = get_trend(aa, ab)

    if pred_trend != actual_trend:
        return 0

    # Correct trend, but not exact score
    if aa == ab:
        # Draw: trend is correct (both predicted draw), score is wrong
        return rule.trend_draw

    # Win: check if goal difference matches
    if (pa - pb) == (aa - ab):
        return rule.diff_win

    # Only trend correct
    return rule.trend_win
