"""CRM read logic: exhibitor/contact search and company/opportunity detail views.

Company/contact name search relies on the pg_trgm GIN indexes created in the initial
migration so ILIKE '%...%' stays index-backed at 100k-row scale (see docs/adr/0002).
"""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import ActivityLogEntry, Company, Contact, Opportunity


def search_companies(
    session: Session, q: str, limit: int = 20
) -> list[tuple[Company, Contact | None]]:
    q = q.strip()
    if not q:
        return []
    pattern = f"%{q}%"
    prefix = f"{q}%"

    name_or_code_matches = session.scalars(
        select(Company)
        .where(or_(Company.company_name.ilike(pattern), Company.company_code.ilike(prefix)))
        .order_by(Company.company_name)
        .limit(limit)
    ).all()

    full_name = func.coalesce(Contact.first_name, "") + " " + func.coalesce(Contact.last_name, "")
    contact_matches = session.execute(
        select(Contact, Company)
        .join(Company, Contact.company_id == Company.id)
        .where(or_(Contact.contact_code.ilike(prefix), full_name.ilike(pattern)))
        .order_by(Company.company_name)
        .limit(limit)
    ).all()

    results: dict[int, tuple[Company, Contact | None]] = {
        company.id: (company, None) for company in name_or_code_matches
    }
    for contact, company in contact_matches:
        if company.id not in results:
            results[company.id] = (company, contact)

    return list(results.values())[:limit]


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
