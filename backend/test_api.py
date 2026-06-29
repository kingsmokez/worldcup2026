#!/usr/bin/env python3
"""
数据源连通性测试脚本

测试 API-Football 和 football-data.org 是否可用。
运行方式: python test_api.py
"""

import os
import sys
import asyncio

# 加载 .env 文件
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_FILE = os.path.join(_PROJECT_ROOT, ".env")
if os.path.exists(_ENV_FILE):
    with open(_ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and value and key not in os.environ:
                os.environ[key] = value

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import DataFetcher


async def test_api_football():
    """测试 API-Football 连通性。"""
    api_key = os.environ.get("API_FOOTBALL_KEY", "")
    if not api_key:
        print("❌ API_FOOTBALL_KEY 未配置")
        print("   注册地址: https://dashboard.api-football.com/register")
        print("   或:       https://rapidapi.com/api-sports/api/api-football-1")
        return False

    print(f"✅ API_FOOTBALL_KEY 已配置 (长度: {len(api_key)}, 前缀: {api_key[:6]}...)")

    fetcher = DataFetcher()
    try:
        # 测试1: 获取球队数据
        print("\n📡 测试1: 获取世界杯球队数据...")
        teams = await fetcher.fetch_teams_from_api()
        if teams:
            print(f"   ✅ 成功获取 {len(teams)} 支球队")
        else:
            print("   ⚠ 未获取到球队数据 (可能赛季数据尚未开放)")

        # 测试2: 获取赛程
        print("\n📡 测试2: 获取世界杯赛程...")
        fixtures = await fetcher.fetch_fixtures_from_api()
        if fixtures:
            print(f"   ✅ 成功获取 {len(fixtures)} 场比赛")
        else:
            print("   ⚠ 未获取到赛程数据 (2026赛季可能尚未发布)")

        # 测试3: 获取积分榜
        print("\n📡 测试3: 获取积分榜...")
        standings = await fetcher.fetch_standings_from_api()
        if standings:
            print(f"   ✅ 成功获取 {len(standings)} 个小组积分")
        else:
            print("   ⚠ 未获取到积分数据")

        # 测试4: 测试获取某支球队的近10场
        print("\n📡 测试4: 获取球队近期比赛 (巴西 id=6)...")
        form = await fetcher.fetch_team_form_from_api(6, last=10)
        if form and form.get("available"):
            print(f"   ✅ 巴西近{form['total']}场: {form['form']} (胜率{form['win_rate']*100:.0f}%)")
        else:
            print("   ⚠ 未获取到近期比赛数据")

        # 测试5: 测试获取球员数据
        print("\n📡 测试5: 获取球队阵容 (巴西 id=6)...")
        squad = await fetcher.fetch_squad_from_api(6)
        if squad:
            print(f"   ✅ 巴西阵容: {len(squad)} 名球员")
            for p in squad[:3]:
                print(f"      {p.get('name', '?')} #{p.get('number', '?')} {p.get('position_zh', '?')}")
        else:
            print("   ⚠ 未获取到阵容数据")

        # 测试6: 检查剩余配额
        print("\n📊 今日API使用情况:")
        if hasattr(fetcher, 'cache') and fetcher.cache:
            count = fetcher.cache.get_request_count()
            print(f"   今日已用: {count}/100 次")

        return True
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return False
    finally:
        await fetcher.close()


async def test_football_data():
    """测试 football-data.org 连通性。"""
    fd_key = os.environ.get("FOOTBALL_DATA_KEY", "")
    if not fd_key:
        print("\n⚠️  FOOTBALL_DATA_KEY 未配置 (可选，作为备用数据源)")
        print("   注册地址: https://www.football-data.org/client/register")
        return False

    print(f"\n✅ FOOTBALL_DATA_KEY 已配置 (长度: {len(fd_key)})")

    import httpx
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.football-data.org/v4/competitions",
                headers={"X-Auth-Token": fd_key},
            )
            if resp.status_code == 200:
                data = resp.json()
                count = len(data.get("competitions", []))
                print(f"   ✅ 连通成功，可访问 {count} 个赛事")
                return True
            elif resp.status_code == 403:
                print("   ❌ 403 - API Key 无效或已过期")
                return False
            else:
                print(f"   ❌ 请求失败: HTTP {resp.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False


async def main():
    print("=" * 60)
    print("  2026 世界杯预测系统 - 数据源连通性测试")
    print("=" * 60)

    api_ok = await test_api_football()
    fd_ok = await test_football_data()

    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)

    if api_ok:
        print("  ✅ API-Football: 可用 (主数据源)")
    else:
        print("  ❌ API-Football: 不可用 (将使用本地静态数据)")
        if not os.environ.get("API_FOOTBALL_KEY", ""):
            print("     → 请在 .env 文件中设置 API_FOOTBALL_KEY")
            print("     → 注册地址: https://dashboard.api-football.com/register")

    if fd_ok:
        print("  ✅ football-data.org: 可用 (备用数据源)")
    else:
        print("  ⬜ football-data.org: 未配置 (可选)")

    print()

    if api_ok:
        print("🚀 配置完成！启动后端服务即可实时获取数据：")
        print("   cd backend && python server.py")
    else:
        print("💡 快速配置步骤：")
        print("   1. 访问 https://dashboard.api-football.com/register 注册免费账户")
        print("   2. 在 Dashboard > API Keys 获取密钥")
        print("   3. 编辑 .env 文件，填入密钥:")
        print(f"      API_FOOTBALL_KEY=你的密钥")
        print("   4. 重新运行此测试: python test_api.py")


if __name__ == "__main__":
    asyncio.run(main())
