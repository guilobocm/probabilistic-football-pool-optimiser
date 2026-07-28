"""Player model — simulate player goals and assists from team goal totals."""

from pathlib import Path
from typing import Dict, List

import numpy as np
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class PlayerModel:
    def __init__(self, data_path: Path = PROJECT_ROOT / "data" / "players.yaml"):
        self.team_players: Dict[str, List[dict]] = {}
        if data_path.exists():
            with open(data_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                for player in data.get("players", []):
                    team = player["team"]
                    if team not in self.team_players:
                        self.team_players[team] = []
                    self.team_players[team].append(player)

        self.team_goal_distributions = {}
        self.team_assist_distributions = {}
        self.player_minutes = {}

        for team, players in self.team_players.items():
            names = []
            goal_probs = []
            assist_probs = []
            for player in players:
                names.append(player["name"])
                goal_probs.append(player.get("goalshare_pct", 0.1))
                assist_probs.append(player.get("assist_share_pct", 0.1))
                self.player_minutes[player["name"]] = player.get(
                    "expected_minutes",
                    90,
                )

            total_goals_share = sum(goal_probs)
            goal_names, normalised_goal_probs = list(names), list(goal_probs)
            if total_goals_share < 1.0:
                other_name = f"Other ({team})"
                goal_names.append(other_name)
                normalised_goal_probs.append(1.0 - total_goals_share)
                self.player_minutes[other_name] = 90
            elif total_goals_share > 1.0:
                normalised_goal_probs = [
                    probability / total_goals_share
                    for probability in normalised_goal_probs
                ]
            self.team_goal_distributions[team] = (
                goal_names,
                normalised_goal_probs,
            )

            total_assist_share = sum(assist_probs)
            assist_names, normalised_assist_probs = list(names), list(assist_probs)
            if total_assist_share < 1.0:
                assist_names.append(f"Other ({team})")
                normalised_assist_probs.append(1.0 - total_assist_share)
            elif total_assist_share > 1.0:
                normalised_assist_probs = [
                    probability / total_assist_share
                    for probability in normalised_assist_probs
                ]
            self.team_assist_distributions[team] = (
                assist_names,
                normalised_assist_probs,
            )

    def distribute_events(
        self,
        team: str,
        goals: int,
        rng: np.random.Generator,
    ) -> tuple[Dict[str, int], Dict[str, int]]:
        """Return goal and assist counts by player for one team performance."""
        goals_result = {}
        assists_result = {}
        if goals == 0:
            return goals_result, assists_result

        if team not in self.team_goal_distributions:
            goals_result[f"Other ({team})"] = goals
        else:
            goal_names, goal_probs = self.team_goal_distributions[team]
            goal_counts = rng.multinomial(goals, goal_probs)
            for name, count in zip(goal_names, goal_counts):
                if count > 0:
                    goals_result[name] = count

        assists = min(rng.poisson(0.8 * goals), goals)
        if assists > 0:
            if team not in self.team_assist_distributions:
                assists_result[f"Other ({team})"] = assists
            else:
                assist_names, assist_probs = self.team_assist_distributions[team]
                assist_counts = rng.multinomial(assists, assist_probs)
                for name, count in zip(assist_names, assist_counts):
                    if count > 0:
                        assists_result[name] = count

        return goals_result, assists_result
