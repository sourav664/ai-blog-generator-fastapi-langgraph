"""remove unique filename constraint

Revision ID: a9411f7a9947
Revises: afae9ab5cd20
Create Date: 2026-06-17 18:20:30.980561

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9411f7a9947'
down_revision: Union[str, Sequence[str], None] = 'afae9ab5cd20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
