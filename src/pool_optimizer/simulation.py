import numpy as np
from numpy.typing import NDArray


FloatMatrix = NDArray[np.float64]


def simulate_matches(
    prob_matrix: FloatMatrix, num_simulations: int, seed: int = 42
) -> list[tuple[int, int]]:
    """
    Simulates matches based on a probability matrix.
    """
    if num_simulations <= 0:
        raise ValueError("Number of simulations must be positive")

    rng = np.random.default_rng(seed)

    flat_probs = prob_matrix.flatten()
    # Normalize just in case
    flat_probs = flat_probs / flat_probs.sum()

    indices = rng.choice(len(flat_probs), size=num_simulations, p=flat_probs)

    results: list[tuple[int, int]] = []
    for idx in indices:
        row, col = np.unravel_index(idx, prob_matrix.shape)
        results.append((int(row), int(col)))

    return results
