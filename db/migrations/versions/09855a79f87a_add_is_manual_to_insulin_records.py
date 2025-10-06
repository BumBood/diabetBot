"""add_is_manual_to_insulin_records

Revision ID: 09855a79f87a
Revises: b6339f363f82
Create Date: 2025-10-06 22:25:42.011196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09855a79f87a'
down_revision: Union[str, None] = 'b6339f363f82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('insulin_records', sa.Column('is_manual', sa.Integer(), nullable=False, server_default='0'))

def downgrade():
    op.drop_column('insulin_records', 'is_manual')
