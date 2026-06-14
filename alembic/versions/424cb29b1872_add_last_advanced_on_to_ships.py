"""add last_advanced_on to ships

Revision ID: 424cb29b1872
Revises: 05b5f3ad2caf
Create Date: 2026-06-15 00:13:32.472139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '424cb29b1872'
down_revision: Union[str, Sequence[str], None] = '05b5f3ad2caf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('ships', sa.Column('last_advanced_on', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ships', 'last_advanced_on')
