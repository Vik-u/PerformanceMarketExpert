"""
Generate synthetic CSV exports for Google, Meta and TikTok so we can test the pipeline
with ~500 rows per platform.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "sample_data" / "synthetic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def random_date(start: date, days: int) -> date:
    return start + timedelta(days=random.randint(0, days))


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def generate_google(num_rows: int = 500) -> None:
    campaigns = ["Brand", "Retargeting", "Prospecting", "DSA", "Shopping", "App Installs"]
    start = date(2024, 1, 1)
    rows = []
    for _ in range(num_rows):
        campaign = random.choice(campaigns)
        impressions = random.randint(500, 5000)
        clicks = max(1, int(impressions * random.uniform(0.01, 0.08)))
        spend = round(random.uniform(20, 600), 2)
        conversions = max(0, int(clicks * random.uniform(0.02, 0.25)))
        rows.append(
            [
                f"{campaign} {random.randint(1,4)}",
                random_date(start, 120).isoformat(),
                impressions,
                clicks,
                spend,
                conversions,
            ]
        )
    write_csv(
        OUTPUT_DIR / "google_ads_synth.csv",
        ["Campaign", "Date", "Impressions", "Clicks", "Cost", "Conversions"],
        rows,
    )


def generate_meta(num_rows: int = 500) -> None:
    campaigns = ["Lookalike", "Retention", "Conversion", "Awareness", "Video"]
    start = date(2024, 1, 1)
    rows = []
    for _ in range(num_rows):
        campaign = random.choice(campaigns)
        impressions = random.randint(400, 4000)
        clicks = max(1, int(impressions * random.uniform(0.015, 0.1)))
        spend = round(random.uniform(15, 450), 2)
        purchases = max(0, int(clicks * random.uniform(0.03, 0.3)))
        rows.append(
            [
                f"{campaign} {random.randint(1,5)}",
                random_date(start, 120).strftime("%m/%d/%Y"),
                impressions,
                clicks,
                spend,
                purchases,
            ]
        )
    write_csv(
        OUTPUT_DIR / "meta_ads_synth.csv",
        ["campaign_name", "reporting_starts", "impressions", "link_clicks", "spend", "purchases"],
        rows,
    )


def generate_tiktok(num_rows: int = 500) -> None:
    campaigns = ["Spark Ads", "Creator Collab", "GenZ Push", "In-Feed"]
    start = date(2024, 1, 1)
    rows = []
    for _ in range(num_rows):
        campaign = random.choice(campaigns)
        impressions = random.randint(300, 3500)
        clicks = max(1, int(impressions * random.uniform(0.02, 0.12)))
        spend = round(random.uniform(10, 380), 2)
        conversions = max(0, int(clicks * random.uniform(0.01, 0.2)))
        rows.append(
            [
                f"{campaign} {random.randint(1,6)}",
                random_date(start, 120).strftime("%Y/%m/%d"),
                impressions,
                clicks,
                spend,
                conversions,
            ]
        )
    write_csv(
        OUTPUT_DIR / "tiktok_ads_synth.csv",
        ["CampaignName", "StatDate", "Impressions", "Clicks", "Cost", "Conversions"],
        rows,
    )


def main() -> None:
    random.seed(42)
    generate_google()
    generate_meta()
    generate_tiktok()
    print(f"Synthetic CSVs created under {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
