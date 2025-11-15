"""AI insights layer for AdPulse."""

from .insights_service import (
    get_account_health_summary,
    get_roas_drop_explanation,
)

__all__ = ["get_account_health_summary", "get_roas_drop_explanation"]
