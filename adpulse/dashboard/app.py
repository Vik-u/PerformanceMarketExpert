"""
Streamlit dashboard for Module 3.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional
import tempfile

import pandas as pd
import streamlit as st

from adpulse.dashboard import api_client
from adpulse.dashboard.utils import aggregate_metric, format_currency, safe_divide
from adpulse.ai.openai_client import generate_completion
from adpulse.connectors.registry import build_default_registry
from adpulse.ingestion.data_ingestor import DataIngestor
from adpulse.storage.database import DatabaseManager
from adpulse.config import load_settings

st.set_page_config(page_title="AdPulse Dashboard", layout="wide")


PLATFORM_SLUG_TO_LABEL = {
    "google_ads": "Google Ads",
    "meta_ads": "Meta Ads",
    "tiktok_ads": "TikTok Ads",
}
PLATFORM_OPTIONS = ["All Platforms"] + list(PLATFORM_SLUG_TO_LABEL.keys())
UPLOAD_PLATFORM_OPTIONS = {
    "google": "Google Ads CSV",
    "meta": "Meta Ads CSV",
    "tiktok": "TikTok Ads CSV",
}


def display_api_error(section: str, message: str) -> None:
    st.error(f"{section}: {message}")
    st.caption("Check that the FastAPI service is running and reachable.")


def build_sidebar_filters():
    st.sidebar.header("Filters")
    default_start = date.today() - timedelta(days=30)
    default_end = date.today()
    start_date = st.sidebar.date_input("Start date", value=default_start)
    end_date = st.sidebar.date_input("End date", value=default_end)
    if isinstance(start_date, list):
        start_date = start_date[0]
    if isinstance(end_date, list):
        end_date = end_date[0]

    platform_choice = st.sidebar.selectbox(
        "Platform",
        PLATFORM_OPTIONS,
        index=0,
        format_func=lambda slug: "All Platforms" if slug == "All Platforms" else slug.replace("_", " ").title(),
    )
    platform_filter = None
    if platform_choice != "All Platforms":
        platform_filter = PLATFORM_SLUG_TO_LABEL.get(platform_choice)

    campaign_id = st.sidebar.text_input(
        "Campaign ID (optional)",
        help="Paste a campaign ID to focus the time series tab.",
    ).strip() or None

    render_upload_widget()

    return start_date, end_date, platform_filter, campaign_id


def render_overview_tab(platform_data: Optional[List[dict]]) -> None:
    st.subheader("Overview")
    if platform_data is None:
        display_api_error("Platform summary", "Unable to retrieve data.")
        return
    if not platform_data:
        st.info("No data available for the selected filters.")
        return

    total_spend = aggregate_metric(platform_data, "total_spend")
    total_revenue = aggregate_metric(platform_data, "total_revenue")
    total_conversions = aggregate_metric(platform_data, "total_conversions")
    roas = safe_divide(total_revenue, total_spend)

    cols = st.columns(4)
    cols[0].metric("Total Spend", format_currency(total_spend))
    cols[1].metric("Total Revenue", format_currency(total_revenue))
    cols[2].metric("Total Conversions", f"{int(total_conversions):,}")
    cols[3].metric("Overall ROAS", f"{roas:.2f}x")

    df = pd.DataFrame(platform_data)
    df = df.rename(
        columns={
            "platform": "Platform",
            "total_spend": "Spend",
            "total_clicks": "Clicks",
            "total_impressions": "Impressions",
            "total_conversions": "Conversions",
            "total_revenue": "Revenue",
        }
    )
    df["ROAS"] = df["Revenue"] / df["Spend"].replace({0: None})
    df["CPC"] = df["Spend"] / df["Clicks"].replace({0: None})
    df["CPA"] = df["Spend"] / df["Conversions"].replace({0: None})

    st.dataframe(
        df[
            [
                "Platform",
                "Spend",
                "Clicks",
                "Impressions",
                "Conversions",
                "Revenue",
                "ROAS",
                "CPC",
                "CPA",
            ]
        ].style.format(
            {
                "Spend": "${:,.2f}",
                "Revenue": "${:,.2f}",
                "ROAS": "{:,.2f}x",
                "CPC": "${:,.2f}",
                "CPA": "${:,.2f}",
            }
        ),
        use_container_width=True,
    )


def render_campaigns_tab(
    campaign_data: Optional[List[dict]],
    platform_filter: Optional[str],
) -> None:
    st.subheader("Campaigns")
    if campaign_data is None:
        display_api_error("Campaign summary", "Unable to retrieve data.")
        return
    if platform_filter:
        st.caption(f"Filtered by platform: {platform_filter}")
    if not campaign_data:
        st.info("No campaign rows for the selected filters.")
        return

    df = pd.DataFrame(campaign_data)
    df = df.rename(
        columns={
            "campaign_id": "Campaign ID",
            "campaign_name": "Campaign Name",
            "platform": "Platform",
            "total_spend": "Spend",
            "total_clicks": "Clicks",
            "total_impressions": "Impressions",
            "total_conversions": "Conversions",
            "total_revenue": "Revenue",
            "roas": "ROAS",
            "cpc": "CPC",
            "cpa": "CPA",
        }
    )
    st.dataframe(
        df[
            [
                "Platform",
                "Campaign Name",
                "Campaign ID",
                "Spend",
                "Clicks",
                "Conversions",
                "Revenue",
                "ROAS",
                "CPC",
                "CPA",
            ]
        ].style.format(
            {
                "Spend": "${:,.2f}",
                "Revenue": "${:,.2f}",
                "ROAS": "{:,.2f}x",
                "CPC": "${:,.2f}",
                "CPA": "${:,.2f}",
            }
        ),
        use_container_width=True,
    )


def render_timeseries_tab(timeseries: Optional[List[dict]]) -> None:
    st.subheader("Daily Time Series")
    if timeseries is None:
        display_api_error("Timeseries", "Unable to retrieve data.")
        return
    if not timeseries:
        st.info("No time series data for the selected filters.")
        return
    df = pd.DataFrame(timeseries)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    spend_chart = df.set_index("date")[["spend"]]
    revenue_chart = df.set_index("date")[["revenue", "conversions"]]

    st.line_chart(spend_chart, use_container_width=True, height=250)
    st.line_chart(revenue_chart, use_container_width=True, height=250)


def render_ai_insights_tab(start_date, end_date, platform_filter):
    st.subheader("AI Insights")
    account_insights = api_client.get_account_health_insights(start_date, end_date)
    if account_insights and account_insights.get("analysis"):
        st.markdown("#### Account Health Summary")
        st.markdown(account_insights["analysis"])
    else:
        display_api_error("Account insights", "Unavailable (check API key or server logs).")

    st.markdown("---")
    st.markdown("#### ROAS Drop Analysis")
    if not platform_filter:
        st.info("Select a platform in the sidebar to fetch ROAS-specific insights.")
        return
    roas_insights = api_client.get_roas_drop_insights(platform_filter, start_date, end_date)
    if roas_insights and roas_insights.get("analysis"):
        st.markdown(roas_insights["analysis"])
    else:
        display_api_error("ROAS insights", "No response returned.")


def render_chatbot_tab(
    platform_data,
    campaign_data,
    timeseries_data,
    start_date,
    end_date,
    platform_filter,
):
    st.subheader("AdPulse Copilot")
    st.caption("Ask natural-language questions about performance. Responses use your configured LLM (OpenAI or Ollama).")
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    for message in st.session_state["chat_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask about campaigns, spend, ROAS, or optimization ideas…")
    if prompt:
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("Generating insight..."):
                try:
                    context_snippet = build_chat_context(
                        platform_data, campaign_data, timeseries_data, start_date, end_date, platform_filter
                    )
                    llm_prompt = f"""
                    You are AdPulse, a performance marketing assistant.
                    Date range: {start_date} to {end_date}
                    Platform filter: {platform_filter or 'All'}

                    Context:
                    {context_snippet}

                    Question: {prompt}
                    """
                    response = generate_completion(llm_prompt.strip(), max_tokens=500)
                except Exception as exc:
                    response = f"Unable to fetch response: {exc}"
                st.markdown(response)
        st.session_state["chat_messages"].append({"role": "assistant", "content": response})


def build_chat_context(platform_data, campaign_data, timeseries_data, start_date, end_date, platform_filter):
    lines = []
    if platform_data:
        lines.append("Platform Summary:")
        for row in platform_data[:5]:
            lines.append(
                f"- {row['platform']}: Spend ${row['total_spend']:,.0f}, Revenue ${row['total_revenue']:,.0f}, "
                f"Conversions {row['total_conversions']}, ROAS {row['roas']:.2f}"
            )
    if campaign_data:
        lines.append("\nTop Campaigns:")
        for row in campaign_data[:5]:
            lines.append(
                f"- {row['campaign_name']} ({row['platform']}): Spend ${row['total_spend']:,.0f}, "
                f"Conv {row['total_conversions']}, ROAS {row['roas']:.2f}"
            )
    if timeseries_data:
        lines.append("\nRecent Daily Spend (last 5 rows):")
        subset = timeseries_data[-5:] if len(timeseries_data) >= 5 else timeseries_data
        for row in subset:
            lines.append(
                f"- {row['date']}: Spend ${row['spend']:,.0f}, Revenue ${row['revenue']:,.0f}, "
                f"Conversions {row['conversions']}"
            )
    lines.append(f"\nUser selected platform: {platform_filter or 'All platforms'}")
    lines.append(f"Date range: {start_date} to {end_date}")
    return "\n".join(lines)


def render_upload_widget():
    st.sidebar.markdown("---")
    st.sidebar.subheader("Upload CSV (ingest to database)")
    platform_slug = st.sidebar.selectbox(
        "Source platform",
        list(UPLOAD_PLATFORM_OPTIONS.keys()),
        format_func=lambda slug: UPLOAD_PLATFORM_OPTIONS[slug],
    )
    uploaded_file = st.sidebar.file_uploader(
        "Choose CSV file",
        type=["csv"],
        help="Upload raw exports from Google/Meta/TikTok.",
        key="csv_uploader",
    )
    disabled = uploaded_file is None
    if st.sidebar.button("Ingest file", disabled=disabled):
        if uploaded_file is None:
            st.sidebar.warning("Please pick a CSV file.")
            return
        try:
            message = ingest_uploaded_csv(platform_slug, uploaded_file)
            st.sidebar.success(message)
        except Exception as exc:  # pragma: no cover - UI feedback
            st.sidebar.error(f"Ingestion failed: {exc}")


def ingest_uploaded_csv(platform_slug: str, uploaded_file) -> str:
    ingestor = get_ingestor()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = Path(tmp.name)
    report = ingestor.ingest_file(platform_slug, tmp_path)
    return f"[{report.platform}] Ingested {report.rows_ingested} rows"


def get_ingestor() -> DataIngestor:
    if "data_ingestor" not in st.session_state:
        settings = load_settings()
        registry = build_default_registry()
        database = DatabaseManager(settings.db_path)
        st.session_state["data_ingestor"] = DataIngestor(registry, database)
    return st.session_state["data_ingestor"]


def main():
    st.title("AdPulse – Performance Dashboard")
    st.write("Visualize ingested campaign data via the Module 2 Metrics API.")

    start_date, end_date, platform_filter, campaign_id = build_sidebar_filters()

    platform_data = api_client.get_platform_summary(start_date=start_date, end_date=end_date)
    if platform_filter and platform_data:
        platform_data = [row for row in platform_data if row["platform"] == platform_filter]

    campaign_data = api_client.get_campaign_summary(
        platform=platform_filter,
        start_date=start_date,
        end_date=end_date,
    )

    timeseries_data = api_client.get_daily_timeseries(
        platform=platform_filter,
        campaign_id=campaign_id,
        start_date=start_date,
        end_date=end_date,
    )

    overview_tab, campaigns_tab, timeseries_tab, insights_tab, chatbot_tab = st.tabs(
        ["Overview", "Campaigns", "Timeseries", "AI Insights", "Chatbot"]
    )

    with overview_tab:
        render_overview_tab(platform_data)

    with campaigns_tab:
        render_campaigns_tab(campaign_data, platform_filter)

    with timeseries_tab:
        render_timeseries_tab(timeseries_data)

    with insights_tab:
        render_ai_insights_tab(start_date, end_date, platform_filter)

    with chatbot_tab:
        render_chatbot_tab(
            platform_data,
            campaign_data,
            timeseries_data,
            start_date,
            end_date,
            platform_filter,
        )


if __name__ == "__main__":
    main()
