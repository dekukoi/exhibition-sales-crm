import json
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.importer import (
    ROME_TZ,
    ImportSummary,
    import_archive,
    normalize_status,
    parse_completion_marker,
    parse_date,
    parse_datetime_rome,
    parse_decimal,
)
from app.models import ActivityLogEntry, Company, Contact, FairEdition, Opportunity

from .conftest import FIXTURES_DIR, REPO_DATA_DIR

# --- interpretation-rule unit tests -----------------------------------------


def test_parse_decimal_empty_is_none():
    assert parse_decimal("") is None
    assert parse_decimal(None) is None


def test_parse_decimal_handles_decimal_comma():
    assert parse_decimal("12500,00") == Decimal("12500.00")


def test_parse_date_empty_is_none():
    assert parse_date("") is None


def test_parse_date_parses_ddmmyyyy():
    assert parse_date("01/09/2026") == date(2026, 9, 1)


def test_parse_datetime_rome_interprets_source_as_europe_rome():
    parsed = parse_datetime_rome("01/02/2026 10:30")
    assert parsed is not None
    assert parsed.astimezone(ROME_TZ) == datetime(2026, 2, 1, 10, 30, tzinfo=ROME_TZ)


def test_parse_datetime_rome_empty_is_none():
    assert parse_datetime_rome("") is None


def test_normalize_status_trims_and_lowercases():
    assert normalize_status(" Open ") == "open"
    assert normalize_status("open") == "open"


def test_normalize_status_empty_is_none():
    assert normalize_status("") is None


def test_parse_completion_marker():
    assert parse_completion_marker("Y") is True
    assert parse_completion_marker("N") is False
    assert parse_completion_marker("") is None


# --- end-to-end importer tests against fixture CSVs -------------------------


def test_import_archive_deduplicates_company_across_contact_rows(db_session):
    import_archive(db_session, FIXTURES_DIR)

    companies = db_session.scalars(select(Company)).all()
    assert len(companies) == 2
    acme = db_session.scalar(select(Company).where(Company.company_code == "C001"))
    assert acme.company_name == "Acme Stands Srl"

    contacts = db_session.scalars(select(Contact).where(Contact.company_id == acme.id)).all()
    assert {c.contact_code for c in contacts} == {"CT001", "CT002"}


def test_import_archive_drops_legacy_print_layout(db_session):
    import_archive(db_session, FIXTURES_DIR)

    contact = db_session.scalar(select(Contact).where(Contact.contact_code == "CT001"))
    assert not hasattr(contact, "legacy_print_layout")


def test_import_archive_treats_empty_fields_as_none(db_session):
    import_archive(db_session, FIXTURES_DIR)

    opp2 = db_session.scalar(select(Opportunity).where(Opportunity.opportunity_code == "OPP002"))
    assert opp2.amount_eur is None
    assert opp2.stand_area_sqm is None
    assert opp2.contact_id is None


def test_import_archive_normalizes_status_casing(db_session):
    import_archive(db_session, FIXTURES_DIR)

    opp1 = db_session.scalar(select(Opportunity).where(Opportunity.opportunity_code == "OPP001"))
    opp2 = db_session.scalar(select(Opportunity).where(Opportunity.opportunity_code == "OPP002"))
    assert opp1.status == "open"
    assert opp2.status == "open"


def test_import_archive_keeps_out_of_range_height_unclamped(db_session):
    import_archive(db_session, FIXTURES_DIR)

    fe1 = db_session.scalar(select(FairEdition).where(FairEdition.fair_edition_code == "FE001"))
    opp1 = db_session.scalar(select(Opportunity).where(Opportunity.opportunity_code == "OPP001"))
    assert opp1.requested_height_m > fe1.max_stand_height_m


def test_import_archive_links_activity_to_opportunity_when_present(db_session):
    import_archive(db_session, FIXTURES_DIR)

    entry = db_session.scalar(select(ActivityLogEntry).where(ActivityLogEntry.entry_id == "A001"))
    opp1 = db_session.scalar(select(Opportunity).where(Opportunity.opportunity_code == "OPP001"))
    assert entry.opportunity_id == opp1.id
    assert entry.completion_marker is False


def test_import_archive_allows_company_only_activity(db_session):
    import_archive(db_session, FIXTURES_DIR)

    entry = db_session.scalar(select(ActivityLogEntry).where(ActivityLogEntry.entry_id == "A002"))
    assert entry.opportunity_id is None
    assert entry.completion_marker is None


def test_import_archive_is_idempotent(db_session):
    first = import_archive(db_session, FIXTURES_DIR)
    second = import_archive(db_session, FIXTURES_DIR)

    assert first.companies == second.companies == 2
    assert first.contacts == second.contacts == 3
    assert first.opportunities == second.opportunities == 2
    assert first.activity_log_entries == second.activity_log_entries == 4

    assert db_session.scalar(select(Company)).id is not None
    all_companies = db_session.scalars(select(Company)).all()
    assert len(all_companies) == 2


# --- full-archive smoke test -------------------------------------------------


@pytest.mark.skipif(
    not (REPO_DATA_DIR / "manifest.json").exists(),
    reason="repo data/ directory not available in this environment",
)
def test_import_archive_matches_manifest_counts(db_session):
    manifest = json.loads((REPO_DATA_DIR / "manifest.json").read_text())
    entities = manifest["entities"]

    summary: ImportSummary = import_archive(db_session, REPO_DATA_DIR)

    assert summary.companies == entities["companies"]
    assert summary.contacts == entities["contacts"]
    assert summary.opportunities == entities["opportunities"]
    assert summary.activity_log_entries == entities["activity_log_entries"]
    assert db_session.scalar(select(FairEdition).limit(1)) is not None

    second: ImportSummary = import_archive(db_session, REPO_DATA_DIR)
    assert second.companies == summary.companies
    assert second.contacts == summary.contacts
    assert second.opportunities == summary.opportunities
    assert second.activity_log_entries == summary.activity_log_entries
