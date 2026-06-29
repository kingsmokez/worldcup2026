"""
World Cup 2026 Database Layer

Uses SQLAlchemy with aiosqlite for async SQLite access.
Provides ORM models and data access functions.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, create_engine, Text,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, relationship

# ─────────────────────────────────────────────
# Database setup
# ─────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "worldcup2026.db")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────
# ORM Models
# ─────────────────────────────────────────────

class Team(Base):
    __tablename__ = "teams"

    code = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    name_zh = Column(String(100), nullable=False)
    group_name = Column(String(10), nullable=False)
    elo_rating = Column(Float, default=1800)
    fifa_rank = Column(Integer, default=30)
    flag_emoji = Column(String(10), default="")
    confederation = Column(String(20), default="")
    formation = Column(String(10), default="4-3-3")
    recent_form = Column(String(20), default="")
    goals_scored_last10 = Column(Integer, default=0)
    goals_conceded_last10 = Column(Integer, default=0)


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    round = Column(String(50), default="Group")
    group_name = Column(String(10), default="")
    date = Column(String(20), default="")
    kick_off = Column(String(30), default="")  # UTC时间，如 "2026-06-11T19:00:00Z"
    team1 = Column(String(10), nullable=False)
    team2 = Column(String(10), nullable=False)
    score1 = Column(Integer, nullable=True)
    score2 = Column(Integer, nullable=True)
    score1_pen = Column(Integer, nullable=True)
    score2_pen = Column(Integer, nullable=True)
    status = Column(String(20), default="upcoming")  # upcoming, live, finished
    stage = Column(String(20), default="group")  # group, round16, quarter, semi, final, third


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_code = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    name_zh = Column(String(100), nullable=False)
    position = Column(String(10), default="")
    position_zh = Column(String(20), default="")
    number = Column(Integer, nullable=True)


class Odds(Base):
    __tablename__ = "odds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, nullable=False)
    bookmaker = Column(String(50), default="")
    home = Column(Float, nullable=True)
    draw = Column(Float, nullable=True)
    away = Column(Float, nullable=True)


# ─────────────────────────────────────────────
# Database initialization
# ─────────────────────────────────────────────

def init_db():
    """Create all tables."""
    Base.metadata.create_all(engine)
    print(f"[DB] Database initialized at {DB_PATH}")


# ─────────────────────────────────────────────
# Data loading helpers
# ─────────────────────────────────────────────

def _load_json(filename: str) -> dict:
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_teams_from_file(session: Session, filename: str = "teams.json") -> int:
    """Load teams and squad players from JSON file into database."""
    data = _load_json(filename)
    teams = data.get("teams", [])
    count = 0
    for t in teams:
        existing = session.query(Team).filter(Team.code == t["code"]).first()
        if existing:
            for key in ["name", "name_zh", "group_name", "elo_rating", "fifa_rank",
                        "flag_emoji", "confederation", "formation", "recent_form",
                        "goals_scored_last10", "goals_conceded_last10"]:
                if key in t:
                    setattr(existing, key, t[key])
        else:
            team = Team(
                code=t["code"],
                name=t.get("name", ""),
                name_zh=t.get("name_zh", ""),
                group_name=t.get("group", ""),
                elo_rating=t.get("elo_rating", 1800),
                fifa_rank=t.get("fifa_rank", 30),
                flag_emoji=t.get("flag_emoji", ""),
                confederation=t.get("confederation", ""),
                formation=t.get("formation", "4-3-3"),
                recent_form=t.get("recent_form", ""),
                goals_scored_last10=t.get("goals_scored_last10", 0),
                goals_conceded_last10=t.get("goals_conceded_last10", 0),
            )
            session.add(team)
        count += 1

        # Load squad players from the "squad" field
        # Always delete old players and reload from file
        session.query(Player).filter(Player.team_code == t["code"]).delete()

        for player in t.get("squad", []):
            session.add(Player(
                team_code=t["code"],
                name=player["name"],
                name_zh=player.get("name_zh", player["name"]),
                position=player.get("position", ""),
                position_zh=player.get("position_zh", ""),
                number=player.get("number", None),
            ))
        print(f"[DB] Loaded {len(t.get('squad', []))} players for {t['code']}")

    session.commit()
    return count


def load_matches_from_data(session: Session, year: int = 2026) -> int:
    """Load match schedule. For 2026, loads upcoming match schedule."""
    count = 0
    if year == 2026:
        # 清除旧的2026比赛数据，确保重新加载
        session.query(Match).filter(Match.stage == "group").delete()
        session.commit()

        # 2026世界杯小组赛真实赛程时间（UTC时间）
        # 北京时间 = UTC + 8
        # 小组赛已完赛，比分已录入
        WORLD_CUP_2026_SCHEDULE = [
            # A组 (墨西哥、南非、韩国、捷克) - 第1轮
            {"team1": "MEX", "team2": "RSA", "group": "A", "date": "2026-06-11", "kick_off": "2026-06-11T19:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            {"team1": "KOR", "team2": "CZE", "group": "A", "date": "2026-06-12", "kick_off": "2026-06-12T02:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 1, "status": "finished"},
            # A组 - 第2轮
            {"team1": "CZE", "team2": "RSA", "group": "A", "date": "2026-06-18", "kick_off": "2026-06-18T16:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 1, "status": "finished"},
            {"team1": "MEX", "team2": "KOR", "group": "A", "date": "2026-06-19", "kick_off": "2026-06-19T01:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 0, "status": "finished"},
            # A组 - 第3轮
            {"team1": "CZE", "team2": "MEX", "group": "A", "date": "2026-06-25", "kick_off": "2026-06-25T01:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 3, "status": "finished"},
            {"team1": "RSA", "team2": "KOR", "group": "A", "date": "2026-06-25", "kick_off": "2026-06-25T01:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 0, "status": "finished"},

            # B组 (加拿大、波黑、卡塔尔、瑞士) - 第1轮
            {"team1": "CAN", "team2": "BIH", "group": "B", "date": "2026-06-12", "kick_off": "2026-06-12T19:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 1, "status": "finished"},
            {"team1": "QAT", "team2": "SUI", "group": "B", "date": "2026-06-13", "kick_off": "2026-06-13T19:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 1, "status": "finished"},
            # B组 - 第2轮
            {"team1": "SUI", "team2": "BIH", "group": "B", "date": "2026-06-18", "kick_off": "2026-06-18T19:00:00Z", "round": "Group", "stage": "group", "score1": 4, "score2": 1, "status": "finished"},
            {"team1": "CAN", "team2": "QAT", "group": "B", "date": "2026-06-18", "kick_off": "2026-06-18T22:00:00Z", "round": "Group", "stage": "group", "score1": 6, "score2": 0, "status": "finished"},
            # B组 - 第3轮
            {"team1": "SUI", "team2": "CAN", "group": "B", "date": "2026-06-24", "kick_off": "2026-06-24T19:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 1, "status": "finished"},
            {"team1": "BIH", "team2": "QAT", "group": "B", "date": "2026-06-24", "kick_off": "2026-06-24T19:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 1, "status": "finished"},

            # C组 (巴西、摩洛哥、海地、苏格兰) - 第1轮
            {"team1": "BRA", "team2": "MAR", "group": "C", "date": "2026-06-13", "kick_off": "2026-06-13T22:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 1, "status": "finished"},
            {"team1": "HAI", "team2": "SCO", "group": "C", "date": "2026-06-14", "kick_off": "2026-06-14T01:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 1, "status": "finished"},
            # C组 - 第2轮
            {"team1": "SCO", "team2": "MAR", "group": "C", "date": "2026-06-19", "kick_off": "2026-06-19T22:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 1, "status": "finished"},
            {"team1": "BRA", "team2": "HAI", "group": "C", "date": "2026-06-20", "kick_off": "2026-06-20T01:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 0, "status": "finished"},
            # C组 - 第3轮
            {"team1": "SCO", "team2": "BRA", "group": "C", "date": "2026-06-24", "kick_off": "2026-06-24T22:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 3, "status": "finished"},
            {"team1": "MAR", "team2": "HAI", "group": "C", "date": "2026-06-24", "kick_off": "2026-06-24T22:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 0, "status": "finished"},

            # D组 (美国、巴拉圭、澳大利亚、土耳其) - 第1轮
            {"team1": "USA", "team2": "PAR", "group": "D", "date": "2026-06-13", "kick_off": "2026-06-13T01:00:00Z", "round": "Group", "stage": "group", "score1": 4, "score2": 1, "status": "finished"},
            {"team1": "AUS", "team2": "TUR", "group": "D", "date": "2026-06-14", "kick_off": "2026-06-14T04:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            # D组 - 第2轮
            {"team1": "USA", "team2": "AUS", "group": "D", "date": "2026-06-19", "kick_off": "2026-06-19T19:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            {"team1": "TUR", "team2": "PAR", "group": "D", "date": "2026-06-20", "kick_off": "2026-06-20T04:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 1, "status": "finished"},
            # D组 - 第3轮
            {"team1": "TUR", "team2": "USA", "group": "D", "date": "2026-06-26", "kick_off": "2026-06-26T02:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 2, "status": "finished"},
            {"team1": "PAR", "team2": "AUS", "group": "D", "date": "2026-06-26", "kick_off": "2026-06-26T02:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 1, "status": "finished"},

            # E组 (德国、库拉索、科特迪瓦、厄瓜多尔) - 第1轮
            {"team1": "GER", "team2": "CUW", "group": "E", "date": "2026-06-14", "kick_off": "2026-06-14T17:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 0, "status": "finished"},
            {"team1": "CIV", "team2": "ECU", "group": "E", "date": "2026-06-14", "kick_off": "2026-06-14T23:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 2, "status": "finished"},
            # E组 - 第2轮
            {"team1": "GER", "team2": "CIV", "group": "E", "date": "2026-06-20", "kick_off": "2026-06-20T20:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 1, "status": "finished"},
            {"team1": "ECU", "team2": "CUW", "group": "E", "date": "2026-06-21", "kick_off": "2026-06-21T00:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 0, "status": "finished"},
            # E组 - 第3轮
            {"team1": "ECU", "team2": "GER", "group": "E", "date": "2026-06-25", "kick_off": "2026-06-25T20:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 2, "status": "finished"},
            {"team1": "CUW", "team2": "CIV", "group": "E", "date": "2026-06-25", "kick_off": "2026-06-25T20:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 1, "status": "finished"},

            # F组 (荷兰、日本、瑞典、突尼斯) - 第1轮
            {"team1": "NED", "team2": "JPN", "group": "F", "date": "2026-06-14", "kick_off": "2026-06-14T20:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            {"team1": "SWE", "team2": "TUN", "group": "F", "date": "2026-06-15", "kick_off": "2026-06-15T02:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 0, "status": "finished"},
            # F组 - 第2轮
            {"team1": "TUN", "team2": "JPN", "group": "F", "date": "2026-06-20", "kick_off": "2026-06-20T04:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 1, "status": "finished"},
            {"team1": "NED", "team2": "SWE", "group": "F", "date": "2026-06-20", "kick_off": "2026-06-20T17:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 0, "status": "finished"},
            # F组 - 第3轮
            {"team1": "JPN", "team2": "SWE", "group": "F", "date": "2026-06-25", "kick_off": "2026-06-25T23:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 1, "status": "finished"},
            {"team1": "TUN", "team2": "NED", "group": "F", "date": "2026-06-25", "kick_off": "2026-06-25T23:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 2, "status": "finished"},

            # G组 (比利时、埃及、伊朗、新西兰) - 第1轮
            {"team1": "BEL", "team2": "EGY", "group": "G", "date": "2026-06-15", "kick_off": "2026-06-15T19:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            {"team1": "IRN", "team2": "NZL", "group": "G", "date": "2026-06-16", "kick_off": "2026-06-16T01:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 0, "status": "finished"},
            # G组 - 第2轮
            {"team1": "BEL", "team2": "IRN", "group": "G", "date": "2026-06-21", "kick_off": "2026-06-21T19:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 0, "status": "finished"},
            {"team1": "NZL", "team2": "EGY", "group": "G", "date": "2026-06-22", "kick_off": "2026-06-22T01:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 2, "status": "finished"},
            # G组 - 第3轮
            {"team1": "EGY", "team2": "IRN", "group": "G", "date": "2026-06-27", "kick_off": "2026-06-27T03:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            {"team1": "NZL", "team2": "BEL", "group": "G", "date": "2026-06-27", "kick_off": "2026-06-27T03:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 3, "status": "finished"},

            # H组 (西班牙、佛得角、沙特、乌拉圭) - 第1轮
            {"team1": "ESP", "team2": "CPV", "group": "H", "date": "2026-06-15", "kick_off": "2026-06-15T16:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 0, "status": "finished"},
            {"team1": "KSA", "team2": "URU", "group": "H", "date": "2026-06-15", "kick_off": "2026-06-15T22:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 2, "status": "finished"},
            # H组 - 第2轮
            {"team1": "ESP", "team2": "KSA", "group": "H", "date": "2026-06-21", "kick_off": "2026-06-21T16:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            {"team1": "URU", "team2": "CPV", "group": "H", "date": "2026-06-21", "kick_off": "2026-06-21T22:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 0, "status": "finished"},
            # H组 - 第3轮
            {"team1": "CPV", "team2": "KSA", "group": "H", "date": "2026-06-27", "kick_off": "2026-06-27T00:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 2, "status": "finished"},
            {"team1": "URU", "team2": "ESP", "group": "H", "date": "2026-06-27", "kick_off": "2026-06-27T00:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 2, "status": "finished"},

            # I组 (法国、塞内加尔、伊拉克、挪威) - 第1轮
            {"team1": "FRA", "team2": "SEN", "group": "I", "date": "2026-06-15", "kick_off": "2026-06-15T19:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 0, "status": "finished"},
            {"team1": "IRQ", "team2": "NOR", "group": "I", "date": "2026-06-15", "kick_off": "2026-06-15T22:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 2, "status": "finished"},
            # I组 - 第2轮
            {"team1": "FRA", "team2": "IRQ", "group": "I", "date": "2026-06-22", "kick_off": "2026-06-22T21:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            {"team1": "NOR", "team2": "SEN", "group": "I", "date": "2026-06-23", "kick_off": "2026-06-23T00:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 1, "status": "finished"},
            # I组 - 第3轮
            {"team1": "NOR", "team2": "FRA", "group": "I", "date": "2026-06-26", "kick_off": "2026-06-26T19:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 1, "status": "finished"},
            {"team1": "SEN", "team2": "IRQ", "group": "I", "date": "2026-06-26", "kick_off": "2026-06-26T19:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},

            # J组 (阿根廷、阿尔及利亚、奥地利、约旦) - 第1轮
            {"team1": "ARG", "team2": "ALG", "group": "J", "date": "2026-06-17", "kick_off": "2026-06-17T01:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 0, "status": "finished"},
            {"team1": "AUT", "team2": "JOR", "group": "J", "date": "2026-06-17", "kick_off": "2026-06-17T04:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            # J组 - 第2轮
            {"team1": "ARG", "team2": "AUT", "group": "J", "date": "2026-06-22", "kick_off": "2026-06-22T17:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            {"team1": "JOR", "team2": "ALG", "group": "J", "date": "2026-06-23", "kick_off": "2026-06-23T03:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 3, "status": "finished"},
            # J组 - 第3轮
            {"team1": "ALG", "team2": "AUT", "group": "J", "date": "2026-06-28", "kick_off": "2026-06-28T02:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 3, "status": "finished"},
            {"team1": "JOR", "team2": "ARG", "group": "J", "date": "2026-06-28", "kick_off": "2026-06-28T02:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 3, "status": "finished"},

            # K组 (葡萄牙、刚果(金)、乌兹别克斯坦、哥伦比亚) - 第1轮
            {"team1": "POR", "team2": "COD", "group": "K", "date": "2026-06-17", "kick_off": "2026-06-17T17:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            {"team1": "UZB", "team2": "COL", "group": "K", "date": "2026-06-18", "kick_off": "2026-06-18T02:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 2, "status": "finished"},
            # K组 - 第2轮
            {"team1": "POR", "team2": "UZB", "group": "K", "date": "2026-06-23", "kick_off": "2026-06-23T17:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 1, "status": "finished"},
            {"team1": "COL", "team2": "COD", "group": "K", "date": "2026-06-24", "kick_off": "2026-06-24T02:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 0, "status": "finished"},
            # K组 - 第3轮
            {"team1": "COL", "team2": "POR", "group": "K", "date": "2026-06-27", "kick_off": "2026-06-27T23:30:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 1, "status": "finished"},
            {"team1": "COD", "team2": "UZB", "group": "K", "date": "2026-06-27", "kick_off": "2026-06-27T23:30:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 2, "status": "finished"},

            # L组 (英格兰、克罗地亚、加纳、巴拿马) - 第1轮
            {"team1": "ENG", "team2": "CRO", "group": "L", "date": "2026-06-17", "kick_off": "2026-06-17T20:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 0, "status": "finished"},
            {"team1": "GHA", "team2": "PAN", "group": "L", "date": "2026-06-17", "kick_off": "2026-06-17T23:00:00Z", "round": "Group", "stage": "group", "score1": 1, "score2": 0, "status": "finished"},
            # L组 - 第2轮
            {"team1": "ENG", "team2": "GHA", "group": "L", "date": "2026-06-23", "kick_off": "2026-06-23T20:00:00Z", "round": "Group", "stage": "group", "score1": 3, "score2": 0, "status": "finished"},
            {"team1": "PAN", "team2": "CRO", "group": "L", "date": "2026-06-23", "kick_off": "2026-06-23T23:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 2, "status": "finished"},
            # L组 - 第3轮
            {"team1": "PAN", "team2": "ENG", "group": "L", "date": "2026-06-27", "kick_off": "2026-06-27T21:00:00Z", "round": "Group", "stage": "group", "score1": 0, "score2": 2, "status": "finished"},
            {"team1": "CRO", "team2": "GHA", "group": "L", "date": "2026-06-27", "kick_off": "2026-06-27T21:00:00Z", "round": "Group", "stage": "group", "score1": 2, "score2": 1, "status": "finished"},
        ]

        # 2026世界杯淘汰赛赛程
        WORLD_CUP_2026_KNOCKOUT = [
            # Round of 32 (1/16决赛)
            {"id": 73, "team1": "RSA", "team2": "CAN", "date": "2026-06-28", "kick_off": "2026-06-28T19:00:00Z", "round": "Round of 32", "stage": "round32", "score1": 0, "score2": 1, "status": "finished"},
            {"id": 74, "team1": "GER", "team2": "PAR", "date": "2026-06-29", "kick_off": "2026-06-29T20:30:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 75, "team1": "NED", "team2": "MAR", "date": "2026-06-29", "kick_off": "2026-06-30T01:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 76, "team1": "BRA", "team2": "JPN", "date": "2026-06-29", "kick_off": "2026-06-29T17:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 77, "team1": "FRA", "team2": "SWE", "date": "2026-06-30", "kick_off": "2026-06-30T21:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 78, "team1": "CIV", "team2": "NOR", "date": "2026-06-30", "kick_off": "2026-06-30T17:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 79, "team1": "MEX", "team2": "ECU", "date": "2026-06-30", "kick_off": "2026-07-01T01:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 80, "team1": "ENG", "team2": "COD", "date": "2026-07-01", "kick_off": "2026-07-01T16:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 81, "team1": "BEL", "team2": "SEN", "date": "2026-07-01", "kick_off": "2026-07-01T20:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 82, "team1": "USA", "team2": "BIH", "date": "2026-07-01", "kick_off": "2026-07-02T00:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 83, "team1": "ESP", "team2": "AUT", "date": "2026-07-02", "kick_off": "2026-07-02T19:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 84, "team1": "POR", "team2": "CRO", "date": "2026-07-02", "kick_off": "2026-07-02T23:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 85, "team1": "SUI", "team2": "ALG", "date": "2026-07-02", "kick_off": "2026-07-03T03:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 86, "team1": "AUS", "team2": "EGY", "date": "2026-07-03", "kick_off": "2026-07-03T18:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 87, "team1": "ARG", "team2": "CPV", "date": "2026-07-03", "kick_off": "2026-07-03T22:00:00Z", "round": "Round of 32", "stage": "round32"},
            {"id": 88, "team1": "COL", "team2": "GHA", "date": "2026-07-03", "kick_off": "2026-07-04T01:30:00Z", "round": "Round of 32", "stage": "round32"},

            # Round of 16 (1/8决赛) - teams TBD until R32 results
            {"id": 89, "team1": "TBD", "team2": "TBD", "date": "2026-07-04", "kick_off": "2026-07-04T21:00:00Z", "round": "Round of 16", "stage": "round16"},
            {"id": 90, "team1": "TBD", "team2": "TBD", "date": "2026-07-04", "kick_off": "2026-07-04T17:00:00Z", "round": "Round of 16", "stage": "round16"},
            {"id": 91, "team1": "TBD", "team2": "TBD", "date": "2026-07-05", "kick_off": "2026-07-05T20:00:00Z", "round": "Round of 16", "stage": "round16"},
            {"id": 92, "team1": "TBD", "team2": "TBD", "date": "2026-07-05", "kick_off": "2026-07-06T00:00:00Z", "round": "Round of 16", "stage": "round16"},
            {"id": 93, "team1": "TBD", "team2": "TBD", "date": "2026-07-06", "kick_off": "2026-07-06T19:00:00Z", "round": "Round of 16", "stage": "round16"},
            {"id": 94, "team1": "TBD", "team2": "TBD", "date": "2026-07-06", "kick_off": "2026-07-07T00:00:00Z", "round": "Round of 16", "stage": "round16"},
            {"id": 95, "team1": "TBD", "team2": "TBD", "date": "2026-07-07", "kick_off": "2026-07-07T16:00:00Z", "round": "Round of 16", "stage": "round16"},
            {"id": 96, "team1": "TBD", "team2": "TBD", "date": "2026-07-07", "kick_off": "2026-07-07T20:00:00Z", "round": "Round of 16", "stage": "round16"},

            # Quarter-finals
            {"id": 97, "team1": "TBD", "team2": "TBD", "date": "2026-07-09", "kick_off": "2026-07-09T20:00:00Z", "round": "Quarter-final", "stage": "quarter"},
            {"id": 98, "team1": "TBD", "team2": "TBD", "date": "2026-07-10", "kick_off": "2026-07-10T19:00:00Z", "round": "Quarter-final", "stage": "quarter"},
            {"id": 99, "team1": "TBD", "team2": "TBD", "date": "2026-07-11", "kick_off": "2026-07-11T21:00:00Z", "round": "Quarter-final", "stage": "quarter"},
            {"id": 100, "team1": "TBD", "team2": "TBD", "date": "2026-07-11", "kick_off": "2026-07-12T01:00:00Z", "round": "Quarter-final", "stage": "quarter"},

            # Semi-finals
            {"id": 101, "team1": "TBD", "team2": "TBD", "date": "2026-07-14", "kick_off": "2026-07-14T19:00:00Z", "round": "Semi-final", "stage": "semi"},
            {"id": 102, "team1": "TBD", "team2": "TBD", "date": "2026-07-15", "kick_off": "2026-07-15T19:00:00Z", "round": "Semi-final", "stage": "semi"},

            # Third Place
            {"id": 103, "team1": "TBD", "team2": "TBD", "date": "2026-07-18", "kick_off": "2026-07-18T21:00:00Z", "round": "Third Place", "stage": "third"},

            # Final
            {"id": 104, "team1": "TBD", "team2": "TBD", "date": "2026-07-19", "kick_off": "2026-07-19T19:00:00Z", "round": "Final", "stage": "final"},
        ]

        match_id = 0
        for sched in WORLD_CUP_2026_SCHEDULE:
            match_id += 1
            existing = session.query(Match).filter(
                Match.group_name == sched["group"],
                Match.team1 == sched["team1"],
                Match.team2 == sched["team2"],
            ).first()
            if not existing:
                session.add(Match(
                    id=match_id,
                    round=sched["round"],
                    group_name=sched["group"],
                    date=sched["date"],
                    kick_off=sched["kick_off"],
                    team1=sched["team1"],
                    team2=sched["team2"],
                    score1=sched.get("score1"),
                    score2=sched.get("score2"),
                    status=sched.get("status", "upcoming"),
                    stage=sched["stage"],
                ))
                count += 1
            else:
                # Update existing match with scores if provided
                if "score1" in sched:
                    existing.score1 = sched["score1"]
                if "score2" in sched:
                    existing.score2 = sched["score2"]
                if "status" in sched:
                    existing.status = sched["status"]
        session.commit()

        # Insert knockout matches
        # First delete existing knockout matches to avoid duplicates
        session.query(Match).filter(Match.stage != "group").delete()
        session.commit()

        for km in WORLD_CUP_2026_KNOCKOUT:
            session.add(Match(
                id=km["id"],
                round=km["round"],
                group_name="",
                date=km["date"],
                kick_off=km["kick_off"],
                team1=km["team1"],
                team2=km["team2"],
                score1=km.get("score1"),
                score2=km.get("score2"),
                status=km.get("status", "upcoming"),
                stage=km["stage"],
            ))
            count += 1
        session.commit()

    elif year in (2018, 2022):
        data = _load_json(f"wc{year}.json")
        mid = 0
        for m in data.get("group_matches", []):
            mid += 1
            existing = session.query(Match).filter(
                Match.group_name == m["group"],
                Match.team1 == m["team1"],
                Match.team2 == m["team2"],
            ).first()
            if not existing:
                session.add(Match(
                    id=mid,
                    round="Group",
                    group_name=m["group"],
                    date=m.get("date", ""),
                    team1=m["team1"],
                    team2=m["team2"],
                    score1=m.get("score1"),
                    score2=m.get("score2"),
                    status="finished",
                    stage="group",
                ))
                count += 1

        for m in data.get("knockout_matches", []):
            mid += 1
            session.add(Match(
                id=mid,
                round=m["round"],
                group_name="",
                date=m.get("date", ""),
                team1=m["team1"],
                team2=m["team2"],
                score1=m.get("score1"),
                score2=m.get("score2"),
                score1_pen=m.get("score1_pen"),
                score2_pen=m.get("score2_pen"),
                status="finished",
                stage=m.get("stage", "knockout"),
            ))
            count += 1
        session.commit()

    return count


# ─────────────────────────────────────────────
# Data access functions
# ─────────────────────────────────────────────

def get_all_teams() -> List[Dict]:
    """Get all teams."""
    with SessionLocal() as session:
        teams = session.query(Team).all()
        return [
            {
                "code": t.code,
                "name": t.name,
                "name_zh": t.name_zh,
                "group_name": t.group_name,
                "elo_rating": t.elo_rating,
                "fifa_rank": t.fifa_rank,
                "flag_emoji": t.flag_emoji,
                "confederation": t.confederation,
                "formation": t.formation,
                "recent_form": t.recent_form,
                "goals_scored_last10": t.goals_scored_last10,
                "goals_conceded_last10": t.goals_conceded_last10,
            }
            for t in teams
        ]


def get_groups_standings() -> List[Dict]:
    """Get current group standings."""
    with SessionLocal() as session:
        teams = {t.code: t for t in session.query(Team).all()}
        matches = session.query(Match).filter(Match.stage == "group", Match.status == "finished").all()

        groups: Dict[str, List[str]] = {}
        for t in teams.values():
            g = t.group_name
            if g not in groups:
                groups[g] = []
            groups[g].append(t.code)

        standings = []
        for group_name, team_codes in sorted(groups.items()):
            group_matches = [m for m in matches if m.group_name == group_name]
            stats = _compute_standings(team_codes, group_matches, teams)
            standings.append({
                "group": group_name,
                "standings": stats,
            })
        return standings


def _compute_standings(team_codes, matches, teams_dict):
    """Compute standings for a group."""
    stats = {}
    for code in team_codes:
        t = teams_dict.get(code)
        stats[code] = {
            "code": code,
            "name": t.name if t else code,
            "name_zh": t.name_zh if t else code,
            "flag_emoji": t.flag_emoji if t else "",
            "elo_rating": t.elo_rating if t else 0,
            "played": 0, "won": 0, "drawn": 0, "lost": 0,
            "goals_for": 0, "goals_against": 0,
            "goals_diff": 0, "points": 0,
        }

    for m in matches:
        t1, t2 = m.team1, m.team2
        s1, s2 = m.score1 or 0, m.score2 or 0
        for t, sc, opp_sc in [(t1, s1, s2), (t2, s2, s1)]:
            if t in stats:
                stats[t]["played"] += 1
                stats[t]["goals_for"] += sc
                stats[t]["goals_against"] += opp_sc
                if sc > opp_sc:
                    stats[t]["won"] += 1
                    stats[t]["points"] += 3
                elif sc == opp_sc:
                    stats[t]["drawn"] += 1
                    stats[t]["points"] += 1
                else:
                    stats[t]["lost"] += 1

    for s in stats.values():
        s["goals_diff"] = s["goals_for"] - s["goals_against"]

    # Pre-tournament (all 0 points): rank by ELO
    has_results = any(s["points"] > 0 for s in stats.values())
    if not has_results:
        return sorted(stats.values(), key=lambda x: -x["elo_rating"])
    return sorted(stats.values(), key=lambda x: (-x["points"], -x["goals_diff"], -x["goals_for"]))


def get_upcoming_matches(days: int = 5) -> List[Dict]:
    """Get upcoming matches within N days, including odds."""
    with SessionLocal() as session:
        matches = session.query(Match).filter(Match.status == "upcoming").all()
        teams_lookup = {t.code: t for t in session.query(Team).all()}
        result = []
        for m in matches:
            t1 = teams_lookup.get(m.team1)
            t2 = teams_lookup.get(m.team2)

            # Get odds for this match
            odds_rows = session.query(Odds).filter(Odds.match_id == m.id).all()
            odds_bookmakers = [{
                "bookmaker": o.bookmaker,
                "home": o.home,
                "draw": o.draw,
                "away": o.away,
            } for o in odds_rows if o.home and o.draw and o.away]

            result.append({
                "id": m.id,
                "round": m.round,
                "group_name": m.group_name,
                "date": m.date,
                "kick_off": m.kick_off,
                "team1": m.team1,
                "team1_name": t1.name if t1 else m.team1,
                "team1_zh": t1.name_zh if t1 else m.team1,
                "team1_flag": t1.flag_emoji if t1 else "",
                "team1_elo": t1.elo_rating if t1 else 0,
                "team2": m.team2,
                "team2_name": t2.name if t2 else m.team2,
                "team2_zh": t2.name_zh if t2 else m.team2,
                "team2_flag": t2.flag_emoji if t2 else "",
                "team2_elo": t2.elo_rating if t2 else 0,
                "score1": m.score1,
                "score2": m.score2,
                "status": m.status,
                "stage": m.stage,
                "odds": {"bookmakers": odds_bookmakers},
            })
        return result


def get_match_squads(team1_code: str, team2_code: str) -> Dict[str, List[Dict]]:
    """Get full squads for both teams in a match."""
    with SessionLocal() as session:
        players1 = session.query(Player).filter(Player.team_code == team1_code).all()
        players2 = session.query(Player).filter(Player.team_code == team2_code).all()
        return {
            "team1": [{
                "number": p.number,
                "name": p.name,
                "name_zh": p.name_zh,
                "position": p.position,
                "position_zh": p.position_zh,
            } for p in players1],
            "team2": [{
                "number": p.number,
                "name": p.name,
                "name_zh": p.name_zh,
                "position": p.position,
                "position_zh": p.position_zh,
            } for p in players2],
        }


def get_match_detail(match_id: int) -> Optional[Dict]:
    """Get full match detail with flat match data, players, h2h, odds."""
    with SessionLocal() as session:
        m = session.query(Match).filter(Match.id == match_id).first()
        if not m:
            return None

        teams_lookup = {t.code: t for t in session.query(Team).all()}
        t1 = teams_lookup.get(m.team1)
        t2 = teams_lookup.get(m.team2)

        players1 = session.query(Player).filter(Player.team_code == m.team1).order_by(Player.number).all()
        players2 = session.query(Player).filter(Player.team_code == m.team2).order_by(Player.number).all()

        odds_list = session.query(Odds).filter(Odds.match_id == match_id).all()

        return {
            # Flat match data
            "match": {
                "id": m.id,
                "round": m.round,
                "group_name": m.group_name,
                "date": m.date,
                "kick_off": m.kick_off,
                "team1": m.team1,
                "team1_name": t1.name if t1 else m.team1,
                "team1_zh": t1.name_zh if t1 else m.team1,
                "team1_flag": t1.flag_emoji if t1 else "",
                "team1_elo": t1.elo_rating if t1 else 0,
                "team1_fifa_rank": t1.fifa_rank if t1 else 30,
                "team1_formation": t1.formation if t1 else "4-3-3",
                "team1_recent_form": t1.recent_form if t1 else "",
                "team2": m.team2,
                "team2_name": t2.name if t2 else m.team2,
                "team2_zh": t2.name_zh if t2 else m.team2,
                "team2_flag": t2.flag_emoji if t2 else "",
                "team2_elo": t2.elo_rating if t2 else 0,
                "team2_fifa_rank": t2.fifa_rank if t2 else 30,
                "team2_formation": t2.formation if t2 else "4-3-3",
                "team2_recent_form": t2.recent_form if t2 else "",
                "score1": m.score1,
                "score2": m.score2,
                "score1_pen": m.score1_pen,
                "score2_pen": m.score2_pen,
                "status": m.status,
                "stage": m.stage,
            },
            # Players
            "players": {
                "team1": [{
                    "number": p.number,
                    "name": p.name,
                    "name_zh": p.name_zh,
                    "position": p.position,
                    "position_zh": p.position_zh,
                } for p in players1],
                "team2": [{
                    "number": p.number,
                    "name": p.name,
                    "name_zh": p.name_zh,
                    "position": p.position,
                    "position_zh": p.position_zh,
                } for p in players2],
            },
            # H2H - empty structure, filled by server
            "h2h": {
                "stats": {"total": 0, "home_wins": 0, "draws": 0, "away_wins": 0},
                "matches": [],
            },
            # Odds
            "odds": {
                "bookmakers": [{
                    "bookmaker": o.bookmaker,
                    "home": o.home,
                    "draw": o.draw,
                    "away": o.away,
                } for o in odds_list],
                "correct_scores": [],
            },
        }


def insert_match(match_data: Dict) -> int:
    """Insert a new match."""
    with SessionLocal() as session:
        m = Match(
            round=match_data.get("round", "Group"),
            group_name=match_data.get("group_name", ""),
            date=match_data.get("date", ""),
            kick_off=match_data.get("kick_off", ""),
            team1=match_data["team1"],
            team2=match_data["team2"],
            status=match_data.get("status", "upcoming"),
            stage=match_data.get("stage", "group"),
        )
        session.add(m)
        session.commit()
        return m.id


def update_match_result(match_id: int, score1: int, score2: int, status: str = "finished") -> None:
    """Update match result."""
    with SessionLocal() as session:
        m = session.query(Match).filter(Match.id == match_id).first()
        if m:
            m.score1 = score1
            m.score2 = score2
            m.status = status
            session.commit()


# ─────────────────────────────────────────────
# Convenience init
# ─────────────────────────────────────────────

def _generate_initial_odds(session: Session):
    """Generate simulated odds for all matches based on ELO ratings.
    These serve as baseline odds until real market odds become available."""
    import math

    matches = session.query(Match).all()
    teams_cache = {}
    for t in session.query(Team).all():
        teams_cache[t.code] = t

    bookmakers = ["Bet365", "William Hill", "1xBet", "sporttery", "Unibet"]
    count = 0

    for match in matches:
        # Skip if odds already exist for this match
        existing = session.query(Odds).filter(Odds.match_id == match.id).first()
        if existing:
            continue

        t1 = teams_cache.get(match.team1)
        t2 = teams_cache.get(match.team2)
        if not t1 or not t2:
            continue

        elo1 = t1.elo_rating or 1800
        elo2 = t2.elo_rating or 1800

        # ELO-based probability
        elo_diff = elo1 - elo2
        exp1 = 1.0 / (1.0 + 10 ** ((elo2 - elo1) / 400))
        exp2 = 1.0 - exp1

        # Approximate 1X2 probabilities from ELO
        draw_base = 0.26  # World Cup average draw rate
        strength_diff = abs(exp1 - exp2)
        draw_prob = max(0.15, draw_base - 0.3 * strength_diff)
        home_prob = exp1 * (1 - draw_prob)
        away_prob = exp2 * (1 - draw_prob)

        # Normalize
        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total
        away_prob /= total

        for i, bk in enumerate(bookmakers):
            # Add small variation per bookmaker
            margin = 1.06 + 0.01 * i  # 6-10% margin
            variation = 0.02 * (i - 2)  # ±4% variation

            h = home_prob + variation
            d = draw_prob - variation * 0.5
            a = away_prob - variation * 0.5

            # Normalize and add margin
            t = h + d + a
            h /= t; d /= t; a /= t

            # Convert to decimal odds
            home_odds = round(margin / h, 2)
            draw_odds = round(margin / d, 2)
            away_odds = round(margin / a, 2)

            odds = Odds(
                match_id=match.id,
                bookmaker=bk,
                home=home_odds,
                draw=draw_odds,
                away=away_odds,
            )
            session.add(odds)
            count += 1

    session.commit()
    return count


def full_init():
    """Full initialization: create tables, load teams (with squads) and matches."""
    init_db()
    with SessionLocal() as session:
        n_teams = load_teams_from_file(session)
        n_matches = load_matches_from_data(session, year=2026)
        n_odds = _generate_initial_odds(session)
        print(f"[DB] Loaded {n_teams} teams (with squads), {n_matches} matches, {n_odds} odds entries")


if __name__ == "__main__":
    full_init()