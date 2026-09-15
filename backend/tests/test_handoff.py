from decimal import Decimal

from app.handoff import HandoffBrief, run_handoff_pipeline


def _complete_brief(**overrides: object) -> HandoffBrief:
    defaults: dict[str, object] = dict(
        opportunity_id=1,
        opportunity_code="OP000001",
        fair_name="Beauty Trade Forum",
        fair_edition_code="BEAUTY-2027",
        max_stand_height_m=Decimal("4.50"),
        client_budget_eur=Decimal("50000.00"),
        stand_area_sqm=Decimal("80.00"),
        requested_height_m=Decimal("4.00"),
        description="Next edition: product launch stand",
        brief_notes="Plot confirmed; artwork supplied.",
    )
    defaults.update(overrides)
    return HandoffBrief(**defaults)  # type: ignore[arg-type]


def test_continue_when_area_and_height_known_and_within_limit():
    outcome = run_handoff_pipeline(_complete_brief())

    assert outcome.coordinator.verdict == "continue"


def test_stop_when_height_missing_names_it_in_the_reason():
    outcome = run_handoff_pipeline(_complete_brief(requested_height_m=None))

    assert outcome.coordinator.verdict == "stop"
    assert "requested height" in outcome.coordinator.reason


def test_stop_when_stand_area_missing_names_it_in_the_reason():
    outcome = run_handoff_pipeline(_complete_brief(stand_area_sqm=None))

    assert outcome.coordinator.verdict == "stop"
    assert "stand area" in outcome.coordinator.reason


def test_stop_when_requested_height_exceeds_edition_limit():
    outcome = run_handoff_pipeline(
        _complete_brief(requested_height_m=Decimal("5.00"), max_stand_height_m=Decimal("4.50"))
    )

    assert outcome.coordinator.verdict == "stop"
    assert "5.00" in outcome.coordinator.reason
    assert "4.50" in outcome.coordinator.reason


def test_heads_up_when_budget_known_even_though_area_and_height_are_missing():
    outcome = run_handoff_pipeline(
        _complete_brief(stand_area_sqm=None, requested_height_m=None, client_budget_eur=Decimal("50000.00"))
    )

    assert outcome.coordinator.verdict == "stop"
    assert outcome.coordinator.heads_up is True


def test_no_heads_up_when_budget_unknown():
    outcome = run_handoff_pipeline(_complete_brief(client_budget_eur=None))

    assert outcome.coordinator.heads_up is False


def test_stop_when_edition_height_limit_is_not_recorded():
    outcome = run_handoff_pipeline(_complete_brief(max_stand_height_m=None))

    assert outcome.coordinator.verdict == "stop"
    assert "maximum stand height" in outcome.coordinator.reason


def test_every_role_output_is_labeled_simulated():
    outcome = run_handoff_pipeline(_complete_brief())

    assert outcome.preparer.simulated is True
    assert outcome.checker.simulated is True
    assert outcome.coordinator.simulated is True


def test_checker_records_the_proposal_it_validated():
    outcome = run_handoff_pipeline(_complete_brief())

    assert outcome.checker.validated_proposal == outcome.preparer.proposed_next_step


def test_checker_records_the_proposal_it_validated_even_when_incomplete():
    outcome = run_handoff_pipeline(_complete_brief(requested_height_m=None))

    assert outcome.checker.validated_proposal == outcome.preparer.proposed_next_step
