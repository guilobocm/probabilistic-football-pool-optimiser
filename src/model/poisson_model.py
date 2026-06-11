"""
Poisson Goal Model — Generates score probability matrices.

Implements independent Poisson and Dixon-Coles adjustment for
low-scoring games (0-0, 1-0, 0-1, 1-1).

The core of the prediction engine:
  P(goals_A = a, goals_B = b) = Poisson(a; λ_A) * Poisson(b; λ_B) * ρ_correction
"""

from __future__ import annotations

import numpy as np
from scipy.stats import poisson
from typing import Optional


# Maximum goals to consider per team in score matrix
MAX_GOALS = 8


def poisson_score_matrix(
    lambda_a: float,
    lambda_b: float,
    max_goals: int = MAX_GOALS,
) -> np.ndarray:
    """
    Generate an independent bivariate Poisson score probability matrix.

    Returns a (max_goals+1) x (max_goals+1) matrix where
    matrix[a][b] = P(team_A scores a, team_B scores b).
    """
    goals_range = np.arange(0, max_goals + 1)

    prob_a = poisson.pmf(goals_range, lambda_a)
    prob_b = poisson.pmf(goals_range, lambda_b)

    # Outer product gives independent joint probability
    matrix = np.outer(prob_a, prob_b)

    # Normalise to ensure sum = 1 (handles truncation)
    matrix /= matrix.sum()

    return matrix


def dixon_coles_correction(
    lambda_a: float,
    lambda_b: float,
    rho: float = -0.10,
    max_goals: int = MAX_GOALS,
) -> np.ndarray:
    """
    Apply Dixon-Coles adjustment to a Poisson score matrix.

    The adjustment corrects for the empirical over/under-prediction
    of low-scoring outcomes (0-0, 1-0, 0-1, 1-1).

    rho < 0: fewer 0-0 and 1-1 than independent Poisson predicts
    rho > 0: more 0-0 and 1-1 than independent Poisson predicts

    For international football, rho ≈ -0.10 is typical.
    """
    matrix = poisson_score_matrix(lambda_a, lambda_b, max_goals)

    # Dixon-Coles tau function adjustments for (0,0), (1,0), (0,1), (1,1)
    if abs(rho) > 1e-10:
        mu1 = lambda_a
        mu2 = lambda_b

        # tau(0,0)
        matrix[0, 0] *= 1.0 - mu1 * mu2 * rho
        # tau(1,0)
        matrix[1, 0] *= 1.0 + mu2 * rho
        # tau(0,1)
        matrix[0, 1] *= 1.0 + mu1 * rho
        # tau(1,1)
        matrix[1, 1] *= 1.0 - rho

        # Re-normalise
        matrix = np.clip(matrix, 0, None)
        matrix /= matrix.sum()

    return matrix


def score_matrix_to_dict(
    matrix: np.ndarray,
    threshold: float = 0.001,
) -> dict[tuple[int, int], float]:
    """
    Convert a numpy score matrix to a dict of {(goals_a, goals_b): probability}.

    Only includes probabilities above the threshold.
    """
    result: dict[tuple[int, int], float] = {}
    rows, cols = matrix.shape

    for a in range(rows):
        for b in range(cols):
            if matrix[a, b] >= threshold:
                result[(a, b)] = float(matrix[a, b])

    return result


def calibrate_lambdas_to_1x2(
    target_p_a: float,
    target_p_draw: float,
    target_p_b: float,
    initial_lambda_a: float = 1.3,
    initial_lambda_b: float = 1.1,
    rho: float = -0.10,
    lr: float = 0.05,
    max_iter: int = 500,
    tol: float = 0.005,
) -> tuple[float, float]:
    """
    Calibrate λ_A and λ_B so that the resulting score matrix
    approximately matches target 1X2 probabilities.

    Uses gradient-free optimisation (coordinate descent).

    Args:
        target_p_a: target P(team A wins)
        target_p_draw: target P(draw)
        target_p_b: target P(team B wins)

    Returns:
        Calibrated (lambda_a, lambda_b)
    """
    la = initial_lambda_a
    lb = initial_lambda_b

    for iteration in range(max_iter):
        matrix = dixon_coles_correction(la, lb, rho)

        # Calculate current 1X2 from matrix
        p_a = 0.0
        p_draw = 0.0
        p_b = 0.0
        rows, cols = matrix.shape
        for a in range(rows):
            for b in range(cols):
                if a > b:
                    p_a += matrix[a, b]
                elif a == b:
                    p_draw += matrix[a, b]
                else:
                    p_b += matrix[a, b]

        # Error
        err_a = target_p_a - p_a
        err_draw = target_p_draw - p_draw
        err_b = target_p_b - p_b

        if abs(err_a) < tol and abs(err_draw) < tol and abs(err_b) < tol:
            break

        # Adjust lambdas
        # If team A should win more → increase λ_A, decrease λ_B
        # If draw should be higher → decrease both lambdas (lower scoring)
        la += lr * (err_a - err_b + 0.3 * err_draw * (-1))
        lb += lr * (err_b - err_a + 0.3 * err_draw * (-1))

        la = max(0.15, min(4.0, la))
        lb = max(0.15, min(4.0, lb))

    return la, lb


def get_1x2_from_matrix(matrix: np.ndarray) -> tuple[float, float, float]:
    """Extract P(win_A), P(draw), P(win_B) from a score matrix."""
    p_a = 0.0
    p_draw = 0.0
    p_b = 0.0
    rows, cols = matrix.shape

    for a in range(rows):
        for b in range(cols):
            if a > b:
                p_a += matrix[a, b]
            elif a == b:
                p_draw += matrix[a, b]
            else:
                p_b += matrix[a, b]

    return p_a, p_draw, p_b


def get_over_under(matrix: np.ndarray, line: float = 2.5) -> tuple[float, float]:
    """Calculate P(over) and P(under) for a given goal line."""
    p_over = 0.0
    p_under = 0.0
    rows, cols = matrix.shape

    for a in range(rows):
        for b in range(cols):
            total = a + b
            if total > line:
                p_over += matrix[a, b]
            else:
                p_under += matrix[a, b]

    return p_over, p_under
