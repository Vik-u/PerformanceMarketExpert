"""
Report generation endpoints.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from adpulse.reporting import build_weekly_report, send_report_via_email

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportRequest(BaseModel):
    start_date: date
    end_date: date
    send_email: bool = False
    email: Optional[str] = None


@router.post("/generate")
def generate_report(request: ReportRequest) -> dict:
    try:
        report_path = build_weekly_report(request.start_date, request.end_date)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="Failed to generate report") from exc

    if request.send_email:
        if not request.email:
            raise HTTPException(status_code=400, detail="Email address required when send_email is true")
        send_report_via_email(request.email, report_path)

    return {
        "report_path": report_path,
        "message": "Report generated successfully",
    }


@router.get("/list")
def list_reports(directory: str = "reports") -> dict:
    path = Path(directory)
    if not path.exists():
        return {"reports": []}
    files = [
        {
            "name": file.name,
            "path": str(file),
            "size_kb": round(file.stat().st_size / 1024, 1),
        }
        for file in sorted(path.glob("*.pdf"))
    ]
    return {"reports": files}
