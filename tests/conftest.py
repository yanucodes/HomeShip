"""Shared pytest fixtures: test database, rollback-per-test session, client."""
# Using a fixture by depending on its name is the pytest idiom, not a bug.
# pylint: disable=redefined-outer-name
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from config import settings
from database import get_session
from main import app
from models import Base


if not settings.test_database_url:
    raise RuntimeError(
        "test_database_url is not set. Add TEST_DATABASE_URL to your .env "
    )
engine = create_engine(settings.test_database_url)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    """Create every table once for the test session, drop them at the end."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def session():
    """A session wrapped in a transaction that is rolled back after
    the test."""
    connection = engine.connect()
    transaction = connection.begin()
    test_session = Session(
        bind=connection, join_transaction_mode="create_savepoint"
    )
    try:
        yield test_session
    finally:
        test_session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(session):
    """A TestClient whose endpoints use the test's rolled-back session.
    """
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
