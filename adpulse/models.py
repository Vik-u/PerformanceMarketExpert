"""
SQLAlchemy ORM models.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String, func, Index

from adpulse.database import Base


class AdPerformance(Base):
    __tablename__ = "ad_performance"
    __table_args__ = (
        Index("idx_ad_perf_campaign_date", "campaign_id", "event_date"),
        Index("idx_ad_perf_platform_date", "platform", "event_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False, index=True)
    campaign_id = Column(String, nullable=False, index=True)
    campaign_name = Column(String, nullable=False)
    event_date = Column(String, nullable=False)
    impressions = Column(Integer, nullable=False)
    clicks = Column(Integer, nullable=False)
    spend = Column(Float, nullable=False)
    conversions = Column(Integer, nullable=False)
    revenue = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, server_default=func.current_timestamp())
