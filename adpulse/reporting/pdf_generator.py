"""
PDF generation utilities using ReportLab.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Spacer,
    Paragraph,
    Table,
    TableStyle,
)


def _heading(text: str, level: int = 1) -> Paragraph:
    styles = getSampleStyleSheet()
    style_name = "Heading1" if level == 1 else "Heading2"
    return Paragraph(text, styles[style_name])


def _body(text: str) -> Paragraph:
    styles = getSampleStyleSheet()
    body_style: ParagraphStyle = styles["BodyText"]
    body_style.leading = 14
    return Paragraph(text, body_style)


def generate_performance_report(output_path: str, report_data: Dict) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_file), pagesize=LETTER, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story: List = []

    story.append(_heading("AdPulse Performance Report", level=1))
    story.append(Spacer(1, 0.2 * inch))
    story.append(_body(report_data.get("title", "Weekly Marketing Overview")))
    story.append(_body(report_data.get("date_range", "")))
    story.append(Spacer(1, 0.3 * inch))

    story.append(_heading("Overall Summary", level=2))
    summary_lines = []
    for platform in report_data.get("platform_summaries", []):
        summary_lines.append(
            f"{platform['platform']}: Spend ${platform['total_spend']:,.2f} | "
            f"Revenue ${platform['total_revenue']:,.2f} | Conversions {platform['total_conversions']:,} | "
            f"ROAS {platform.get('roas', 0):.2f}x"
        )
    if summary_lines:
        story.append(_body("<br/>".join(summary_lines)))
    else:
        story.append(_body("No platform data available for this period."))
    story.append(Spacer(1, 0.3 * inch))

    for platform in report_data.get("platform_summaries", []):
        story.append(_heading(platform["platform"], level=2))
        text = (
            f"Spend: ${platform['total_spend']:,.2f}<br/>"
            f"Revenue: ${platform['total_revenue']:,.2f}<br/>"
            f"Impressions: {platform['total_impressions']:,}<br/>"
            f"Clicks: {platform['total_clicks']:,}<br/>"
            f"Conversions: {platform['total_conversions']:,}<br/>"
            f"ROAS: {platform.get('roas', 0):.2f}x, CPC: ${platform.get('cpc', 0):.2f}, CPA: ${platform.get('cpa', 0):.2f}"
        )
        story.append(_body(text))
        story.append(Spacer(1, 0.2 * inch))

    story.append(_heading("Top Campaigns", level=2))
    top_campaigns: List[Dict] = report_data.get("top_campaigns", [])
    if top_campaigns:
        table_data = [["Campaign", "Platform", "Spend", "Revenue", "ROAS"]]
        for campaign in top_campaigns:
            table_data.append(
                [
                    campaign["campaign_name"],
                    campaign["platform"],
                    f"${campaign['total_spend']:,.2f}",
                    f"${campaign['total_revenue']:,.2f}",
                    f"{campaign.get('roas', 0):.2f}x",
                ]
            )
        table = Table(table_data, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(table)
    else:
        story.append(_body("No campaign data available."))
    story.append(Spacer(1, 0.3 * inch))

    story.append(_heading("AI Account Health Summary", level=2))
    story.append(_body(report_data.get("ai_account_health", "No AI summary available.")))
    story.append(Spacer(1, 0.2 * inch))

    if report_data.get("ai_roas_insights"):
        story.append(_heading("AI ROAS Insights", level=2))
        story.append(_body(report_data["ai_roas_insights"]))

    doc.build(story)
