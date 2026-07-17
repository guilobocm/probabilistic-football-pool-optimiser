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
    rows, cols = np.unravel_index(indices, prob_matrix.shape)

    return list(
        zip(
            rows.astype(int).tolist(),
            cols.astype(int).tolist(),
            strict=True,
        )
    )
