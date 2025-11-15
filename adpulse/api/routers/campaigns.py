"""
Campaign-focused endpoints.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from adpulse.api.dependencies import get_db
from adpulse.api.utils import apply_date_filters, calc_ctr, calc_rate, parse_event_date
from adpulse.models import AdPerformance
from adpulse.schemas import CampaignDetail, CampaignSummary, DailyTimeseriesPoint

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _filtered_campaign_query(
    db: Session,
    campaign_id: str,
    start_date: Optional[date],
    end_date: Optional[date],
) -> Query:
    query = db.query(AdPerformance).filter(AdPerformance.campaign_id == campaign_id)
    return apply_date_filters(query, start_date, end_date)


@router.get("/summary", response_model=List[CampaignSummary])
def campaign_summary(
    platform: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
) -> List[CampaignSummary]:
    query = (
        db.query(
            AdPerformance.campaign_id,
            AdPerformance.campaign_name,
            AdPerformance.platform,
            func.sum(AdPerformance.spend).label("total_spend"),
            func.sum(AdPerformance.clicks).label("total_clicks"),
            func.sum(AdPerformance.impressions).label("total_impressions"),
            func.sum(AdPerformance.conversions).label("total_conversions"),
            func.sum(AdPerformance.revenue).label("total_revenue"),
        )
        .group_by(
            AdPerformance.campaign_id,
            AdPerformance.campaign_name,
            AdPerformance.platform,
        )
        .order_by(AdPerformance.platform, AdPerformance.campaign_name)
    )
    query = apply_date_filters(query, start_date, end_date)
    if platform:
        query = query.filter(AdPerformance.platform == platform)
    rows = query.all()
    summaries: List[CampaignSummary] = []
    for row in rows:
        spend = row.total_spend or 0.0
        clicks = row.total_clicks or 0
        impressions = row.total_impressions or 0
        conversions = row.total_conversions or 0
        revenue = row.total_revenue or 0.0
        summaries.append(
            CampaignSummary(
                campaign_id=row.campaign_id,
                campaign_name=row.campaign_name,
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


@router.get("/{campaign_id}/detail", response_model=CampaignDetail)
def campaign_detail(
    campaign_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
) -> CampaignDetail:
    base_query = _filtered_campaign_query(db, campaign_id, start_date, end_date)
    campaign_row = base_query.first()
    if not campaign_row:
        raise HTTPException(status_code=404, detail="Campaign not found")

    metrics_query = (
        db.query(
            func.sum(AdPerformance.spend).label("total_spend"),
            func.sum(AdPerformance.clicks).label("total_clicks"),
            func.sum(AdPerformance.impressions).label("total_impressions"),
            func.sum(AdPerformance.conversions).label("total_conversions"),
            func.sum(AdPerformance.revenue).label("total_revenue"),
        )
        .filter(AdPerformance.campaign_id == campaign_id)
    )
    metrics_query = apply_date_filters(metrics_query, start_date, end_date)
    metrics = metrics_query.one()
    spend = metrics.total_spend or 0.0
    clicks = metrics.total_clicks or 0
    impressions = metrics.total_impressions or 0
    conversions = metrics.total_conversions or 0
    revenue = metrics.total_revenue or 0.0

    ts_query = (
        db.query(
            AdPerformance.event_date,
            func.sum(AdPerformance.spend).label("spend"),
            func.sum(AdPerformance.clicks).label("clicks"),
            func.sum(AdPerformance.impressions).label("impressions"),
            func.sum(AdPerformance.conversions).label("conversions"),
            func.sum(AdPerformance.revenue).label("revenue"),
        )
        .filter(AdPerformance.campaign_id == campaign_id)
        .group_by(AdPerformance.event_date)
        .order_by(AdPerformance.event_date)
    )
    ts_query = apply_date_filters(ts_query, start_date, end_date)
    ts_rows = ts_query.all()
    timeseries: List[DailyTimeseriesPoint] = []
    for row in ts_rows:
        spend_row = row.spend or 0.0
        revenue_row = row.revenue or 0.0
        timeseries.append(
            DailyTimeseriesPoint(
                date=parse_event_date(row.event_date),
                platform=campaign_row.platform,
                campaign_id=campaign_id,
                spend=spend_row,
                clicks=row.clicks or 0,
                impressions=row.impressions or 0,
                conversions=row.conversions or 0,
                revenue=revenue_row,
                roas=calc_rate(revenue_row, spend_row),
            )
        )

    return CampaignDetail(
        campaign_id=campaign_id,
        campaign_name=campaign_row.campaign_name,
        platform=campaign_row.platform,
        total_spend=spend,
        total_clicks=clicks,
        total_impressions=impressions,
        total_conversions=conversions,
        total_revenue=revenue,
        ctr=calc_ctr(clicks, impressions),
        cpc=calc_rate(spend, clicks),
        cpa=calc_rate(spend, conversions),
        roas=calc_rate(revenue, spend),
        timeseries=timeseries,
    )
