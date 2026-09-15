"""Idempotent importer for the legacy sales archive (data/*.csv).

Interpretation rules (see data/README.md and docs/adr/0002):
- Empty CSV fields mean unknown -> None, never a zero/false placeholder.
- Monetary/area/height values use a decimal comma, no thousands separator.
- Dates are DD/MM/YYYY; date-times are DD/MM/YYYY HH:mm interpreted as Europe/Rome.
- `legacy_status` is trimmed and lowercased so casing/whitespace variants collapse.
- `legacy_print_layout` is obsolete presentation metadata and is not imported.
- An out-of-range `requested_height_m` is imported unchanged, never clamped/rejected.

Upserts key off each entity's legacy code, so re-running against the same or a
replaced `data/` folder never duplicates rows.
"""

from __future__ import annotations

import csv
import hashlib
import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import ActivityLogEntry, Company, Contact, FairEdition, ImportState, Opportunity

logger = logging.getLogger(__name__)

ROME_TZ = ZoneInfo("Europe/Rome")
_BATCH_SIZE = 2000
_IMPORT_STATE_ID = 1


@dataclass
class ImportSummary:
    companies: int = 0
    contacts: int = 0
    fair_editions: int = 0
    opportunities: int = 0
    activity_log_entries: int = 0
    skipped: list[str] = field(default_factory=list)


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def parse_decimal(value: str | None) -> Decimal | None:
    value = _empty_to_none(value)
    if value is None:
        return None
    try:
        return Decimal(value.replace(",", "."))
    except InvalidOperation:
        return None


def parse_date(value: str | None) -> date | None:
    value = _empty_to_none(value)
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        return None


def parse_datetime_rome(value: str | None) -> datetime | None:
    value = _empty_to_none(value)
    if value is None:
        return None
    try:
        naive = datetime.strptime(value, "%d/%m/%Y %H:%M")
    except ValueError:
        return None
    return naive.replace(tzinfo=ROME_TZ)


def normalize_status(value: str | None) -> str | None:
    value = _empty_to_none(value)
    return value.lower() if value is not None else None


def parse_completion_marker(value: str | None) -> bool | None:
    value = _empty_to_none(value)
    if value is None:
        return None
    return {"Y": True, "N": False}.get(value.upper())


def _read_csv(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f, delimiter=";")


def _chunks(rows: list[dict[str, Any]], size: int = _BATCH_SIZE) -> Iterable[list[dict[str, Any]]]:
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def _upsert(
    session: Session, model: Any, rows: list[dict[str, Any]], conflict_col: str, label: str
) -> None:
    """Insert rows not already present by their legacy code; leave existing rows alone.

    A plain restart must not overwrite values the app itself has since written (an
    edited opportunity, a completed follow-up, ...) back to the original CSV import —
    "later starts must keep user changes" per the assignment. A full re-seed only ever
    happens against an empty database (reset.sh wipes it first), where every row is a
    fresh insert regardless, so DO NOTHING costs nothing there.
    """
    if not rows:
        logger.info("%s: nothing to import", label)
        return
    table = model.__table__
    total = len(rows)
    done = 0
    for batch in _chunks(rows):
        stmt = pg_insert(table).values(batch)
        stmt = stmt.on_conflict_do_nothing(index_elements=[conflict_col])
        session.execute(stmt)
        done += len(batch)
        logger.info("%s: upserted %d/%d rows", label, done, total)


def _code_to_id(session: Session, model: Any, code_col: str) -> dict[str, int]:
    table = model.__table__
    rows = session.execute(select(table.c[code_col], table.c.id)).all()
    return {code: id_ for code, id_ in rows}


def _manifest_fingerprint(data_dir: Path) -> str | None:
    """Sha256 of `data/manifest.json`'s bytes, or None when the archive has no
    manifest. An opaque fingerprint of "which archive this is" — its content is never
    otherwise parsed, so any change to it (a different archive) is enough to trigger
    a re-import.
    """
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def import_archive_if_needed(session: Session, data_dir: Path) -> ImportSummary | None:
    """Run `import_archive` unless the archive is unchanged since the last import.

    This is an optimisation only: `import_archive` stays idempotent on its own
    merits (see `_upsert`), so skipping it here never risks correctness — worst
    case, a missing or unreadable manifest just means every start re-imports.
    Returns None when the import was skipped.
    """
    fingerprint = _manifest_fingerprint(data_dir)
    state = session.get(ImportState, _IMPORT_STATE_ID)
    if fingerprint is not None and state is not None and state.manifest_sha256 == fingerprint:
        logger.info("Archive unchanged (manifest sha256=%s); skipping import", fingerprint[:12])
        return None

    logger.info("Importing archive from %s", data_dir)
    summary = import_archive(session, data_dir)

    if fingerprint is not None:
        session.merge(
            ImportState(
                id=_IMPORT_STATE_ID,
                manifest_sha256=fingerprint,
                imported_at=datetime.now(UTC),
            )
        )
        session.commit()

    return summary


def import_archive(session: Session, data_dir: Path) -> ImportSummary:
    logger.info("Import starting: %s", data_dir)
    summary = ImportSummary()

    _import_fair_editions(session, data_dir, summary)
    _import_companies_and_contacts(session, data_dir, summary)
    fair_edition_ids = _code_to_id(session, FairEdition, "fair_edition_code")
    company_ids = _code_to_id(session, Company, "company_code")
    contact_ids = _code_to_id(session, Contact, "contact_code")
    _import_opportunities(session, data_dir, summary, company_ids, contact_ids, fair_edition_ids)
    opportunity_ids = _code_to_id(session, Opportunity, "opportunity_code")
    _import_activity_log(session, data_dir, summary, company_ids, opportunity_ids)

    session.commit()
    logger.info(
        "Import complete: %d companies, %d contacts, %d fair editions, "
        "%d opportunities, %d activity log entries (%d skipped)",
        summary.companies,
        summary.contacts,
        summary.fair_editions,
        summary.opportunities,
        summary.activity_log_entries,
        len(summary.skipped),
    )
    return summary


def _import_fair_editions(session: Session, data_dir: Path, summary: ImportSummary) -> None:
    rows = []
    for raw in _read_csv(data_dir / "fair_editions.csv"):
        code = _empty_to_none(raw["fair_edition_code"])
        if code is None:
            summary.skipped.append("fair_editions: row missing fair_edition_code")
            continue
        rows.append(
            {
                "fair_edition_code": code,
                "fair_name": raw["fair_name"],
                "city": _empty_to_none(raw.get("city")),
                "venue": _empty_to_none(raw.get("venue")),
                "starts_on": parse_date(raw.get("starts_on")),
                "ends_on": parse_date(raw.get("ends_on")),
                "max_stand_height_m": parse_decimal(raw.get("max_stand_height_m")),
            }
        )
    _upsert(session, FairEdition, rows, "fair_edition_code", "fair_editions")
    summary.fair_editions = len(rows)


def _import_companies_and_contacts(
    session: Session, data_dir: Path, summary: ImportSummary
) -> None:
    companies: dict[str, dict[str, Any]] = {}
    contacts: list[dict[str, Any]] = []
    contact_codes_seen: set[str] = set()

    for raw in _read_csv(data_dir / "companies_and_contacts.csv"):
        company_code = _empty_to_none(raw["company_code"])
        if company_code is None:
            summary.skipped.append(
                f"companies_and_contacts: row {raw.get('legacy_row_id')} missing company_code"
            )
            continue
        companies[company_code] = {
            "company_code": company_code,
            "company_name": raw["company_name"],
            "province_code": _empty_to_none(raw.get("province_code")),
            "region": _empty_to_none(raw.get("region")),
            "sales_rep": _empty_to_none(raw.get("sales_rep")),
        }

        contact_code = _empty_to_none(raw.get("contact_code"))
        if contact_code is None:
            summary.skipped.append(
                f"companies_and_contacts: row {raw.get('legacy_row_id')} missing contact_code"
            )
            continue
        if contact_code in contact_codes_seen:
            continue
        contact_codes_seen.add(contact_code)
        contacts.append(
            {
                "contact_code": contact_code,
                "company_code": company_code,
                "first_name": _empty_to_none(raw.get("contact_first_name")),
                "last_name": _empty_to_none(raw.get("contact_last_name")),
                "email": _empty_to_none(raw.get("email")),
                "phone": _empty_to_none(raw.get("phone")),
                "fax": _empty_to_none(raw.get("fax")),
            }
        )

    _upsert(session, Company, list(companies.values()), "company_code", "companies")
    summary.companies = len(companies)

    company_ids = _code_to_id(session, Company, "company_code")
    contact_rows = [
        {
            "contact_code": c["contact_code"],
            "company_id": company_ids[c["company_code"]],
            "first_name": c["first_name"],
            "last_name": c["last_name"],
            "email": c["email"],
            "phone": c["phone"],
            "fax": c["fax"],
        }
        for c in contacts
        if c["company_code"] in company_ids
    ]
    _upsert(session, Contact, contact_rows, "contact_code", "contacts")
    summary.contacts = len(contact_rows)


def _import_opportunities(
    session: Session,
    data_dir: Path,
    summary: ImportSummary,
    company_ids: dict[str, int],
    contact_ids: dict[str, int],
    fair_edition_ids: dict[str, int],
) -> None:
    rows = []
    for raw in _read_csv(data_dir / "opportunities.csv"):
        code = _empty_to_none(raw["opportunity_code"])
        company_code = _empty_to_none(raw.get("company_code"))
        fair_edition_code = _empty_to_none(raw.get("fair_edition_code"))
        if code is None:
            summary.skipped.append("opportunities: row missing opportunity_code")
            continue
        if company_code not in company_ids:
            summary.skipped.append(f"opportunities: {code} has unresolved company_code")
            continue
        if fair_edition_code not in fair_edition_ids:
            summary.skipped.append(f"opportunities: {code} has unresolved fair_edition_code")
            continue

        contact_code = _empty_to_none(raw.get("contact_code"))
        contact_id = contact_ids.get(contact_code) if contact_code else None

        rows.append(
            {
                "opportunity_code": code,
                "company_id": company_ids[company_code],
                "contact_id": contact_id,
                "fair_edition_id": fair_edition_ids[fair_edition_code],
                "description": _empty_to_none(raw.get("description")),
                "amount_eur": parse_decimal(raw.get("amount_eur")),
                "status": normalize_status(raw.get("legacy_status")),
                "opened_on": parse_date(raw.get("opened_on")),
                "expected_close_on": parse_date(raw.get("expected_close_on")),
                "historical_campaign_code": _empty_to_none(raw.get("historical_campaign_code")),
                "stand_area_sqm": parse_decimal(raw.get("stand_area_sqm")),
                "client_budget_eur": parse_decimal(raw.get("client_budget_eur")),
                "requested_height_m": parse_decimal(raw.get("requested_height_m")),
                "brief_notes": _empty_to_none(raw.get("brief_notes")),
            }
        )
    _upsert(session, Opportunity, rows, "opportunity_code", "opportunities")
    summary.opportunities = len(rows)


def _import_activity_log(
    session: Session,
    data_dir: Path,
    summary: ImportSummary,
    company_ids: dict[str, int],
    opportunity_ids: dict[str, int],
) -> None:
    rows = []
    for raw in _read_csv(data_dir / "activity_log.csv"):
        entry_id = _empty_to_none(raw["entry_id"])
        company_code = _empty_to_none(raw.get("company_code"))
        if entry_id is None:
            summary.skipped.append("activity_log: row missing entry_id")
            continue
        if company_code not in company_ids:
            summary.skipped.append(f"activity_log: {entry_id} has unresolved company_code")
            continue

        opportunity_code = _empty_to_none(raw.get("opportunity_code"))
        opportunity_id = opportunity_ids.get(opportunity_code) if opportunity_code else None

        rows.append(
            {
                "entry_id": entry_id,
                "company_id": company_ids[company_code],
                "opportunity_id": opportunity_id,
                "activity_type": raw["activity_type"],
                "occurred_at": parse_datetime_rome(raw.get("occurred_at")),
                "details": _empty_to_none(raw.get("details")),
                "follow_up_on": parse_date(raw.get("follow_up_on")),
                "completion_marker": parse_completion_marker(raw.get("completion_marker")),
                "legacy_author": _empty_to_none(raw.get("legacy_author")),
            }
        )
    _upsert(session, ActivityLogEntry, rows, "entry_id", "activity_log")
    summary.activity_log_entries = len(rows)
