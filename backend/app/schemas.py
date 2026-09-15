import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ContactSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contact_code: str
    first_name: str | None
    last_name: str | None
    email: str | None
    phone: str | None


class CompanySearchResult(BaseModel):
    id: int
    company_code: str
    company_name: str
    region: str | None
    sales_rep: str | None
    matched_contact: ContactSummary | None = None


class CompanySearchListResult(BaseModel):
    items: list[CompanySearchResult]
    total: int


class FairEditionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fair_edition_code: str
    fair_name: str
    city: str | None
    venue: str | None
    starts_on: datetime.date | None
    ends_on: datetime.date | None
    max_stand_height_m: Decimal | None


class OpportunitySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    opportunity_code: str
    description: str | None
    status: str | None
    amount_eur: Decimal | None
    opened_on: datetime.date | None
    expected_close_on: datetime.date | None
    stand_area_sqm: Decimal | None
    client_budget_eur: Decimal | None
    requested_height_m: Decimal | None
    brief_notes: str | None
    contact_id: int | None
    fair_edition: FairEditionSummary


class OpportunityUpdate(BaseModel):
    """Editable opportunity fields — the legacy commercial/technical-adjacent columns
    only; no field is required outside that vocabulary."""

    status: str | None = None
    amount_eur: Decimal | None = None
    opened_on: datetime.date | None = None
    expected_close_on: datetime.date | None = None
    stand_area_sqm: Decimal | None = None
    client_budget_eur: Decimal | None = None
    requested_height_m: Decimal | None = None
    brief_notes: str | None = None


ActivityType = Literal["call", "email", "meeting", "note", "task"]


class ActivityCreate(BaseModel):
    activity_type: ActivityType
    details: str | None = None
    follow_up_on: datetime.date | None = None


class CompanyDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_code: str
    company_name: str
    province_code: str | None
    region: str | None
    sales_rep: str | None
    contacts: list[ContactSummary]
    opportunities: list[OpportunitySummary]


class ActivityEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entry_id: str
    opportunity_id: int | None
    activity_type: str
    occurred_at: datetime.datetime | None
    details: str | None
    follow_up_on: datetime.date | None
    completion_marker: bool | None
    legacy_author: str | None


class FollowUpItem(BaseModel):
    id: int
    follow_up_on: datetime.date
    activity_type: str
    details: str | None
    occurred_at: datetime.datetime | None
    legacy_author: str | None
    company_id: int
    company_name: str
    sales_rep: str | None
    opportunity_id: int | None
    opportunity_code: str | None


class FollowUpListResult(BaseModel):
    items: list[FollowUpItem]
    has_more: bool
    total: int


class HandoffRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    opportunity_id: int
    created_at: datetime.datetime
    brief: dict[str, object]
    preparer_output: dict[str, object]
    checker_output: dict[str, object]
    verdict: Literal["continue", "stop"]
    heads_up: bool
    reason: str
    simulated: bool
