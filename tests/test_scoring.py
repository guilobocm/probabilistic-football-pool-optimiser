import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.optimizer.scoring_rules import calculate_points, TOURNAMENT_RULE

# Use rule loaded from config
RULE = TOURNAMENT_RULE


def test_exact_score():
    """Exact score hit always yields 4 points."""
    assert calculate_points((1, 0), (1, 0), RULE) == 4
    assert calculate_points((2, 1), (2, 1), RULE) == 4
    assert calculate_points((0, 0), (0, 0), RULE) == 4
    assert calculate_points((1, 1), (1, 1), RULE) == 4


def test_win_goal_difference():
    """Correct goal difference in a win, but wrong scoreline, yields 3 points."""
    assert calculate_points((2, 1), (1, 0), RULE) == 3
    assert calculate_points((3, 1), (2, 0), RULE) == 3
    assert calculate_points((0, 2), (1, 3), RULE) == 3


def test_win_trend_only():
    """Correct trend for a win yields 2 points."""
    assert calculate_points((2, 1), (2, 0), RULE) == 2  # Errou diferença
    assert calculate_points((3, 0), (1, 0), RULE) == 2  # Errou diferença
    assert calculate_points((0, 1), (0, 3), RULE) == 2  # Errou diferença


def test_draw_trend():
    """Correct trend for a draw (wrong scoreline) yields 3 points."""
    assert calculate_points((1, 1), (0, 0), RULE) == 3
    assert calculate_points((2, 2), (1, 1), RULE) == 3
    assert calculate_points((0, 0), (1, 1), RULE) == 3


def test_miss():
    """Missing the trend zeroes the points."""
    assert calculate_points((1, 0), (0, 1), RULE) == 0
    assert calculate_points((1, 1), (1, 0), RULE) == 0
    assert calculate_points((0, 1), (0, 0), RULE) == 0


def test_anomalies_expected_value_logic():
    """Testes específicos para garantir ausência de bugs e comprovar a lógica."""
    assert calculate_points((2, 1), (2, 1), RULE) == 4
    assert calculate_points((1, 0), (2, 1), RULE) == 3
    assert calculate_points((2, 0), (2, 1), RULE) == 2
    # Correction: The draw yields 3 points for the trend, making 0-0 more valuable if result is 1-1
    assert calculate_points((0, 0), (1, 1), RULE) == 3
    assert calculate_points((1, 1), (1, 1), RULE) == 4
    assert calculate_points((1, 2), (1, 2), RULE) == 4
