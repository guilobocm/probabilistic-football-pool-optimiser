"""
Pick Optimizer — The brain of the system.

Selects the score prediction that maximizes EXPECTED POINTS,
not the most probable score. This is the key distinction:

  p* = argmax_p Σ P(r) · S(p, r)

Where:
  p = your pick (predicted score)
  r = each possible real result
  P(r) = probability of result r
  S(p, r) = points awarded if you picked p and r happened
"""

from __future__ import annotations

from dataclasses import dataclass

from src.optimizer.scoring_rules import (
    ScoringRule,
    TOURNAMENT_RULE,
    calculate_points,
)


@dataclass
class PickResult:
    """Result of the pick optimization for a single match."""

    match_id: str
    team_a: str
    team_b: str
    best_pick: tuple[int, int]
    expected_points: float
    confidence: float  # How much better than 2nd best
    top_picks: list[tuple[tuple[int, int], float]]  # Top 5 picks with EP
    most_probable_score: tuple[int, int]
    most_probable_prob: float
    rationale: str


def generate_candidates(max_goals: int = 5) -> list[tuple[int, int]]:
    """
    Generate candidate score predictions.

    For World Cup matches, scores above 5-X are extremely rare.
    We generate all permutations up to max_goals.
    """
    candidates = []
    for a in range(max_goals + 1):
        for b in range(max_goals + 1):
            candidates.append((a, b))
    return candidates


def expected_points(
    pick: tuple[int, int],
    score_probs: dict[tuple[int, int], float],
    rule: ScoringRule | None = None,
) -> float:
    """
    Calculate expected points for a specific pick.

    EP(pick) = Σ P(result) * points(pick, result)
    """
    if rule is None:
        rule = TOURNAMENT_RULE

    ep = 0.0
    for result, prob in score_probs.items():
        pts = calculate_points(pick, result, rule)
        ep += prob * pts

    return ep


def optimize_pick(
    match_id: str,
    team_a: str,
    team_b: str,
    score_probs: dict[tuple[int, int], float],
    rule: ScoringRule | None = None,
    max_goals: int = 5,
) -> PickResult:
    """
    Find the pick that maximizes expected points for a single match.

    This is the core optimization:
      p* = argmax_p EP(p)

    Returns a PickResult with the best pick, EP, alternatives, and rationale.
    """
    if rule is None:
        rule = TOURNAMENT_RULE

    candidates = generate_candidates(max_goals)

    # Calculate EP for each candidate
    ep_results: list[tuple[tuple[int, int], float]] = []
    for candidate in candidates:
        ep = expected_points(candidate, score_probs, rule)
        ep_results.append((candidate, ep))

    # Sort by EP descending
    ep_results.sort(key=lambda x: x[1], reverse=True)

    # Best pick
    best_pick, best_ep = ep_results[0]

    # Confidence: gap between 1st and 2nd
    second_ep = ep_results[1][1] if len(ep_results) > 1 else 0.0
    confidence = best_ep - second_ep

    # Top 5
    top_picks = ep_results[:5]

    # Most probable score
    most_probable = max(score_probs.items(), key=lambda x: x[1])
    most_probable_score = most_probable[0]
    most_probable_prob = most_probable[1]

    # Generate rationale
    rationale = _generate_rationale(
        best_pick,
        best_ep,
        most_probable_score,
        most_probable_prob,
        top_picks,
        team_a,
        team_b,
        score_probs,
        rule,
    )

    return PickResult(
        match_id=match_id,
        team_a=team_a,
        team_b=team_b,
        best_pick=best_pick,
        expected_points=best_ep,
        confidence=confidence,
        top_picks=top_picks,
        most_probable_score=most_probable_score,
        most_probable_prob=most_probable_prob,
        rationale=rationale,
    )


def _generate_rationale(
    best_pick: tuple[int, int],
    best_ep: float,
    most_probable: tuple[int, int],
    most_probable_prob: float,
    top_picks: list[tuple[tuple[int, int], float]],
    team_a: str,
    team_b: str,
    score_probs: dict[tuple[int, int], float],
    rule: ScoringRule,
) -> str:
    """Generate human-readable rationale for the pick."""
    pa, pb = best_pick
    mp_a, mp_b = most_probable

    # Determine trend
    if pa > pb:
        trend = f"win {team_a}"
    elif pa < pb:
        trend = f"win {team_b}"
    else:
        trend = "draw"

    parts = [
        f"Pick: {team_a} {pa}-{pb} {team_b}",
        f"EP: {best_ep:.3f} pts",
        f"Tendência: {trend}",
    ]

    if best_pick != most_probable:
        parts.append(
            f"Placar mais provável: {mp_a}-{mp_b} ({most_probable_prob:.1%}), "
            f"mas {pa}-{pb} maximiza EP"
        )

    # Check if draw is being picked over win
    if pa == pb and mp_a != mp_b:
        # Calculate how much draw tendency contributes
        draw_prob = sum(p for (a, b), p in score_probs.items() if a == b)
        parts.append(
            f"Draw: P={draw_prob:.1%}, yielding {rule.trend_draw}pts for the trend "
            f"vs {rule.trend_win}pts for a win - favours draw in balanced matches"
        )

    # Show alternatives
    alt_str = " | ".join(f"{a}-{b}: {ep:.3f}" for (a, b), ep in top_picks[:3])
    parts.append(f"Alternativas: {alt_str}")

    return " | ".join(parts)


def optimize_all_matches(
    matches: list[dict],
    score_probs_by_match: dict[str, dict[tuple[int, int], float]],
    rule: ScoringRule | None = None,
) -> list[PickResult]:
    """
    Optimize picks for all matches.

    Args:
        matches: list of {match_id, team_a, team_b}
        score_probs_by_match: {match_id: {(a,b): prob}}

    Returns:
        List of PickResult for each match
    """
    results = []
    for match in matches:
        mid = match["match_id"]
        if mid not in score_probs_by_match:
            continue

        result = optimize_pick(
            match_id=mid,
            team_a=match["team_a"],
            team_b=match["team_b"],
            score_probs=score_probs_by_match[mid],
            rule=rule,
        )
        results.append(result)

    return results
