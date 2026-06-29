from playwright.sync_api import sync_playwright
import os

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    # 1. Test Dashboard page
    print("[1/5] Testing Dashboard page...")
    page.goto('http://localhost:5173')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, '01_dashboard.png'), full_page=True)
    print("  Dashboard screenshot saved")

    # Check key elements exist
    title = page.locator('h1')
    if title.count() > 0:
        print(f"  Title found: {title.first.text_content()}")
    else:
        print("  WARNING: No h1 title found")

    # Check match cards
    match_cards = page.locator('[class*="match"], [class*="card"]')
    print(f"  Match/card elements: {match_cards.count()}")

    # 2. Test Groups page
    print("[2/5] Testing Groups page...")
    groups_tab = page.locator('button:has-text("小组赛")')
    if groups_tab.count() > 0:
        groups_tab.first.click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, '02_groups.png'), full_page=True)
        print("  Groups screenshot saved")

        # Check group tables
        tables = page.locator('table, [class*="standings"], [class*="group"]')
        print(f"  Table/group elements: {tables.count()}")
    else:
        print("  WARNING: Groups tab not found")

    # 3. Test Bracket page
    print("[3/5] Testing Bracket page...")
    bracket_tab = page.locator('button:has-text("淘汰赛")')
    if bracket_tab.count() > 0:
        bracket_tab.first.click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, '03_bracket.png'), full_page=True)
        print("  Bracket screenshot saved")
    else:
        print("  WARNING: Bracket tab not found")

    # 4. Test Backtest page
    print("[4/5] Testing Backtest page...")
    backtest_tab = page.locator('button:has-text("模型回溯")')
    if backtest_tab.count() > 0:
        backtest_tab.first.click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, '04_backtest.png'), full_page=True)
        print("  Backtest screenshot saved")
    else:
        print("  WARNING: Backtest tab not found")

    # 5. Go back to dashboard and try clicking a match
    print("[5/5] Testing match detail...")
    dashboard_tab = page.locator('button:has-text("首页")')
    if dashboard_tab.count() > 0:
        dashboard_tab.first.click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)

        # Try clicking on a match card
        clickable_matches = page.locator('[class*="cursor-pointer"], [class*="clickable"], a[href*="match"]')
        if clickable_matches.count() > 0:
            clickable_matches.first.click()
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, '05_match_detail.png'), full_page=True)
            print("  Match detail screenshot saved")
        else:
            # Try any card-like element
            cards = page.locator('[class*="card"], [class*="match"]')
            if cards.count() > 0:
                cards.first.click()
                page.wait_for_timeout(2000)
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, '05_match_detail.png'), full_page=True)
                print("  Match detail screenshot saved (via card click)")
            else:
                print("  WARNING: No clickable match elements found")

    # Check for console errors
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

    # Final check - reload and capture any errors
    page.goto('http://localhost:5173')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)

    browser.close()

print("\n=== Test Complete ===")
print(f"Screenshots saved to: {SCREENSHOT_DIR}")
