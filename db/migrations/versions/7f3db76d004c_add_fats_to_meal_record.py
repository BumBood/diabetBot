"""add fats to meal_record

Revision ID: 7f3db76d004c
Revises: 62a2fa6e0e3f
Create Date: 2025-09-30 18:21:53.309198

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f3db76d004c'
down_revision: Union[str, None] = '62a2fa6e0e3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
