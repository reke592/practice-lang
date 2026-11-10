"""users

Revision ID: afb93ea0f562
Revises: 58df1fee1b77
Create Date: 2026-11-07 06:25:18.916126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afb93ea0f562'
down_revision: Union[str, Sequence[str], None] = '58df1fee1b77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sa.text(
        """
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_verified BOOLEAN NOT NULL DEFAULT FALSE,
            is_admin BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        );
        """
    ))


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("DROP TABLE IF EXISTS users;"))
