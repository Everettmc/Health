import aiosqlite
from typing import List, Dict, Any, Optional
from datetime import date, timedelta
import os

DB_PATH = os.getenv("DB_PATH", "health.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS sleep_sessions (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                sleep_score INTEGER,
                total_sleep_minutes INTEGER,
                deep_sleep_minutes INTEGER,
                rem_sleep_minutes INTEGER,
                light_sleep_minutes INTEGER,
                awake_minutes INTEGER,
                hrv_avg REAL,
                respiratory_rate REAL,
                bed_temp_delta REAL,
                toss_turns INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS health_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                source TEXT DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, metric_type, source)
            );

            CREATE TABLE IF NOT EXISTS daily_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                diet TEXT,
                workout TEXT,
                sleep TEXT,
                insights TEXT,
                priority_focus TEXT,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_sleep_date ON sleep_sessions(date);
            CREATE INDEX IF NOT EXISTS idx_metrics_date ON health_metrics(date);
            CREATE INDEX IF NOT EXISTS idx_suggestions_date ON daily_suggestions(date);
        """)
        await db.commit()


async def upsert_sleep_session(session: Dict[str, Any]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO sleep_sessions
               (id, date, sleep_score, total_sleep_minutes, deep_sleep_minutes,
                rem_sleep_minutes, light_sleep_minutes, awake_minutes,
                hrv_avg, respiratory_rate, bed_temp_delta, toss_turns)
               VALUES (:id, :date, :sleep_score, :total_sleep_minutes, :deep_sleep_minutes,
                       :rem_sleep_minutes, :light_sleep_minutes, :awake_minutes,
                       :hrv_avg, :respiratory_rate, :bed_temp_delta, :toss_turns)""",
            session,
        )
        await db.commit()


async def upsert_health_metric(metric: Dict[str, Any]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO health_metrics (date, metric_type, value, unit, source)
               VALUES (:date, :metric_type, :value, :unit, :source)""",
            metric,
        )
        await db.commit()


async def batch_upsert_metrics(metrics: List[Dict[str, Any]]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            """INSERT OR REPLACE INTO health_metrics (date, metric_type, value, unit, source)
               VALUES (:date, :metric_type, :value, :unit, :source)""",
            metrics,
        )
        await db.commit()


async def get_sleep_sessions(days: int = 30) -> List[Dict]:
    cutoff = str(date.today() - timedelta(days=days))
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM sleep_sessions WHERE date >= ? ORDER BY date DESC", (cutoff,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_health_metrics(
    days: int = 30, metric_types: Optional[List[str]] = None
) -> List[Dict]:
    cutoff = str(date.today() - timedelta(days=days))
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if metric_types:
            placeholders = ",".join("?" * len(metric_types))
            async with db.execute(
                f"SELECT * FROM health_metrics WHERE date >= ? AND metric_type IN ({placeholders}) ORDER BY date DESC",
                (cutoff, *metric_types),
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            async with db.execute(
                "SELECT * FROM health_metrics WHERE date >= ? ORDER BY date DESC", (cutoff,)
            ) as cursor:
                rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def save_suggestions(suggestion_date: str, suggestions: Dict[str, str], model: str = "claude-opus-4-7"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO daily_suggestions (date, diet, workout, sleep, insights, priority_focus, model)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                suggestion_date,
                suggestions.get("diet", ""),
                suggestions.get("workout", ""),
                suggestions.get("sleep", ""),
                suggestions.get("insights", ""),
                suggestions.get("priority_focus", ""),
                model,
            ),
        )
        await db.commit()


async def get_suggestions(days: int = 7) -> List[Dict]:
    cutoff = str(date.today() - timedelta(days=days))
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM daily_suggestions WHERE date >= ? ORDER BY date DESC", (cutoff,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_latest_suggestion() -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM daily_suggestions ORDER BY date DESC, id DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT value FROM user_settings WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else default


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_settings (key, value) VALUES (?, ?)", (key, value)
        )
        await db.commit()
