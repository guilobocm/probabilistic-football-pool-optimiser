"""
Pick Optimiser — the decision engine of the system.

Selects the scoreline that maximises expected prediction-pool points rather
than simply choosing the single most probable scoreline:

    p* = argmax_p Σ P(r) · S(p, r)

where p is the submitted pick, r is a possible result, P(r) is the modelled
probability of that result, and S(p, r) is the scoring-rule payoff.
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
    """Optimisation result for one match."""

    match_id: str
    team_a: str
    team_b: str
    best_pick: tuple[int, int]
    expected_points: float
    confidence: float
    top_picks: list[tuple[tuple[int, int], float]]
    most_probable_score: tuple[int, int]
    most_probable_prob: float
    rationale: str


def generate_candidates(max_goals: int = 5) -> list[tuple[int, int]]:
    """Generate every candidate scoreline from 0-0 to max_goals–max_goals."""
    return [
        (goals_a, goals_b)
        for goals_a in range(max_goals + 1)
        for goals_b in range(max_goals + 1)
    ]


def expected_points(
    pick: tuple[int, int],
    score_probs: dict[tuple[int, int], float],
    rule: ScoringRule | None = None,
) -> float:
    """Calculate expected points for one candidate scoreline."""
    if rule is None:
        rule = TOURNAMENT_RULE

    return sum(
        probability * calculate_points(pick, result, rule)
        for result, probability in score_probs.items()
    )


def optimize_pick(
    match_id: str,
    team_a: str,
    team_b: str,
    score_probs: dict[tuple[int, int], float],
    rule: ScoringRule | None = None,
    max_goals: int = 5,
) -> PickResult:
    """Find the expected-points-maximising pick for one match."""
    if rule is None:
        rule = TOURNAMENT_RULE

    ep_results = [
        (candidate, expected_points(candidate, score_probs, rule))
        for candidate in generate_candidates(max_goals)
    ]
    ep_results.sort(key=lambda item: item[1], reverse=True)

    best_pick, best_ep = ep_results[0]
    second_ep = ep_results[1][1] if len(ep_results) > 1 else 0.0
    confidence = best_ep - second_ep
    top_picks = ep_results[:5]

    most_probable_score, most_probable_prob = max(
        score_probs.items(),
        key=lambda item: item[1],
    )

    rationale = _generate_rationale(
        best_pick=best_pick,
        best_ep=best_ep,
        most_probable=most_probable_score,
        most_probable_prob=most_probable_prob,
        top_picks=top_picks,
        team_a=team_a,
        team_b=team_b,
        score_probs=score_probs,
        rule=rule,
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
    """Generate a compact, human-readable explanation for a selected pick."""
    pick_a, pick_b = best_pick
    modal_a, modal_b = most_probable

    if pick_a > pick_b:
        outcome = f"{team_a} win"
    elif pick_a < pick_b:
        outcome = f"{team_b} win"
    else:
        outcome = "draw"

    parts = [
        f"Pick: {team_a} {pick_a}-{pick_b} {team_b}",
        f"EP: {best_ep:.3f} pts",
        f"Outcome: {outcome}",
    ]

    if best_pick != most_probable:
        parts.append(
            f"Modal score: {modal_a}-{modal_b} ({most_probable_prob:.1%}), "
            f"but {pick_a}-{pick_b} maximises EP"
        )

    if pick_a == pick_b and modal_a != modal_b:
        draw_probability = sum(
            probability
            for (goals_a, goals_b), probability in score_probs.items()
            if goals_a == goals_b
        )
        parts.append(
            f"Draw probability: {draw_probability:.1%}; a non-exact draw earns "
            f"{rule.trend_draw} pts versus {rule.trend_win} pts for a non-exact "
            "win, favouring the draw in sufficiently balanced matches"
        )

    alternatives = " | ".join(
        f"{goals_a}-{goals_b}: {ep:.3f}"
        for (goals_a, goals_b), ep in top_picks[:3]
    )
    parts.append(f"Alternatives: {alternatives}")

    return " | ".join(parts)


def optimize_all_matches(
    matches: list[dict],
    score_probs_by_match: dict[str, dict[tuple[int, int], float]],
    rule: ScoringRule | None = None,
) -> list[PickResult]:
    """Optimise picks for every match with an available score distribution."""
    results = []
    for match in matches:
        match_id = match["match_id"]
        if match_id not in score_probs_by_match:
            continue

        results.append(
            optimize_pick(
                match_id=match_id,
                team_a=match["team_a"],
                team_b=match["team_b"],
                score_probs=score_probs_by_match[match_id],
                rule=rule,
            )
        )

    return results
