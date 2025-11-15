"""
Typer-based CLI for AdPulse operations.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Optional

import typer
from tabulate import tabulate

from adpulse.config import Settings, load_settings
from adpulse.connectors.registry import build_default_registry
from adpulse.ingestion.data_ingestor import DataIngestor
from adpulse.reporting import build_weekly_report, send_report_via_email
from adpulse.storage.database import DatabaseManager

app = typer.Typer(help="AdPulse CLI (ingestion, reporting)")


def _build_ingestor(settings: Settings | None = None) -> DataIngestor:
    settings = settings or load_settings()
    registry = build_default_registry()
    database = DatabaseManager(settings.db_path)
    return DataIngestor(registry, database)


@app.command()
def load(
    platform: str = typer.Argument(..., help="Platform slug (google, meta, tiktok)"),
    csv_path: Path = typer.Argument(..., exists=True, readable=True),
) -> None:
    """
    Load a CSV file for the specified platform into the SQLite database.
    """
    ingestor = _build_ingestor()
    report = ingestor.ingest_file(platform, csv_path)
    typer.secho(
        f"[{report.platform}] Ingested {report.rows_ingested} rows from {csv_path}",
        fg=typer.colors.GREEN,
    )


@app.command()
def summary() -> None:
    """
    Show aggregated metrics per platform.
    """
    ingestor = _build_ingestor()
    rows = ingestor.summary_rows()
    if not rows:
        typer.echo("No data found. Load CSV files first with `adpulse load ...`.")
        raise typer.Exit(code=0)

    table = tabulate(
        [
            [
                row["platform"],
                row["rows_ingested"] or 0,
                row["impressions"] or 0,
                row["clicks"] or 0,
                f"${(row['spend'] or 0):,.2f}",
                row["conversions"] or 0,
                f"${(row['revenue'] or 0):,.2f}",
            ]
            for row in rows
        ],
        headers=["Platform", "Rows", "Impressions", "Clicks", "Spend", "Conversions", "Revenue"],
        tablefmt="github",
    )
    typer.echo(table)

    totals = ingestor.database.fetch_totals()
    if totals:
        typer.echo(
            f"\nGrand Total Rows: {totals['rows_ingested'] or 0} | "
            f"Spend: ${(totals['spend'] or 0):,.2f} | "
            f"Conversions: {totals['conversions'] or 0} | "
            f"Revenue: ${(totals['revenue'] or 0):,.2f}"
        )


@app.command()
def verify() -> None:
    """
    Quick sanity check to confirm records exist in the database.
    """
    ingestor = _build_ingestor()
    count = ingestor.table_row_count()
    typer.echo(f"ad_performance rows: {count}")


@app.command("generate-report")
def generate_report_cmd(
    start_date: str = typer.Option(..., help="Report start date YYYY-MM-DD"),
    end_date: str = typer.Option(..., help="Report end date YYYY-MM-DD"),
    email: Optional[str] = typer.Option(None, help="Email address to send the report stub to"),
) -> None:
    """
    Build a PDF report for the provided date window (Module 5).
    """
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    typer.echo(f"Building report for {start} to {end} ...")
    report_path = build_weekly_report(start, end)
    typer.secho(f"Report generated at {report_path}", fg=typer.colors.GREEN)
    if email:
        send_report_via_email(email, report_path)


@app.command("list-reports")
def list_reports(directory: Path = typer.Option(Path("reports"), exists=False, help="Reports directory")) -> None:
    """
    List generated PDF reports.
    """
    if not directory.exists():
        typer.echo("No reports directory found yet.")
        raise typer.Exit(code=0)

    files = sorted(p for p in directory.glob("*.pdf"))
    if not files:
        typer.echo("No PDF reports found.")
        raise typer.Exit(code=0)

    typer.echo("Available reports:")
    for file in files:
        size_kb = file.stat().st_size / 1024
        typer.echo(f"- {file.name} ({size_kb:.1f} KB)")
