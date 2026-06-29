@echo off
REM sporttery.cn 爬取脚本 - 一键安装依赖并运行
REM ================================================

cd /d "D:\UI\world\backend"

echo.
echo [Step 1] Installing dependencies...
pip install playwright beautifulsoup4 lxml --break-system-packages 2>nul
if errorlevel 1 (
    pip install playwright beautifulsoup4 lxml 2>nul
)

echo [Step 2] Installing Chromium browser for Playwright...
playwright install chromium

echo.
echo [Step 3] Running sporttery.cn scraper...
python scrape_sporttery_browser.py

echo.
echo Done! Check the output above for results.
echo Data will be saved to: D:\UI\world\data\sporttery_odds.json
echo.
pause