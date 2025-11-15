"""Reporting and automation helpers (Module 5)."""

from .report_service import build_weekly_report, build_daily_report
from .email_stub import send_report_via_email

__all__ = ["build_weekly_report", "build_daily_report", "send_report_via_email"]
