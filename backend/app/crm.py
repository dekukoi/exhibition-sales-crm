"""CRM read logic: exhibitor/contact search and company/opportunity detail views.

Company/contact name search relies on the pg_trgm GIN indexes created in the initial
migration so ILIKE '%...%' stays index-backed at 100k-row scale (see docs/adr/0002).
Each matchable column gets its own UNION ALL branch rather than combining columns with
OR in one WHERE: Postgres won't use an index for one side of an OR predicate when the
other side isn't indexable (company_code/contact_code ILIKE can't use their plain btree
indexes, since ILIKE is case-insensitive) — confirmed via EXPLAIN ANALYZE, an OR'd
`company_name ILIKE ... OR company_code ILIKE ...` forces a full sequential scan even
though company_name alone is index-backed. Separate branches let each column use
whatever index actually applies to it, independent of the others.

A company that matches by its own name/code always wins over one that only matches via
a contact (so the result never highlights a contact match when the company itself named
the hit) — deduped per company with `DISTINCT ON` over the unioned branches, so
LIMIT/OFFSET/COUNT stay correct instead of merging independently-limited Python lists
(which can't paginate past page one without silently losing or duplicating rows).
"""

from sqlalchemy import Integer, cast, func, null, select
from sqlalchemy.orm import Session, selectinload

from app.models import ActivityLogEntry, Company, Contact, Opportunity


def search_companies(
    session: Session, q: str, limit: int = 15, offset: int = 0
) -> tuple[list[tuple[Company, Contact | None]], int]:
    """Returns (this page of (company, matched_contact) results, total distinct matches)."""
    q = q.strip()
    if not q:
        return [], 0
    pattern = f"%{q}%"
    prefix = f"{q}%"

    full_name = func.coalesce(Contact.first_name, "") + " " + func.coalesce(Contact.last_name, "")
    no_contact = cast(null(), Integer).label("contact_id")

    by_company_name = select(Company.id.label("company_id"), no_contact).where(
        Company.company_name.ilike(pattern)
    )
    by_company_code = select(Company.id.label("company_id"), no_contact).where(
        Company.company_code.ilike(prefix)
    )
    by_contact_code = select(
        Contact.company_id.label("company_id"), Contact.id.label("contact_id")
    ).where(Contact.contact_code.ilike(prefix))
    by_contact_name = select(
        Contact.company_id.label("company_id"), Contact.id.label("contact_id")
    ).where(full_name.ilike(pattern))

    matches = by_company_name.union_all(by_company_code, by_contact_code, by_contact_name).subquery(
        "matches"
    )

    deduped = (
        select(matches.c.company_id, matches.c.contact_id)
        .distinct(matches.c.company_id)
        .order_by(matches.c.company_id, matches.c.contact_id.nulls_first())
        .subquery("deduped")
    )

    total = session.scalar(select(func.count()).select_from(deduped)) or 0
    if total == 0:
        return [], 0

    page = session.execute(
        select(deduped.c.company_id, deduped.c.contact_id)
        .join(Company, Company.id == deduped.c.company_id)
        .order_by(Company.company_name)
        .limit(limit)
        .offset(offset)
    ).all()
    if not page:
        return [], total

    company_ids = [row.company_id for row in page]
    contact_ids = [row.contact_id for row in page if row.contact_id is not None]

    companies = {
        c.id: c for c in session.scalars(select(Company).where(Company.id.in_(company_ids)))
    }
    contacts = (
        {c.id: c for c in session.scalars(select(Contact).where(Contact.id.in_(contact_ids)))}
        if contact_ids
        else {}
    )

    results = [
        (companies[row.company_id], contacts.get(row.contact_id) if row.contact_id else None)
        for row in page
    ]
    return results, total


def get_company_detail(session: Session, company_id: int) -> Company | None:
    return session.scalar(
        select(Company)
        .where(Company.id == company_id)
        .options(
            selectinload(Company.contacts),
            selectinload(Company.opportunities).selectinload(Opportunity.fair_edition),
        )
    )


def get_opportunity_activity(session: Session, opportunity_id: int) -> list[ActivityLogEntry]:
    return list(
        session.scalars(
            select(ActivityLogEntry)
            .where(ActivityLogEntry.opportunity_id == opportunity_id)
            .order_by(ActivityLogEntry.occurred_at.desc())
        ).all()
    )


def get_company_activity(session: Session, company_id: int) -> list[ActivityLogEntry]:
    return list(
        session.scalars(
            select(ActivityLogEntry)
            .where(ActivityLogEntry.company_id == company_id)
            .order_by(ActivityLogEntry.occurred_at.desc())
        ).all()
    )
