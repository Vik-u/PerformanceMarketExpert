"""
Health check endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from adpulse.api.dependencies import get_db
from adpulse.models import AdPerformance

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Health status")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.query(func.count(AdPerformance.id)).scalar()
        status = "ok"
        db_status = "ok"
    except Exception:
        # Keep response minimal but actionable.
        status = "degraded"
        db_status = "error"
    return {"status": status, "db_connection": db_status}
