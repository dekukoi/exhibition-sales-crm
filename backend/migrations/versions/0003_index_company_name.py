"""index company_name for the unfiltered browse listing

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-15
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_company_company_name", "company", ["company_name"])


def downgrade() -> None:
    op.drop_index("ix_company_company_name", table_name="company")
