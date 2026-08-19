from __future__ import annotations

import json

import pytest

from edge_imci.evaluation.parsing import ParseStatus, parse_model_output
from edge_imci.evaluation.scoring import score_prediction
from edge_imci.generation.cases import generate_cases


def _payload(case_id: str) -> dict:
    case = next(case for case in generate_cases() if case.case_id == case_id)
    payload = case.expected_result.to_dict()
    payload["sufficient_information"] = not case.expected_result.missing_required_observations
    payload.pop("fired_rule_ids")
    return payload


def test_valid_output_parses_to_typed_prediction():
    result = parse_model_output(json.dumps(_payload("resp_normal_cold_child")))

    assert result.status is ParseStatus.SUCCESS
    assert result.prediction is not None
    assert result.prediction.to_dict() == _payload("resp_normal_cold_child")


def test_markdown_json_fence_and_whitespace_are_harmless():
    raw = f"  ```json\n{json.dumps(_payload('resp_normal_cold_child'))}\n```  "

    result = parse_model_output(raw)

    assert result.status is ParseStatus.SUCCESS


@pytest.mark.parametrize(
    ("raw", "error_code"),
    [
        ("not-json", "invalid_json"),
        (json.dumps({"sufficient_information": True}), "invalid_fields"),
        ('{"sufficient_information": true, "sufficient_information": false}', "duplicate_key"),
    ],
)
def test_malformed_or_missing_output_fails(raw, error_code):
    result = parse_model_output(raw)

    assert result.status is ParseStatus.FAILURE
    assert result.error_code == error_code
    assert result.prediction is None


def test_unknown_enum_value_fails_without_inference():
    payload = _payload("resp_normal_cold_child")
    payload["actions"] = ["INVENTED_ACTION"]

    result = parse_model_output(json.dumps(payload))

    assert result.status is ParseStatus.FAILURE
    assert result.error_code == "invalid_prediction"


def test_classification_valid_for_another_pathway_is_still_rejected():
    payload = _payload("resp_normal_cold_child")
    payload["classifications"] = {"respiratory": "NO_DEHYDRATION"}

    result = parse_model_output(json.dumps(payload))

    assert result.status is ParseStatus.FAILURE
    assert result.error_code == "invalid_prediction"


def test_contradictory_sufficient_information_fails():
    payload = _payload("resp_missing_rate")
    payload["sufficient_information"] = True

    result = parse_model_output(json.dumps(payload))

    assert result.status is ParseStatus.FAILURE
    assert result.error_code == "invalid_prediction"


def test_insufficient_information_response_preserves_missing_fields():
    payload = _payload("resp_missing_rate")

    result = parse_model_output(json.dumps(payload))

    assert result.status is ParseStatus.SUCCESS
    assert result.prediction is not None
    assert not result.prediction.sufficient_information
    assert [item.value for item in result.prediction.missing_required_observations] == [
        "respiratory.respiratory_rate"
    ]


def test_known_but_unsupported_classification_and_actions_score_as_wrong():
    case = next(case for case in generate_cases() if case.case_id == "resp_normal_cold_child")
    payload = _payload(case.case_id)
    payload["classifications"] = {"respiratory": "PNEUMONIA"}
    payload["actions"] = [
        "GIVE_ORAL_AMOXICILLIN_5_DAYS",
        "SOOTHE_THROAT_AND_RELIEVE_COUGH",
        "ADVISE_WHEN_TO_RETURN_IMMEDIATELY",
        "FOLLOW_UP_3_DAYS",
    ]
    parsed = parse_model_output(json.dumps(payload))

    assert parsed.status is ParseStatus.SUCCESS
    assert parsed.prediction is not None
    score = score_prediction(parsed.prediction, case.expected_result)
    assert not score.classification_correct
    assert not score.actions_correct
    assert not score.no_unsupported_output
    assert not score.overall_pass


def test_text_outside_json_fence_is_not_silently_discarded():
    raw = f"Here is the answer:\n```json\n{json.dumps(_payload('resp_normal_cold_child'))}\n```"

    result = parse_model_output(raw)

    assert result.status is ParseStatus.FAILURE
    assert result.error_code == "invalid_wrapper"
