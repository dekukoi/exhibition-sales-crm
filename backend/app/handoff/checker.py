"""Checker role: validates the brief — and the preparer's proposed next step — against
the project's hybrid staged handoff policy (docs/adr/0004).

The verdict-candidate fields below (`missing_fields`, `edition_limit_known`,
`height_within_limit`, `heads_up_ready`) are derived from the brief alone, same as
before this role received the preparer's proposal: the checker reaches its conclusion
independently of what was proposed, then records which proposal that conclusion applies
to via `validated_proposal`, so a saved run shows the chain of custody between roles.

- "Heads-up" is available as soon as the client-stated budget is known (the fair
  edition is always known by this point, since `Opportunity.fair_edition_id` is
  required).
- A "continue" verdict needs stand area and requested height both present, with the
  height checked against the fair edition's `max_stand_height_m`.
"""

from decimal import Decimal

from app.handoff.types import CheckerOutput, HandoffBrief


def check(brief: HandoffBrief, proposed_next_step: str) -> CheckerOutput:
    missing: list[str] = []
    if brief.stand_area_sqm is None:
        missing.append("stand area")
    if brief.requested_height_m is None:
        missing.append("requested height")

    edition_limit_known = brief.max_stand_height_m is not None
    height_within_limit: bool | None = None
    if brief.requested_height_m is not None and edition_limit_known:
        height_within_limit = _within_limit(brief.requested_height_m, brief.max_stand_height_m)

    heads_up_ready = brief.client_budget_eur is not None

    notes = _notes_for(brief, missing, edition_limit_known, height_within_limit)

    return CheckerOutput(
        simulated=True,
        heads_up_ready=heads_up_ready,
        missing_fields=missing,
        edition_limit_known=edition_limit_known,
        height_within_limit=height_within_limit,
        notes=notes,
        validated_proposal=proposed_next_step,
    )


def _within_limit(requested_height_m: Decimal, max_stand_height_m: Decimal | None) -> bool:
    assert max_stand_height_m is not None
    return requested_height_m <= max_stand_height_m


def height_conflict_message(brief: HandoffBrief) -> str:
    """The height-vs-limit conflict, worded identically wherever it surfaces (here and
    in the coordinator's stop reason) so the two roles never describe the same fact
    differently."""
    return (
        f"Requested height {brief.requested_height_m}m exceeds {brief.fair_name}'s "
        f"{brief.max_stand_height_m}m limit."
    )


def _notes_for(
    brief: HandoffBrief,
    missing: list[str],
    edition_limit_known: bool,
    height_within_limit: bool | None,
) -> str:
    if missing:
        return f"Missing {' and '.join(missing)}."
    if not edition_limit_known:
        return (
            f"{brief.fair_name}'s maximum stand height isn't recorded; "
            "can't check the requested height."
        )
    if height_within_limit is False:
        return height_conflict_message(brief)
    return "Stand area and requested height are known and within the fair edition's limit."
