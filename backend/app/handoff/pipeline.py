"""The DB-free seam: chains preparer -> checker -> coordinator over one `HandoffBrief`.

This is what `tests/test_handoff.py` calls directly against constructed fixtures. The
DB-touching entrypoint (`app/handoff/service.py:run_handoff`) builds a `HandoffBrief`
from the database and delegates here.
"""

from app.handoff.checker import check
from app.handoff.coordinator import coordinate
from app.handoff.preparer import prepare
from app.handoff.types import HandoffBrief, HandoffOutcome


def run_handoff_pipeline(brief: HandoffBrief) -> HandoffOutcome:
    preparer_output = prepare(brief)
    checker_output = check(brief)
    coordinator_output = coordinate(brief, checker_output)
    return HandoffOutcome(
        brief=brief,
        preparer=preparer_output,
        checker=checker_output,
        coordinator=coordinator_output,
    )
