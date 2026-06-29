"""
Monte Carlo Tournament Simulation for World Cup 2026

Simulates the entire tournament 10,000 times to calculate:
- Each team's probability of reaching each stage
- Each team's probability of winning the tournament
- Most likely final matchups

Important: Betting/odds only apply to 90-min regular time.
Extra time and penalties are separate from the 90-min prediction.
Knockout matches: if draw after 90 min → extra time → penalties.
"""

import random
import math
from typing import Dict, List, Optional, Tuple
from collections import Counter

from predictor import MatchPredictor


class MonteCarloSimulator:
    """
    Monte Carlo simulation of the full 2026 World Cup tournament.
    Uses the fast ELO prediction engine for match-by-match simulation.
    """

    # 2026 WC: 12 groups A-L, each with 4 teams
    # 32 teams advance: 12 group winners + 12 runners-up + 8 best 3rd place
    NUM_SIMULATIONS = 10000

    def __init__(self, predictor: MatchPredictor, teams_data: Dict[str, Dict]):
        self.predictor = predictor
        self.teams_data = teams_data
        self.results: Dict = {}

    def _simulate_match(self, team1_code: str, team2_code: str, stage: str = "group") -> Tuple[int, int]:
        """
        Simulate a single 90-minute match using fast ELO prediction.
        Returns (score1, score2) for regular time only.
        """
        t1 = self.teams_data.get(team1_code, {"code": team1_code, "elo_rating": 1800, "fifa_rank": 30})
        t2 = self.teams_data.get(team2_code, {"code": team2_code, "elo_rating": 1800, "fifa_rank": 30})

        pred = self.predictor.predict_match_fast(t1, t2, stage=stage)

        home_prob = pred["home_win_prob"] / 100.0
        draw_prob = pred["draw_prob"] / 100.0
        away_prob = pred["away_win_prob"] / 100.0

        r = random.random()
        if r < home_prob:
            winner = "home"
        elif r < home_prob + draw_prob:
            winner = "draw"
        else:
            winner = "away"

        eg_home = pred["expected_goals_home"]
        eg_away = pred["expected_goals_away"]

        score1 = self._poisson_sample(eg_home)
        score2 = self._poisson_sample(eg_away)

        # Ensure result matches sampled outcome
        if winner == "home" and score1 <= score2:
            diff = score2 - score1 + 1
            score1 += diff
        elif winner == "away" and score2 <= score1:
            diff = score1 - score2 + 1
            score2 += diff
        elif winner == "draw" and score1 != score2:
            avg = (score1 + score2) // 2
            score1 = avg
            score2 = avg

        return score1, score2

    def _simulate_extra_time(self, team1_code: str, team2_code: str) -> Tuple[str, int, int]:
        """
        Simulate extra time (2x15 min) after a 90-min draw in knockout.
        Extra time uses reduced expected goals (~30 min = 1/3 of 90 min).
        Extra time CANNOT end in a draw — if still level, go to penalties.
        Returns (winner_code, et_score1, et_score2).
        """
        t1 = self.teams_data.get(team1_code, {"code": team1_code, "elo_rating": 1800, "fifa_rank": 30})
        t2 = self.teams_data.get(team2_code, {"code": team2_code, "elo_rating": 1800, "fifa_rank": 30})

        pred = self.predictor.predict_match_fast(t1, t2, stage=stage)

        # Extra time is ~1/3 of normal time, reduce expected goals proportionally
        eg_home = pred["expected_goals_home"] * 0.35
        eg_away = pred["expected_goals_away"] * 0.35

        # Sample extra time goals
        et1 = self._poisson_sample(eg_home)
        et2 = self._poisson_sample(eg_home)

        if et1 > et2:
            return team1_code, et1, et2
        elif et2 > et1:
            return team2_code, et1, et2
        else:
            # Still level after extra time → penalties
            winner = self._simulate_penalties(team1_code, team2_code)
            return winner, et1, et2

    def _simulate_penalties(self, team1_code: str, team2_code: str) -> str:
        """
        Simulate penalty shootout.
        Stronger team has advantage: ~55-60% win rate based on ELO and experience.
        """
        t1 = self.teams_data.get(team1_code, {"code": team1_code, "elo_rating": 1800})
        t2 = self.teams_data.get(team2_code, {"code": team2_code, "elo_rating": 1800})

        elo1 = t1.get("elo_rating", 1800)
        elo2 = t2.get("elo_rating", 1800)
        elo_diff = elo1 - elo2

        # Stronger team wins ~55-60% of shootouts, not 50/50
        # Base: 0.50, plus ELO-adjusted bonus
        team1_win_prob = 0.50 + 0.08 * (elo_diff / 400.0)
        team1_win_prob = max(0.35, min(0.65, team1_win_prob))

        # Simulate best-of-5 then sudden death
        goals1 = 0
        goals2 = 0

        # Best of 5 rounds
        for _ in range(5):
            # Each kick: ~75% conversion rate, better team slightly higher
            kick_prob1 = 0.75 + 0.02 * (elo_diff / 400.0)
            kick_prob2 = 0.75 - 0.02 * (elo_diff / 400.0)
            if random.random() < kick_prob1:
                goals1 += 1
            if random.random() < kick_prob2:
                goals2 += 1

        # Check if decided
        if goals1 != goals2:
            return team1_code if goals1 > goals2 else team2_code

        # Sudden death
        while True:
            sd1 = random.random() < (0.75 + 0.02 * (elo_diff / 400.0))
            sd2 = random.random() < (0.75 - 0.02 * (elo_diff / 400.0))
            if sd1 and not sd2:
                return team1_code
            elif sd2 and not sd1:
                return team2_code
            # Both score or both miss → continue

    @staticmethod
    def _poisson_sample(lam: float) -> int:
        """Fast Poisson random sampling without numpy."""
        if lam < 0.5:
            L = math.exp(-lam)
            k = 0
            p = 1.0
            while True:
                k += 1
                p *= random.random()
                if p < L:
                    return k - 1
        else:
            L = math.exp(-lam)
            k = 0
            p = 1.0
            while p > L:
                k += 1
                p *= random.random()
            return k - 1

    def _simulate_group_stage(self, groups: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
        """
        Simulate all group stage matches.
        Returns group standings for each group.
        """
        group_results = {}

        for group_name, team_codes in groups.items():
            standings = {code: {"code": code, "played": 0, "won": 0, "drawn": 0, "lost": 0,
                                "goals_for": 0, "goals_against": 0, "points": 0}
                        for code in team_codes}

            for i in range(len(team_codes)):
                for j in range(i + 1, len(team_codes)):
                    t1 = team_codes[i]
                    t2 = team_codes[j]
                    s1, s2 = self._simulate_match(t1, t2, stage="group")

                    standings[t1]["played"] += 1
                    standings[t2]["played"] += 1
                    standings[t1]["goals_for"] += s1
                    standings[t1]["goals_against"] += s2
                    standings[t2]["goals_for"] += s2
                    standings[t2]["goals_against"] += s1

                    if s1 > s2:
                        standings[t1]["won"] += 1
                        standings[t1]["points"] += 3
                        standings[t2]["lost"] += 1
                    elif s1 == s2:
                        standings[t1]["drawn"] += 1
                        standings[t1]["points"] += 1
                        standings[t2]["drawn"] += 1
                        standings[t2]["points"] += 1
                    else:
                        standings[t2]["won"] += 1
                        standings[t2]["points"] += 3
                        standings[t1]["lost"] += 1

            sorted_teams = sorted(standings.values(),
                                  key=lambda x: (-x["points"],
                                                -(x["goals_for"] - x["goals_against"]),
                                                -x["goals_for"]))
            group_results[group_name] = sorted_teams

        return group_results

    def _select_best_third_place(self, group_results: Dict[str, List[Dict]], num: int = 8) -> List[str]:
        """Select the 8 best third-place teams from 12 groups."""
        third_place_teams = []
        for group_name, standings in group_results.items():
            if len(standings) >= 3:
                third = standings[2]
                third_place_teams.append(third)

        sorted_third = sorted(third_place_teams,
                              key=lambda x: (-x["points"],
                                            -(x["goals_for"] - x["goals_against"]),
                                            -x["goals_for"]))

        return [t["code"] for t in sorted_third[:num]]

    def _build_round32_bracket(self, group_winners: Dict[str, str],
                                 group_runners_up: Dict[str, str],
                                 best_third: List[str]) -> List[Tuple[str, str]]:
        """
        Build the Round of 32 bracket per FIFA 2026 World Cup format.

        12 groups A-L. Top 2 from each (24) + 8 best 3rd place = 32 teams.
        The bracket defines which group winners face which 3rd-place teams,
        and which runners-up face each other.

        Matchups (based on FIFA official bracket):
          M49: 1A vs 3B/C/D     M50: 1B vs 3A/C/D
          M51: 1C vs 3D/E/F     M52: 1D vs 3A/B/C
          M53: 1E vs 3F/G/H     M54: 1F vs 3E/G/H
          M55: 1G vs 3E/F/H     M56: 1H vs 3G/H/I
          M57: 1I vs 3H/I/J     M58: 1J vs 3I/J/K
          M59: 1K vs 3J/K/L     M60: 1L vs 3K/L/A
          M61: 2A vs 2B          M62: 2C vs 2D
          M63: 2E vs 2F          M64: 2G vs 2H

        For 3rd-place matchups: pick the best available 3rd-place team
        from the eligible groups.
        """
        # All 3rd-place teams ranked by performance
        third_ranked = list(best_third)  # Already sorted by points/GD/GF

        # Helper: find best 3rd-place team from eligible groups
        def pick_third(eligible_groups: List[str]) -> Optional[str]:
            for code in third_ranked:
                # Find which group this team came from
                for g in eligible_groups:
                    if g in self._third_place_by_group and self._third_place_by_group[g] == code:
                        return code
            # Fallback: pick any available
            for code in third_ranked:
                if code in self._used_third:
                    continue
                return code
            return None

        matchups = []

        # M49-M60: Group winners vs 3rd-place teams
        winner_vs_third = [
            ("A", ["B", "C", "D"]),   # M49: 1A vs 3B/C/D
            ("B", ["A", "C", "D"]),   # M50: 1B vs 3A/C/D
            ("C", ["D", "E", "F"]),   # M51: 1C vs 3D/E/F
            ("D", ["A", "B", "C"]),   # M52: 1D vs 3A/B/C
            ("E", ["F", "G", "H"]),   # M53: 1E vs 3F/G/H
            ("F", ["E", "G", "H"]),   # M54: 1F vs 3E/G/H
            ("G", ["E", "F", "H"]),   # M55: 1G vs 3E/F/H
            ("H", ["G", "H", "I"]),   # M56: 1H vs 3G/H/I
            ("I", ["H", "I", "J"]),   # M57: 1I vs 3H/I/J
            ("J", ["I", "J", "K"]),   # M58: 1J vs 3I/J/K
            ("K", ["J", "K", "L"]),   # M59: 1K vs 3J/K/L
            ("L", ["K", "L", "A"]),   # M60: 1L vs 3K/L/A
        ]

        self._used_third = set()

        for winner_group, eligible in winner_vs_third:
            t1 = group_winners.get(winner_group)
            if not t1:
                continue
            t2 = pick_third(eligible)
            if t2:
                self._used_third.add(t2)
            matchups.append((t1, t2))

        # M61-M64: Runners-up vs runners-up (remaining groups I-L)
        # Also need 2I vs 2J, 2K vs 2L for groups not covered above
        runner_up_matchups = [
            ("A", "B"),   # M61: 2A vs 2B
            ("C", "D"),   # M62: 2C vs 2D
            ("E", "F"),   # M63: 2E vs 2F
            ("G", "H"),   # M64: 2G vs 2H
        ]

        for g1, g2 in runner_up_matchups:
            t1 = group_runners_up.get(g1)
            t2 = group_runners_up.get(g2)
            if t1 and t2:
                matchups.append((t1, t2))

        # Remaining groups I-L runners-up face each other
        remaining_ru = []
        for g in ["I", "J", "K", "L"]:
            ru = group_runners_up.get(g)
            if ru:
                remaining_ru.append(ru)

        for i in range(0, len(remaining_ru) - 1, 2):
            matchups.append((remaining_ru[i], remaining_ru[i + 1]))

        return matchups

    def _simulate_knockout_match(self, team1: str, team2: str, stage: str) -> Tuple[str, str]:
        """
        Simulate a knockout match.
        Returns (winner_code, result_type) where result_type is:
        - "regular": decided in 90 minutes
        - "extra_time": decided in extra time
        - "penalties": decided by penalty shootout
        """
        s1, s2 = self._simulate_match(team1, team2, stage=stage)

        if s1 > s2:
            return team1, "regular"
        elif s2 > s1:
            return team2, "regular"
        else:
            # Draw after 90 min → extra time (knockout only)
            winner, et1, et2 = self._simulate_extra_time(team1, team2)
            if et1 != et2:
                return winner, "extra_time"
            else:
                return winner, "penalties"

    def _simulate_knockout_stage(self, r32_matchups: List[Tuple[str, str]]) -> Dict[str, str]:
        """
        Simulate the entire knockout stage from Round of 32 matchups.
        Returns mapping of team_code -> furthest_stage_reached.
        """
        stage_reached = {}

        def mark_stage(team: str, stage: str):
            if team not in stage_reached:
                stage_reached[team] = stage

        # Round of 32 (16 matches)
        r32_winners = []
        for t1, t2 in r32_matchups[:16]:
            if not t1 or not t2:
                continue
            winner, _ = self._simulate_knockout_match(t1, t2, "round32")
            r32_winners.append(winner)
            mark_stage(t1, "round32")
            mark_stage(t2, "round32")

        # Round of 16 (8 matches)
        r16_winners = []
        for i in range(0, min(16, len(r32_winners)) - 1, 2):
            winner, _ = self._simulate_knockout_match(r32_winners[i], r32_winners[i + 1], "round16")
            r16_winners.append(winner)
        for t in r32_winners:
            mark_stage(t, "round16")

        # Quarter-finals (4 matches)
        qf_winners = []
        for i in range(0, min(8, len(r16_winners)) - 1, 2):
            winner, _ = self._simulate_knockout_match(r16_winners[i], r16_winners[i + 1], "quarter")
            qf_winners.append(winner)
        for t in r16_winners:
            mark_stage(t, "quarter")

        # Semi-finals (2 matches)
        sf_winners = []
        sf_losers = []
        if len(qf_winners) >= 4:
            for i in range(0, 4, 2):
                winner, _ = self._simulate_knockout_match(qf_winners[i], qf_winners[i + 1], "semi")
                loser = qf_winners[i + 1] if winner == qf_winners[i] else qf_winners[i]
                sf_winners.append(winner)
                sf_losers.append(loser)
        for t in qf_winners:
            mark_stage(t, "semi")

        # Third place
        if len(sf_losers) >= 2:
            third_winner, _ = self._simulate_knockout_match(sf_losers[0], sf_losers[1], "third")
            mark_stage(sf_losers[0], "third")
            mark_stage(sf_losers[1], "third")

        # Final
        if len(sf_winners) >= 2:
            champion, _ = self._simulate_knockout_match(sf_winners[0], sf_winners[1], "final")
            runner_up = sf_winners[1] if champion == sf_winners[0] else sf_winners[0]
            mark_stage(sf_winners[0], "final")
            mark_stage(sf_winners[1], "final")
        else:
            champion = sf_winners[0] if sf_winners else None
            runner_up = None

        return {
            "champion": champion,
            "runner_up": runner_up,
            "stage_reached": stage_reached,
        }

    def run_simulation(self, groups: Dict[str, List[str]], num_sims: int = None) -> Dict:
        """
        Run full Monte Carlo simulation.

        Args:
            groups: {group_name: [team_code1, team_code2, team_code3, team_code4]}
            num_sims: number of simulations (default: 10000)
        """
        num_sims = num_sims or self.NUM_SIMULATIONS

        champion_counts = Counter()
        runner_up_counts = Counter()
        final_matchups = Counter()
        stage_counts = {code: Counter() for code in self.teams_data}

        for sim in range(num_sims):
            if (sim + 1) % 2000 == 0:
                print(f"[MonteCarlo] Simulation {sim + 1}/{num_sims}")

            # 1. Group stage
            group_results = self._simulate_group_stage(groups)

            # 2. Determine advancing teams
            group_winners = {}
            group_runners_up = {}
            self._third_place_by_group = {}

            for g_name, standings in sorted(group_results.items()):
                if len(standings) >= 3:
                    group_winners[g_name] = standings[0]["code"]
                    group_runners_up[g_name] = standings[1]["code"]
                    self._third_place_by_group[g_name] = standings[2]["code"]

            # 8 best third-place teams
            best_third = self._select_best_third_place(group_results, 8)

            # 3. Build Round of 32 bracket per FIFA 2026 format
            r32_matchups = self._build_round32_bracket(
                group_winners, group_runners_up, best_third
            )

            # 4. Simulate knockout
            ko_result = self._simulate_knockout_stage(r32_matchups)

            # 5. Record results
            if ko_result["champion"]:
                champion_counts[ko_result["champion"]] += 1
            if ko_result["runner_up"]:
                runner_up_counts[ko_result["runner_up"]] += 1
            if ko_result["champion"] and ko_result["runner_up"]:
                final_matchups[(ko_result["champion"], ko_result["runner_up"])] += 1

            for team, stage in ko_result["stage_reached"].items():
                if team in stage_counts:
                    stage_counts[team][stage] += 1

        # Calculate probabilities
        champion_probs = {code: count / num_sims for code, count in champion_counts.most_common(20)}
        runner_up_probs = {code: count / num_sims for code, count in runner_up_counts.most_common(20)}

        # Stage probabilities
        stages = ["round32", "round16", "quarter", "semi", "third", "final"]
        stage_probs = {}
        for code in self.teams_data:
            probs = {}
            for s in stages:
                p = stage_counts[code].get(s, 0) / num_sims
                probs[s] = round(p, 4)
            probs["champion"] = round(champion_counts.get(code, 0) / num_sims, 4)
            stage_probs[code] = probs

        # Most likely final
        most_likely_final = final_matchups.most_common(1)
        if most_likely_final:
            (t1, t2), count = most_likely_final[0]
            most_likely_final_result = {"team1": t1, "team2": t2, "probability": round(count / num_sims, 4)}
        else:
            most_likely_final_result = None

        # Most likely champion
        top_champ = champion_counts.most_common(1)
        if top_champ:
            t, count = top_champ[0]
            most_likely_champ = {"team": t, "probability": round(count / num_sims, 4)}
        else:
            most_likely_champ = None

        self.results = {
            "num_simulations": num_sims,
            "champion_probs": champion_probs,
            "runner_up_probs": runner_up_probs,
            "stage_probs": stage_probs,
            "most_likely_final": most_likely_final_result,
            "most_likely_champion": most_likely_champ,
            "top_10_champions": [
                {"code": code, "name": self.teams_data.get(code, {}).get("name", code),
                 "name_zh": self.teams_data.get(code, {}).get("name_zh", code),
                 "probability": round(count / num_sims, 4)}
                for code, count in champion_counts.most_common(10)
            ],
        }

        return self.results
