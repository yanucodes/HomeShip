"""Database configuration and the request-scoped session provider.

Reads connection settings, builds the engine and session factory,
and exposes `get_session` as the single source of sessions for the rest of
the app.
"""
from collections.abc import Iterator

from config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


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
