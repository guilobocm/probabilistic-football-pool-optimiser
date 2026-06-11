"""
Player Model — Simulates player goals and assists given team goals.
"""

from typing import Dict, List
import yaml
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class PlayerModel:
    def __init__(self, data_path: Path = PROJECT_ROOT / "data" / "players.yaml"):
        self.team_players: Dict[str, List[dict]] = {}
        if data_path.exists():
            with open(data_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                for p in data.get("players", []):
                    team = p["team"]
                    if team not in self.team_players:
                        self.team_players[team] = []
                    self.team_players[team].append(p)
                    
        # Normalize shares
        self.team_goal_distributions = {}
        self.team_assist_distributions = {}
        self.player_minutes = {}
        
        for team, players in self.team_players.items():
            names = []
            goal_probs = []
            assist_probs = []
            for p in players:
                names.append(p["name"])
                goal_probs.append(p.get("goalshare_pct", 0.1))
                assist_probs.append(p.get("assist_share_pct", 0.1))
                self.player_minutes[p["name"]] = p.get("expected_minutes", 90)
                
            # Normalize goal probs
            total_g = sum(goal_probs)
            names_g, probs_g = list(names), list(goal_probs)
            if total_g < 1.0:
                names_g.append(f"Outros ({team})")
                probs_g.append(1.0 - total_g)
                self.player_minutes[f"Outros ({team})"] = 90
            elif total_g > 1.0:
                probs_g = [p / total_g for p in probs_g]
            self.team_goal_distributions[team] = (names_g, probs_g)
            
            # Normalize assist probs
            total_a = sum(assist_probs)
            names_a, probs_a = list(names), list(assist_probs)
            if total_a < 1.0:
                names_a.append(f"Outros ({team})")
                probs_a.append(1.0 - total_a)
            elif total_a > 1.0:
                probs_a = [p / total_a for p in probs_a]
            self.team_assist_distributions[team] = (names_a, probs_a)

    def distribute_events(self, team: str, goals: int, rng: np.random.Generator) -> tuple[Dict[str, int], Dict[str, int]]:
        """
        Returns (goal_dict, assist_dict).
        Assists are generally ~0.8 * goals.
        """
        goals_res = {}
        assists_res = {}
        if goals == 0:
            return goals_res, assists_res
            
        # Distribute Goals
        if team not in self.team_goal_distributions:
            goals_res[f"Outros ({team})"] = goals
        else:
            names_g, probs_g = self.team_goal_distributions[team]
            counts_g = rng.multinomial(goals, probs_g)
            for name, count in zip(names_g, counts_g):
                if count > 0:
                    goals_res[name] = count
                    
        # Distribute Assists
        assists = rng.poisson(0.8 * goals)
        # Cap assists so it doesn't exceed goals wildly
        assists = min(assists, goals)
        
        if assists > 0:
            if team not in self.team_assist_distributions:
                assists_res[f"Outros ({team})"] = assists
            else:
                names_a, probs_a = self.team_assist_distributions[team]
                counts_a = rng.multinomial(assists, probs_a)
                for name, count in zip(names_a, counts_a):
                    if count > 0:
                        assists_res[name] = count
                        
        return goals_res, assists_res
