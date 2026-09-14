"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "company",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_code", sa.String(length=50), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("province_code", sa.String(length=2), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("sales_rep", sa.String(length=100), nullable=True),
        sa.UniqueConstraint("company_code", name="uq_company_company_code"),
    )
    op.create_index("ix_company_company_code", "company", ["company_code"])
    op.execute("CREATE INDEX ix_company_name_trgm ON company USING gin (company_name gin_trgm_ops)")

    op.create_table(
        "fair_edition",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fair_edition_code", sa.String(length=50), nullable=False),
        sa.Column("fair_name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("venue", sa.String(length=255), nullable=True),
        sa.Column("starts_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("max_stand_height_m", sa.Numeric(6, 2), nullable=True),
        sa.UniqueConstraint("fair_edition_code", name="uq_fair_edition_fair_edition_code"),
    )
    op.create_index("ix_fair_edition_fair_edition_code", "fair_edition", ["fair_edition_code"])

    op.create_table(
        "contact",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contact_code", sa.String(length=50), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("company.id"), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("fax", sa.String(length=50), nullable=True),
        sa.UniqueConstraint("contact_code", name="uq_contact_contact_code"),
    )
    op.create_index("ix_contact_contact_code", "contact", ["contact_code"])
    op.create_index("ix_contact_company_id", "contact", ["company_id"])
    op.execute(
        "CREATE INDEX ix_contact_full_name_trgm ON contact "
        "USING gin ((coalesce(first_name, '') || ' ' || coalesce(last_name, '')) gin_trgm_ops)"
    )

    op.create_table(
        "opportunity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_code", sa.String(length=50), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("company.id"), nullable=False),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contact.id"), nullable=True),
        sa.Column(
            "fair_edition_id", sa.Integer(), sa.ForeignKey("fair_edition.id"), nullable=False
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("amount_eur", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("opened_on", sa.Date(), nullable=True),
        sa.Column("expected_close_on", sa.Date(), nullable=True),
        sa.Column("historical_campaign_code", sa.String(length=50), nullable=True),
        sa.Column("stand_area_sqm", sa.Numeric(8, 2), nullable=True),
        sa.Column("client_budget_eur", sa.Numeric(12, 2), nullable=True),
        sa.Column("requested_height_m", sa.Numeric(6, 2), nullable=True),
        sa.Column("brief_notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("opportunity_code", name="uq_opportunity_opportunity_code"),
    )
    op.create_index("ix_opportunity_opportunity_code", "opportunity", ["opportunity_code"])
    op.create_index("ix_opportunity_company_id", "opportunity", ["company_id"])
    op.create_index("ix_opportunity_contact_id", "opportunity", ["contact_id"])
    op.create_index("ix_opportunity_fair_edition_id", "opportunity", ["fair_edition_id"])
    op.create_index("ix_opportunity_status", "opportunity", ["status"])
    op.create_index("ix_opportunity_status_opened_on", "opportunity", ["status", "opened_on"])

    op.create_table(
        "activity_log_entry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entry_id", sa.String(length=50), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("company.id"), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunity.id"), nullable=True),
        sa.Column("activity_type", sa.String(length=20), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("follow_up_on", sa.Date(), nullable=True),
        sa.Column("completion_marker", sa.Boolean(), nullable=True),
        sa.Column("legacy_author", sa.String(length=100), nullable=True),
        sa.UniqueConstraint("entry_id", name="uq_activity_log_entry_entry_id"),
    )
    op.create_index("ix_activity_log_entry_entry_id", "activity_log_entry", ["entry_id"])
    op.create_index("ix_activity_log_entry_company_id", "activity_log_entry", ["company_id"])
    op.create_index(
        "ix_activity_log_entry_opportunity_id", "activity_log_entry", ["opportunity_id"]
    )
    op.create_index(
        "ix_activity_log_follow_up_completion",
        "activity_log_entry",
        ["follow_up_on", "completion_marker"],
    )


def downgrade() -> None:
    op.drop_table("activity_log_entry")
    op.drop_table("opportunity")
    op.execute("DROP INDEX IF EXISTS ix_contact_full_name_trgm")
    op.drop_table("contact")
    op.drop_table("fair_edition")
    op.execute("DROP INDEX IF EXISTS ix_company_name_trgm")
    op.drop_table("company")
