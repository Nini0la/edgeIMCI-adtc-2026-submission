from __future__ import annotations

import pytest

from edge_imci.evaluation.reference import evaluate_case
from edge_imci.generation.cases import complete_danger_signs
from edge_imci.rules.loader import load_rule_set
from edge_imci.schemas.case import (
    Action,
    Classification,
    DangerSign,
    DehydrationObservations,
    DrinkingStatus,
    Pathway,
    RespiratoryObservations,
    SkinPinch,
)
from tests.helpers import make_case


@pytest.mark.parametrize(
    ("age_months", "respiratory_rate", "classification"),
    [
        (2, 49, Classification.COUGH_OR_COLD),
        (2, 50, Classification.PNEUMONIA),
        (11, 49, Classification.COUGH_OR_COLD),
        (11, 50, Classification.PNEUMONIA),
        (12, 39, Classification.COUGH_OR_COLD),
        (12, 40, Classification.PNEUMONIA),
        (59, 39, Classification.COUGH_OR_COLD),
        (59, 40, Classification.PNEUMONIA),
    ],
)
def test_respiratory_thresholds_at_supported_age_bounds(age_months, respiratory_rate, classification):
    result = evaluate_case(
        make_case(
            age_months=age_months,
            respiratory=RespiratoryObservations(respiratory_rate, False, False),
        )
    )

    assert result.classifications[Pathway.RESPIRATORY] is classification


def test_threshold_changes_exactly_at_twelve_months():
    just_below = evaluate_case(
        make_case(age_months=11, respiratory=RespiratoryObservations(45, False, False))
    )
    at_boundary = evaluate_case(
        make_case(age_months=12, respiratory=RespiratoryObservations(45, False, False))
    )

    assert just_below.classifications[Pathway.RESPIRATORY] is Classification.COUGH_OR_COLD
    assert at_boundary.classifications[Pathway.RESPIRATORY] is Classification.PNEUMONIA


@pytest.mark.parametrize("age_months", [1, 60])
def test_age_outside_selected_scope_is_rejected(age_months):
    with pytest.raises(ValueError, match="age_months must be at least 2 and less than 60"):
        make_case(age_months=age_months)


def test_severe_respiratory_classification_dominates_pneumonia_predicates():
    result = evaluate_case(
        make_case(respiratory=RespiratoryObservations(50, True, True))
    )

    assert result.classifications[Pathway.RESPIRATORY] is Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE
    assert "IMCI-RESP-SEVERE-STRIDOR" in result.fired_rule_ids
    assert "IMCI-RESP-PNEUMONIA-CHEST-INDRAWING" not in result.fired_rule_ids
    assert "IMCI-RESP-PNEUMONIA-FAST-BREATHING" not in result.fired_rule_ids


def test_pneumonia_dominates_cough_or_cold_fallback():
    result = evaluate_case(
        make_case(respiratory=RespiratoryObservations(20, True, False))
    )

    assert result.classifications[Pathway.RESPIRATORY] is Classification.PNEUMONIA
    assert "IMCI-RESP-PNEUMONIA-CHEST-INDRAWING" in result.fired_rule_ids
    assert "IMCI-RESP-COUGH-OR-COLD" not in result.fired_rule_ids


def test_severe_dehydration_dominates_simultaneously_satisfied_some_dehydration():
    result = evaluate_case(
        make_case(
            dehydration=DehydrationObservations(
                restless_or_irritable=True,
                sunken_eyes=True,
                drinking_status=DrinkingStatus.POORLY,
                skin_pinch=SkinPinch.NORMAL,
            )
        )
    )

    assert result.classifications[Pathway.DEHYDRATION] is Classification.SEVERE_DEHYDRATION
    assert "IMCI-DIARRHOEA-SEVERE-DEHYDRATION" in result.fired_rule_ids
    assert "IMCI-DIARRHOEA-SOME-DEHYDRATION" not in result.fired_rule_ids


def test_some_dehydration_dominates_no_dehydration_fallback():
    result = evaluate_case(
        make_case(
            dehydration=DehydrationObservations(
                restless_or_irritable=True,
                sunken_eyes=True,
                drinking_status=DrinkingStatus.NORMAL,
                skin_pinch=SkinPinch.NORMAL,
            )
        )
    )

    assert result.classifications[Pathway.DEHYDRATION] is Classification.SOME_DEHYDRATION
    assert "IMCI-DIARRHOEA-SOME-DEHYDRATION" in result.fired_rule_ids
    assert "IMCI-DIARRHOEA-NO-DEHYDRATION" not in result.fired_rule_ids


def test_missing_information_does_not_trigger_fallback_classifications():
    respiratory = evaluate_case(
        make_case(respiratory=RespiratoryObservations(None, False, False))
    )
    dehydration = evaluate_case(
        make_case(
            dehydration=DehydrationObservations(
                restless_or_irritable=False,
                sunken_eyes=True,
                drinking_status=None,
                skin_pinch=SkinPinch.NORMAL,
            )
        )
    )

    assert Pathway.RESPIRATORY not in respiratory.classifications
    assert "IMCI-RESP-COUGH-OR-COLD" not in respiratory.fired_rule_ids
    assert "respiratory.respiratory_rate" in respiratory.missing_required_observations
    assert Pathway.DEHYDRATION not in dehydration.classifications
    assert "IMCI-DIARRHOEA-NO-DEHYDRATION" not in dehydration.fired_rule_ids
    assert "dehydration.drinking_status" in dehydration.missing_required_observations


def test_multiple_general_danger_sign_rules_fire_together():
    result = evaluate_case(
        make_case(
            danger=complete_danger_signs(
                unable_to_drink_or_breastfeed=True,
                convulsing_now=True,
            )
        )
    )

    assert set(result.detected_danger_signs) == {
        DangerSign.UNABLE_TO_DRINK_OR_BREASTFEED,
        DangerSign.CONVULSING_NOW,
    }
    assert {
        "IMCI-GDS-UNABLE-TO-DRINK",
        "IMCI-GDS-CONVULSING-NOW",
    } <= set(result.fired_rule_ids)


def test_convulsing_now_preserves_diazepam_with_shared_severe_classification():
    result = evaluate_case(
        make_case(
            danger=complete_danger_signs(
                unable_to_drink_or_breastfeed=True,
                convulsing_now=True,
            )
        )
    )

    assert result.classifications[Pathway.GENERAL_DANGER_SIGNS] is Classification.VERY_SEVERE_DISEASE
    assert Action.GIVE_DIAZEPAM_IF_CONVULSING_NOW in result.actions


def test_fast_breathing_is_derived_then_consumed_by_pneumonia_rule():
    rules = {rule.rule_id: rule for rule in load_rule_set().rules}
    threshold_id = "IMCI-RESP-FAST-BREATHING-2-12M"
    classification_id = "IMCI-RESP-PNEUMONIA-FAST-BREATHING"

    assert rules[threshold_id].result == {"fast_breathing": True}
    assert "classification" not in rules[threshold_id].result
    assert rules[classification_id].conditions == {"fast_breathing": True}

    result = evaluate_case(
        make_case(age_months=8, respiratory=RespiratoryObservations(50, False, False))
    )

    assert result.classifications[Pathway.RESPIRATORY] is Classification.PNEUMONIA
    assert threshold_id in result.fired_rule_ids
    assert classification_id in result.fired_rule_ids


def test_other_severe_classification_changes_dehydration_actions_not_classification():
    dehydration = DehydrationObservations(
        restless_or_irritable=False,
        sunken_eyes=True,
        drinking_status=DrinkingStatus.POORLY,
        skin_pinch=SkinPinch.NORMAL,
    )
    without_other_severe = evaluate_case(make_case(dehydration=dehydration))
    with_other_severe = evaluate_case(
        make_case(
            respiratory=RespiratoryObservations(20, False, True),
            dehydration=dehydration,
        )
    )

    assert without_other_severe.classifications[Pathway.DEHYDRATION] is Classification.SEVERE_DEHYDRATION
    assert with_other_severe.classifications[Pathway.DEHYDRATION] is Classification.SEVERE_DEHYDRATION
    assert Action.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C in without_other_severe.actions
    assert Action.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C not in with_other_severe.actions
    assert {
        Action.URGENT_REFERRAL,
        Action.FREQUENT_ORS_SIPS_DURING_REFERRAL,
        Action.CONTINUE_BREASTFEEDING,
    } <= set(with_other_severe.actions)


def test_selected_scope_action_aggregation_preserves_every_provider():
    result = evaluate_case(
        make_case(
            danger=complete_danger_signs(
                unable_to_drink_or_breastfeed=True,
                convulsing_now=True,
            ),
            respiratory=RespiratoryObservations(20, False, False),
            dehydration=DehydrationObservations(
                restless_or_irritable=True,
                sunken_eyes=True,
                drinking_status=DrinkingStatus.NORMAL,
                skin_pinch=SkinPinch.NORMAL,
            ),
        )
    )

    assert set(result.actions) == {
        Action.COMPLETE_ASSESSMENT_QUICKLY,
        Action.GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY,
        Action.PREVENT_LOW_BLOOD_SUGAR,
        Action.KEEP_WARM,
        Action.URGENT_REFERRAL,
        Action.GIVE_DIAZEPAM_IF_CONVULSING_NOW,
        Action.GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC,
        Action.FREQUENT_ORS_SIPS_DURING_REFERRAL,
        Action.CONTINUE_BREASTFEEDING,
    }
    assert {
        "IMCI-GDS-UNABLE-TO-DRINK",
        "IMCI-GDS-CONVULSING-NOW",
        "IMCI-RESP-SEVERE-DANGER-SIGN",
        "IMCI-DIARRHOEA-SOME-DEHYDRATION",
    } <= set(result.fired_rule_ids)
