#!/usr/bin/env python3
"""
sporttery.cn 数据爬取脚本 (Playwright 浏览器版)

使用无头浏览器获取动态渲染的页面数据。
比 requests 版更可靠，因为 sporttery.cn 是 JS 渲染的。

安装:
  pip install playwright
  playwright install chromium

运行: cd D:\UI\world\backend && python scrape_sporttery_browser.py
"""

import os
import sys
import json
import time
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("请先安装 Playwright:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)


BASE_URL = "https://www.sporttery.cn/jc/jsq/zqbf/"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def scrape_with_playwright():
    """使用 Playwright 浏览器获取 sporttery.cn 数据"""
    all_matches = []

    with sync_playwright() as p:
        print("[Launching] Chromium browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )

        page = context.new_page()

        # 监听网络请求，捕获 API 数据
        api_responses = []

        def handle_response(response):
            url = response.url
            if any(keyword in url for keyword in ["match", "odds", "zqbf", "list", "data", "api"]):
                try:
                    if "json" in response.headers.get("content-type", "") or url.endswith(".json"):
                        body = response.json()
                        api_responses.append({
                            "url": url,
                            "data": body,
                        })
                        print(f"  [API] {url[:80]}... => {type(body).__name__}")
                except Exception:
                    pass

        page.on("response", handle_response)

        print(f"[Navigating] {BASE_URL}")
        try:
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"  [Warn] Navigation timeout (may be OK): {e}")

        # 等待页面加载
        print("[Waiting] Page loading...")
        time.sleep(5)

        # 尝试点击"竞彩足球"标签（如果有）
        try:
            tabs = page.query_selector_all(".tab-item, .nav-item, [class*='tab']")
            for tab in tabs:
                text = tab.inner_text()
                if "竞彩" in text or "足球" in text or "比分" in text:
                    tab.click()
                    time.sleep(2)
                    break
        except Exception:
            pass

        # 获取页面 HTML
        html = page.content()
        debug_path = os.path.join(os.path.dirname(__file__), "sporttery_debug_browser.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Debug] HTML saved to {debug_path}")

        # 方法1: 从捕获的 API 响应中提取数据
        print()
        print(f"[API] Captured {len(api_responses)} API responses")
        for resp in api_responses:
            data = resp["data"]
            if isinstance(data, list) and len(data) > 0:
                all_matches.extend(data)
                print(f"  [Found] {len(data)} items from {resp['url'][:60]}...")
            elif isinstance(data, dict):
                for key in ["data", "list", "matchList", "result", "matches"]:
                    if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                        all_matches.extend(data[key])
                        print(f"  [Found] {len(data[key])} items (key={key}) from {resp['url'][:60]}...")

        # 方法2: 用 JavaScript 直接提取页面数据
        if not all_matches:
            print()
            print("[JS] Extracting data from page DOM...")
            js_data = page.evaluate("""
                () => {
                    const results = [];
                    // Try to find match data in common React/Vue state
                    if (window.__INITIAL_STATE__) {
                        return JSON.stringify(window.__INITIAL_STATE__);
                    }
                    if (window.__NUXT__) {
                        return JSON.stringify(window.__NUXT__);
                    }

                    // Try to find table rows with match data
                    const rows = document.querySelectorAll('tr, .match-item, .match-row, [class*="match"]');
                    for (const row of rows) {
                        const cells = row.querySelectorAll('td, .cell, span, [class*="sp"], [class*="odds"]');
                        const texts = [];
                        for (const cell of cells) {
                            const t = cell.textContent.trim();
                            if (t) texts.push(t);
                        }
                        if (texts.length >= 3) {
                            results.push(texts);
                        }
                    }
                    return JSON.stringify(results);
                }
            """)

            try:
                parsed = json.loads(js_data)
                if isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, list) and len(item) >= 3:
                            all_matches.append({"raw": item, "source": "dom"})
                elif isinstance(parsed, dict):
                    for key in ["data", "list", "matchList"]:
                        if key in parsed and isinstance(parsed[key], list):
                            all_matches.extend(parsed[key])
            except json.JSONDecodeError:
                pass

        # 方法3: 滚动页面加载更多数据
        if not all_matches:
            print()
            print("[Scroll] Scrolling to load more data...")
            for i in range(5):
                page.evaluate("window.scrollBy(0, 500)")
                time.sleep(1)

            # Re-check API responses after scrolling
            for resp in api_responses:
                data = resp["data"]
                if isinstance(data, list) and len(data) > 0 and not any(data is m for m in all_matches):
                    all_matches.extend(data)

        # 方法4: 尝试直接访问已知的 API 端点
        if not all_matches:
            print()
            print("[Direct] Trying known API endpoints...")
            api_urls = [
                "https://www.sporttery.cn/api/jc/match/list",
                "https://www.sporttery.cn/api/jc/zqbf/list",
            ]
            for url in api_urls:
                try:
                    resp = page.evaluate(f'fetch("{url}").then(r => r.json()).then(d => JSON.stringify(d))')
                    if resp:
                        data = json.loads(resp)
                        if isinstance(data, list):
                            all_matches.extend(data)
                        elif isinstance(data, dict):
                            for key in ["data", "list", "result"]:
                                if key in data and isinstance(data[key], list):
                                    all_matches.extend(data[key])
                except Exception:
                    pass

        # 截图保存
        screenshot_path = os.path.join(os.path.dirname(__file__), "sporttery_screenshot.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"[Screenshot] Saved to {screenshot_path}")

        browser.close()

    return all_matches


def parse_sporttery_data(raw_data: list) -> list:
    """将原始数据转换为统一格式"""
    parsed = []
    for item in raw_data:
        if not isinstance(item, dict):
            continue

        # 尝试多种字段名
        home = (item.get("homeTeamName") or item.get("homeName") or
                item.get("home") or item.get("hostName") or "")
        away = (item.get("awayTeamName") or item.get("awayName") or
                item.get("away") or item.get("guestName") or "")

        sp_win = (item.get("spWin") or item.get("spH") or
                  item.get("hSp") or item.get("winSp") or 0)
        sp_draw = (item.get("spDraw") or item.get("spD") or
                   item.get("dSp") or item.get("drawSp") or 0)
        sp_loss = (item.get("spLoss") or item.get("spA") or
                   item.get("aSp") or item.get("lossSp") or 0)

        match_date = (item.get("matchDate") or item.get("date") or
                      item.get("matchTime") or item.get("startTime") or "")

        match_num = item.get("matchNum") or item.get("matchId") or item.get("id") or ""

        entry = {
            "match_num": str(match_num),
            "home_team": home,
            "away_team": away,
            "match_date": match_date,
            "sp_win": float(sp_win) if sp_win else 0,
            "sp_draw": float(sp_draw) if sp_draw else 0,
            "sp_loss": float(sp_loss) if sp_loss else 0,
            "source": "sporttery.cn",
            "raw": item,  # 保留原始数据
        }

        # 提取让球
        handicap = item.get("letBall") or item.get("handicap") or item.get("let")
        if handicap is not None:
            try:
                entry["handicap"] = float(handicap)
            except (ValueError, TypeError):
                pass

        # 提取大小球
        ou = item.get("bs0") or item.get("sizeLine") or item.get("overUnderLine")
        if ou is not None:
            try:
                entry["over_under_line"] = float(ou)
            except (ValueError, TypeError):
                pass

        if home or away:
            parsed.append(entry)

    return parsed


def main():
    print("=" * 60)
    print("  sporttery.cn 数据爬取 (Playwright 浏览器版)")
    print("=" * 60)
    print()

    raw_data = scrape_with_playwright()

    # 解析数据
    parsed_data = parse_sporttery_data(raw_data)

    # 也保存原始数据
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    raw_path = os.path.join(OUTPUT_DIR, "sporttery_raw.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved] Raw data: {raw_path} ({len(raw_data)} items)")

    if parsed_data:
        parsed_path = os.path.join(OUTPUT_DIR, "sporttery_odds.json")
        with open(parsed_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        print(f"[Saved] Parsed data: {parsed_path} ({len(parsed_data)} items)")

        print("\n数据样例:")
        for m in parsed_data[:3]:
            print(f"  {m['home_team']} vs {m['away_team']} | "
                  f"SP: {m['sp_win']}/{m['sp_draw']}/{m['sp_loss']} | "
                  f"日期: {m['match_date']}")
    else:
        print("\n未能解析到比赛数据")
        print("请查看:")
        print(f"  1. 截图: {os.path.join(os.path.dirname(__file__), 'sporttery_screenshot.png')}")
        print(f"  2. HTML: {os.path.join(os.path.dirname(__file__), 'sporttery_debug_browser.html')}")
        print(f"  3. 原始API: {raw_path}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
