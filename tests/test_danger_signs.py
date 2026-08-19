from __future__ import annotations

import pytest

from edge_imci.evaluation.reference import evaluate_case
from edge_imci.generation.cases import complete_danger_signs
from edge_imci.schemas.case import Action, Classification, DangerSign, Pathway, ReferralRequirement
from tests.helpers import make_case


@pytest.mark.parametrize(
    ("field_name", "expected_sign", "expected_rule"),
    [
        ("unable_to_drink_or_breastfeed", DangerSign.UNABLE_TO_DRINK_OR_BREASTFEED, "IMCI-GDS-UNABLE-TO-DRINK"),
        ("vomits_everything", DangerSign.VOMITS_EVERYTHING, "IMCI-GDS-VOMITS-EVERYTHING"),
        ("had_convulsions", DangerSign.HAD_CONVULSIONS, "IMCI-GDS-CONVULSIONS-HISTORY"),
        ("lethargic_or_unconscious", DangerSign.LETHARGIC_OR_UNCONSCIOUS, "IMCI-GDS-LETHARGIC-OR-UNCONSCIOUS"),
        ("convulsing_now", DangerSign.CONVULSING_NOW, "IMCI-GDS-CONVULSING-NOW"),
    ],
)
def test_each_general_danger_sign_requires_urgent_referral(field_name, expected_sign, expected_rule):
    case = make_case(danger=complete_danger_signs(**{field_name: True}))

    result = evaluate_case(case)

    assert result.detected_danger_signs == (expected_sign,)
    assert result.classifications[Pathway.GENERAL_DANGER_SIGNS] is Classification.VERY_SEVERE_DISEASE
    assert result.referral is ReferralRequirement.URGENT
    assert Action.URGENT_REFERRAL in result.actions
    assert expected_rule in result.fired_rule_ids


def test_convulsing_now_adds_diazepam_action():
    result = evaluate_case(make_case(danger=complete_danger_signs(convulsing_now=True)))

    assert Action.GIVE_DIAZEPAM_IF_CONVULSING_NOW in result.actions


def test_no_danger_sign_has_no_general_classification_or_referral():
    result = evaluate_case(make_case())

    assert result.detected_danger_signs == ()
    assert Pathway.GENERAL_DANGER_SIGNS not in result.classifications
    assert result.referral is ReferralRequirement.NONE
