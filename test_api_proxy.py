import httpx

# Test frontend page loads
r = httpx.get('http://localhost:5173')
print('Frontend status:', r.status_code)
print('Has React root:', 'id="root"' in r.text)
print('Page title check:', 'Vite' in r.text or 'World Cup' in r.text)

# Test API proxy through Vite
r2 = httpx.get('http://localhost:5173/api/status')
print('\nAPI proxy status:', r2.status_code)
if r2.status_code == 200:
    print('API response:', r2.json())
else:
    print('API proxy failed:', r2.text[:200])

# Test groups API
r3 = httpx.get('http://localhost:5173/api/groups')
print('\nGroups API status:', r3.status_code)
if r3.status_code == 200:
    data = r3.json()
    print('Groups count:', len(data.get('groups', [])))
    for g in data.get('groups', [])[:2]:
        print(f"  Group {g['group']}: {len(g['standings'])} teams")

# Test dashboard API
r4 = httpx.get('http://localhost:5173/api/dashboard')
print('\nDashboard API status:', r4.status_code)
if r4.status_code == 200:
    data = r4.json()
    print('Upcoming matches:', data.get('total_upcoming', 0))

# Test bracket API
r5 = httpx.get('http://localhost:5173/api/bracket')
print('\nBracket API status:', r5.status_code)

# Test backtest API
r6 = httpx.get('http://localhost:5173/api/backtest')
print('\nBacktest API status:', r6.status_code)
if r6.status_code == 200:
    data = r6.json()
    print('Backtest years:', list(data.get('results', {}).keys()))

print('\n=== All API tests complete ===')
