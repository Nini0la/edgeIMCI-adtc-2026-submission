from __future__ import annotations

import pytest

from edge_imci.evaluation.reference import evaluate_case
from edge_imci.generation.cases import complete_danger_signs
from edge_imci.schemas.case import (
    Action,
    Classification,
    DehydrationObservations,
    DrinkingStatus,
    Pathway,
    ReferralRequirement,
    SkinPinch,
)
from tests.helpers import make_case


@pytest.mark.parametrize(
    "observations",
    [
        DehydrationObservations(False, True, DrinkingStatus.POORLY, SkinPinch.NORMAL),
        DehydrationObservations(False, True, DrinkingStatus.NORMAL, SkinPinch.VERY_SLOWLY),
        DehydrationObservations(False, False, DrinkingStatus.POORLY, SkinPinch.VERY_SLOWLY),
    ],
)
def test_two_severe_signs_classify_severe_dehydration(observations):
    result = evaluate_case(make_case(dehydration=observations))

    assert result.classifications[Pathway.DEHYDRATION] is Classification.SEVERE_DEHYDRATION
    assert Action.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C in result.actions
    assert result.referral is ReferralRequirement.NONE


def test_severe_dehydration_with_general_danger_sign_refers_urgently():
    case = make_case(
        danger=complete_danger_signs(lethargic_or_unconscious=True),
        dehydration=DehydrationObservations(False, True, DrinkingStatus.NORMAL, SkinPinch.NORMAL),
    )

    result = evaluate_case(case)

    assert result.classifications[Pathway.DEHYDRATION] is Classification.SEVERE_DEHYDRATION
    assert result.referral is ReferralRequirement.URGENT
    assert Action.FREQUENT_ORS_SIPS_DURING_REFERRAL in result.actions
    assert Action.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C not in result.actions


@pytest.mark.parametrize(
    "observations",
    [
        DehydrationObservations(True, True, DrinkingStatus.NORMAL, SkinPinch.NORMAL),
        DehydrationObservations(True, False, DrinkingStatus.EAGER_OR_THIRSTY, SkinPinch.NORMAL),
        DehydrationObservations(False, True, DrinkingStatus.NORMAL, SkinPinch.SLOWLY),
        DehydrationObservations(False, False, DrinkingStatus.EAGER_OR_THIRSTY, SkinPinch.SLOWLY),
    ],
)
def test_two_some_dehydration_signs_classify_some_dehydration(observations):
    result = evaluate_case(make_case(dehydration=observations))

    assert result.classifications[Pathway.DEHYDRATION] is Classification.SOME_DEHYDRATION
    assert Action.GIVE_FLUID_ZINC_AND_FOOD_PLAN_B in result.actions


@pytest.mark.parametrize(
    "observations",
    [
        DehydrationObservations(False, False, DrinkingStatus.NORMAL, SkinPinch.NORMAL),
        DehydrationObservations(False, True, DrinkingStatus.NORMAL, SkinPinch.NORMAL),
        DehydrationObservations(True, False, DrinkingStatus.NORMAL, SkinPinch.NORMAL),
        DehydrationObservations(True, False, DrinkingStatus.POORLY, SkinPinch.NORMAL),
    ],
)
def test_insufficient_qualifying_signs_classify_no_dehydration(observations):
    result = evaluate_case(make_case(dehydration=observations))

    assert result.classifications[Pathway.DEHYDRATION] is Classification.NO_DEHYDRATION
    assert Action.GIVE_FLUID_ZINC_AND_FOOD_PLAN_A in result.actions


@pytest.mark.parametrize(
    ("observations", "missing_fields"),
    [
        (DehydrationObservations(False, True, None, SkinPinch.NORMAL), {"dehydration.drinking_status"}),
        (DehydrationObservations(True, None, DrinkingStatus.NORMAL, SkinPinch.NORMAL), {"dehydration.sunken_eyes"}),
        (DehydrationObservations(False, None, None, SkinPinch.NORMAL), {"dehydration.sunken_eyes", "dehydration.drinking_status"}),
    ],
)
def test_missing_dehydration_information_blocks_unsupported_classification(observations, missing_fields):
    result = evaluate_case(make_case(dehydration=observations))

    assert Pathway.DEHYDRATION not in result.classifications
    assert missing_fields <= set(result.missing_required_observations)
