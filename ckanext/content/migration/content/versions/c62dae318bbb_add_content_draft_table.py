"""Add content draft table

Revision ID: c62dae318bbb
Revises: 2f5c6dac0cc2
Create Date: 2026-02-22 17:18:07.746168

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "c62dae318bbb"
down_revision = "2f5c6dac0cc2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "content_draft",
        sa.Column("id", sa.Text, primary_key=True, unique=True),
        sa.Column("content_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("alias", sa.Text(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column(
            "data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "modified",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column(
            "translations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["content_id"], ["content.id"], ondelete="CASCADE"
        ),
    )


def downgrade():
    op.drop_table("content_draft")
