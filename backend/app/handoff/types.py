"""Plain data shapes passed between the handoff-assistant's three roles.

Deliberately not SQLAlchemy models: the preparer/checker/coordinator seam is tested
against hand-constructed fixtures with no database involved (see docs/adr/0004 and
tests/test_handoff.py). `app/handoff/service.py` is the only place that bridges these to
ORM rows and persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Verdict = Literal["continue", "stop"]


@dataclass(frozen=True)
class HandoffBrief:
    """The CRM + fair-edition snapshot a handoff run is evaluated against."""

    opportunity_id: int
    opportunity_code: str
    fair_name: str
    fair_edition_code: str
    max_stand_height_m: Decimal | None
    client_budget_eur: Decimal | None
    stand_area_sqm: Decimal | None
    requested_height_m: Decimal | None
    description: str | None
    brief_notes: str | None


@dataclass(frozen=True)
class PreparerOutput:
    simulated: bool
    proposed_next_step: str


@dataclass(frozen=True)
class CheckerOutput:
    simulated: bool
    heads_up_ready: bool
    missing_fields: list[str]
    edition_limit_known: bool
    height_within_limit: bool | None
    notes: str


@dataclass(frozen=True)
class CoordinatorOutput:
    simulated: bool
    verdict: Verdict
    heads_up: bool
    reason: str


@dataclass(frozen=True)
class HandoffOutcome:
    brief: HandoffBrief
    preparer: PreparerOutput
    checker: CheckerOutput
    coordinator: CoordinatorOutput
