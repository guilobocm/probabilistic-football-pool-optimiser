import math
import operator

import numpy as np
from numpy.typing import NDArray
from scipy.stats import poisson


FloatMatrix = NDArray[np.float64]


def generate_probability_matrix(
    home_attack: float,
    home_defense: float,
    away_attack: float,
    away_defense: float,
    max_goals: int = 10,
    base_lambda: float = 1.0,
) -> FloatMatrix:
    """
    Generate a truncated independent Poisson distribution for a match.

    The returned matrix is conditioned on both teams scoring at most
    ``max_goals`` goals.
    """
    if isinstance(max_goals, bool):
        raise ValueError("max_goals must be a non-negative integer.")

    try:
        max_goals = operator.index(max_goals)
    except TypeError as exc:
        raise ValueError("max_goals must be a non-negative integer.") from exc

    if max_goals < 0:
        raise ValueError("max_goals must be a non-negative integer.")

    strengths = {
        "home_attack": home_attack,
        "home_defense": home_defense,
        "away_attack": away_attack,
        "away_defense": away_defense,
    }
    for name, strength in strengths.items():
        if not math.isfinite(strength):
            raise ValueError(f"{name} must be finite.")
        if strength < 0.0:
            raise ValueError(f"{name} must be non-negative.")

    if not math.isfinite(base_lambda) or base_lambda <= 0.0:
        raise ValueError("base_lambda must be finite and positive.")

    home_lambda = base_lambda * home_attack * away_defense
    away_lambda = base_lambda * away_attack * home_defense

    if not math.isfinite(home_lambda) or not math.isfinite(away_lambda):
        raise ValueError("Expected-goals rates must be finite.")

    home_probs = np.asarray(
        poisson.pmf(np.arange(max_goals + 1), home_lambda), dtype=np.float64
    )
    away_probs = np.asarray(
        poisson.pmf(np.arange(max_goals + 1), away_lambda), dtype=np.float64
    )

    matrix = np.outer(home_probs, away_probs).astype(np.float64, copy=False)
    total_mass = float(matrix.sum())

    if not np.isfinite(total_mass) or total_mass <= 0.0:
        raise ValueError("Probability matrix has invalid total mass.")

    return matrix / total_mass
