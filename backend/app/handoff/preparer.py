"""Preparer role: gathers the CRM/fair-edition snapshot and drafts a proposed next step.

The "model response" is a deterministic, rule-based stand-in (ADR-0004) — never a real
model call — and is labeled `simulated=True` on its output so nothing mistakes it for
one.
"""

from app.handoff.types import HandoffBrief, PreparerOutput

_MISSING_FIELD_LABELS = (
    ("stand area", "stand_area_sqm"),
    ("requested height", "requested_height_m"),
)


def prepare(brief: HandoffBrief) -> PreparerOutput:
    missing = [label for label, attr in _MISSING_FIELD_LABELS if getattr(brief, attr) is None]

    if missing:
        step = (
            f"Follow up with the client for {' and '.join(missing)} before drafting "
            f"the technical brief for {brief.fair_name}."
        )
    else:
        budget = (
            f"€{brief.client_budget_eur}"
            if brief.client_budget_eur is not None
            else "not yet known"
        )
        step = (
            f"Draft the technical brief for {brief.fair_name}: stand area "
            f"{brief.stand_area_sqm}m², requested height {brief.requested_height_m}m, "
            f"client budget {budget}."
        )

    return PreparerOutput(simulated=True, proposed_next_step=step)
