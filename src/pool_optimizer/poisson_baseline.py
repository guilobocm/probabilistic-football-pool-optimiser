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
    Generates a basic independent Poisson probability matrix for a match.
    """
    home_lambda = base_lambda * home_attack * away_defense
    away_lambda = base_lambda * away_attack * home_defense

    home_probs = np.asarray(
        poisson.pmf(np.arange(max_goals + 1), home_lambda), dtype=np.float64
    )
    away_probs = np.asarray(
        poisson.pmf(np.arange(max_goals + 1), away_lambda), dtype=np.float64
    )

    matrix = np.outer(home_probs, away_probs)
    return matrix
