"""
Configuration helpers for the AdPulse ingestion module.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_PATH = DATA_DIR / "adpulse.db"


@dataclass(frozen=True)
class Settings:
    """Container for runtime configuration."""

    db_path: Path = DEFAULT_DB_PATH


def load_settings() -> Settings:
    """
    Return the Settings object, honoring environment overrides.
    """
    db_path_env = os.getenv("ADPULSE_DB_PATH")
    if db_path_env:
        db_path = Path(db_path_env).expanduser()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return Settings(db_path=db_path)
    return Settings()
