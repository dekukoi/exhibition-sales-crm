"""The DB-touching entrypoint: loads an opportunity, runs the handoff pipeline, and
persists the result as an append-only `HandoffRun` row.

This is the seam the API calls; `app/handoff/pipeline.py` is the seam the unit tests
call. Keeping the split means the preparer/checker/coordinator logic never needs a
database to be exercised (see docs/adr/0004 and tests/test_handoff.py).
"""

import dataclasses
import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.handoff.pipeline import run_handoff_pipeline
from app.handoff.types import HandoffBrief
from app.importer import ROME_TZ
from app.models import HandoffRun, Opportunity


def _build_brief(opportunity: Opportunity) -> HandoffBrief:
    fair_edition = opportunity.fair_edition
    return HandoffBrief(
        opportunity_id=opportunity.id,
        opportunity_code=opportunity.opportunity_code,
        fair_name=fair_edition.fair_name,
        fair_edition_code=fair_edition.fair_edition_code,
        max_stand_height_m=fair_edition.max_stand_height_m,
        client_budget_eur=opportunity.client_budget_eur,
        stand_area_sqm=opportunity.stand_area_sqm,
        requested_height_m=opportunity.requested_height_m,
        description=opportunity.description,
        brief_notes=opportunity.brief_notes,
    )


def _json_safe(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        value = dataclasses.asdict(value)
    if isinstance(value, dict):
        return {key: _json_safe(v) for key, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, Decimal):
        return str(value)
    return value


def _get_opportunity(session: Session, opportunity_id: int) -> Opportunity | None:
    return session.scalar(
        select(Opportunity)
        .where(Opportunity.id == opportunity_id)
        .options(selectinload(Opportunity.fair_edition))
    )


def run_handoff(session: Session, opportunity_id: int) -> HandoffRun | None:
    opportunity = _get_opportunity(session, opportunity_id)
    if opportunity is None:
        return None

    outcome = run_handoff_pipeline(_build_brief(opportunity))

    run = HandoffRun(
        opportunity_id=opportunity_id,
        created_at=datetime.datetime.now(ROME_TZ),
        brief=_json_safe(outcome.brief),
        preparer_output=_json_safe(outcome.preparer),
        checker_output=_json_safe(outcome.checker),
        verdict=outcome.coordinator.verdict,
        heads_up=outcome.coordinator.heads_up,
        reason=outcome.coordinator.reason,
        simulated=outcome.coordinator.simulated,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def list_handoff_runs(session: Session, opportunity_id: int) -> list[HandoffRun]:
    return list(
        session.scalars(
            select(HandoffRun)
            .where(HandoffRun.opportunity_id == opportunity_id)
            .order_by(HandoffRun.created_at.desc())
        ).all()
    )
