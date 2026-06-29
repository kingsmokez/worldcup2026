import httpx

# Test that the frontend JS bundle loads
r = httpx.get('http://localhost:5173')
html = r.text

# Check for key indicators
checks = {
    'HTML loads (200)': r.status_code == 200,
    'Has React root div': 'id="root"' in html,
    'Has script tag': '<script' in html,
    'Has CSS link': '<link' in html and 'stylesheet' in html,
}

print("=== Frontend Page Checks ===")
for check, passed in checks.items():
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {check}")

# Test all API endpoints through Vite proxy
endpoints = [
    ('/api/status', 'Status'),
    ('/api/dashboard', 'Dashboard'),
    ('/api/groups', 'Groups'),
    ('/api/bracket', 'Bracket'),
    ('/api/teams', 'Teams'),
    ('/api/backtest', 'Backtest'),
    ('/api/predict?team1=BRA&team2=GER', 'Predict BRA vs GER'),
]

print("\n=== API Endpoint Checks (via Vite proxy) ===")
for endpoint, name in endpoints:
    try:
        r = httpx.get(f'http://localhost:5173{endpoint}', timeout=10)
        status = "PASS" if r.status_code == 200 else f"FAIL ({r.status_code})"
        print(f"  [{status}] {name}: {endpoint}")
    except Exception as e:
        print(f"  [FAIL] {name}: {endpoint} - {e}")

# Detailed data checks
print("\n=== Data Integrity Checks ===")

# Groups
r = httpx.get('http://localhost:5173/api/groups')
data = r.json()
groups = data.get('groups', [])
print(f"  Groups: {len(groups)} groups (expected 8)")
for g in groups:
    teams = g.get('standings', [])
    print(f"    Group {g['group']}: {len(teams)} teams", end="")
    if teams:
        top = teams[0]
        print(f" | Top: {top.get('name','?')} ({top.get('points',0)}pts)")
    else:
        print()

# Dashboard
r = httpx.get('http://localhost:5173/api/dashboard')
data = r.json()
upcoming = data.get('upcoming_matches', [])
print(f"\n  Upcoming matches: {len(upcoming)}")
if upcoming:
    m = upcoming[0]
    print(f"    First match: {m.get('team1_name','?')} vs {m.get('team2_name','?')}")
    pred = m.get('prediction', {})
    if pred:
        print(f"    Prediction: {pred.get('home_win_prob',0):.1f}% / {pred.get('draw_prob',0):.1f}% / {pred.get('away_win_prob',0):.1f}%")

# Predict
r = httpx.get('http://localhost:5173/api/predict', params={'team1': 'BRA', 'team2': 'GER'})
data = r.json()
pred = data.get('prediction', {})
print(f"\n  BRA vs GER prediction:")
print(f"    Win probs: {pred.get('home_win_prob',0):.1f}% / {pred.get('draw_prob',0):.1f}% / {pred.get('away_win_prob',0):.1f}%")
print(f"    Expected goals: {pred.get('expected_goals_home',0):.2f} - {pred.get('expected_goals_away',0):.2f}")
top5 = pred.get('top_5_scorelines', [])
if top5:
    score_strs = [f"{s['score']}({s['probability']}%)" for s in top5[:3]]
    print(f"    Top scorelines: {', '.join(score_strs)}")

print("\n=== All checks complete ===")
