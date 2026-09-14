"""Coordinator role: turns the checker's verdict-candidate into continue/stop plus the
specific reason (docs/adr/0004) — a missing field, the height-vs-limit conflict, or
confirmation everything required is known and within limit.
"""

from app.handoff.checker import height_conflict_message
from app.handoff.types import CheckerOutput, CoordinatorOutput, HandoffBrief


def coordinate(brief: HandoffBrief, checker_output: CheckerOutput) -> CoordinatorOutput:
    heads_up = checker_output.heads_up_ready

    if checker_output.missing_fields:
        reason = (
            f"Missing {' and '.join(checker_output.missing_fields)} before this can go "
            "to technical."
        )
        if heads_up:
            reason += f" Heads-up: {brief.fair_name} and the client's budget are already known."
        return CoordinatorOutput(simulated=True, verdict="stop", heads_up=heads_up, reason=reason)

    if not checker_output.edition_limit_known:
        reason = (
            f"{brief.fair_name}'s maximum stand height isn't recorded, so the requested "
            "height can't be checked against it."
        )
        return CoordinatorOutput(simulated=True, verdict="stop", heads_up=heads_up, reason=reason)

    if checker_output.height_within_limit is False:
        return CoordinatorOutput(
            simulated=True, verdict="stop", heads_up=heads_up, reason=height_conflict_message(brief)
        )

    reason = (
        f"Stand area ({brief.stand_area_sqm}m²) and requested height "
        f"({brief.requested_height_m}m) are known and within {brief.fair_name}'s "
        f"{brief.max_stand_height_m}m limit."
    )
    return CoordinatorOutput(simulated=True, verdict="continue", heads_up=heads_up, reason=reason)
