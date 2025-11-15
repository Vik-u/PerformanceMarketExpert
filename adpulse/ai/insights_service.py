"""
AI-powered insights utilities that build on top of the Metrics API.
"""
from __future__ import annotations

import json
import os
from datetime import date
from statistics import fmean
from typing import Any, Dict, List, Optional, Sequence

import requests

from adpulse.ai.anomaly import find_recent_anomalies
from adpulse.ai.openai_client import generate_completion

API_BASE_URL = os.getenv("ADPULSE_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _call_api(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = f"{API_BASE_URL}{path}"
    response = requests.get(
        url,
        params=_clean_params(params or {}),
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def _clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        cleaned[key] = value.isoformat() if isinstance(value, date) else value
    return cleaned


def _split_period(values: Sequence[float]) -> tuple[list[float], list[float]]:
    if not values:
        return [], []
    half = max(1, len(values) // 2)
    previous = list(values[:half])
    recent = list(values[half:])
    if not recent:  # if len==1
        recent = previous
    return previous, recent


def get_roas_drop_explanation(platform: str, start_date: date, end_date: date) -> str:
    timeseries = _call_api(
        "/timeseries/daily",
        params={"platform": platform, "start_date": start_date, "end_date": end_date},
    )
    if not timeseries:
        return "No time series data was available for this platform in the selected window."

    dates = [row["date"] for row in timeseries]
    spend = [float(row.get("spend", 0)) for row in timeseries]
    revenue = [float(row.get("revenue", 0)) for row in timeseries]
    roas_series = [
        (rev / s) if s else 0.0
        for s, rev in zip(spend, revenue)
    ]

    prev_values, recent_values = _split_period(roas_series)
    avg_prev = fmean(prev_values) if prev_values else 0.0
    avg_recent = fmean(recent_values) if recent_values else 0.0
    pct_change = ((avg_recent - avg_prev) / avg_prev * 100) if avg_prev else 0.0

    anomalies = find_recent_anomalies(dates, roas_series)
    summary_payload = {
        "platform": platform,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "avg_roas_previous": round(avg_prev, 4),
        "avg_roas_recent": round(avg_recent, 4),
        "percentage_change": round(pct_change, 2),
        "anomalies": anomalies,
    }

    table_lines = ["Date | Spend | Revenue | ROAS"]
    for day, s, r, roas in zip(dates, spend, revenue, roas_series):
        table_lines.append(f"{day} | ${s:,.2f} | ${r:,.2f} | {roas:.2f}x")
    tabular = "\n".join(table_lines)

    prompt = f"""
You are an expert performance marketing analyst.
Here is ROAS data for platform {platform}.

Summary JSON:
{json.dumps(summary_payload, indent=2)}

Daily data (date | spend | revenue | roas):
{tabular}

Explain in plain language why ROAS might have dropped recently.
Provide 3-5 possible reasons and 3 concrete optimization suggestions.
Keep it concise and actionable.
    """.strip()

    return generate_completion(prompt)


def get_account_health_summary(start_date: date, end_date: date) -> str:
    platforms = _call_api(
        "/summary/platforms",
        params={"start_date": start_date, "end_date": end_date},
    )
    if not platforms:
        return "No platform data found for the requested window."

    summary = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "platforms": platforms,
        "aggregate": {
            "spend": sum(float(p["total_spend"] or 0) for p in platforms),
            "revenue": sum(float(p["total_revenue"] or 0) for p in platforms),
            "conversions": sum(int(p["total_conversions"] or 0) for p in platforms),
        },
    }
    summary["aggregate"]["roas"] = (
        (summary["aggregate"]["revenue"] / summary["aggregate"]["spend"])
        if summary["aggregate"]["spend"]
        else 0.0
    )

    prompt = f"""
You are an elite paid media strategist.
Assess the following cross-platform performance data between {summary['start_date']} and {summary['end_date']}.

Data JSON:
{json.dumps(summary, indent=2)}

Provide:
1. A concise overall health summary (1 paragraph).
2. Which platforms to scale up/down and why.
3. 3 actionable recommendations for budget shifts or campaign testing.
Keep language concise for an executive audience.
    """.strip()

    return generate_completion(prompt)
