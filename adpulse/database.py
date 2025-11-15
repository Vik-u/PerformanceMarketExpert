"""
SQLAlchemy database configuration shared across modules.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from adpulse.config import load_settings

settings = load_settings()
DATABASE_URL = f"sqlite:///{settings.db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    """Ensure tables exist for SQLAlchemy consumers."""
    import adpulse.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
