"""
Bonus Optimiser — optimise picks for four bonus-question categories:
1. Group winners: 12 groups, four points for each correct answer
2. Semi-finalists: four points for each correct answer
3. Champion: four points
4. Team represented by the Golden Boot winner: four points

Each bonus is scored independently and order does not matter, so the optimiser
selects the team with the highest marginal probability for each available slot.
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
    alternatives: list[tuple[str, float]]


def optimize_group_winners(
    sim_results: SimulationResults,
    points_per_correct: int = 4,
) -> list[BonusPick]:
    """Select the most likely winner of each group."""
    picks = []

    for group, probs in sorted(sim_results.group_winners.items()):
        sorted_teams = sorted(probs.items(), key=lambda item: item[1], reverse=True)
        best_team, best_prob = sorted_teams[0]

        picks.append(
            BonusPick(
                question=f"Which team will win Group {group}?",
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
    """Select the teams with the highest marginal semi-final probabilities."""
    sorted_teams = sorted(
        sim_results.semifinalists.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    picks = []
    for index in range(min(n_picks, len(sorted_teams))):
        team, probability = sorted_teams[index]
        picks.append(
            BonusPick(
                question=f"Which team will reach the semi-finals? (Pick {index + 1})",
                pick=team,
                probability=probability,
                points_if_correct=points_per_correct,
                expected_points=probability * points_per_correct,
                alternatives=(
                    sorted_teams[index + 1 : index + 4]
                    if index + 1 < len(sorted_teams)
                    else []
                ),
            )
        )

    return picks


def optimize_champion(
    sim_results: SimulationResults,
    points_per_correct: int = 4,
) -> BonusPick:
    """Select the team with the highest simulated championship probability."""
    sorted_teams = sorted(
        sim_results.champion.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    best_team, best_prob = sorted_teams[0]

    return BonusPick(
        question="Which team will win the World Cup?",
        pick=best_team,
        probability=best_prob,
        points_if_correct=points_per_correct,
        expected_points=best_prob * points_per_correct,
        alternatives=sorted_teams[1:5],
    )


def optimize_golden_boot_team(
    sim_results: SimulationResults,
    points_per_correct: int = 4,
) -> BonusPick | None:
    """Select the team most likely to be represented by the Golden Boot winner."""
    if not sim_results.golden_boot_team:
        return None

    sorted_teams = sorted(
        sim_results.golden_boot_team.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    best_team, best_prob = sorted_teams[0]

    return BonusPick(
        question="Which national team will be represented by the Golden Boot winner?",
        pick=best_team,
        probability=best_prob,
        points_if_correct=points_per_correct,
        expected_points=best_prob * points_per_correct,
        alternatives=sorted_teams[1:5],
    )


def optimize_all_bonuses(
    sim_results: SimulationResults,
    points_per_correct: int = 4,
) -> dict[str, list[BonusPick] | BonusPick | None]:
    """Optimise every supported bonus-question category."""
    return {
        "group_winners": optimize_group_winners(sim_results, points_per_correct),
        "semifinalists": optimize_semifinalists(
            sim_results,
            4,
            points_per_correct,
        ),
        "champion": optimize_champion(sim_results, points_per_correct),
        "golden_boot_team": optimize_golden_boot_team(
            sim_results,
            points_per_correct,
        ),
    }
