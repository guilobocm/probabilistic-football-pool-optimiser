import numpy as np
from typing import Tuple, List

def simulate_matches(prob_matrix: np.ndarray, num_simulations: int, seed: int = 42) -> List[Tuple[int, int]]:
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
    
    results = []
    for idx in indices:
        row, col = np.unravel_index(idx, prob_matrix.shape)
        results.append((int(row), int(col)))
        
    return results
