"""Add action_type to attendance

Revision ID: c1b306313fae
Revises: e92387af1801
Create Date: 2026-06-04 21:04:44.351663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1b306313fae'
down_revision: Union[str, Sequence[str], None] = 'e92387af1801'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('attendances', sa.Column('action_type', sa.String(length=50), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('attendances', 'action_type')
    # ### end Alembic commands ###
