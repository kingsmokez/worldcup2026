#!/usr/bin/env python3
"""
sporttery.cn 数据爬取脚本 (优化版)

已知 sporttery.cn 的竞彩比分页面数据来源:
1. 页面内嵌 JavaScript 变量
2. 隐藏的 API 接口
3. 静态 JSON 数据

此脚本依次尝试所有方法获取数据。

运行: cd D:\UI\world\backend && python scrape_sporttery.py
"""

import os
import sys
import json
import re
import time

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# sporttery.cn 已知的数据接口模式
# 这些是常见的 API 路径模式，需要逐个尝试
SPORTTERY_API_URLS = [
    # 竞彩比分页面
    "https://www.sporttery.cn/jc/jsq/zqbf/",
    # 可能的 API 端点
    "https://www.sporttery.cn/jc/jsq/zqbf/index.html",
    # 常见的彩票数据 API 格式
    "https://api.sporttery.cn/jc/match/list",
    "https://api.sporttery.cn/jc/zqbf/list",
    "https://www.sporttery.cn/api/jc/match/list",
    "https://www.sporttery.cn/api/jc/zqbf/list",
    # 另一种常见格式
    "https://www.sporttery.cn/jc/jsq/getMatchOddsList",
    "https://www.sporttery.cn/jc/jsq/getZqbfData",
    # 带参数的接口
    "https://www.sporttery.cn/jc/jsq/zqbf/getData",
    "https://www.sporttery.cn/jc/jsq/zqbf/matchList",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, text/html, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.sporttery.cn/jc/jsq/zqbf/",
    "X-Requested-With": "XMLHttpRequest",
}


def main():
    print("=" * 60)
    print("  sporttery.cn 数据爬取工具 (优化版)")
    print("=" * 60)
    print()

    # 1. 先尝试安装依赖
    try:
        import httpx
        print("[OK] httpx available")
    except ImportError:
        print("[Installing] httpx...")
        os.system("pip install httpx --break-system-packages 2>nul || pip install httpx 2>nul")
        import httpx

    try:
        from bs4 import BeautifulSoup
        print("[OK] beautifulsoup4 available")
    except ImportError:
        print("[Installing] beautifulsoup4 lxml...")
        os.system("pip install beautifulsoup4 lxml --break-system-packages 2>nul || pip install beautifulsoup4 lxml 2>nul")
        from bs4 import BeautifulSoup

    all_matches = []
    working_urls = []

    # 2. 逐个尝试 API 端点
    print()
    print("[Step 1] Testing API endpoints...")
    with httpx.Client(timeout=15, headers=HEADERS, follow_redirects=True) as client:
        for url in SPORTTERY_API_URLS:
            try:
                print(f"  Trying: {url[:70]}...")
                resp = client.get(url)
                print(f"    Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type', 'N/A')[:40]}, Length: {len(resp.text)}")

                if resp.status_code != 200:
                    continue

                content_type = resp.headers.get("content-type", "")

                # 尝试直接解析 JSON
                if "json" in content_type or resp.text.strip().startswith("{") or resp.text.strip().startswith("["):
                    try:
                        data = resp.json()
                        matches = extract_matches_from_json(data)
                        if matches:
                            print(f"    >>> FOUND {len(matches)} matches!")
                            all_matches.extend(matches)
                            working_urls.append(url)
                    except json.JSONDecodeError:
                        pass

                # 尝试从 HTML 中提取 JSON
                if not all_matches or "html" in content_type:
                    matches = extract_matches_from_html(resp.text)
                    if matches:
                        print(f"    >>> FOUND {len(matches)} matches in HTML!")
                        all_matches.extend(matches)
                        working_urls.append(url)

            except httpx.TimeoutException:
                print(f"    Timeout")
            except Exception as e:
                print(f"    Error: {str(e)[:50]}")

    # 3. 如果还没有数据，尝试 Playwright
    if not all_matches:
        print()
        print("[Step 2] Trying Playwright browser...")
        try:
            from playwright.sync_api import sync_playwright

            # Check if chromium is installed
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()

                    # 监听所有网络请求
                    api_responses = []

                    def handle_response(response):
                        url = response.url
                        if any(kw in url.lower() for kw in ["match", "odds", "zqbf", "data", "list", "api"]):
                            try:
                                ct = response.headers.get("content-type", "")
                                if "json" in ct:
                                    body = response.json()
                                    api_responses.append({"url": url, "data": body})
                                    print(f"    [API Captured] {url[:80]}...")
                            except Exception:
                                pass

                    page.on("response", handle_response)

                    print("  Navigating to sporttery.cn...")
                    page.goto("https://www.sporttery.cn/jc/jsq/zqbf/",
                              wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(5000)

                    # Scroll to trigger lazy loading
                    for i in range(5):
                        page.evaluate("window.scrollBy(0, 500)")
                        page.wait_for_timeout(1000)

                    # Save screenshot for debugging
                    screenshot_path = os.path.join(os.path.dirname(__file__), "sporttery_screenshot.png")
                    page.screenshot(path=screenshot_path, full_page=True)
                    print(f"  Screenshot saved: {screenshot_path}")

                    # Save HTML for debugging
                    html = page.content()
                    html_path = os.path.join(os.path.dirname(__file__), "sporttery_debug.html")
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"  HTML saved: {html_path}")

                    # Parse captured API data
                    for resp in api_responses:
                        matches = extract_matches_from_json(resp["data"])
                        if matches:
                            print(f"  >>> FOUND {len(matches)} matches from API: {resp['url'][:60]}...")
                            all_matches.extend(matches)

                    # If still no data, try parsing the page HTML
                    if not all_matches:
                        matches = extract_matches_from_html(html)
                        if matches:
                            print(f"  >>> FOUND {len(matches)} matches from page HTML!")
                            all_matches.extend(matches)

                    browser.close()

            except Exception as e:
                print(f"  Playwright error: {e}")
                # Try installing chromium
                if "chromium" in str(e).lower() or "executable" in str(e).lower():
                    print("  Installing Chromium...")
                    os.system("playwright install chromium")
                    print("  Please run this script again after Chromium is installed.")

        except ImportError:
            print("  Playwright not installed. Install with:")
            print("    pip install playwright")
            print("    playwright install chromium")

    # 4. 保存结果
    print()
    print("=" * 60)
    if all_matches:
        # 去重
        seen = set()
        unique = []
        for m in all_matches:
            key = f"{m.get('home_team','')}|{m.get('away_team','')}|{m.get('match_date','')}"
            if key not in seen:
                seen.add(key)
                unique.append(m)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, "sporttery_odds.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(unique, f, ensure_ascii=False, indent=2)

        print(f"  SUCCESS! {len(unique)} matches (from {len(all_matches)} raw, {len(unique)} unique)")
        print(f"  Saved to: {output_path}")
        print(f"  Working URLs: {working_urls}")
        print()
        print("  Sample data:")
        for m in unique[:5]:
            ht = m.get("home_team", "?")
            at = m.get("away_team", "?")
            sw = m.get("sp_win") or m.get("home", 0)
            sd = m.get("sp_draw") or m.get("draw", 0)
            sl = m.get("sp_loss") or m.get("away", 0)
            print(f"    {ht} vs {at} | SP: {sw}/{sd}/{sl}")
    else:
        print("  NO DATA FOUND")
        print()
        print("  Debugging tips:")
        print("  1. Open https://www.sporttery.cn/jc/jsq/zqbf/ in Chrome")
        print("  2. Press F12 -> Network tab -> Refresh page")
        print("  3. Look for XHR/Fetch requests returning JSON data")
        print("  4. Send me the API URL you find")

    print("=" * 60)


def extract_matches_from_json(data) -> list:
    """从 JSON 数据中提取比赛列表"""
    matches = []

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # Try common keys
        for key in ["data", "list", "matchList", "result", "matches", "matchs",
                     "matchOddsList", "oddsList", "body", "value", "rows"]:
            val = data.get(key)
            if isinstance(val, list) and len(val) > 0:
                items = val
                break
        else:
            # If no list key found, check if data itself looks like a match
            if any(k in data for k in ["spWin", "spH", "homeTeamName", "matchNum"]):
                items = [data]
            else:
                return []
    else:
        return []

    for item in items:
        if not isinstance(item, dict):
            continue

        # 提取球队名称 - 尝试所有可能的字段名
        home = (item.get("homeTeamName") or item.get("homeName") or
                item.get("homeTeam") or item.get("hostName") or
                item.get("hName") or item.get("home") or "")
        away = (item.get("awayTeamName") or item.get("awayName") or
                item.get("awayTeam") or item.get("guestName") or
                item.get("aName") or item.get("away") or "")

        # 提取 SP/赔率
        sp_win = (item.get("spWin") or item.get("spH") or item.get("hSp") or
                  item.get("winSp") or item.get("homeOdds") or item.get("h") or 0)
        sp_draw = (item.get("spDraw") or item.get("spD") or item.get("dSp") or
                   item.get("drawSp") or item.get("drawOdds") or item.get("d") or 0)
        sp_loss = (item.get("spLoss") or item.get("spA") or item.get("aSp") or
                   item.get("lossSp") or item.get("awayOdds") or item.get("a") or 0)

        # 提取日期
        match_date = (item.get("matchDate") or item.get("matchTime") or
                      item.get("date") or item.get("startTime") or
                      item.get("saleEndTime") or item.get("playDate") or "")

        # 提取赛事编号
        match_num = str(item.get("matchNum") or item.get("matchId") or
                        item.get("id") or item.get("num") or "")

        # 只保存有赔率数据的条目
        try:
            has_odds = float(sp_win) > 0 and float(sp_draw) > 0 and float(sp_loss) > 0
        except (ValueError, TypeError):
            has_odds = False

        entry = {
            "match_num": match_num,
            "home_team": home,
            "away_team": away,
            "match_date": match_date,
            "source": "sporttery.cn",
            "raw_keys": list(item.keys())[:20],  # 保留字段名用于调试
        }

        if has_odds:
            entry["sp_win"] = float(sp_win)
            entry["sp_draw"] = float(sp_draw)
            entry["sp_loss"] = float(sp_loss)

        # 让球
        handicap = item.get("letBall") or item.get("handicap") or item.get("let") or item.get("rq")
        if handicap is not None:
            try:
                entry["handicap"] = float(handicap)
            except (ValueError, TypeError):
                pass

        # 大小球
        ou = item.get("bs0") or item.get("sizeLine") or item.get("overUnderLine") or item.get("dxq")
        if ou is not None:
            try:
                entry["over_under_line"] = float(ou)
            except (ValueError, TypeError):
                pass

        if home or away or match_num:
            matches.append(entry)

    return matches


def extract_matches_from_html(html: str) -> list:
    """从 HTML 页面中提取嵌入的 JSON 数据"""
    matches = []

    # 方法1: 查找 script 标签中的 JSON
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script"):
        text = script.string or ""
        if not text or len(text) < 50:
            continue

        # 查找 JSON 数组或对象
        patterns = [
            r'(?:var|let|const)\s+\w+\s*=\s*(\[[\s\S]+?\]);',
            r'(?:var|let|const)\s+\w+\s*=\s*(\{[\s\S]+?\});',
            r'window\.\w+\s*=\s*(\{[\s\S]+?\});',
            r'"matchList"\s*:\s*(\[[\s\S]+?\])',
            r'"data"\s*:\s*(\[[\s\S]+?\])',
        ]

        for pattern in patterns:
            try:
                match = re.search(pattern, text)
                if match:
                    json_str = match.group(1)
                    data = json.loads(json_str)
                    extracted = extract_matches_from_json(data)
                    matches.extend(extracted)
            except (json.JSONDecodeError, re.error):
                continue

    # 方法2: 全文搜索 JSON
    json_pattern = r'\{[^{}]*"spWin"[^{}]*\}|\{[^{}]*"spH"[^{}]*\}|\{[^{}]*"homeTeamName"[^{}]*\}'
    for match in re.finditer(json_pattern, html):
        try:
            data = json.loads(match.group(0))
            extracted = extract_matches_from_json(data)
            matches.extend(extracted)
        except json.JSONDecodeError:
            pass

    return matches


if __name__ == "__main__":
    main()
