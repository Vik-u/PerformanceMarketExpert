"""
Generate performance reports by composing API + AI outputs.
"""
from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import requests

from adpulse.reporting.pdf_generator import generate_performance_report

API_BASE_URL = os.getenv("ADPULSE_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, date):
            cleaned[key] = value.isoformat()
        else:
            cleaned[key] = value
    return cleaned


def _safe_get(path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    url = f"{API_BASE_URL}{path}"
    try:
        response = requests.get(url, params=_clean_params(params or {}), timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def _ensure_date(value) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value).date()
    raise ValueError("Expected date or isoformat string")


def build_weekly_report(start_date, end_date, output_dir: str = "reports") -> str:
    start = _ensure_date(start_date)
    end = _ensure_date(end_date)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    platform_summaries = _safe_get(
        "/summary/platforms", params={"start_date": start, "end_date": end}
    ) or []
    campaign_summaries = _safe_get(
        "/campaigns/summary", params={"start_date": start, "end_date": end}
    ) or []

    top_campaigns = sorted(
        campaign_summaries,
        key=lambda row: row.get("total_spend", 0),
        reverse=True,
    )[:10]

    account_health = _safe_get(
        "/insights/account-health", params={"start_date": start, "end_date": end}
    )
    account_text = (account_health or {}).get("analysis") or "AI account insights unavailable."

    roas_text = None
    if platform_summaries:
        primary_platform = platform_summaries[0]["platform"]
        roas_insight = _safe_get(
            "/insights/roas-drop",
            params={"platform": primary_platform, "start_date": start, "end_date": end},
        )
        roas_text = (roas_insight or {}).get("analysis")

    report_data = {
        "title": "AdPulse Weekly Performance Overview",
        "date_range": f"{start.isoformat()} to {end.isoformat()}",
        "platform_summaries": platform_summaries,
        "top_campaigns": top_campaigns,
        "ai_account_health": account_text,
        "ai_roas_insights": roas_text,
    }

    filename = f"adpulse_report_{start.isoformat()}_{end.isoformat()}.pdf"
    pdf_path = output_path / filename
    generate_performance_report(str(pdf_path), report_data)
    return str(pdf_path)


def build_daily_report(target_date, output_dir: str = "reports") -> str:
    day = _ensure_date(target_date)
    return build_weekly_report(day, day, output_dir=output_dir)
