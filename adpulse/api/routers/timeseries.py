"""
Time series endpoints.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from adpulse.api.dependencies import get_db
from adpulse.api.utils import apply_date_filters, calc_rate, parse_event_date
from adpulse.models import AdPerformance
from adpulse.schemas import DailyTimeseriesPoint

router = APIRouter(prefix="/timeseries", tags=["timeseries"])


@router.get("/daily", response_model=List[DailyTimeseriesPoint])
def daily_timeseries(
    platform: Optional[str] = None,
    campaign_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
) -> List[DailyTimeseriesPoint]:
    group_fields = [AdPerformance.event_date]
    select_fields = [
        AdPerformance.event_date,
        func.sum(AdPerformance.spend).label("spend"),
        func.sum(AdPerformance.clicks).label("clicks"),
        func.sum(AdPerformance.impressions).label("impressions"),
        func.sum(AdPerformance.conversions).label("conversions"),
        func.sum(AdPerformance.revenue).label("revenue"),
    ]
    if not platform:
        select_fields.append(AdPerformance.platform)
        group_fields.append(AdPerformance.platform)

    query = db.query(*select_fields)
    if platform:
        query = query.filter(AdPerformance.platform == platform)
    if campaign_id:
        query = query.filter(AdPerformance.campaign_id == campaign_id)

    query = apply_date_filters(query, start_date, end_date)
    query = query.group_by(*group_fields).order_by(AdPerformance.event_date)
    rows = query.all()
    points: List[DailyTimeseriesPoint] = []
    for row in rows:
        spend = row.spend or 0.0
        revenue = row.revenue or 0.0
        platform_value = platform or getattr(row, "platform", None)
        points.append(
            DailyTimeseriesPoint(
                date=parse_event_date(row.event_date),
                platform=platform_value,
                campaign_id=campaign_id,
                spend=spend,
                clicks=row.clicks or 0,
                impressions=row.impressions or 0,
                conversions=row.conversions or 0,
                revenue=revenue,
                roas=calc_rate(revenue, spend),
            )
        )
    return points
