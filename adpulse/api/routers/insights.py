"""
AI insights endpoints.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from adpulse.ai import get_account_health_summary, get_roas_drop_explanation

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/roas-drop")
def roas_drop(
    platform: str = Query(..., description="Platform name as stored in the DB (e.g., 'Google Ads')"),
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> dict:
    try:
        analysis = get_roas_drop_explanation(platform, start_date, end_date)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail="Failed to generate ROAS insight") from exc
    return {
        "platform": platform,
        "start_date": start_date,
        "end_date": end_date,
        "analysis": analysis,
    }


@router.get("/account-health")
def account_health(
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> dict:
    try:
        analysis = get_account_health_summary(start_date, end_date)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="Failed to generate account insight") from exc
    return {
        "start_date": start_date,
        "end_date": end_date,
        "analysis": analysis,
    }
