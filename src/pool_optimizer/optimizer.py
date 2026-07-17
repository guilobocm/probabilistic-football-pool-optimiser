import numpy as np
from numpy.typing import NDArray

from .scoring import ScoringRule


FloatMatrix = NDArray[np.float64]


def get_expected_points_matrix(
    prob_matrix: FloatMatrix,
    rule: ScoringRule,
    max_goals: int = 10,
) -> FloatMatrix:
    """
    Computes the expected points for each possible predicted scoreline.
    """
    expected_shape = (max_goals + 1, max_goals + 1)

    if prob_matrix.shape != expected_shape:
        raise ValueError(
            f"Expected probability matrix with shape {expected_shape}, "
            f"received {prob_matrix.shape}."
        )

    if not np.all(np.isfinite(prob_matrix)):
        raise ValueError("Probability matrix contains NaN or infinity.")

    if np.any(prob_matrix < 0.0):
        raise ValueError("Probability matrix contains negative values.")

    ep_matrix = np.zeros((max_goals + 1, max_goals + 1))

    for p_home in range(max_goals + 1):
        for p_away in range(max_goals + 1):
            ep = 0.0
            for a_home in range(max_goals + 1):
                for a_away in range(max_goals + 1):
                    prob = prob_matrix[a_home, a_away]
                    pts = rule.calculate_points((p_home, p_away), (a_home, a_away))
                    ep += prob * pts
            ep_matrix[p_home, p_away] = ep

    return ep_matrix


def find_optimal_prediction(ep_matrix: FloatMatrix) -> tuple[int, int]:
    """
    Finds the scoreline that maximizes expected points.
    """
    flat_index = np.argmax(ep_matrix)
    row, col = np.unravel_index(flat_index, ep_matrix.shape)
    return int(row), int(col)
