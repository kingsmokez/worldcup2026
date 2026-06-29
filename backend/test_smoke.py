"""Quick smoke test for all backend modules."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("Testing database...")
from database import full_init, get_all_teams, get_groups_standings
full_init()
teams = get_all_teams()
print(f"  Teams in DB: {len(teams)}")
groups = get_groups_standings()
print(f"  Groups: {len(groups)}")
for g in groups:
    print(f"    Group {g['group']}: {len(g['standings'])} teams")

print()
print("Testing predictor...")
from predictor import MatchPredictor
p = MatchPredictor()
p.load_teams_from_file("teams.json")
print(f"  Teams loaded: {len(p.teams)}")
pred = p.predict_match(p.teams["ARG"], p.teams["FRA"])
print(f"  ARG vs FRA: W={pred['home_win_prob']}% D={pred['draw_prob']}% L={pred['away_win_prob']}%")
print(f"  Expected goals: {pred['expected_goals_home']} - {pred['expected_goals_away']}")
print(f"  Confidence: {pred['confidence_level']}")
print(f"  Top scoreline: {pred['top_5_scorelines'][0]['score']} ({pred['top_5_scorelines'][0]['probability']}%)")

pred2 = p.predict_match(p.teams["BRA"], p.teams["GER"])
print(f"  BRA vs GER: W={pred2['home_win_prob']}% D={pred2['draw_prob']}% L={pred2['away_win_prob']}%")
print(f"  Confidence: {pred2['confidence_level']}")

pred3 = p.predict_match(p.teams["ESP"], p.teams["ITA"])
print(f"  ESP vs ITA: W={pred3['home_win_prob']}% D={pred3['draw_prob']}% L={pred3['away_win_prob']}%")

print()
print("Testing backtester...")
from backtester import Backtester
bt = Backtester()
bt.predictor.teams = p.teams
for year in [2018, 2022]:
    result = bt.run_backtest(year)
    print(f"  {year}: Direction={result['direction_accuracy']}% Exact={result['exact_score_accuracy']}%")
    print(f"         Group={result['group_stage_accuracy']}% KO={result['knockout_accuracy']}%")

print()
print("ALL TESTS PASSED")