"""
Placeholder email sender – logs intent without sending.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def send_report_via_email(to_email: str, report_path: str) -> None:
    message = f"[Email Stub] Would send report '{report_path}' to '{to_email}'."
    logger.info(message)
    print(message)
