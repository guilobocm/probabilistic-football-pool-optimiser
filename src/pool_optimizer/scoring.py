from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ScoringRule:
    exact_score: int
    correct_outcome: int
    correct_goal_difference: int

    def calculate_points(
        self, predicted: Tuple[int, int], actual: Tuple[int, int]
    ) -> int:
        p_home, p_away = predicted
        a_home, a_away = actual

        if predicted == actual:
            return self.exact_score

        p_diff = p_home - p_away
        a_diff = a_home - a_away

        # Outcome: 1 for home win, 0 for draw, -1 for away win
        p_outcome = 1 if p_diff > 0 else (0 if p_diff == 0 else -1)
        a_outcome = 1 if a_diff > 0 else (0 if a_diff == 0 else -1)

        if p_outcome == a_outcome:
            if p_diff == a_diff:
                return self.correct_goal_difference
            return self.correct_outcome

        return 0
