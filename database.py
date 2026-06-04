"""Database configuration and the request-scoped session provider.

Reads connection settings from the environment (`.env`), builds the engine
and session factory, and exposes `get_session` as the single source of
sessions for the rest of the app.
"""
from collections.abc import Iterator

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


class Settings(BaseSettings):
    """Environment-backed app settings.

    Attributes:
        database_url: Connection URL for the application database.
        test_database_url: Connection URL for the test database, or None
            when not running tests.
    """
    model_config = SettingsConfigDict(env_file=".env")
    database_url: str
    test_database_url: str | None = None


settings = Settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


def get_session() -> Iterator[Session]:
    """Provide a request-scoped session.

    If the endpoint returns normally, the session is committed; if anything
    raises, the entire request is rolled back. Repositories only flush (to
    populate PKs mid-request) — the durable commit happens here at the end.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
