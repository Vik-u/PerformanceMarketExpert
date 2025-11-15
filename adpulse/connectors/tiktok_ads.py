"""
TikTok Ads CSV connector.
"""
from __future__ import annotations

from typing import Iterable, List

from adpulse.connectors.base import CSVConnector
from adpulse.ingestion.schema import NormalizedRecord, parse_date, parse_float, parse_int
from adpulse.utils import build_campaign_id

DEFAULT_CONVERSION_VALUE = 25.0


def _resolve_revenue(row: dict[str, str], conversions: int) -> float:
    for key in ("Revenue", "ConversionValue", "PurchaseValue", "Value"):
        if key in row and row[key]:
            return parse_float(row[key], default=0.0)
    return conversions * DEFAULT_CONVERSION_VALUE


class TikTokAdsCSVConnector(CSVConnector):
    platform_slug = "tiktok"
    platform_name = "TikTok Ads"

    def normalize_rows(self, rows: Iterable[dict[str, str]]) -> List[NormalizedRecord]:
        normalized: List[NormalizedRecord] = []
        for row in rows:
            campaign_name = (row.get("CampaignName") or row.get("campaign_name") or "Unknown Campaign").strip()
            conversions = parse_int(row.get("Conversions") or row.get("Leads"))
            record = NormalizedRecord(
                platform=self.platform_name,
                campaign_id=build_campaign_id(self.platform_slug, campaign_name, row.get("CampaignId")),
                campaign_name=campaign_name,
                event_date=parse_date(row.get("StatDate") or row.get("date")),
                impressions=parse_int(row.get("Impressions")),
                clicks=parse_int(row.get("Clicks")),
                spend=parse_float(row.get("Cost") or row.get("Spend"), default=0.0),
                conversions=conversions,
                revenue=_resolve_revenue(row, conversions),
            )
            normalized.append(record)
        return normalized
