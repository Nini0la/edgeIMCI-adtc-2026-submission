from __future__ import annotations

import pytest

from edge_imci.evaluation.reference import evaluate_case
from edge_imci.generation.cases import complete_danger_signs
from edge_imci.schemas.case import Classification, Pathway, ReferralRequirement, RespiratoryObservations
from tests.helpers import make_case


@pytest.mark.parametrize(("age_months", "threshold"), [(8, 50), (24, 40)])
def test_fast_breathing_threshold_below_exact_and_above(age_months, threshold):
    below = evaluate_case(make_case(age_months=age_months, respiratory=RespiratoryObservations(threshold - 1, False, False)))
    exact = evaluate_case(make_case(age_months=age_months, respiratory=RespiratoryObservations(threshold, False, False)))
    above = evaluate_case(make_case(age_months=age_months, respiratory=RespiratoryObservations(threshold + 1, False, False)))

    assert below.classifications[Pathway.RESPIRATORY] is Classification.COUGH_OR_COLD
    assert exact.classifications[Pathway.RESPIRATORY] is Classification.PNEUMONIA
    assert above.classifications[Pathway.RESPIRATORY] is Classification.PNEUMONIA


def test_age_boundary_changes_fast_breathing_threshold():
    age_11 = evaluate_case(make_case(age_months=11, respiratory=RespiratoryObservations(45, False, False)))
    age_12 = evaluate_case(make_case(age_months=12, respiratory=RespiratoryObservations(45, False, False)))

    assert age_11.classifications[Pathway.RESPIRATORY] is Classification.COUGH_OR_COLD
    assert age_12.classifications[Pathway.RESPIRATORY] is Classification.PNEUMONIA


@pytest.mark.parametrize(
    ("observations", "danger", "classification", "referral"),
    [
        (RespiratoryObservations(34, False, False), complete_danger_signs(), Classification.COUGH_OR_COLD, ReferralRequirement.NONE),
        (RespiratoryObservations(45, False, False), complete_danger_signs(), Classification.PNEUMONIA, ReferralRequirement.NONE),
        (RespiratoryObservations(34, True, False), complete_danger_signs(), Classification.PNEUMONIA, ReferralRequirement.NONE),
        (RespiratoryObservations(34, False, True), complete_danger_signs(), Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE, ReferralRequirement.URGENT),
        (RespiratoryObservations(34, False, False), complete_danger_signs(vomits_everything=True), Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE, ReferralRequirement.URGENT),
    ],
)
def test_respiratory_classification_precedence(observations, danger, classification, referral):
    result = evaluate_case(make_case(danger=danger, respiratory=observations))

    assert result.classifications[Pathway.RESPIRATORY] is classification
    assert result.referral is referral


@pytest.mark.parametrize(
    ("observations", "danger", "missing_field"),
    [
        (RespiratoryObservations(None, False, False), complete_danger_signs(), "respiratory.respiratory_rate"),
        (RespiratoryObservations(34, None, False), complete_danger_signs(), "respiratory.chest_indrawing"),
        (RespiratoryObservations(34, False, None), complete_danger_signs(), "respiratory.stridor_when_calm"),
        (RespiratoryObservations(34, False, False), complete_danger_signs(vomits_everything=None), "danger_signs.vomits_everything"),
    ],
)
def test_missing_required_respiratory_information_blocks_classification(observations, danger, missing_field):
    result = evaluate_case(make_case(danger=danger, respiratory=observations))

    assert Pathway.RESPIRATORY not in result.classifications
    assert missing_field in result.missing_required_observations
