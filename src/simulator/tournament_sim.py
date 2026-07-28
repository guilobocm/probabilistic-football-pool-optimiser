"""
Tournament Simulator — Monte Carlo simulation of the FIFA World Cup 2026.

Simulates 100,000 or more iterations of:
1. The full group stage
2. Ranking of the best third-placed teams
3. Round of 32 through to the final
4. Marginal probabilities for each bonus question

Outputs include:
- P(team wins group) for each of the 12 groups
- P(team reaches the semi-finals)
- P(team reaches the final)
- P(team wins the tournament)
- P(player wins the Golden Boot)
- P(team is represented by the Golden Boot winner)
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

import numpy as np

from src.model.player_model import PlayerModel
from src.model.team_strength import TeamStrength, estimate_lambdas
from src.simulator.annexe_c_official import get_annexe_c_mapping


@dataclass
class SimulationResults:
    """Aggregated results from Monte Carlo tournament simulation."""

    n_simulations: int
    group_winners: dict[str, dict[str, float]]
    group_runners_up: dict[str, dict[str, float]]
    semifinalists: dict[str, float]
    finalists: dict[str, float]
    champion: dict[str, float]
    top_scorer: dict[str, float] | None = None
    golden_boot_team: dict[str, float] | None = None


class TournamentSimulator:
    """Monte Carlo simulator for the FIFA World Cup 2026."""

    def __init__(
        self,
        groups: dict[str, list[str]],
        strengths: dict[str, TeamStrength],
        rho: float = -0.10,
        avg_goals: float = 2.65,
    ):
        self.groups = groups
        self.strengths = strengths
        self.rho = rho
        self.avg_goals = avg_goals

        self.player_model = PlayerModel()

        self._player_team_lookup: dict[str, str] = {}
        for team, players in self.player_model.team_players.items():
            for player in players:
                self._player_team_lookup[player["name"]] = team

        self._lambda_cache: dict[tuple[str, str], tuple[float, float]] = {}

    def _get_lambdas(self, team_a: str, team_b: str) -> tuple[float, float]:
        """Return cached Poisson lambdas for a match-up."""
        key = (team_a, team_b)
        if key not in self._lambda_cache:
            strength_a = self.strengths.get(team_a)
            strength_b = self.strengths.get(team_b)
            if strength_a is None or strength_b is None:
                self._lambda_cache[key] = (1.0, 1.0)
            else:
                self._lambda_cache[key] = estimate_lambdas(
                    strength_a,
                    strength_b,
                    self.avg_goals,
                )
        return self._lambda_cache[key]

    def _simulate_match(
        self,
        team_a: str,
        team_b: str,
        rng: np.random.Generator,
        allow_draw: bool = True,
    ) -> tuple[int, int, str]:
        """Simulate one match and return both goal counts and the winner."""
        lambda_a, lambda_b = self._get_lambdas(team_a, team_b)
        goals_a = rng.poisson(lambda_a)
        goals_b = rng.poisson(lambda_b)

        if goals_a > 0 and hasattr(self, "current_sim_player_goals"):
            distributed_goals, distributed_assists = self.player_model.distribute_events(
                team_a,
                goals_a,
                rng,
            )
            for player, count in distributed_goals.items():
                self.current_sim_player_goals[player] += count
            for player, count in distributed_assists.items():
                self.current_sim_player_assists[player] += count

        if goals_b > 0 and hasattr(self, "current_sim_player_goals"):
            distributed_goals, distributed_assists = self.player_model.distribute_events(
                team_b,
                goals_b,
                rng,
            )
            for player, count in distributed_goals.items():
                self.current_sim_player_goals[player] += count
            for player, count in distributed_assists.items():
                self.current_sim_player_assists[player] += count

        if not allow_draw and goals_a == goals_b:
            elo_a = self.strengths.get(team_a, TeamStrength(team_a)).elo
            elo_b = self.strengths.get(team_b, TeamStrength(team_b)).elo
            probability_a_wins_pens = 0.5 + 0.0002 * (elo_a - elo_b)
            probability_a_wins_pens = max(0.35, min(0.65, probability_a_wins_pens))
            winner = team_a if rng.random() < probability_a_wins_pens else team_b
            return goals_a, goals_b, winner

        if goals_a > goals_b:
            winner = team_a
        elif goals_b > goals_a:
            winner = team_b
        else:
            winner = "draw"

        return goals_a, goals_b, winner

    def _simulate_group(
        self,
        group_teams: list[str],
        rng: np.random.Generator,
    ) -> list[tuple[str, int, int, int]]:
        """Simulate a four-team group and return its ordered standings."""
        standings: dict[str, dict] = {
            team: {"pts": 0, "gf": 0, "ga": 0, "gd": 0}
            for team in group_teams
        }

        for i in range(len(group_teams)):
            for j in range(i + 1, len(group_teams)):
                team_a = group_teams[i]
                team_b = group_teams[j]
                goals_a, goals_b, winner = self._simulate_match(
                    team_a,
                    team_b,
                    rng,
                    allow_draw=True,
                )

                standings[team_a]["gf"] += goals_a
                standings[team_a]["ga"] += goals_b
                standings[team_a]["gd"] += goals_a - goals_b
                standings[team_b]["gf"] += goals_b
                standings[team_b]["ga"] += goals_a
                standings[team_b]["gd"] += goals_b - goals_a

                if winner == team_a:
                    standings[team_a]["pts"] += 3
                elif winner == team_b:
                    standings[team_b]["pts"] += 3
                else:
                    standings[team_a]["pts"] += 1
                    standings[team_b]["pts"] += 1

        sorted_teams = sorted(
            standings.items(),
            key=lambda item: (
                item[1]["pts"],
                item[1]["gd"],
                item[1]["gf"],
                rng.random(),
            ),
            reverse=True,
        )

        return [
            (team, data["pts"], data["gd"], data["gf"])
            for team, data in sorted_teams
        ]

    def _select_best_thirds(
        self,
        all_thirds: list[tuple[str, int, int, int, str]],
        rng: np.random.Generator,
    ) -> list[str]:
        """Select the eight best third-placed teams from the 12 groups."""
        sorted_thirds = sorted(
            all_thirds,
            key=lambda item: (item[1], item[2], item[3], rng.random()),
            reverse=True,
        )
        return [item[0] for item in sorted_thirds[:8]]

    def simulate(
        self,
        n_simulations: int = 100_000,
        seed: int = 42,
    ) -> SimulationResults:
        """Run the full-tournament Monte Carlo simulation."""
        self.n_simulations = n_simulations
        self.rng = np.random.default_rng(seed=seed)

        if not hasattr(self, "audit_teams"):
            self.audit_teams = [
                "Portugal",
                "Brazil",
                "Argentina",
                "France",
                "Spain",
                "England",
            ]
        self.opponent_tracker = {
            team: {phase: Counter() for phase in ["R32", "R16", "QF", "SF"]}
            for team in self.audit_teams
        }

        group_winner_counts = {group: Counter() for group in self.groups}
        group_runner_up_counts = {group: Counter() for group in self.groups}
        semifinal_counts = Counter()
        finalist_counts = Counter()
        champion_counts = Counter()
        top_scorer_counts = Counter()
        golden_boot_team_counts = Counter()

        group_letters = sorted(self.groups.keys())

        for _ in range(n_simulations):
            self.current_sim_player_goals = defaultdict(int)
            self.current_sim_player_assists = defaultdict(int)

            group_standings: dict[str, list[tuple[str, int, int, int]]] = {}
            all_thirds: list[tuple[str, int, int, int, str]] = []

            for group_letter in group_letters:
                teams = self.groups[group_letter]
                standings = self._simulate_group(teams, self.rng)
                group_standings[group_letter] = standings

                group_winner_counts[group_letter][standings[0][0]] += 1
                group_runner_up_counts[group_letter][standings[1][0]] += 1

                if len(standings) >= 3:
                    third = standings[2]
                    all_thirds.append(
                        (third[0], third[1], third[2], third[3], group_letter)
                    )

            best_thirds = self._select_best_thirds(all_thirds, self.rng)

            firsts = {group: group_standings[group][0][0] for group in group_letters}
            seconds = {group: group_standings[group][1][0] for group in group_letters}

            team_to_group = {}
            for group in group_letters:
                for team, _, _, _ in group_standings[group]:
                    team_to_group[team] = group

            winner_slots = ["A", "B", "D", "E", "G", "I", "K", "L"]
            third_groups = [team_to_group[team] for team in best_thirds]
            allocation_map = get_annexe_c_mapping(third_groups)
            thirds_by_group = {team_to_group[team]: team for team in best_thirds}

            matched_thirds = {}
            for winner_group in winner_slots:
                slot_id = f"1{winner_group}"
                assigned_third = allocation_map[slot_id]
                assigned_group = assigned_third[1]
                matched_thirds[winner_group] = thirds_by_group[assigned_group]

            r32_matches = [
                (firsts["E"], matched_thirds["E"]),
                (firsts["I"], matched_thirds["I"]),
                (seconds["A"], seconds["B"]),
                (firsts["F"], seconds["C"]),
                (firsts["C"], seconds["F"]),
                (seconds["E"], seconds["I"]),
                (firsts["A"], matched_thirds["A"]),
                (firsts["L"], matched_thirds["L"]),
                (seconds["K"], seconds["L"]),
                (firsts["H"], seconds["J"]),
                (firsts["D"], matched_thirds["D"]),
                (firsts["G"], matched_thirds["G"]),
                (firsts["J"], seconds["H"]),
                (seconds["D"], seconds["G"]),
                (firsts["B"], matched_thirds["B"]),
                (firsts["K"], matched_thirds["K"]),
            ]

            r16_winners = []
            for team_a, team_b in r32_matches:
                if team_a in self.audit_teams:
                    self.opponent_tracker[team_a]["R32"][team_b] += 1
                if team_b in self.audit_teams:
                    self.opponent_tracker[team_b]["R32"][team_a] += 1

                if team_a == "TBD" or team_b == "TBD":
                    r16_winners.append(team_a if team_b == "TBD" else team_b)
                    continue
                _, _, winner = self._simulate_match(
                    team_a,
                    team_b,
                    self.rng,
                    allow_draw=False,
                )
                r16_winners.append(winner)

            qf_matches = [
                (r16_winners[i], r16_winners[i + 1])
                for i in range(0, 16, 2)
            ]
            qf_winners = []
            for team_a, team_b in qf_matches:
                if team_a in self.audit_teams:
                    self.opponent_tracker[team_a]["R16"][team_b] += 1
                if team_b in self.audit_teams:
                    self.opponent_tracker[team_b]["R16"][team_a] += 1
                _, _, winner = self._simulate_match(
                    team_a,
                    team_b,
                    self.rng,
                    allow_draw=False,
                )
                qf_winners.append(winner)

            sf_matches = [
                (qf_winners[i], qf_winners[i + 1])
                for i in range(0, 8, 2)
            ]
            sf_winners = []
            for team_a, team_b in sf_matches:
                if team_a in self.audit_teams:
                    self.opponent_tracker[team_a]["QF"][team_b] += 1
                if team_b in self.audit_teams:
                    self.opponent_tracker[team_b]["QF"][team_a] += 1
                _, _, winner = self._simulate_match(
                    team_a,
                    team_b,
                    self.rng,
                    allow_draw=False,
                )
                sf_winners.append(winner)

            for team in sf_winners:
                semifinal_counts[team] += 1

            final_matches = [
                (sf_winners[0], sf_winners[1]),
                (sf_winners[2], sf_winners[3]),
            ]
            finalists = []
            for team_a, team_b in final_matches:
                if team_a in self.audit_teams:
                    self.opponent_tracker[team_a]["SF"][team_b] += 1
                if team_b in self.audit_teams:
                    self.opponent_tracker[team_b]["SF"][team_a] += 1
                _, _, winner = self._simulate_match(
                    team_a,
                    team_b,
                    self.rng,
                    allow_draw=False,
                )
                finalists.append(winner)

            for team in finalists:
                finalist_counts[team] += 1

            _, _, champion = self._simulate_match(
                finalists[0],
                finalists[1],
                self.rng,
                allow_draw=False,
            )
            champion_counts[champion] += 1

            if self.current_sim_player_goals:
                valid_players = {
                    player: goals
                    for player, goals in self.current_sim_player_goals.items()
                    if not player.startswith("Other")
                }
                if valid_players:
                    top_players_sorted = sorted(
                        valid_players,
                        key=lambda player: (
                            valid_players[player],
                            self.current_sim_player_assists.get(player, 0),
                            -self.player_model.player_minutes.get(player, 90),
                            self.rng.random(),
                        ),
                        reverse=True,
                    )
                    top_player = top_players_sorted[0]
                    top_scorer_counts[top_player] += 1
                    team_of_winner = self._player_team_lookup.get(
                        top_player,
                        "Unknown",
                    )
                    golden_boot_team_counts[team_of_winner] += 1

        n = n_simulations
        group_winners = {
            group: {team: count / n for team, count in counts.items()}
            for group, counts in group_winner_counts.items()
        }
        group_runners = {
            group: {team: count / n for team, count in counts.items()}
            for group, counts in group_runner_up_counts.items()
        }
        semifinalists = {
            team: count / n for team, count in semifinal_counts.most_common()
        }
        finalists_probs = {
            team: count / n for team, count in finalist_counts.most_common()
        }
        champion_probs = {
            team: count / n for team, count in champion_counts.most_common()
        }
        top_scorer_probs = {
            player: count / n for player, count in top_scorer_counts.most_common()
        }
        golden_boot_team_probs = {
            team: count / n
            for team, count in golden_boot_team_counts.most_common()
        }

        return SimulationResults(
            n_simulations=n,
            group_winners=group_winners,
            group_runners_up=group_runners,
            semifinalists=semifinalists,
            finalists=finalists_probs,
            champion=champion_probs,
            top_scorer=top_scorer_probs,
            golden_boot_team=golden_boot_team_probs,
        )

    def print_audit_report(self) -> None:
        """Print observed knockout-opponent frequencies for selected teams."""
        print("\n🔎 BRACKET-PATH AUDIT (opponent tracker)")
        print(
            "   Note: third-placed teams were allocated using the official "
            "Annexe C table with 495 combinations."
        )
        for team in self.audit_teams:
            print(f"\n   [{team}]")
            for phase in ["R32", "R16", "QF", "SF"]:
                counts = self.opponent_tracker[team][phase]
                if counts:
                    opponents = counts.most_common()
                    print(f"      {phase}:")
                    for opponent, count in opponents:
                        percentage = count / self.n_simulations * 100
                        print(f"         - {opponent}: {percentage:.1f}%")
                else:
                    print(f"      {phase}: N/A")
