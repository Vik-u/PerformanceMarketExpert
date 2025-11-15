"""
Platform-level summary endpoints.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from adpulse.api.dependencies import get_db
from adpulse.api.utils import apply_date_filters, calc_ctr, calc_rate
from adpulse.models import AdPerformance
from adpulse.schemas import PlatformSummary

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/platforms", response_model=List[PlatformSummary])
def platform_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
) -> List[PlatformSummary]:
    query = (
        db.query(
            AdPerformance.platform.label("platform"),
            func.sum(AdPerformance.spend).label("total_spend"),
            func.sum(AdPerformance.clicks).label("total_clicks"),
            func.sum(AdPerformance.impressions).label("total_impressions"),
            func.sum(AdPerformance.conversions).label("total_conversions"),
            func.sum(AdPerformance.revenue).label("total_revenue"),
        )
        .group_by(AdPerformance.platform)
        .order_by(AdPerformance.platform)
    )
    query = apply_date_filters(query, start_date, end_date)
    results = query.all()
    summaries: List[PlatformSummary] = []
    for row in results:
        spend = row.total_spend or 0.0
        clicks = row.total_clicks or 0
        impressions = row.total_impressions or 0
        conversions = row.total_conversions or 0
        revenue = row.total_revenue or 0.0
        summaries.append(
            PlatformSummary(
                platform=row.platform,
                total_spend=spend,
                total_clicks=clicks,
                total_impressions=impressions,
                total_conversions=conversions,
                total_revenue=revenue,
                ctr=calc_ctr(clicks, impressions),
                cpc=calc_rate(spend, clicks),
                cpa=calc_rate(spend, conversions),
                roas=calc_rate(revenue, spend),
            )
        )
    return summaries
