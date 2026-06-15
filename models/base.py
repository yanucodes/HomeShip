"""Shared SQLAlchemy declarative base.

Every ORM model in this app must inherit from the single `Base` defined here,
so they all share one `MetaData` object. That shared metadata is what lets
`Base.metadata.create_all(...)` and Alembic autogenerate see every table.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""
