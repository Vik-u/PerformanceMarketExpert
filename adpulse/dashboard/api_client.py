"""
HTTP client wrapper for talking to the FastAPI service.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
API_BASE_URL = os.getenv("ADPULSE_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _prepare_params(params: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
    for key, value in params.items():
        if value is None or value == "":
            continue
        cleaned[key] = value.isoformat() if hasattr(value, "isoformat") else value
    return cleaned


def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = f"{API_BASE_URL}{path}"
    try:
        response = requests.get(url, params=_prepare_params(params or {}), timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.error("API request failed: %s %s (%s)", "GET", url, exc, exc_info=exc)
        return None


def get_platform_summary(start_date=None, end_date=None) -> Optional[List[Dict[str, Any]]]:
    return _get(
        "/summary/platforms",
        params={"start_date": start_date, "end_date": end_date},
    )


def get_campaign_summary(
    platform: Optional[str] = None,
    start_date=None,
    end_date=None,
) -> Optional[List[Dict[str, Any]]]:
    return _get(
        "/campaigns/summary",
        params={
            "platform": platform,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


def get_daily_timeseries(
    platform: Optional[str] = None,
    campaign_id: Optional[str] = None,
    start_date=None,
    end_date=None,
) -> Optional[List[Dict[str, Any]]]:
    return _get(
        "/timeseries/daily",
        params={
            "platform": platform,
            "campaign_id": campaign_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


def get_account_health_insights(start_date, end_date) -> Optional[Dict[str, Any]]:
    return _get(
        "/insights/account-health",
        params={"start_date": start_date, "end_date": end_date},
    )


def get_roas_drop_insights(platform: str, start_date, end_date) -> Optional[Dict[str, Any]]:
    return _get(
        "/insights/roas-drop",
        params={
            "platform": platform,
            "start_date": start_date,
            "end_date": end_date,
        },
    )
