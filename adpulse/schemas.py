"""
Pydantic schemas shared across API endpoints.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class PlatformSummary(BaseModel):
    platform: str
    total_spend: float = Field(0, description="Total spend in currency units")
    total_clicks: int = 0
    total_impressions: int = 0
    total_conversions: int = 0
    total_revenue: float = 0.0
    ctr: float = 0.0
    cpc: float = 0.0
    cpa: float = 0.0
    roas: float = 0.0


class CampaignSummary(BaseModel):
    campaign_id: str
    campaign_name: str
    platform: str
    total_spend: float
    total_clicks: int
    total_impressions: int
    total_conversions: int
    total_revenue: float
    ctr: float
    cpc: float
    cpa: float
    roas: float


class DailyTimeseriesPoint(BaseModel):
    date: date
    platform: Optional[str] = None
    campaign_id: Optional[str] = None
    spend: float
    clicks: int
    impressions: int
    conversions: int
    revenue: float
    roas: float


class CampaignDetail(BaseModel):
    campaign_id: str
    campaign_name: str
    platform: str
    total_spend: float
    total_clicks: int
    total_impressions: int
    total_conversions: int
    total_revenue: float
    ctr: float
    cpc: float
    cpa: float
    roas: float
    timeseries: List[DailyTimeseriesPoint]
