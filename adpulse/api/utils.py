"""
Utilities for API routers.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Query

from adpulse.models import AdPerformance


def apply_date_filters(
    query: Query,
    start_date: Optional[date],
    end_date: Optional[date],
) -> Query:
    if start_date:
        query = query.filter(AdPerformance.event_date >= start_date.isoformat())
    if end_date:
        query = query.filter(AdPerformance.event_date <= end_date.isoformat())
    return query


def calc_ctr(clicks: int, impressions: int) -> float:
    return round(clicks / impressions, 4) if impressions else 0.0


def calc_rate(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def parse_event_date(value: str) -> date:
    return date.fromisoformat(value)
