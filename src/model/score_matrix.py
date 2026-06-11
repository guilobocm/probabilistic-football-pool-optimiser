"""
Score Matrix Generator — Combines team strength, Poisson model,
and external calibration into a final probability distribution
over match outcomes.

This is the integration layer that produces the P(a,b) matrix
that feeds into the pool scoring optimizer.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from src.model.team_strength import TeamStrength, estimate_lambdas
from src.model.poisson_model import (
    dixon_coles_correction,
    score_matrix_to_dict,
    get_1x2_from_matrix,
)
from src.model.lambda_calibrator import calibrate_lambdas


def generate_score_matrix(
    team_a: TeamStrength,
    team_b: TeamStrength,
    external_1x2: Optional[tuple[float, float, float]] = None,
    weight_external: float = 0.45,
    rho: float = -0.10,
    avg_goals: float = 2.65,
    target_over_25: Optional[float] = None,
) -> dict[tuple[int, int], float]:
    """
    Generate the full score probability distribution for a match.

    Steps:
    1. Estimate λ from team strength model
    2. If external 1X2 provided (from odds), calibrate λ to blend
    3. Generate Dixon-Coles corrected matrix
    4. Convert to dict

    Args:
        team_a: TeamStrength for team A
        team_b: TeamStrength for team B
        external_1x2: (P_win_A, P_draw, P_win_B) from odds/external model
        weight_external: weight given to external probabilities (0-1)
        rho: Dixon-Coles rho parameter
        avg_goals: average total goals per match

    Returns:
        Dict of {(goals_a, goals_b): probability}
    """
    # Step 1: Get base lambdas from team strength
    lambda_a, lambda_b = estimate_lambdas(team_a, team_b, avg_goals)

    # Step 2: If we have external 1X2, calibrate lambdas directly to market
    if external_1x2 is not None:
        target_pa, target_pd, target_pb = external_1x2

        # Re-calibrate lambdas to match target directly using SciPy
        lambda_a, lambda_b = calibrate_lambdas(
            target_1x2=(target_pa, target_pd, target_pb),
            initial_la=lambda_a,
            initial_lb=lambda_b,
            rho=rho,
            target_over_25=target_over_25,
        )

    # Step 3: Generate final matrix
    matrix = dixon_coles_correction(lambda_a, lambda_b, rho)

    # Step 4: Convert to dict
    return score_matrix_to_dict(matrix, threshold=0.0005)


def generate_score_matrix_raw(
    team_a: TeamStrength,
    team_b: TeamStrength,
    external_1x2: Optional[tuple[float, float, float]] = None,
    weight_external: float = 0.45,
    rho: float = -0.10,
    avg_goals: float = 2.65,
    target_over_25: Optional[float] = None,
) -> np.ndarray:
    """
    Same as generate_score_matrix but returns numpy array instead of dict.
    Useful for tournament simulation where speed matters.
    """
    lambda_a, lambda_b = estimate_lambdas(team_a, team_b, avg_goals)

    if external_1x2 is not None:
        target_pa, target_pd, target_pb = external_1x2
        lambda_a, lambda_b = calibrate_lambdas(
            target_1x2=(target_pa, target_pd, target_pb),
            initial_la=lambda_a,
            initial_lb=lambda_b,
            rho=rho,
            target_over_25=target_over_25,
        )

    return dixon_coles_correction(lambda_a, lambda_b, rho)
