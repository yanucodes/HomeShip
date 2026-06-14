"""add string length limits

Revision ID: 26471b9f5cce
Revises: 8116bdb9269e
Create Date: 2026-06-14 15:08:53.689668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26471b9f5cce'
down_revision: Union[str, Sequence[str], None] = '8116bdb9269e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, column, capped length) for every length cap added in this revision.
# Caps mirror the Pydantic schema limits (schemas.validators.bounded_str).
# Filled in by hand: Alembic does not detect an unbounded VARCHAR being
# tightened to VARCHAR(N), even with compare_type enabled.
_LIMITS = [
    ("users", "username", 30),
    ("users", "display_name", 30),
    ("users", "email", 254),
    ("ships", "shipname", 50),
    ("ship_members", "role", 30),
    ("tasks", "content", 200),
    ("supplies", "name", 200),
]


def upgrade() -> None:
    """Tighten each column from unbounded VARCHAR to VARCHAR(N)."""
    for table, column, length in _LIMITS:
        op.alter_column(
            table, column,
            existing_type=sa.String(),
            type_=sa.String(length=length),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Widen each column back to unbounded VARCHAR."""
    for table, column, _ in _LIMITS:
        op.alter_column(
            table, column,
            existing_type=sa.String(),
            type_=sa.String(),
            existing_nullable=False,
        )
