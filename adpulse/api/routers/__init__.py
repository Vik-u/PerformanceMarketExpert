"""Router exports for the API layer."""

from .health import router as health_router
from .summary import router as summary_router
from .campaigns import router as campaigns_router
from .timeseries import router as timeseries_router
from .insights import router as insights_router
from .reports import router as reports_router

__all__ = [
    "health_router",
    "summary_router",
    "campaigns_router",
    "timeseries_router",
    "insights_router",
    "reports_router",
]
