"""enable vector extension

Revision ID: 58df1fee1b77
Revises: 
Create Date: 2026-11-07 05:13:41.350883

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58df1fee1b77'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector;"))


def downgrade() -> None:
    """Downgrade schema."""
    pass
