"""
SQLite database helpers for persisting normalized data.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence

from adpulse.ingestion.schema import NormalizedRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS ad_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    campaign_id TEXT NOT NULL,
    campaign_name TEXT NOT NULL,
    event_date TEXT NOT NULL,
    impressions INTEGER NOT NULL,
    clicks INTEGER NOT NULL,
    spend REAL NOT NULL,
    conversions INTEGER NOT NULL,
    revenue REAL NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = _connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


class DatabaseManager:
    """Thin wrapper around sqlite3 to keep responsibilities tidy."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        with _connection(self.db_path) as conn:
            conn.executescript(SCHEMA)

    def insert_records(self, records: Sequence[NormalizedRecord]) -> int:
        if not records:
            return 0
        with _connection(self.db_path) as conn:
            conn.executemany(
                """
                INSERT INTO ad_performance (
                    platform, campaign_id, campaign_name, event_date,
                    impressions, clicks, spend, conversions, revenue
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [record.as_db_tuple() for record in records],
            )
        return len(records)

    def fetch_summary(self) -> List[sqlite3.Row]:
        query = """
        SELECT
            platform,
            COUNT(*) AS rows_ingested,
            SUM(impressions) AS impressions,
            SUM(clicks) AS clicks,
            SUM(spend) AS spend,
            SUM(conversions) AS conversions,
            SUM(revenue) AS revenue
        FROM ad_performance
        GROUP BY platform
        ORDER BY platform;
        """
        with _connection(self.db_path) as conn:
            cursor = conn.execute(query)
            return cursor.fetchall()

    def fetch_totals(self) -> sqlite3.Row | None:
        query = """
        SELECT
            COUNT(*) AS rows_ingested,
            SUM(impressions) AS impressions,
            SUM(clicks) AS clicks,
            SUM(spend) AS spend,
            SUM(conversions) AS conversions,
            SUM(revenue) AS revenue
        FROM ad_performance;
        """
        with _connection(self.db_path) as conn:
            cursor = conn.execute(query)
            return cursor.fetchone()

    def row_count(self) -> int:
        with _connection(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM ad_performance")
            result = cursor.fetchone()
        return int(result[0]) if result else 0
