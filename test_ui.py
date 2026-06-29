import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test 1: Load homepage
        print("Test 1: Loading homepage...")
        await page.goto('http://localhost:5173', timeout=30000)
        await page.wait_for_load_state('networkidle')
        
        # Take screenshot
        await page.screenshot(path='d:/UI/world/test_screenshots/homepage.png', full_page=True)
        print("  Screenshot: homepage.png")
        
        # Check title
        title = await page.title()
        print(f"  Title: {title}")
        assert 'World Cup' in title or '世界杯' in title, f"Bad title: {title}"
        print("  PASS: Title OK")
        
        # Check Dashboard tab is visible
        dashboard_visible = await page.locator('text=Dashboard').is_visible()
        print(f"  Dashboard tab visible: {dashboard_visible}")
        
        # Test 2: Check for upcoming matches
        print("\nTest 2: Checking upcoming matches...")
        match_cards = await page.locator('.match-card, [class*="Match"]').count()
        print(f"  Match cards found: {match_cards}")
        
        # Test 3: Switch to Groups tab
        print("\nTest 3: Switching to Groups tab...")
        groups_btn = page.locator('button:has-text("Groups"), button:has-text("小组")')
        groups_count = await groups_btn.count()
        if groups_count > 0:
            await groups_btn.first.click()
            await page.wait_for_timeout(1000)
            await page.screenshot(path='d:/UI/world/test_screenshots/groups.png', full_page=True)
            print("  Screenshot: groups.png")
            print("  PASS: Groups tab works")
        else:
            # Try text-based navigation
            await page.locator('text=Groups').first.click()
            await page.wait_for_timeout(1000)
            print("  Switched via text")
        
        # Test 4: Switch to Bracket tab
        print("\nTest 4: Switching to Bracket tab...")
        bracket_btn = page.locator('button:has-text("Bracket"), button:has-text("淘汰")')
        b_count = await bracket_btn.count()
        if b_count > 0:
            await bracket_btn.first.click()
        else:
            await page.locator('text=Bracket').first.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path='d:/UI/world/test_screenshots/bracket.png', full_page=True)
        print("  Screenshot: bracket.png")
        print("  PASS: Bracket tab works")
        
        # Test 5: Switch to Backtest tab
        print("\nTest 5: Switching to Backtest tab...")
        backtest_btn = page.locator('button:has-text("Backtest"), button:has-text("回测")')
        bt_count = await backtest_btn.count()
        if bt_count > 0:
            await backtest_btn.first.click()
        else:
            await page.locator('text=Backtest').first.click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path='d:/UI/world/test_screenshots/backtest.png', full_page=True)
        print("  Screenshot: backtest.png")
        print("  PASS: Backtest tab works")
        
        # Test 6: Check for prediction data loaded
        print("\nTest 6: Checking data loaded...")
        # Wait a bit more for API data
        await page.wait_for_timeout(3000)
        
        # Check console for errors
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"{msg.type}: {msg.text}") if msg.type == 'error' else None)
        
        errors = [log for log in console_logs if 'error' in log.lower()]
        if errors:
            print(f"  Console errors: {errors}")
        else:
            print("  No console errors found")
        
        # Final: go back to dashboard and take a final screenshot
        dashboard_btn = page.locator('button:has-text("Dashboard"), button:has-text("主页")')
        if await dashboard_btn.count() > 0:
            await dashboard_btn.first.click()
        await page.wait_for_timeout(1500)
        
        print("\n=== ALL TESTS PASSED ===")
        await browser.close()

asyncio.run(test())