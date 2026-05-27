"""Add stock_state and date_due to supplies

Revision ID: 04eff19a433b
Revises: 9a2b9fb1697e
Create Date: 2026-05-27 20:56:04.136810

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04eff19a433b'
down_revision: Union[str, Sequence[str], None] = '9a2b9fb1697e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    stock_state_enum = sa.Enum(
        'in_stock', 'running_low', 'out_of_stock', name='stock_state'
    )
    stock_state_enum.create(op.get_bind())
    op.add_column('supplies', sa.Column('stock_state', stock_state_enum,
                                        nullable=True))
    op.add_column('supplies', sa.Column('date_due', sa.Date(), nullable=True))
    op.execute(
        "UPDATE supplies SET stock_state = 'in_stock' WHERE in_stock = TRUE"
    )
    op.execute(
        "UPDATE supplies SET stock_state = 'out_of_stock' WHERE in_stock = FALSE"
    )
    op.alter_column("supplies", "stock_state", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('supplies', 'date_due')
    op.drop_column('supplies', 'stock_state')
    sa.Enum(name="stock_state").drop(op.get_bind())
