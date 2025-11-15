"""
Meta Ads CSV connector.
"""
from __future__ import annotations

from typing import Iterable, List

from adpulse.connectors.base import CSVConnector
from adpulse.ingestion.schema import NormalizedRecord, parse_date, parse_float, parse_int
from adpulse.utils import build_campaign_id

DEFAULT_CONVERSION_VALUE = 25.0


def _resolve_revenue(row: dict[str, str], conversions: int) -> float:
    for key in ("purchase_roas", "purchase_value", "purchase_conversion_value", "revenue", "value"):
        if key in row and row[key]:
            return parse_float(row[key], default=0.0)
    return conversions * DEFAULT_CONVERSION_VALUE


class MetaAdsCSVConnector(CSVConnector):
    platform_slug = "meta"
    platform_name = "Meta Ads"

    def normalize_rows(self, rows: Iterable[dict[str, str]]) -> List[NormalizedRecord]:
        normalized: List[NormalizedRecord] = []
        for row in rows:
            campaign_name = (row.get("campaign_name") or "Unknown Campaign").strip()
            conversions = parse_int(row.get("purchases") or row.get("conversions"))
            record = NormalizedRecord(
                platform=self.platform_name,
                campaign_id=build_campaign_id(self.platform_slug, campaign_name, row.get("campaign_id")),
                campaign_name=campaign_name,
                event_date=parse_date(row.get("reporting_starts") or row.get("date")),
                impressions=parse_int(row.get("impressions")),
                clicks=parse_int(row.get("link_clicks") or row.get("clicks")),
                spend=parse_float(row.get("spend")),
                conversions=conversions,
                revenue=_resolve_revenue(row, conversions),
            )
            normalized.append(record)
        return normalized
