"""
Google Ads CSV connector implementation.
"""
from __future__ import annotations

from typing import Iterable, List

from adpulse.connectors.base import CSVConnector
from adpulse.ingestion.schema import NormalizedRecord, parse_date, parse_float, parse_int
from adpulse.utils import build_campaign_id


def _clean_money(value: str | None) -> str | None:
    if value is None:
        return None
    return value.replace("$", "").replace(",", "").strip()


DEFAULT_CONVERSION_VALUE = 25.0


def _resolve_revenue(row: dict[str, str], conversions: int) -> float:
    for key in ("Revenue", "ConversionValue", "Conversion value", "PurchaseValue"):
        if key in row and row[key]:
            return parse_float(row[key], default=0.0)
    return conversions * DEFAULT_CONVERSION_VALUE


class GoogleAdsCSVConnector(CSVConnector):
    platform_slug = "google"
    platform_name = "Google Ads"

    def normalize_rows(self, rows: Iterable[dict[str, str]]) -> List[NormalizedRecord]:
        normalized: List[NormalizedRecord] = []
        for row in rows:
            campaign_name = (row.get("Campaign") or "Unknown Campaign").strip()
            conversions = parse_int(row.get("Conversions"))
            record = NormalizedRecord(
                platform=self.platform_name,
                campaign_id=build_campaign_id(self.platform_slug, campaign_name, row.get("Campaign ID")),
                campaign_name=campaign_name,
                event_date=parse_date(row.get("Date")),
                impressions=parse_int(row.get("Impressions")),
                clicks=parse_int(row.get("Clicks")),
                spend=parse_float(_clean_money(row.get("Cost")), default=0.0),
                conversions=conversions,
                revenue=_resolve_revenue(row, conversions),
            )
            normalized.append(record)
        return normalized
