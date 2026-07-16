import numpy as np
import pytest
from src.pool_optimizer.scoring import ScoringRule
from src.pool_optimizer.poisson_baseline import generate_probability_matrix
from src.pool_optimizer.optimizer import get_expected_points_matrix, find_optimal_prediction
from src.pool_optimizer.simulation import simulate_matches

def test_probability_mass_is_one():
    matrix = generate_probability_matrix(1.5, 1.0, 1.0, 1.5)
    assert np.isclose(matrix.sum(), 1.0, atol=1e-4)

def test_expected_points_matches_manual_calculation():
    rule = ScoringRule(exact_score=3, correct_outcome=1, correct_goal_difference=2)
    # create a dummy matrix
    prob_matrix = np.zeros((3, 3))
    prob_matrix[1, 0] = 1.0  # 100% chance of 1-0
    
    ep_matrix = get_expected_points_matrix(prob_matrix, rule, max_goals=2)
    
    # If we predict 1-0, we get exact score (3 pts)
    assert np.isclose(ep_matrix[1, 0], 3.0)
    # If we predict 2-0, we get correct outcome (1 pt)
    assert np.isclose(ep_matrix[2, 0], 1.0)
    # If we predict 2-1, we get correct goal difference (2 pts)
    assert np.isclose(ep_matrix[2, 1], 2.0)
    # If we predict 0-1, we get nothing (0 pts)
    assert np.isclose(ep_matrix[0, 1], 0.0)

def test_optimizer_returns_global_maximum():
    rule = ScoringRule(exact_score=3, correct_outcome=1, correct_goal_difference=2)
    prob_matrix = np.zeros((3, 3))
    prob_matrix[1, 1] = 0.4
    prob_matrix[1, 0] = 0.3
    prob_matrix[2, 1] = 0.3
    
    ep_matrix = get_expected_points_matrix(prob_matrix, rule, max_goals=2)
    opt_home, opt_away = find_optimal_prediction(ep_matrix)
    
    # 1-0 would give 0.3*3 + 0.3*1 + 0.4*0 = 1.2
    # 1-1 would give 0.4*3 + 0.3*0 + 0.3*0 = 1.2
    # 2-1 would give 0.3*3 + 0.3*1 + 0.4*0 = 1.2
    # Wait, let's make it unambiguous
    prob_matrix = np.zeros((3, 3))
    prob_matrix[1, 1] = 0.6
    prob_matrix[1, 0] = 0.4
    
    ep_matrix = get_expected_points_matrix(prob_matrix, rule, max_goals=2)
    opt_home, opt_away = find_optimal_prediction(ep_matrix)
    assert (opt_home, opt_away) == (1, 1)

def test_same_seed_produces_same_frequencies():
    matrix = generate_probability_matrix(1.5, 1.0, 1.0, 1.5)
    sim1 = simulate_matches(matrix, 1000, seed=42)
    sim2 = simulate_matches(matrix, 1000, seed=42)
    assert sim1 == sim2

def test_different_seeds_change_frequencies():
    matrix = generate_probability_matrix(1.5, 1.0, 1.0, 1.5)
    sim1 = simulate_matches(matrix, 1000, seed=42)
    sim2 = simulate_matches(matrix, 1000, seed=1337)
    assert sim1 != sim2

def test_invalid_simulation_count_is_rejected():
    matrix = generate_probability_matrix(1.5, 1.0, 1.0, 1.5)
    with pytest.raises(ValueError):
        simulate_matches(matrix, 0)
    with pytest.raises(ValueError):
        simulate_matches(matrix, -5)
