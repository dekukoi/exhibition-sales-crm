import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Company(Base):
    __tablename__ = "company"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    province_code: Mapped[str | None] = mapped_column(String(2))
    region: Mapped[str | None] = mapped_column(String(100))
    sales_rep: Mapped[str | None] = mapped_column(String(100))

    contacts: Mapped[list["Contact"]] = relationship(back_populates="company")
    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="company")
    activity_log_entries: Mapped[list["ActivityLogEntry"]] = relationship(back_populates="company")


class Contact(Base):
    __tablename__ = "contact"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), index=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    fax: Mapped[str | None] = mapped_column(String(50))

    company: Mapped["Company"] = relationship(back_populates="contacts")
    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="contact")


class FairEdition(Base):
    __tablename__ = "fair_edition"

    id: Mapped[int] = mapped_column(primary_key=True)
    fair_edition_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    fair_name: Mapped[str] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    venue: Mapped[str | None] = mapped_column(String(255))
    starts_on: Mapped[datetime.date | None] = mapped_column(Date)
    ends_on: Mapped[datetime.date | None] = mapped_column(Date)
    max_stand_height_m: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))

    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="fair_edition")


class Opportunity(Base):
    __tablename__ = "opportunity"
    __table_args__ = (Index("ix_opportunity_status_opened_on", "status", "opened_on"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contact.id"), index=True)
    fair_edition_id: Mapped[int] = mapped_column(ForeignKey("fair_edition.id"), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    amount_eur: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    status: Mapped[str | None] = mapped_column(String(50), index=True)
    opened_on: Mapped[datetime.date | None] = mapped_column(Date)
    expected_close_on: Mapped[datetime.date | None] = mapped_column(Date)
    historical_campaign_code: Mapped[str | None] = mapped_column(String(50))
    stand_area_sqm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    client_budget_eur: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    requested_height_m: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    brief_notes: Mapped[str | None] = mapped_column(Text)

    company: Mapped["Company"] = relationship(back_populates="opportunities")
    contact: Mapped["Contact | None"] = relationship(back_populates="opportunities")
    fair_edition: Mapped["FairEdition"] = relationship(back_populates="opportunities")
    activity_log_entries: Mapped[list["ActivityLogEntry"]] = relationship(
        back_populates="opportunity"
    )
    handoff_runs: Mapped[list["HandoffRun"]] = relationship(back_populates="opportunity")


class ActivityLogEntry(Base):
    __tablename__ = "activity_log_entry"
    __table_args__ = (
        Index("ix_activity_log_follow_up_completion", "follow_up_on", "completion_marker"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), index=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunity.id"), index=True)
    activity_type: Mapped[str] = mapped_column(String(20))
    occurred_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    details: Mapped[str | None] = mapped_column(Text)
    follow_up_on: Mapped[datetime.date | None] = mapped_column(Date)
    completion_marker: Mapped[bool | None] = mapped_column()
    legacy_author: Mapped[str | None] = mapped_column(String(100))

    company: Mapped["Company"] = relationship(back_populates="activity_log_entries")
    opportunity: Mapped["Opportunity | None"] = relationship(back_populates="activity_log_entries")


class HandoffRun(Base):
    """One run of the handoff assistant against an opportunity — append-only: editing
    the opportunity's brief and re-running creates a new row rather than overwriting
    the previous one, so the full history stays reviewable (see app/handoff/service.py).
    """

    __tablename__ = "handoff_run"
    __table_args__ = (Index("ix_handoff_run_opportunity_created", "opportunity_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunity.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    brief: Mapped[dict[str, Any]] = mapped_column(JSONB)
    preparer_output: Mapped[dict[str, Any]] = mapped_column(JSONB)
    checker_output: Mapped[dict[str, Any]] = mapped_column(JSONB)
    verdict: Mapped[str] = mapped_column(String(20))
    heads_up: Mapped[bool] = mapped_column()
    reason: Mapped[str] = mapped_column(Text)
    simulated: Mapped[bool] = mapped_column()

    opportunity: Mapped["Opportunity"] = relationship(back_populates="handoff_runs")
