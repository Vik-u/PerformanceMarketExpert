"""
FastAPI entry point for Module 2 - Metrics API.
"""
from __future__ import annotations

from fastapi import FastAPI

from adpulse.api.routers import (
    campaigns_router,
    health_router,
    summary_router,
    timeseries_router,
    insights_router,
    reports_router,
)
from adpulse.database import init_db

init_db()

app = FastAPI(title="AdPulse Metrics API", version="0.1.0")

app.include_router(health_router)
app.include_router(summary_router)
app.include_router(campaigns_router)
app.include_router(timeseries_router)
app.include_router(insights_router)
app.include_router(reports_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "AdPulse Metrics API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("adpulse.api.main:app", host="0.0.0.0", port=8000, reload=True)
