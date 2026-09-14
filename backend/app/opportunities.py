"""Opportunity write logic: editing an opportunity and logging a conversation against it.

`completion_marker` on a new activity is derived, not asked of the user, mirroring the
meaning already established by the legacy import (data/README.md): a note doesn't carry
a completion state (n/a); otherwise an entry is pending — and so must surface on the
follow-ups screen (app/follow_ups.py's `(follow_up_on, completion_marker)` query) —
whenever it still has outstanding work, i.e. it names a `follow_up_on` date or it's a
task. A call/email/meeting with no follow-up date is a closed-out record of a
conversation that already happened, so it's marked completed.
"""

import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.importer import ROME_TZ, normalize_status
from app.models import ActivityLogEntry, Opportunity
from app.schemas import ActivityCreate, ActivityType, OpportunityUpdate


def _completion_marker(
    activity_type: ActivityType, follow_up_on: datetime.date | None
) -> bool | None:
    if activity_type == "note":
        return None
    if follow_up_on is not None or activity_type == "task":
        return False
    return True


def get_opportunity(session: Session, opportunity_id: int) -> Opportunity | None:
    return session.scalar(
        select(Opportunity)
        .where(Opportunity.id == opportunity_id)
        .options(selectinload(Opportunity.fair_edition))
    )


def list_statuses(session: Session) -> list[str]:
    statuses = session.scalars(
        select(Opportunity.status)
        .where(Opportunity.status.is_not(None))
        .distinct()
        .order_by(Opportunity.status)
    ).all()
    return [status for status in statuses if status is not None]


def update_opportunity(
    session: Session, opportunity_id: int, update: OpportunityUpdate
) -> Opportunity | None:
    opportunity = get_opportunity(session, opportunity_id)
    if opportunity is None:
        return None

    fields = update.model_dump(exclude_unset=True)
    if "status" in fields:
        fields["status"] = normalize_status(fields["status"])
    for field, value in fields.items():
        setattr(opportunity, field, value)

    session.commit()
    session.refresh(opportunity)
    return opportunity


def add_activity(
    session: Session, opportunity_id: int, activity: ActivityCreate
) -> ActivityLogEntry | None:
    opportunity = get_opportunity(session, opportunity_id)
    if opportunity is None:
        return None

    entry = ActivityLogEntry(
        entry_id=f"crm-{uuid4().hex}",
        company_id=opportunity.company_id,
        opportunity_id=opportunity.id,
        activity_type=activity.activity_type,
        occurred_at=datetime.datetime.now(ROME_TZ),
        details=activity.details,
        follow_up_on=activity.follow_up_on,
        completion_marker=_completion_marker(activity.activity_type, activity.follow_up_on),
        legacy_author=None,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry
