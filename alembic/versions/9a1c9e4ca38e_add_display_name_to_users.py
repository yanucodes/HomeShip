"""Add display_name to users

Revision ID: 9a1c9e4ca38e
Revises: 04eff19a433b
Create Date: 2026-05-27 21:12:31.632483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a1c9e4ca38e'
down_revision: Union[str, Sequence[str], None] = '04eff19a433b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('display_name', sa.String(30),
                                     nullable=True))
    op.execute(
        "UPDATE users SET display_name = INITCAP(username)"
    )
    op.alter_column("users", "display_name", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'display_name')

