"""Database configuration and the request-scoped session provider.

Reads connection settings, builds the engine and session factory,
and exposes `get_session` as the single source of sessions for the rest of
the app.
"""
from collections.abc import Iterator

from config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


# pool_pre_ping issues a lightweight check on a pooled connection before use
# and transparently replaces it if it has gone stale, so the app survives the
# idle-connection drops common with cloud Postgres (e.g. Render).
engine = create_engine(settings.database_url, pool_pre_ping=True)
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
