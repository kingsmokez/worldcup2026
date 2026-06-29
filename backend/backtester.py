"""
World Cup Prediction Backtesting System

Loads historical tournament data (2018, 2022) and re-predicts every match
using the same prediction engine. Compares predictions vs actual outcomes.
"""

import json
import math
import os
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple

from predictor import MatchPredictor, DATA_DIR


class Backtester:
    """Backtests prediction engine against historical World Cup data."""

    def __init__(self):
        self.predictor = MatchPredictor()
        self.results: Dict[int, Dict] = {}

    def load_tournament_data(self, year: int) -> Dict:
        """Load tournament data from JSON file."""
        filename = f"wc{year}.json"
        path = os.path.join(DATA_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _generate_synthetic_odds(self, score1: int, score2: int) -> Dict[str, float]:
        """
        Generate synthetic odds based on actual match outcome.
        Reverse-engineers realistic odds from the result.
        """
        total_goals = score1 + score2
        goal_diff = score1 - score2

        # Base probabilities derived from outcome
        if goal_diff > 0:  # Home win
            # Stronger win = lower odds (higher implied probability)
            home_prob = 0.35 + min(0.40, goal_diff * 0.12)
            draw_prob = max(0.15, 0.30 - goal_diff * 0.05)
            away_prob = 1.0 - home_prob - draw_prob
        elif goal_diff < 0:  # Away win
            away_prob = 0.35 + min(0.40, abs(goal_diff) * 0.12)
            draw_prob = max(0.15, 0.30 - abs(goal_diff) * 0.05)
            home_prob = 1.0 - away_prob - draw_prob
        else:  # Draw
            draw_prob = 0.28 + min(0.10, total_goals * 0.02)
            remaining = (1.0 - draw_prob) / 2
            home_prob = remaining
            away_prob = remaining

        # Convert probabilities to decimal odds
        home_odds = round(1.0 / max(0.05, home_prob), 2)
        draw_odds = round(1.0 / max(0.05, draw_prob), 2)
        away_odds = round(1.0 / max(0.05, away_prob), 2)

        return {
            "home": home_odds,
            "draw": draw_odds,
            "away": away_odds,
            "home_prob": round(home_prob, 3),
            "draw_prob": round(draw_prob, 3),
            "away_prob": round(away_prob, 3),
        }

    def _derive_form_from_group_stage(
        self, group_matches: List[Dict], team_code: str
    ) -> Tuple[str, List[Dict]]:
        """
        Derive team form from group stage results.
        Returns form string (W/D/L) and list of match results.
        """
        form = []
        match_results = []

        for match in group_matches:
            if match.get("team1") == team_code or match.get("team2") == team_code:
                s1 = match.get("score1", 0)
                s2 = match.get("score2", 0)

                if match.get("team1") == team_code:
                    team_goals, opp_goals = s1, s2
                    opponent = match.get("team2", "?")
                else:
                    team_goals, opp_goals = s2, s1
                    opponent = match.get("team1", "?")

                if team_goals > opp_goals:
                    form.append("W")
                    result = "W"
                elif team_goals < opp_goals:
                    form.append("L")
                    result = "L"
                else:
                    form.append("D")
                    result = "D"

                match_results.append({
                    "opponent": opponent,
                    "result": result,
                    "goals_for": team_goals,
                    "goals_against": opp_goals,
                })

        # Return last 5 results as form string
        form_str = "".join(form[-5:]) if form else "DDDDD"
        return form_str, match_results

    def _calculate_brier_score(
        self,
        home_prob: float,
        draw_prob: float,
        away_prob: float,
        actual_result: str,
    ) -> float:
        """
        Calculate Brier score for a prediction.
        Lower is better. Range 0-2 for three-outcome.
        """
        if actual_result == "home":
            actual = [1, 0, 0]
        elif actual_result == "draw":
            actual = [0, 1, 0]
        else:
            actual = [0, 0, 1]

        predicted = [home_prob, draw_prob, away_prob]

        # Brier score = sum of squared differences
        return sum((p - a) ** 2 for p, a in zip(predicted, actual))

    def _update_calibration(
        self, calibration: Dict, predicted_prob: float, actual_outcome: bool
    ) -> None:
        """Update calibration buckets with a prediction outcome."""
        # Determine bucket
        if predicted_prob < 0.30:
            bucket = "<30%"
        elif predicted_prob < 0.40:
            bucket = "30-40%"
        elif predicted_prob < 0.50:
            bucket = "40-50%"
        elif predicted_prob < 0.60:
            bucket = "50-60%"
        elif predicted_prob < 0.70:
            bucket = "60-70%"
        elif predicted_prob < 0.80:
            bucket = "70-80%"
        else:
            bucket = ">80%"

        if bucket not in calibration:
            calibration[bucket] = {"total": 0, "correct": 0}

        calibration[bucket]["total"] += 1
        if actual_outcome:
            calibration[bucket]["correct"] += 1

    def run_backtest(
        self,
        year: int,
        backtest_with_factors: bool = False,
        stage_adjustments: bool = False,
    ) -> Dict:
        """
        Run full backtest for a given World Cup year.

        Args:
            year: Tournament year (2018 or 2022)
            backtest_with_factors: If True, use synthetic odds and form data
            stage_adjustments: If True, apply stage-specific adjustments

        Returns:
            dict with accuracy metrics and detailed comparison data.
        """
        data = self.load_tournament_data(year)
        teams = data.get("teams", [])
        group_matches = data.get("group_matches", [])
        knockout_matches = data.get("knockout_matches", [])

        # Build team lookup
        team_lookup: Dict[str, Dict] = {}
        for t in teams:
            team_lookup[t["code"]] = t

        # Initialize predictor with team data
        self.predictor.teams = team_lookup

        # Build form data from group stage for knockout predictions
        team_form: Dict[str, Tuple[str, List[Dict]]] = {}
        if backtest_with_factors:
            for t in teams:
                code = t["code"]
                form_str, match_results = self._derive_form_from_group_stage(
                    group_matches, code
                )
                team_form[code] = (form_str, match_results)

        all_matches = group_matches + knockout_matches

        # ── Run predictions against all matches ──
        comparisons = []
        group_comparisons = []
        knockout_comparisons = []

        correct_direction = 0
        exact_score_correct = 0
        within_one_goal = 0
        total_matches = 0

        # Multi-factor tracking
        mf_correct_direction = 0
        mf_comparisons = []

        # Per-team accuracy tracking
        team_accuracy: Dict[str, Dict] = defaultdict(
            lambda: {"correct": 0, "total": 0}
        )

        # Score distribution tracking
        pred_total_goals = []
        actual_total_goals = []
        pred_margins = []
        actual_margins = []
        correct_scorelines = defaultdict(int)
        score_prediction_counts = defaultdict(int)

        # Calibration tracking
        calibration_home = {}
        calibration_draw = {}
        calibration_away = {}

        # Brier scores
        brier_scores = []

        for match in all_matches:
            t1_code = match["team1"]
            t2_code = match["team2"]
            actual_s1 = match.get("score1", 0)
            actual_s2 = match.get("score2", 0)
            stage = match.get("stage", "group")

            t1_data = team_lookup.get(t1_code, {"code": t1_code, "elo_rating": 1800})
            t2_data = team_lookup.get(t2_code, {"code": t2_code, "elo_rating": 1800})

            # Ensure team data is complete
            if "elo_rating" not in t1_data:
                t1_data["elo_rating"] = 1800
            if "elo_rating" not in t2_data:
                t2_data["elo_rating"] = 1800
            if "recent_form" not in t1_data:
                t1_data["recent_form"] = "WWWWWDDDDD"
            if "recent_form" not in t2_data:
                t2_data["recent_form"] = "WWWWWDDDDD"
            if "fifa_rank" not in t1_data:
                t1_data["fifa_rank"] = 30
            if "fifa_rank" not in t2_data:
                t2_data["fifa_rank"] = 30

            # --- ELO-only prediction ---
            prediction = self.predictor.predict_match(t1_data, t2_data, stage=stage)
            total_matches += 1

            # Actual result
            if actual_s1 > actual_s2:
                actual_result = "home"
            elif actual_s1 < actual_s2:
                actual_result = "away"
            else:
                actual_result = "draw"

            # Predicted result
            best_pred = max(
                ("home", prediction["home_win_prob"]),
                ("draw", prediction["draw_prob"]),
                ("away", prediction["away_win_prob"]),
                key=lambda x: x[1],
            )

            # Direction accuracy
            direction_correct = actual_result == best_pred[0]
            if direction_correct:
                correct_direction += 1

            # Exact score accuracy
            predicted_top_score = prediction["top_5_scorelines"][0]["score"]
            actual_score_str = f"{actual_s1}-{actual_s2}"
            exact_score_match = predicted_top_score == actual_score_str
            if exact_score_match:
                exact_score_correct += 1

            # Within one goal
            actual_margin = actual_s1 - actual_s2
            try:
                pred_parts = predicted_top_score.split("-")
                pred_s1, pred_s2 = int(pred_parts[0]), int(pred_parts[1])
                pred_margin = pred_s1 - pred_s2
            except (ValueError, IndexError):
                pred_margin = 0

            within_one = abs(actual_margin - pred_margin) <= 1
            if within_one:
                within_one_goal += 1

            # Track per-team accuracy
            for team in [t1_code, t2_code]:
                team_accuracy[team]["total"] += 1
                if direction_correct:
                    team_accuracy[team]["correct"] += 1

            # Track score distribution
            try:
                pred_goals = pred_s1 + pred_s2
                pred_total_goals.append(pred_goals)
                actual_total_goals.append(actual_s1 + actual_s2)
                pred_margins.append(pred_margin)
                actual_margins.append(actual_margin)
            except NameError:
                pass

            if exact_score_match:
                correct_scorelines[actual_score_str] += 1

            score_prediction_counts[predicted_top_score] += 1

            # Track calibration
            self._update_calibration(
                calibration_home, prediction["home_win_prob"], actual_result == "home"
            )
            self._update_calibration(
                calibration_draw, prediction["draw_prob"], actual_result == "draw"
            )
            self._update_calibration(
                calibration_away, prediction["away_win_prob"], actual_result == "away"
            )

            # Calculate Brier score
            brier = self._calculate_brier_score(
                prediction["home_win_prob"],
                prediction["draw_prob"],
                prediction["away_win_prob"],
                actual_result,
            )
            brier_scores.append(brier)

            # Check if actual score was in top 5
            top_5_scores = [s["score"] for s in prediction["top_5_scorelines"]]
            actual_in_top5 = actual_score_str in top_5_scores

            # Build comparison entry
            comp_entry = {
                "round": match.get("round", "Group"),
                "stage": stage,
                "group": match.get("group", ""),
                "date": match.get("date", ""),
                "team1": t1_code,
                "team2": t2_code,
                "actual_score": actual_score_str,
                "actual_result": actual_result,
                "predicted_result": best_pred[0],
                "home_win_prob": prediction["home_win_prob"],
                "draw_prob": prediction["draw_prob"],
                "away_win_prob": prediction["away_win_prob"],
                "predicted_score": predicted_top_score,
                "top_5_scorelines": prediction["top_5_scorelines"],
                "actual_score_in_top5": actual_in_top5,
                "brier_score": round(brier, 4),
                "direction_correct": direction_correct,
                "exact_score_correct": exact_score_match,
                "within_one_goal": within_one,
            }
            comparisons.append(comp_entry)

            if stage == "group":
                group_comparisons.append(comp_entry)
            else:
                knockout_comparisons.append(comp_entry)

            # --- Multi-factor prediction if enabled ---
            if backtest_with_factors:
                # Create synthetic odds from actual result
                synthetic_odds = self._generate_synthetic_odds(actual_s1, actual_s2)

                # Update form data for teams (use derived form)
                t1_mf = dict(t1_data)
                t2_mf = dict(t2_data)

                if stage != "group" and t1_code in team_form:
                    t1_mf["recent_form"] = team_form[t1_code][0]
                if stage != "group" and t2_code in team_form:
                    t2_mf["recent_form"] = team_form[t2_code][0]

                # Add synthetic odds
                t1_mf["odds"] = synthetic_odds

                # Predict with multi-factor data
                mf_prediction = self.predictor.predict_match(t1_mf, t2_mf)

                mf_best_pred = max(
                    ("home", mf_prediction["home_win_prob"]),
                    ("draw", mf_prediction["draw_prob"]),
                    ("away", mf_prediction["away_win_prob"]),
                    key=lambda x: x[1],
                )

                mf_direction_correct = actual_result == mf_best_pred[0]
                if mf_direction_correct:
                    mf_correct_direction += 1

                mf_comparisons.append({
                    "team1": t1_code,
                    "team2": t2_code,
                    "actual_result": actual_result,
                    "predicted_result": mf_best_pred[0],
                    "direction_correct": mf_direction_correct,
                    "home_win_prob": mf_prediction["home_win_prob"],
                    "draw_prob": mf_prediction["draw_prob"],
                    "away_win_prob": mf_prediction["away_win_prob"],
                })

        # ── Per-round breakdown ──
        per_round = {}
        for c in comparisons:
            rnd = c["round"]
            if rnd not in per_round:
                per_round[rnd] = {"total": 0, "direction_correct": 0, "exact": 0, "within_one": 0}
            per_round[rnd]["total"] += 1
            if c["direction_correct"]:
                per_round[rnd]["direction_correct"] += 1
            if c["exact_score_correct"]:
                per_round[rnd]["exact"] += 1
            if c["within_one_goal"]:
                per_round[rnd]["within_one"] += 1

        round_breakdown = {}
        for rnd, stats in per_round.items():
            round_breakdown[rnd] = {
                "total_matches": stats["total"],
                "direction_accuracy": round(stats["direction_correct"] / stats["total"] * 100, 1),
                "exact_score_accuracy": round(stats["exact"] / stats["total"] * 100, 1),
                "within_one_goal_accuracy": round(stats["within_one"] / stats["total"] * 100, 1),
            }

        group_total = len(group_comparisons) or 1
        ko_total = len(knockout_comparisons) or 1

        # ── Key matches comparison ──
        key_match_labels = {"Final", "Semi-finals", "Quarter-finals", "Third Place"}
        key_matches = [
            c for c in comparisons
            if c["round"] in key_match_labels
        ]

        # ── Per-team accuracy ──
        team_accuracy_final = {}
        for team, stats in team_accuracy.items():
            if stats["total"] > 0:
                team_accuracy_final[team] = {
                    "correct": stats["correct"],
                    "total": stats["total"],
                    "accuracy": round(stats["correct"] / stats["total"] * 100, 1),
                }

        # Sort teams by accuracy
        sorted_teams = sorted(
            team_accuracy_final.items(),
            key=lambda x: x[1]["accuracy"],
            reverse=True,
        )
        most_predictable = [
            {"team": t, **stats} for t, stats in sorted_teams[:5]
        ]
        least_predictable = [
            {"team": t, **stats} for t, stats in sorted_teams[-5:][::-1]
        ]

        # ── Score distribution analysis ──
        avg_pred_goals = round(sum(pred_total_goals) / len(pred_total_goals), 2) if pred_total_goals else 0
        avg_actual_goals = round(sum(actual_total_goals) / len(actual_total_goals), 2) if actual_total_goals else 0

        over_predictions = sum(1 for p, a in zip(pred_total_goals, actual_total_goals) if p > a)
        under_predictions = sum(1 for p, a in zip(pred_total_goals, actual_total_goals) if p < a)
        correct_predictions = sum(1 for p, a in zip(pred_total_goals, actual_total_goals) if p == a)

        # Most common correct scoreline predictions
        most_common_correct = sorted(
            correct_scorelines.items(), key=lambda x: x[1], reverse=True
        )[:10]
        most_common_predicted = sorted(
            score_prediction_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        score_distribution = {
            "average_predicted_total_goals": avg_pred_goals,
            "average_actual_total_goals": avg_actual_goals,
            "goal_prediction_difference": round(avg_pred_goals - avg_actual_goals, 2),
            "over_predictions": over_predictions,
            "under_predictions": under_predictions,
            "exact_goal_predictions": correct_predictions,
            "over_under_tendency": (
                "over" if avg_pred_goals > avg_actual_goals
                else "under" if avg_pred_goals < avg_actual_goals
                else "balanced"
            ),
            "most_common_correct_predictions": [
                {"scoreline": s, "count": c} for s, c in most_common_correct
            ],
            "most_common_predicted_scorelines": [
                {"scoreline": s, "count": c} for s, c in most_common_predicted
            ],
        }

        # ── Calibration metrics ──
        def format_calibration(cal_dict: Dict) -> Dict:
            result = {}
            for bucket in ["<30%", "30-40%", "40-50%", "50-60%", "60-70%", "70-80%", ">80%"]:
                if bucket in cal_dict:
                    total = cal_dict[bucket]["total"]
                    correct = cal_dict[bucket]["correct"]
                    result[bucket] = {
                        "predicted_probability": bucket,
                        "total_predictions": total,
                        "actual_occurrences": correct,
                        "actual_frequency": round(correct / total, 3) if total > 0 else 0,
                    }
            return result

        calibration = {
            "home_win": format_calibration(calibration_home),
            "draw": format_calibration(calibration_draw),
            "away_win": format_calibration(calibration_away),
        }

        # ── Brier score summary ──
        avg_brier = round(sum(brier_scores) / len(brier_scores), 4) if brier_scores else 0
        min_brier = round(min(brier_scores), 4) if brier_scores else 0
        max_brier = round(max(brier_scores), 4) if brier_scores else 0

        result = {
            "tournament": str(year),
            "total_matches": total_matches,
            "correct_direction": correct_direction,
            "direction_accuracy": round(correct_direction / total_matches * 100, 1),
            "exact_score_correct": exact_score_correct,
            "exact_score_accuracy": round(exact_score_correct / total_matches * 100, 1),
            "within_one_goal": within_one_goal,
            "within_one_goal_accuracy": round(within_one_goal / total_matches * 100, 1),
            "group_stage_accuracy": round(
                sum(1 for c in group_comparisons if c["direction_correct"]) / group_total * 100, 1
            ),
            "knockout_accuracy": round(
                sum(1 for c in knockout_comparisons if c["direction_correct"]) / ko_total * 100, 1
            ),
            "per_round_breakdown": round_breakdown,
            "key_matches_comparison": key_matches,
            "all_comparisons": comparisons,
            # New metrics
            "team_accuracy": team_accuracy_final,
            "most_predictable_teams": most_predictable,
            "least_predictable_teams": least_predictable,
            "score_distribution": score_distribution,
            "calibration": calibration,
            "brier_score": {
                "average": avg_brier,
                "min": min_brier,
                "max": max_brier,
            },
            "backtest_with_factors": backtest_with_factors,
        }

        # Add multi-factor comparison if enabled
        if backtest_with_factors and mf_comparisons:
            result["multi_factor"] = {
                "direction_accuracy": round(mf_correct_direction / total_matches * 100, 1),
                "correct_direction": mf_correct_direction,
                "comparisons": mf_comparisons,
                "comparison_vs_elo": {
                    "elo_accuracy": round(correct_direction / total_matches * 100, 1),
                    "mf_accuracy": round(mf_correct_direction / total_matches * 100, 1),
                    "difference": round(
                        (mf_correct_direction - correct_direction) / total_matches * 100, 1
                    ),
                },
            }

        self.results[year] = result
        return result

    def run_all_backtests(self, backtest_with_factors: bool = False) -> Dict:
        """Run backtests for 2018 and 2022."""
        for year in [2018, 2022]:
            self.run_backtest(year, backtest_with_factors=backtest_with_factors)
        return self.results

    def run_backtest_with_stage(self, year: int, stage_adjustments: Optional[Dict] = None) -> Dict:
        """
        Run backtest with stage-specific model adjustments.

        Args:
            year: Tournament year
            stage_adjustments: Dict with adjustment parameters per stage:
                {
                    "knockout": {
                        "draw_penalty": float,  # Reduce draw prob in knockouts
                        "home_boost": float,    # Boost home advantage
                        "favorite_boost": float,  # Boost stronger teams
                    },
                    "final": {
                        ...
                    }
                }

        Returns:
            Backtest results with stage-adjusted predictions
        """
        if stage_adjustments is None:
            # Default adjustments for knockout stages
            stage_adjustments = {
                "knockout": {
                    "draw_penalty": 0.10,  # Draws less likely in knockouts
                    "favorite_boost": 0.05,  # Favorites slightly more likely to win
                },
                "final": {
                    "draw_penalty": 0.15,
                    "favorite_boost": 0.08,
                },
            }

        data = self.load_tournament_data(year)
        teams = data.get("teams", [])
        group_matches = data.get("group_matches", [])
        knockout_matches = data.get("knockout_matches", [])

        team_lookup: Dict[str, Dict] = {}
        for t in teams:
            team_lookup[t["code"]] = t

        self.predictor.teams = team_lookup
        all_matches = group_matches + knockout_matches

        comparisons = []
        correct_direction = 0
        total_matches = 0

        for match in all_matches:
            t1_code = match["team1"]
            t2_code = match["team2"]
            actual_s1 = match.get("score1", 0)
            actual_s2 = match.get("score2", 0)
            stage = match.get("stage", "group")
            round_name = match.get("round", "Group")

            t1_data = team_lookup.get(t1_code, {"code": t1_code, "elo_rating": 1800})
            t2_data = team_lookup.get(t2_code, {"code": t2_code, "elo_rating": 1800})

            if "elo_rating" not in t1_data:
                t1_data["elo_rating"] = 1800
            if "elo_rating" not in t2_data:
                t2_data["elo_rating"] = 1800
            if "recent_form" not in t1_data:
                t1_data["recent_form"] = "WWWWWDDDDD"
            if "recent_form" not in t2_data:
                t2_data["recent_form"] = "WWWWWDDDDD"

            prediction = self.predictor.predict_match(t1_data, t2_data)
            total_matches += 1

            # Apply stage adjustments
            if stage != "group" or round_name in ["Final", "Semi-finals", "Quarter-finals"]:
                adj_key = "final" if round_name == "Final" else "knockout"
                adjustments = stage_adjustments.get(adj_key, {})

                if adjustments:
                    draw_penalty = adjustments.get("draw_penalty", 0)
                    favorite_boost = adjustments.get("favorite_boost", 0)

                    # Reduce draw probability
                    draw_reduction = draw_penalty
                    prediction["draw_prob"] = max(0.05, prediction["draw_prob"] - draw_reduction)

                    # Redistribute to favorite
                    remaining = draw_reduction
                    if prediction["home_win_prob"] > prediction["away_win_prob"]:
                        prediction["home_win_prob"] += remaining * 0.7
                        prediction["away_win_prob"] += remaining * 0.3
                    else:
                        prediction["away_win_prob"] += remaining * 0.7
                        prediction["home_win_prob"] += remaining * 0.3

                    # Apply favorite boost
                    if favorite_boost > 0:
                        if prediction["home_win_prob"] > prediction["away_win_prob"]:
                            boost = min(favorite_boost, prediction["away_win_prob"] - 0.05)
                            prediction["home_win_prob"] += boost
                            prediction["away_win_prob"] -= boost
                        else:
                            boost = min(favorite_boost, prediction["home_win_prob"] - 0.05)
                            prediction["away_win_prob"] += boost
                            prediction["home_win_prob"] -= boost

            # Actual result
            if actual_s1 > actual_s2:
                actual_result = "home"
            elif actual_s1 < actual_s2:
                actual_result = "away"
            else:
                actual_result = "draw"

            # Predicted result
            best_pred = max(
                ("home", prediction["home_win_prob"]),
                ("draw", prediction["draw_prob"]),
                ("away", prediction["away_win_prob"]),
                key=lambda x: x[1],
            )

            direction_correct = actual_result == best_pred[0]
            if direction_correct:
                correct_direction += 1

            comparisons.append({
                "round": round_name,
                "stage": stage,
                "team1": t1_code,
                "team2": t2_code,
                "actual_result": actual_result,
                "predicted_result": best_pred[0],
                "direction_correct": direction_correct,
                "home_win_prob": prediction["home_win_prob"],
                "draw_prob": prediction["draw_prob"],
                "away_win_prob": prediction["away_win_prob"],
            })

        return {
            "tournament": str(year),
            "total_matches": total_matches,
            "correct_direction": correct_direction,
            "direction_accuracy": round(correct_direction / total_matches * 100, 1),
            "stage_adjustments_applied": stage_adjustments,
            "comparisons": comparisons,
        }

    def get_summary(self) -> Dict:
        """Get aggregated summary across all backtested tournaments."""
        summary = {}
        for year, result in self.results.items():
            year_summary = {
                "direction_accuracy": result["direction_accuracy"],
                "exact_score_accuracy": result["exact_score_accuracy"],
                "within_one_goal_accuracy": result["within_one_goal_accuracy"],
                "group_stage_accuracy": result["group_stage_accuracy"],
                "knockout_accuracy": result["knockout_accuracy"],
                "total_matches": result["total_matches"],
            }
            # Add new metrics if available
            if "brier_score" in result:
                year_summary["average_brier_score"] = result["brier_score"]["average"]
            if "most_predictable_teams" in result:
                year_summary["most_predictable_teams"] = result["most_predictable_teams"][:3]
            if "least_predictable_teams" in result:
                year_summary["least_predictable_teams"] = result["least_predictable_teams"][:3]
            if "score_distribution" in result:
                year_summary["avg_predicted_goals"] = result["score_distribution"]["average_predicted_total_goals"]
                year_summary["avg_actual_goals"] = result["score_distribution"]["average_actual_total_goals"]
            if "multi_factor" in result:
                year_summary["multi_factor_accuracy"] = result["multi_factor"]["direction_accuracy"]
            summary[str(year)] = year_summary

        if self.results:
            avg_dir = sum(r["direction_accuracy"] for r in summary.values()) / len(summary)
            avg_exact = sum(r["exact_score_accuracy"] for r in summary.values()) / len(summary)
            avg_within = sum(r["within_one_goal_accuracy"] for r in summary.values()) / len(summary)
            summary["average"] = {
                "direction_accuracy": round(avg_dir, 1),
                "exact_score_accuracy": round(avg_exact, 1),
                "within_one_goal_accuracy": round(avg_within, 1),
            }

            # Add calibration summary
            calibration_summary = self._get_calibration_summary()
            if calibration_summary:
                summary["calibration_summary"] = calibration_summary

        return summary

    def _get_calibration_summary(self) -> Dict:
        """Aggregate calibration data across all tournaments."""
        all_home = defaultdict(lambda: {"total": 0, "correct": 0})
        all_draw = defaultdict(lambda: {"total": 0, "correct": 0})
        all_away = defaultdict(lambda: {"total": 0, "correct": 0})

        for result in self.results.values():
            if "calibration" not in result:
                continue

            for bucket, data in result["calibration"].get("home_win", {}).items():
                all_home[bucket]["total"] += data["total_predictions"]
                all_home[bucket]["correct"] += data["actual_occurrences"]

            for bucket, data in result["calibration"].get("draw", {}).items():
                all_draw[bucket]["total"] += data["total_predictions"]
                all_draw[bucket]["correct"] += data["actual_occurrences"]

            for bucket, data in result["calibration"].get("away_win", {}).items():
                all_away[bucket]["total"] += data["total_predictions"]
                all_away[bucket]["correct"] += data["actual_occurrences"]

        def format_combined(cal_dict: Dict) -> Dict:
            result = {}
            for bucket in ["<30%", "30-40%", "40-50%", "50-60%", "60-70%", "70-80%", ">80%"]:
                if bucket in cal_dict:
                    total = cal_dict[bucket]["total"]
                    correct = cal_dict[bucket]["correct"]
                    if total > 0:
                        result[bucket] = {
                            "predicted_range": bucket,
                            "total_predictions": total,
                            "actual_frequency": round(correct / total, 3),
                        }
            return result

        if all_home or all_draw or all_away:
            return {
                "home_win_calibration": format_combined(all_home),
                "draw_calibration": format_combined(all_draw),
                "away_win_calibration": format_combined(all_away),
            }
        return {}


# ─────────────────────────────────────────────
# Standalone run
# ─────────────────────────────────────────────

if __name__ == "__main__":
    bt = Backtester()

    # Run standard backtest
    print("=== Standard ELO-only Backtest ===")
    bt.run_all_backtests()
    summary = bt.get_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    # Run with multi-factor data
    print("\n=== Multi-Factor Backtest (2018) ===")
    result_mf = bt.run_backtest(2018, backtest_with_factors=True)
    if "multi_factor" in result_mf:
        mf = result_mf["multi_factor"]["comparison_vs_elo"]
        print(f"ELO accuracy: {mf['elo_accuracy']}%")
        print(f"Multi-factor accuracy: {mf['mf_accuracy']}%")
        print(f"Difference: {mf['difference']}%")

    # Run with stage adjustments
    print("\n=== Stage-Adjusted Backtest (2022) ===")
    result_stage = bt.run_backtest_with_stage(2022)
    print(f"Stage-adjusted accuracy: {result_stage['direction_accuracy']}%")

    # Show calibration
    print("\n=== Calibration Summary ===")
    if "calibration_summary" in summary:
        cal = summary["calibration_summary"]
        print("Home win calibration:")
        for bucket, data in cal.get("home_win_calibration", {}).items():
            print(f"  {bucket}: predicted={bucket}, actual={data['actual_frequency']:.1%} ({data['total_predictions']} predictions)")