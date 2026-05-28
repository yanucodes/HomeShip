"""Drop in_stock from supplies

Revision ID: b000c0124de1
Revises: 9a1c9e4ca38e
Create Date: 2026-05-28 13:25:17.498414

NOTE: the downgrade is lossy. The RUNNING_LOW state cannot be faithfully
represented as a boolean and collapses to FALSE.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b000c0124de1'
down_revision: Union[str, Sequence[str], None] = '9a1c9e4ca38e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('supplies', 'in_stock')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('supplies', sa.Column('in_stock', sa.BOOLEAN(),
                                        autoincrement=False, nullable=True))
    op.execute(
        "UPDATE supplies SET in_stock = TRUE WHERE stock_state = 'in_stock'"
    )
    op.execute(
        "UPDATE supplies SET in_stock = FALSE WHERE stock_state != 'in_stock'"
    )
    op.alter_column('supplies', 'in_stock', nullable=False)