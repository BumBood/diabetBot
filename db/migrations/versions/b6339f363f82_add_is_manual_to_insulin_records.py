"""add_is_manual_to_insulin_records

Revision ID: b6339f363f82
Revises: 64647219cdfc
Create Date: 2025-10-06 22:25:25.990441

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6339f363f82'
down_revision: Union[str, None] = '64647219cdfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
