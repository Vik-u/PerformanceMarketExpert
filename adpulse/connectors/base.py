"""
Connector abstractions for platform-specific ingestion logic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List

from adpulse.ingestion.schema import NormalizedRecord


class BaseConnector(ABC):
    """
    Shared interface for ingestion connectors regardless of the source system.
    """

    platform_slug: str
    platform_name: str

    def __init__(self) -> None:
        if not getattr(self, "platform_slug", None):
            raise ValueError("Connector must define platform_slug")
        if not getattr(self, "platform_name", None):
            raise ValueError("Connector must define platform_name")

    @abstractmethod
    def load_file(self, source: Path | str) -> List[NormalizedRecord]:
        """Return normalized records from the provided file."""

    @abstractmethod
    def normalize_rows(self, rows: Iterable[dict[str, str]]) -> List[NormalizedRecord]:
        """
        Transform raw source rows to NormalizedRecord instances.

        Implementations can assume that missing/invalid fields raised upstream.
        """


class CSVConnector(BaseConnector):
    """
    Convenience base class for CSV-based connectors.
    """

    def load_file(self, source: Path | str) -> List[NormalizedRecord]:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        import csv

        with path.open("r", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = [row for row in reader if any(value.strip() for value in row.values() if value)]
        return self.normalize_rows(rows)
