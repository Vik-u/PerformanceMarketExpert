"""
Normalized schema definitions used across the ingestion layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Tuple


@dataclass
class NormalizedRecord:
    platform: str
    campaign_id: str
    campaign_name: str
    event_date: date
    impressions: int
    clicks: int
    spend: float
    conversions: int
    revenue: float = 0.0

    def as_db_tuple(self) -> Tuple[str, str, str, str, int, int, float, int, float]:
        """Return the tuple ordering expected by the database writer."""
        return (
            self.platform,
            self.campaign_id,
            self.campaign_name,
            self.event_date.isoformat(),
            self.impressions,
            self.clicks,
            self.spend,
            self.conversions,
            self.revenue,
        )


def parse_int(value: str | None, default: int = 0) -> int:
    try:
        return int(float(value)) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(value: str | None) -> date:
    if not value:
        raise ValueError("Date value is mandatory")

    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    # Last resort: try fromisoformat which handles YYYY-MM-DD
    return date.fromisoformat(value)
