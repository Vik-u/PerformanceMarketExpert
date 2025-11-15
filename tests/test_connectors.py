from pathlib import Path

from adpulse.connectors.google_ads import GoogleAdsCSVConnector
from adpulse.connectors.meta_ads import MetaAdsCSVConnector
from adpulse.connectors.tiktok_ads import TikTokAdsCSVConnector


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    import csv

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def test_google_connector_normalizes(tmp_path):
    csv_path = tmp_path / "google.csv"
    _write_csv(
        csv_path,
        ["Campaign", "Date", "Impressions", "Clicks", "Cost", "Conversions"],
        [["Brand", "2024-01-01", "1000", "25", "12.3", "5"]],
    )
    connector = GoogleAdsCSVConnector()
    records = connector.load_file(csv_path)
    assert len(records) == 1
    record = records[0]
    assert record.platform == "Google Ads"
    assert record.campaign_id.startswith("google-")
    assert record.campaign_name == "Brand"
    assert record.impressions == 1000
    assert record.clicks == 25
    assert round(record.spend, 1) == 12.3
    assert record.conversions == 5
    assert record.revenue == record.conversions * 25.0


def test_meta_connector_normalizes(tmp_path):
    csv_path = tmp_path / "meta.csv"
    _write_csv(
        csv_path,
        [
            "campaign_name",
            "reporting_starts",
            "impressions",
            "link_clicks",
            "spend",
            "purchases",
        ],
        [["Prospecting", "01/02/2024", "500", "10", "5.00", "2"]],
    )
    connector = MetaAdsCSVConnector()
    records = connector.load_file(csv_path)
    assert len(records) == 1
    record = records[0]
    assert record.platform == "Meta Ads"
    assert record.campaign_id.startswith("meta-")
    assert record.campaign_name == "Prospecting"
    assert record.event_date.year == 2024
    assert record.impressions == 500
    assert record.clicks == 10
    assert record.conversions == 2
    assert record.revenue == record.conversions * 25.0


def test_tiktok_connector_normalizes(tmp_path):
    csv_path = tmp_path / "tiktok.csv"
    _write_csv(
        csv_path,
        ["CampaignName", "StatDate", "Impressions", "Clicks", "Cost", "Conversions"],
        [["Launch", "2024/03/01", "250", "9", "3.5", "1"]],
    )
    connector = TikTokAdsCSVConnector()
    records = connector.load_file(csv_path)
    assert len(records) == 1
    record = records[0]
    assert record.platform == "TikTok Ads"
    assert record.campaign_id.startswith("tiktok-")
    assert record.campaign_name == "Launch"
    assert record.impressions == 250
    assert record.clicks == 9
    assert record.spend == 3.5
    assert record.revenue == record.conversions * 25.0
