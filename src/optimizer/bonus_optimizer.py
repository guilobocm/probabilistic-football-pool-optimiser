"""
Bonus Optimizer — Optimizes picks for the bonus questions:
1. Group winners (12 groups × 4 pts each)
2. Semifinalists (4 pts per correct pick)
3. Champion (4 pts)
4. Team with top scorer (4 pts)

For individual-scoring bonuses (no order matters), pick the
team with highest marginal probability for each slot.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.simulator.tournament_sim import SimulationResults


@dataclass
class BonusPick:
    """A single bonus prediction."""

    question: str
    pick: str
    probability: float
    points_if_correct: int
    expected_points: float
    alternatives: list[tuple[str, float]]  # Top alternatives


def optimize_group_winners(
    sim_results: SimulationResults,
    points_per_correct: int = 4,
) -> list[BonusPick]:
    """
    Pick the most likely winner for each of the 12 groups.

    Since each correct answer gives 4 pts independently,
    we simply pick the team with highest P(1st) in each group.
    """
    picks = []

    for group, probs in sorted(sim_results.group_winners.items()):
        sorted_teams = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        best_team, best_prob = sorted_teams[0]

        picks.append(
            BonusPick(
                question=f"Who will win Group {group}?",
                pick=best_team,
                probability=best_prob,
                points_if_correct=points_per_correct,
                expected_points=best_prob * points_per_correct,
                alternatives=sorted_teams[1:4],
            )
        )

    return picks


def optimize_semifinalists(
    sim_results: SimulationResults,
    n_picks: int = 4,
    points_per_correct: int = 4,
) -> list[BonusPick]:
    """
    Pick the 4 most likely semifinalists.

    Since the scoring is 4 pts per correct pick with no order,
    we pick the 4 teams with highest marginal P(semifinal).

    NOTE: This is correct because the scoring is individual,
    not joint. We don't need the most probable SET of 4,
    just the 4 individually most probable.
    """
    sorted_teams = sorted(
        sim_results.semifinalists.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    picks = []
    for i in range(min(n_picks, len(sorted_teams))):
        team, prob = sorted_teams[i]
        picks.append(
            BonusPick(
                question=f"Quem chega às semifinais? (Pick {i + 1})",
                pick=team,
                probability=prob,
                points_if_correct=points_per_correct,
                expected_points=prob * points_per_correct,
                alternatives=sorted_teams[i + 1 : i + 4]
                if i + 1 < len(sorted_teams)
                else [],
            )
        )

    return picks


def optimize_champion(
    sim_results: SimulationResults,
    points_per_correct: int = 4,
) -> BonusPick:
    """
    Pick the most likely champion.

    Simple: pick the team with highest P(champion).
    """
    sorted_teams = sorted(
        sim_results.champion.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    best_team, best_prob = sorted_teams[0]

    return BonusPick(
        question="Who will be the World Champion?",
        pick=best_team,
        probability=best_prob,
        points_if_correct=points_per_correct,
        expected_points=best_prob * points_per_correct,
        alternatives=sorted_teams[1:5],
    )


def optimize_golden_boot_team(
    sim_results: SimulationResults,
    points_per_correct: int = 4,
) -> BonusPick:
    """
    Pick the team most likely to have the tournament's top scorer.

    The bolão asks "which TEAM will the top scorer belong to?",
    not the specific player. To solve this mathematically without player data.
    """
    if not sim_results.golden_boot_team:
        return None

    sorted_teams = sorted(
        sim_results.golden_boot_team.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    best_team, best_prob = sorted_teams[0]

    return BonusPick(
        question="Qual seleção terá o artilheiro do torneio?",
        pick=best_team,
        probability=best_prob,
        points_if_correct=points_per_correct,
        expected_points=best_prob * points_per_correct,
        alternatives=sorted_teams[1:5],
    )


def optimize_all_bonuses(
    sim_results: SimulationResults,
    points_per_correct: int = 4,
) -> dict[str, list[BonusPick] | BonusPick]:
    """
    Optimize all bonus questions.

    Returns dict with:
        'group_winners': list of 12 BonusPick
        'semifinalists': list of 4 BonusPick
        'champion': single BonusPick
    """
    return {
        "group_winners": optimize_group_winners(sim_results, points_per_correct),
        "semifinalists": optimize_semifinalists(sim_results, 4, points_per_correct),
        "champion": optimize_champion(sim_results, points_per_correct),
        "golden_boot_team": optimize_golden_boot_team(sim_results, points_per_correct),
    }
