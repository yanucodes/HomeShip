"""add timezone to ships

Revision ID: 05b5f3ad2caf
Revises: 26471b9f5cce
Create Date: 2026-06-14 23:54:10.059553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05b5f3ad2caf'
down_revision: Union[str, Sequence[str], None] = '26471b9f5cce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the ships.timezone column."""
    op.add_column('ships', sa.Column('timezone', sa.String(length=64),
                                     nullable=True))
    op.execute(
        "UPDATE ships SET timezone = 'UTC'"
    )
    op.alter_column(
        'ships', 'timezone',
        nullable=False,
    )


def downgrade() -> None:
    """Drop the ships.timezone column."""
    op.drop_column('ships', 'timezone')
