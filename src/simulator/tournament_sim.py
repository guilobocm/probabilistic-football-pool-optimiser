"""
Tournament Simulator — Monte Carlo simulation of the entire World Cup.

Simulates 100K+ iterations of:
1. Group stage (all 36 matches per group)
2. Best third-place ranking
3. Round of 32 → Round of 16 → QF → SF → Final
4. Tracks marginal probabilities for each bonus question

Outputs:
- P(team wins group) for each of the 12 groups
- P(team reaches semifinals)
- P(team wins tournament)
- P(team has top scorer) — future extension
"""

from __future__ import annotations

import numpy as np
from collections import Counter, defaultdict
from dataclasses import dataclass

from src.model.team_strength import TeamStrength, estimate_lambdas
from src.simulator.annexe_c_official import get_annexe_c_mapping
from src.model.player_model import PlayerModel


@dataclass
class SimulationResults:
    """Aggregated results from Monte Carlo tournament simulation."""

    n_simulations: int
    group_winners: dict[str, dict[str, float]]  # {group: {team: P(1st)}}
    group_runners_up: dict[str, dict[str, float]]  # {group: {team: P(2nd)}}
    semifinalists: dict[str, float]  # {team: P(semifinal)}
    finalists: dict[str, float]  # {team: P(final)}
    champion: dict[str, float]  # {team: P(champion)}
    top_scorer: dict[str, float] = None  # {player: P(top scorer)}
    golden_boot_team: dict[str, float] = None  # {team: P(team has top scorer)}


class TournamentSimulator:
    """Monte Carlo simulator for the World Cup 2026."""

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

        # Build player -> team lookup for golden boot team aggregation
        self._player_team_lookup: dict[str, str] = {}
        for team, players in self.player_model.team_players.items():
            for p in players:
                self._player_team_lookup[p["name"]] = team

        # Pre-compute lambdas for all possible matchups to speed up simulation
        self._lambda_cache: dict[tuple[str, str], tuple[float, float]] = {}

    def _get_lambdas(self, team_a: str, team_b: str) -> tuple[float, float]:
        """Get cached Poisson lambdas for a matchup."""
        key = (team_a, team_b)
        if key not in self._lambda_cache:
            sa = self.strengths.get(team_a)
            sb = self.strengths.get(team_b)
            if sa is None or sb is None:
                # Fallback for unknown teams
                self._lambda_cache[key] = (1.0, 1.0)
            else:
                self._lambda_cache[key] = estimate_lambdas(sa, sb, self.avg_goals)
        return self._lambda_cache[key]

    def _simulate_match(
        self,
        team_a: str,
        team_b: str,
        rng: np.random.Generator,
        allow_draw: bool = True,
    ) -> tuple[int, int, str]:
        """
        Simulate a single match.

        Returns (goals_a, goals_b, winner)
        If allow_draw=False (knockout), simulates penalties.
        """
        la, lb = self._get_lambdas(team_a, team_b)
        goals_a = rng.poisson(la)
        goals_b = rng.poisson(lb)

        if goals_a > 0 and hasattr(self, "current_sim_player_goals"):
            dist_g, dist_a = self.player_model.distribute_events(team_a, goals_a, rng)
            for p, g in dist_g.items():
                self.current_sim_player_goals[p] += g
            for p, a in dist_a.items():
                self.current_sim_player_assists[p] += a
        if goals_b > 0 and hasattr(self, "current_sim_player_goals"):
            dist_g, dist_a = self.player_model.distribute_events(team_b, goals_b, rng)
            for p, g in dist_g.items():
                self.current_sim_player_goals[p] += g
            for p, a in dist_a.items():
                self.current_sim_player_assists[p] += a

        if not allow_draw and goals_a == goals_b:
            # Simulate penalties: roughly 50/50 with slight advantage to higher Elo
            elo_a = self.strengths.get(team_a, TeamStrength(team_a)).elo
            elo_b = self.strengths.get(team_b, TeamStrength(team_b)).elo
            p_a_wins_pens = 0.5 + 0.0002 * (elo_a - elo_b)
            p_a_wins_pens = max(0.35, min(0.65, p_a_wins_pens))

            if rng.random() < p_a_wins_pens:
                winner = team_a
            else:
                winner = team_b
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
        """
        Simulate a group of 4 teams (6 matches).

        Returns sorted list of (team, points, goal_diff, goals_scored) — 1st to 4th.
        """
        standings: dict[str, dict] = {
            team: {"pts": 0, "gf": 0, "ga": 0, "gd": 0} for team in group_teams
        }

        # Round-robin: each pair plays once
        for i in range(len(group_teams)):
            for j in range(i + 1, len(group_teams)):
                ta = group_teams[i]
                tb = group_teams[j]
                ga, gb, winner = self._simulate_match(ta, tb, rng, allow_draw=True)

                standings[ta]["gf"] += ga
                standings[ta]["ga"] += gb
                standings[ta]["gd"] += ga - gb
                standings[tb]["gf"] += gb
                standings[tb]["ga"] += ga
                standings[tb]["gd"] += gb - ga

                if winner == ta:
                    standings[ta]["pts"] += 3
                elif winner == tb:
                    standings[tb]["pts"] += 3
                else:
                    standings[ta]["pts"] += 1
                    standings[tb]["pts"] += 1

        # Sort: points desc, goal diff desc, goals scored desc, random noise desc
        sorted_teams = sorted(
            standings.items(),
            key=lambda x: (x[1]["pts"], x[1]["gd"], x[1]["gf"], rng.random()),
            reverse=True,
        )

        return [
            (team, data["pts"], data["gd"], data["gf"]) for team, data in sorted_teams
        ]

    def _select_best_thirds(
        self,
        all_thirds: list[tuple[str, int, int, int, str]],
        rng: np.random.Generator,
    ) -> list[str]:
        """
        Select 8 best third-placed teams from 12 groups.

        Input: list of (team, points, goal_diff, goals_scored, group_letter)
        Returns: list of 8 team names
        """
        sorted_thirds = sorted(
            all_thirds,
            key=lambda x: (
                x[1],
                x[2],
                x[3],
                rng.random(),
            ),  # points, goal diff, goals scored, random tiebreaker
            reverse=True,
        )
        return [t[0] for t in sorted_thirds[:8]]

    def simulate(
        self,
        n_simulations: int = 100_000,
        seed: int = 42,
    ) -> SimulationResults:
        """
        Run full tournament Monte Carlo simulation.
        """
        self.n_simulations = n_simulations
        self.rng = np.random.default_rng(seed=seed)

        # Load Annexe C
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

        # Counters
        group_winner_counts = {g: Counter() for g in self.groups}
        group_runner_up_counts = {g: Counter() for g in self.groups}
        semifinal_counts = Counter()
        finalist_counts = Counter()
        champion_counts = Counter()
        top_scorer_counts = Counter()
        golden_boot_team_counts = Counter()

        group_letters = sorted(self.groups.keys())

        for sim in range(n_simulations):
            self.current_sim_player_goals = defaultdict(int)
            self.current_sim_player_assists = defaultdict(int)
            # ============ GROUP STAGE ============
            group_standings: dict[str, list[tuple[str, int, int]]] = {}
            all_thirds: list[tuple[str, int, int, str]] = []

            for group_letter in group_letters:
                teams = self.groups[group_letter]
                standings = self._simulate_group(teams, self.rng)
                group_standings[group_letter] = standings

                # Track group winner
                group_winner_counts[group_letter][standings[0][0]] += 1
                group_runner_up_counts[group_letter][standings[1][0]] += 1

                # Third-place team
                if len(standings) >= 3:
                    third = standings[2]
                    all_thirds.append(
                        (third[0], third[1], third[2], third[3], group_letter)
                    )

            # ============ BEST THIRDS ============
            best_thirds = self._select_best_thirds(all_thirds, self.rng)

            # ============ KNOCKOUT STAGE ============
            # Retrieve specifically by group to ensure deterministic paths
            firsts = {g: group_standings[g][0][0] for g in group_letters}
            seconds = {g: group_standings[g][1][0] for g in group_letters}

            team_to_group = {}
            for g in group_letters:
                for t, _, _, _ in group_standings[g]:
                    team_to_group[t] = g

            # The 8 group winners that face third-placed teams according to FIFA Annexe C
            w_slots = ["A", "B", "D", "E", "G", "I", "K", "L"]
            t_groups = [team_to_group[t] for t in best_thirds]

            # Official FIFA Annexe C allocation for 3rd placed teams
            allocation_map = get_annexe_c_mapping(t_groups)

            # Map slots 1A, 1B, 1D, 1E, 1G, 1I, 1K, 1L to the designated third-placed teams
            # `thirds_dict` allows us to look up the Team object by group letter
            thirds_dict = {team_to_group[t]: t for t in best_thirds}
            matched_thirds = {}
            for slot_winner in w_slots:
                slot_id = f"1{slot_winner}"
                assigned_third_str = allocation_map[slot_id]  # e.g. "3E"
                assigned_group = assigned_third_str[1]
                matched_thirds[slot_winner] = thirds_dict[assigned_group]

            # R32 ordered to naturally feed into R16 matches:
            # R16 pairings are (89, 90), (91, 92), (93, 94), (95, 96)
            # Match 89: 74 vs 77
            # Match 90: 73 vs 75
            # Match 91: 76 vs 78
            # Match 92: 79 vs 80
            # Match 93: 83 vs 84
            # Match 94: 81 vs 82
            # Match 95: 86 vs 88
            # Match 96: 85 vs 87

            r32_matches = [
                # R16 Match 89
                (firsts["E"], matched_thirds["E"]),  # Match 74
                (firsts["I"], matched_thirds["I"]),  # Match 77
                # R16 Match 90
                (seconds["A"], seconds["B"]),  # Match 73
                (firsts["F"], seconds["C"]),  # Match 75
                # R16 Match 91
                (firsts["C"], seconds["F"]),  # Match 76
                (seconds["E"], seconds["I"]),  # Match 78
                # R16 Match 92
                (firsts["A"], matched_thirds["A"]),  # Match 79
                (firsts["L"], matched_thirds["L"]),  # Match 80
                # R16 Match 93
                (seconds["K"], seconds["L"]),  # Match 83
                (firsts["H"], seconds["J"]),  # Match 84
                # R16 Match 94
                (firsts["D"], matched_thirds["D"]),  # Match 81
                (firsts["G"], matched_thirds["G"]),  # Match 82
                # R16 Match 95
                (firsts["J"], seconds["H"]),  # Match 86
                (seconds["D"], seconds["G"]),  # Match 88
                # R16 Match 96
                (firsts["B"], matched_thirds["B"]),  # Match 85
                (firsts["K"], matched_thirds["K"]),  # Match 87
            ]

            # ============ ROUND OF 32 → ROUND OF 16 ============
            r16_winners = []
            for ta, tb in r32_matches:
                if ta in self.audit_teams:
                    self.opponent_tracker[ta]["R32"][tb] += 1
                if tb in self.audit_teams:
                    self.opponent_tracker[tb]["R32"][ta] += 1

                if ta == "TBD" or tb == "TBD":
                    r16_winners.append(ta if tb == "TBD" else tb)
                    continue
                _, _, winner = self._simulate_match(ta, tb, self.rng, allow_draw=False)
                r16_winners.append(winner)

            # ============ ROUND OF 16 → QUARTER FINALS ============
            qf_matches = [(r16_winners[i], r16_winners[i + 1]) for i in range(0, 16, 2)]
            qf_winners = []
            for ta, tb in qf_matches:
                if ta in self.audit_teams:
                    self.opponent_tracker[ta]["R16"][tb] += 1
                if tb in self.audit_teams:
                    self.opponent_tracker[tb]["R16"][ta] += 1

                _, _, winner = self._simulate_match(ta, tb, self.rng, allow_draw=False)
                qf_winners.append(winner)

            # ============ QUARTER FINALS → SEMI FINALS ============
            sf_matches = [(qf_winners[i], qf_winners[i + 1]) for i in range(0, 8, 2)]
            sf_winners = []
            for ta, tb in sf_matches:
                if ta in self.audit_teams:
                    self.opponent_tracker[ta]["QF"][tb] += 1
                if tb in self.audit_teams:
                    self.opponent_tracker[tb]["QF"][ta] += 1

                _, _, winner = self._simulate_match(ta, tb, self.rng, allow_draw=False)
                sf_winners.append(winner)

            # Track semifinalists (QF winners)
            for team in sf_winners:
                semifinal_counts[team] += 1

            # ============ SEMI FINALS → FINAL ============
            final_match = [
                (sf_winners[0], sf_winners[1]),
                (sf_winners[2], sf_winners[3]),
            ]
            finalists = []
            for ta, tb in final_match:
                if ta in self.audit_teams:
                    self.opponent_tracker[ta]["SF"][tb] += 1
                if tb in self.audit_teams:
                    self.opponent_tracker[tb]["SF"][ta] += 1

                _, _, winner = self._simulate_match(ta, tb, self.rng, allow_draw=False)
                finalists.append(winner)

            for f in finalists:
                finalist_counts[f] += 1

            _, _, champion = self._simulate_match(
                finalists[0], finalists[1], self.rng, allow_draw=False
            )
            champion_counts[champion] += 1

            if self.current_sim_player_goals:
                # === INDIVIDUAL TOP SCORER (excludes Outros) ===
                valid_players = {
                    p: g
                    for p, g in self.current_sim_player_goals.items()
                    if not p.startswith("Outros")
                }
                if valid_players:
                    top_players_sorted = sorted(
                        valid_players.keys(),
                        key=lambda p: (
                            valid_players[p],
                            self.current_sim_player_assists.get(p, 0),
                            -self.player_model.player_minutes.get(p, 90),
                            self.rng.random(),
                        ),
                        reverse=True,
                    )
                    top_player = top_players_sorted[0]
                    top_scorer_counts[top_player] += 1

                    # === GOLDEN BOOT TEAM (derived from the same individual winner) ===
                    # The bolão asks "which TEAM will have the top scorer?"
                    # This must be the team of the actual individual winner,
                    # not a separate race where "Outros (Morocco)" competes as one blob.
                    team_of_winner = self._player_team_lookup.get(top_player, "Unknown")
                    golden_boot_team_counts[team_of_winner] += 1

        # ============ AGGREGATE RESULTS ============
        n = n_simulations

        group_winners = {
            g: {team: count / n for team, count in counts.items()}
            for g, counts in group_winner_counts.items()
        }
        group_runners = {
            g: {team: count / n for team, count in counts.items()}
            for g, counts in group_runner_up_counts.items()
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
            team: count / n for team, count in golden_boot_team_counts.most_common()
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

    def print_audit_report(self):
        print("\n🔎 AUDITORIA DE CAMINHOS (Opponent Tracker)")
        print(
            "   Nota: Terceiros alocados usando a tabela oficial Annexe C (495 combinações)."
        )
        for team in self.audit_teams:
            print(f"\n   [{team}]")
            for phase in ["R32", "R16", "QF", "SF"]:
                counts = self.opponent_tracker[team][phase]
                if counts:
                    # Imprimir toda a lista ordenada para provar ausência de viés
                    opponents = counts.most_common()
                    print(f"      {phase}:")
                    for opp, c in opponents:
                        print(f"         - {opp}: {c / self.n_simulations * 100:.1f}%")
                else:
                    print(f"      {phase}: N/A")
