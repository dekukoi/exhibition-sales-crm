"""Follow-up read/write logic: the pending-task list and its completion action.

A row counts as a pending follow-up when `follow_up_on` is set and `completion_marker`
is not `True`. `completion_marker` empty alongside a set `follow_up_on` (~1,100 rows in
the supplied archive) is treated as pending rather than "not applicable" per
data/README.md: a requested follow-up date is itself evidence the task is outstanding,
and silently dropping it would hide real work from the sales team.

Filters and sort stay on `(follow_up_on, completion_marker)`, the indexed pair from the
initial migration, so the list scan stays index-backed as the archive grows.
"""

from datetime import date
from typing import cast

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import ActivityLogEntry, Company, Opportunity

FollowUpRow = tuple[ActivityLogEntry, Company, Opportunity | None]


def _pending_query() -> Select[FollowUpRow]:
    return cast(
        "Select[FollowUpRow]",
        select(ActivityLogEntry, Company, Opportunity)
        .join(Company, ActivityLogEntry.company_id == Company.id)
        .outerjoin(Opportunity, ActivityLogEntry.opportunity_id == Opportunity.id)
        .where(
            ActivityLogEntry.follow_up_on.is_not(None),
            or_(
                ActivityLogEntry.completion_marker.is_(None),
                ActivityLogEntry.completion_marker.is_(False),
            ),
        ),
    )


def _filtered_query(
    sales_rep: str | None, company: str | None, due_before: date | None
) -> Select[FollowUpRow]:
    stmt = _pending_query()
    if sales_rep:
        stmt = stmt.where(Company.sales_rep == sales_rep)
    if company:
        stmt = stmt.where(Company.company_name.ilike(f"%{company}%"))
    if due_before:
        stmt = stmt.where(ActivityLogEntry.follow_up_on <= due_before)
    return stmt


def list_pending_follow_ups(
    session: Session,
    sales_rep: str | None = None,
    company: str | None = None,
    due_before: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[FollowUpRow]:
    stmt = _filtered_query(sales_rep, company, due_before).order_by(
        ActivityLogEntry.follow_up_on.asc(), ActivityLogEntry.id.asc()
    )
    return list(session.execute(stmt.limit(limit).offset(offset)).tuples())


def count_pending_follow_ups(
    session: Session,
    sales_rep: str | None = None,
    company: str | None = None,
    due_before: date | None = None,
) -> int:
    stmt = select(func.count()).select_from(
        _filtered_query(sales_rep, company, due_before).subquery()
    )
    return session.scalar(stmt) or 0


def list_sales_reps(session: Session) -> list[str]:
    reps = session.scalars(
        select(Company.sales_rep)
        .where(Company.sales_rep.is_not(None))
        .distinct()
        .order_by(Company.sales_rep)
    ).all()
    return [rep for rep in reps if rep is not None]


def mark_follow_up_complete(session: Session, follow_up_id: int) -> FollowUpRow | None:
    entry = session.get(
        ActivityLogEntry,
        follow_up_id,
        options=[
            selectinload(ActivityLogEntry.company),
            selectinload(ActivityLogEntry.opportunity),
        ],
    )
    if entry is None:
        return None
    if entry.completion_marker is not True:
        entry.completion_marker = True
        session.commit()
    return entry, entry.company, entry.opportunity
