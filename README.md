# 2026 FIFA World Cup Prediction System

2026年世界杯预测分析平台 — 基于 ELO/Poisson 多因子模型，提供赛前预测、赔率分析、历史交锋、阵型对比、蒙特卡洛模拟等功能。

## Features

- **赛前预测** — 多因子综合预测（ELO模型 + 赔率分析 + 阵容分析 + 状态分析），给出胜平负概率、TOP5比分概率及赔率
- **赔率数据** — 多家博彩公司胜平负赔率、亚盘让球、大小球、比分赔率市场共识
- **历史交锋** — 两队历史交锋统计与详细记录
- **球员信息** — 双方阵容球员列表（号码、姓名、位置）
- **阵型对比** — 可视化阵型图（4-3-3、4-2-3-1 等）
- **近10场比赛** — 双方近期战绩，含对手国旗、比分、赛事、日期
- **小组积分榜** — 12组实时积分排名
- **淘汰赛对阵** — 32强至决赛完整对阵图
- **蒙特卡洛模拟** — 万次模拟夺冠概率、各阶段晋级率
- **回测验证** — 2018/2022世界杯历史回测，验证模型准确度
- **体彩赔率** — 自动抓取 sporttery.cn 中国体彩赔率数据

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.10+, FastAPI, SQLAlchemy, httpx |
| Frontend | React 19, TypeScript, Vite 8, Tailwind CSS 4 |
| Data | API-Football v3, football-data.org, sporttery.cn |
| Model | ELO Rating + Poisson + 多因子加权融合 |

## Quick Start

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **API-Football Key**（推荐，免费100次/天）— [注册地址](https://dashboard.api-football.com)

### 1. Clone & Install

```bash
git clone https://github.com/kingsmokez/worldcup2026.git
cd worldcup2026
```

### 2. Configure Environment

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API Key：

```env
# 主数据源（强烈推荐）— 包含球队/球员/赔率/赛程/伤停/交锋
API_FOOTBALL_KEY=your_api_football_key_here
API_FOOTBALL_PLATFORM=auto

# 备用数据源（可选）— 赔率/赛程补充
FOOTBALL_DATA_KEY=your_football_data_key_here

# 代理（国内用户可能需要）
# HTTPS_PROXY=http://127.0.0.1:7890
# HTTP_PROXY=http://127.0.0.1:7890
```

> **不配置 API Key 也能运行**，系统会使用内置的本地数据（球队ELO评分、赛程等），但赔率、球员、交锋等实时数据将不可用。

### 3. Start the System

**Windows 一键启动：**

```bash
start.bat
```

**手动启动：**

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
python server.py
# → Running on http://localhost:6100

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
# → Running on http://localhost:6101
```

打开浏览器访问 **http://localhost:6101**

## API Reference

后端启动后，访问 **http://localhost:6100/docs** 查看完整 Swagger 文档。

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard` | GET | 首页仪表盘（近期赛程+预测） |
| `/api/match/{id}` | GET | 比赛详情（预测/球员/交锋/赔率/近10场） |
| `/api/predict?team1=ARG&team2=FRA` | GET | 任意两队快速预测 |
| `/api/groups` | GET | 12组积分榜 |
| `/api/bracket` | GET | 淘汰赛对阵图 |
| `/api/teams` | GET | 全部48支球队数据 |
| `/api/team/{code}` | GET | 单支球队详情 |
| `/api/recent-matches/{code}` | GET | 球队近10场比赛 |
| `/api/injuries/{fixture_id}` | GET | 伤停/缺阵信息 |
| `/api/monte-carlo` | POST | 蒙特卡洛模拟（参数: `num_sims`） |
| `/api/backtest` | GET | 2018/2022回测结果 |
| `/api/refresh` | POST | 手动刷新数据 |
| `/api/status` | GET | 系统状态 |

## Project Structure

```
worldcup2026/
├── backend/
│   ├── server.py              # FastAPI 主服务
│   ├── predictor.py           # 预测引擎（ELO/Poisson/多因子）
│   ├── data_fetcher.py        # API 数据获取与缓存
│   ├── database.py            # SQLAlchemy 数据库层
│   ├── monte_carlo.py         # 蒙特卡洛模拟
│   ├── backtester.py          # 历史回测
│   ├── scrape_sporttery.py    # 体彩赔率爬虫（API）
│   ├── scrape_sporttery_browser.py  # 体彩赔率爬虫（Playwright）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx       # 首页仪表盘
│   │   │   ├── MatchAnalysis.tsx   # 赛前分析（6个Tab）
│   │   │   ├── Predictions.tsx     # 任意两队预测
│   │   │   ├── GroupStandings.tsx  # 小组积分榜
│   │   │   ├── Bracket.tsx        # 淘汰赛对阵图
│   │   │   ├── Formation.tsx      # 阵型可视化
│   │   │   ├── MonteCarloPanel.tsx # 蒙特卡洛模拟
│   │   │   ├── BacktestPanel.tsx   # 回测结果
│   │   │   └── ...
│   │   ├── hooks/useData.ts       # 数据层（API hooks + 类型定义）
│   │   ├── App.tsx
│   │   └── index.css              # 全局样式
│   ├── vite.config.ts
│   └── package.json
├── data/
│   ├── teams.json            # 48支球队基础数据
│   ├── wc2018.json           # 2018世界杯历史数据（回测用）
│   └── wc2022.json           # 2022世界杯历史数据（回测用）
├── .env.example              # 环境变量模板
├── start.bat                 # Windows 一键启动
└── run_scraper.bat           # 体彩赔率爬虫启动
```

## Prediction Model

### Multi-Factor Fusion

系统采用多因子加权融合模型，各因子及默认权重：

| Factor | Weight | Data Source | Description |
|--------|--------|-------------|-------------|
| ELO Model | 40% | 内置ELO评分 | ELO差值 → 胜率 + Poisson进球分布 |
| Odds Analysis | 45% | API-Football + sporttery | 多家机构赔率 → 隐含概率，含比分/让球/大小球 |
| Squad Analysis | 0%* | API-Football | 球员身价/位置深度/攻防评分 |
| Form Analysis | 15% | API-Football | 近期胜率/场均进球/势头/对手质量 |

> *权重根据数据可用性动态调整：有赔率数据时赔率权重提升，无赔率时ELO权重提升。

### Scoreline Prediction

1. ELO差值 → 期望进球数（Poisson参数 λ）
2. Poisson分布生成比分概率矩阵（0-0 到 4-4）
3. 赔率比分共识融合（如有赔率数据）
4. 输出 TOP 5 最可能比分 + 概率 + 隐含赔率

### Confidence Level

| Level | Condition |
|-------|-----------|
| High | ELO差 > 150 或 赔率共识强 |
| Medium | ELO差 50-150 |
| Low | ELO差 < 50 或 赔率分歧大 |

## Data Sources

### API-Football v3（主数据源）

- **注册**: https://dashboard.api-football.com 或 https://rapidapi.com/api-sports
- **免费额度**: 100 次/天
- **数据**: 赛程、球员、赔率、交锋、伤停、近期战绩、球队统计

### football-data.org（备用数据源）

- **注册**: https://www.football-data.org/client
- **免费额度**: 10 次/分钟
- **数据**: 赔率、赛程、积分榜

### sporttery.cn（中国体彩赔率）

- 自动抓取中国体育彩票官方赔率
- 运行 `run_scraper.bat` 或 `python backend/scrape_sporttery_browser.py`
- 需要安装 Playwright: `pip install playwright && playwright install chromium`

## Screenshots

启动后访问 http://localhost:6101，主要页面：

- **首页仪表盘** — 近期赛程卡片，显示双方国旗、ELO评分、胜平负概率条
- **赛前分析** — 点击任意比赛进入，包含6个标签页：
  - 赛前预测：综合概率 + TOP5比分(概率+赔率) + 多因子分析明细
  - 球员信息：双方阵容列表
  - 历史交锋：交锋统计 + 历史比赛记录
  - 赔率数据：胜平负赔率表 + 比分赔率 + 盘口/大小球
  - 阵型：可视化阵型图
  - 近10场：双方近期战绩（含对手国旗、比分、赛事）
- **任意两队预测** — 输入球队代码即可预测
- **小组积分榜** — 12组实时排名
- **淘汰赛对阵** — 32强到决赛完整图
- **蒙特卡洛模拟** — 万次模拟夺冠概率

## Configuration

### Port

默认端口：后端 `6100`，前端 `6101`。可在以下位置修改：

- 后端: `backend/server.py` 最后一行 `uvicorn.run(..., port=6100)`
- 前端: `frontend/vite.config.ts` 中 `server.port`

### Proxy (for China users)

如果无法直连 API-Football，在 `.env` 中配置代理：

```env
HTTPS_PROXY=http://127.0.0.1:7890
HTTP_PROXY=http://127.0.0.1:7890
```

## License

MIT
