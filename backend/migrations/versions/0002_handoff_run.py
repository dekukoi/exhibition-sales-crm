"""handoff_run table

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "handoff_run",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunity.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("brief", postgresql.JSONB(), nullable=False),
        sa.Column("preparer_output", postgresql.JSONB(), nullable=False),
        sa.Column("checker_output", postgresql.JSONB(), nullable=False),
        sa.Column("verdict", sa.String(length=20), nullable=False),
        sa.Column("heads_up", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("simulated", sa.Boolean(), nullable=False),
    )
    op.create_index(
        "ix_handoff_run_opportunity_created", "handoff_run", ["opportunity_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_table("handoff_run")
