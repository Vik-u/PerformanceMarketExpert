"""
Utility helpers for the dashboard UI.
"""
from __future__ import annotations

from typing import Iterable, Mapping


def format_currency(value: float | int | None) -> str:
    if value is None:
        value = 0
    return f"${float(value):,.2f}"


def format_percent(value: float | None) -> str:
    if value is None:
        value = 0
    return f"{float(value) * 100:,.2f}%"


def aggregate_metric(rows: Iterable[Mapping[str, float]], key: str) -> float:
    total = 0.0
    for row in rows:
        total += float(row.get(key, 0) or 0)
    return total


def safe_divide(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator
