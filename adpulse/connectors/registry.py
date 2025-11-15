"""
Connector registry keeps track of supported ingestion sources.
"""
from __future__ import annotations

from typing import Dict, Iterable

from adpulse.connectors.base import BaseConnector


class ConnectorRegistry:
    """Runtime container for connector implementations."""

    def __init__(self) -> None:
        self._connectors: Dict[str, BaseConnector] = {}

    def register(self, connector: BaseConnector) -> None:
        slug = connector.platform_slug.lower()
        self._connectors[slug] = connector

    def get(self, slug: str) -> BaseConnector:
        normalized = slug.lower()
        if normalized not in self._connectors:
            supported = ", ".join(sorted(self._connectors))
            raise KeyError(f"Unsupported platform '{slug}'. Supported: {supported}")
        return self._connectors[normalized]

    def supported_platforms(self) -> Iterable[str]:
        return sorted(self._connectors)

    def __contains__(self, slug: str) -> bool:
        return slug.lower() in self._connectors


def build_default_registry() -> ConnectorRegistry:
    """
    Helper to lazily import connectors and register them.

    Avoid heavy imports at module import time for CLI responsiveness.
    """
    from adpulse.connectors.google_ads import GoogleAdsCSVConnector
    from adpulse.connectors.meta_ads import MetaAdsCSVConnector
    from adpulse.connectors.tiktok_ads import TikTokAdsCSVConnector

    registry = ConnectorRegistry()
    registry.register(GoogleAdsCSVConnector())
    registry.register(MetaAdsCSVConnector())
    registry.register(TikTokAdsCSVConnector())
    return registry
