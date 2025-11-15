"""
Identifier helpers for normalized campaign data.
"""
from __future__ import annotations

import re


def slugify_name(value: str) -> str:
    """Generate a filesystem/url friendly slug from a campaign name."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-")
    cleaned = cleaned.lower()
    return cleaned or "campaign"


def build_campaign_id(platform_slug: str, campaign_name: str, explicit_id: str | None = None) -> str:
    """
    Return a stable campaign identifier.

    Prefer the explicit ID embedded in the source CSV when present, otherwise
    fallback to 'platform-slugified-campaign-name'.
    """
    if explicit_id:
        return explicit_id.strip()
    slug = slugify_name(campaign_name)
    return f"{platform_slug}-{slug}"
