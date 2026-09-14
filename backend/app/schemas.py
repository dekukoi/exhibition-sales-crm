import datetime
from decimal import Decimal

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
