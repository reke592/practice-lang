"""document embeddings

Revision ID: 38ba3f4e2657
Revises: afb93ea0f562
Create Date: 2026-11-07 06:25:21.073613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38ba3f4e2657'
down_revision: Union[str, Sequence[str], None] = 'afb93ea0f562'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    """Upgrade schema."""
    # metadata
    op.execute(sa.text(
    """
    CREATE TABLE IF NOT EXISTS documents(
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        file_path TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,

        created_by_id INTEGER NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS document_embeddings(
        id SERIAL PRIMARY KEY,
        document_id INTEGER NOT NULL,
        embedding vector(768) NOT NULL,
        metadata JSONB,
        content TEXT,

        created_by_id INTEGER NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        
        -- foreign key constraint
        CONSTRAINT fk_document
            FOREIGN KEY(document_id)
            REFERENCES documents(id)
            ON DELETE CASCADE
    );

    CREATE INDEX documents_created_by_ix ON documents(created_by_id, is_active);
    CREATE INDEX document_embeddings_ix ON document_embeddings(document_id);
    CREATE INDEX document_embeddings_created_by_ix ON document_embeddings(created_by_id);
    CREATE INDEX document_embeddings_embedding_ix ON document_embeddings USING hnsw (embedding vector_cosine_ops);
    """
    ))


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text(
    """
    DROP TABLE IF EXISTS document_embeddings;
    DROP TABLE IF EXISTS documents;
    """
    ))
