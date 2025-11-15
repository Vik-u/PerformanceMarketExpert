"""
Data ingestion orchestration entry point.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from adpulse.connectors.registry import ConnectorRegistry
from adpulse.storage.database import DatabaseManager


@dataclass(frozen=True)
class IngestionReport:
    platform: str
    source_file: Path
    rows_ingested: int


class DataIngestor:
    """
    Coordinates the flow between connectors and persistent storage.
    """

    def __init__(self, registry: ConnectorRegistry, database: DatabaseManager) -> None:
        self.registry = registry
        self.database = database
        self.database.initialize()

    def ingest_file(self, platform_slug: str, csv_path: Path | str) -> IngestionReport:
        connector = self.registry.get(platform_slug)
        path = Path(csv_path)
        records = connector.load_file(path)
        ingested = self.database.insert_records(records)
        return IngestionReport(connector.platform_name, path, ingested)

    def summary_rows(self):
        return self.database.fetch_summary()

    def table_row_count(self) -> int:
        return self.database.row_count()
