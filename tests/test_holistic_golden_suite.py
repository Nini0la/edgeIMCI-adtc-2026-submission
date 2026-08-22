from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from edge_imci.corpus_policy import CorpusUse
from edge_imci.generation.holistic_golden import (
    DEFAULT_JSONL_PATH,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_REVIEW_PATH,
    DEFAULT_SCOPE_DISPOSITIONS_PATH,
    DEFAULT_SCOPE_DISPOSITIONS_YAML_PATH,
    DEFAULT_YAML_PATH,
    DECISION_SET_ID,
    RECORD_SCHEMA_ID,
    SUITE_ID,
    SCOPE_DISPOSITION_SET_ID,
    VALIDATOR_ID,
    build_holistic_golden_suite,
    load_holistic_golden_suite,
    load_scope_dispositions,
    validate_holistic_golden_record,
)
from edge_imci.information_policy.holistic_artifacts import load_holistic_artifacts
from edge_imci.schemas.holistic import HolisticClassification
from edge_imci.schemas.trajectory import CorpusRole


@pytest.fixture(scope="module")
def records() -> list[dict]:
    return load_holistic_golden_suite()


def _by_id(records: list[dict]) -> dict[str, dict]:
    return {record["golden_case_id"]: record for record in records}


def test_suite_is_review_sized_unique_and_product_specific(records: list[dict]) -> None:
    assert len(records) == 78
    assert 50 <= len(records) <= 100
    assert len({record["golden_case_id"] for record in records}) == len(records)
    assert all(record["suite_id"] == SUITE_ID for record in records)
    assert all(record["record_schema_id"] == RECORD_SCHEMA_ID for record in records)
    assert all(record["corpus_role"] == CorpusRole.HOLISTIC_PRODUCT_GOLDEN.value for record in records)
    assert all(record["status"] == "PROPOSED_FOR_DOMAIN_REVIEW" for record in records)
    assert all("DOMAIN_REVIEW_REQUIRED" in record["review_flags"] for record in records)


def test_committed_jsonl_and_yaml_are_deterministic_mirrors(records: list[dict]) -> None:
    assert records == build_holistic_golden_suite()
    assert yaml.safe_load(DEFAULT_YAML_PATH.read_text(encoding="utf-8")) == records


def test_every_record_recomputes_or_rejects_exactly(records: list[dict]) -> None:
    for record in records:
        validate_holistic_golden_record(record)


def test_all_approved_review_decisions_are_represented(records: list[dict]) -> None:
    represented = {
        question_id
        for record in records
        for question_id in record["provenance"]["review_decision_ids"]
    }
    approved = {
        item["question_id"]
        for item in load_holistic_artifacts().decisions["decisions"]
    }
    assert represented == approved


def test_manifest_pins_lifecycle_hash_and_noneligibility(records: list[dict]) -> None:
    manifest = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["suite_id"] == SUITE_ID
    assert manifest["lifecycle_status"] == "PROPOSED_FOR_DOMAIN_REVIEW"
    assert manifest["case_count"] == len(records)
    assert manifest["artifact_pins"]["review_decision_set_id"] == DECISION_SET_ID
    assert manifest["artifact_pins"]["scope_disposition_set_id"] == SCOPE_DISPOSITION_SET_ID
    assert manifest["artifact_pins"]["validator_id"] == VALIDATOR_ID
    assert manifest["semantic_cases_sha256"] == hashlib.sha256(DEFAULT_JSONL_PATH.read_bytes()).hexdigest()
    assert manifest["unknown_semantics"] == {
        "omitted_is_unknown": True,
        "unknown_is_negative": False,
    }
    assert manifest["eligibility"]["DOMAIN_REVIEW"] is True
    for use in ("HOLISTIC_GENERATION", "PRODUCT_EVALUATION", "TEACHER_BAKEOFF", "TRAINING"):
        assert manifest["eligibility"][use] is False


@pytest.mark.parametrize(
    "use",
    [
        CorpusUse.HOLISTIC_GENERATION,
        CorpusUse.PRODUCT_EVALUATION,
        CorpusUse.TEACHER_BAKEOFF,
        CorpusUse.TRAINING,
    ],
)
def test_proposed_suite_loader_rejects_premature_uses(use: CorpusUse) -> None:
    with pytest.raises(ValueError, match="is not eligible"):
        load_holistic_golden_suite(corpus_use=use)


def test_proposed_suite_loader_allows_review_and_component_validation() -> None:
    assert load_holistic_golden_suite(corpus_use=CorpusUse.DOMAIN_REVIEW)
    assert load_holistic_golden_suite(corpus_use=CorpusUse.COMPONENT_VALIDATION)


def test_every_encoded_classification_family_has_a_review_case(records: list[dict]) -> None:
    covered = {
        trace["classification"]
        for record in records
        if record["expected"]["kind"] == "HOLISTIC_EVALUATION"
        for trace in record["expected"]["evaluation"]["internal_classifications"]
    }
    assert covered == {classification.value for classification in HolisticClassification}


def test_required_semantic_families_are_explicitly_covered(records: list[dict]) -> None:
    tags = {tag for record in records for tag in record["coverage"]}
    assert {
        "complete",
        "low_severity",
        "simultaneous_classifications",
        "integrated_action_plan",
        "cross_pathway_action_dependency",
        "urgent_incomplete",
        "grouped_missing_elements",
        "explicit_negative_omission_twin",
        "bronchodilator_reassessment",
        "complete_post_reassessment",
        "plan_b",
        "plan_c",
        "malaria",
        "measles",
        "mastoiditis",
        "contradiction",
        "schema_rejection",
    } <= tags


def test_incomplete_cases_withhold_final_synthesis_but_keep_known_urgency(records: list[dict]) -> None:
    by_id = _by_id(records)
    urgent = by_id["hpg-073-incomplete-known-urgent"]["expected"]["evaluation"]
    assert urgent["supported_encounter_complete"] is False
    assert urgent["urgent_action_required"] is True
    assert urgent["urgent_actions"]
    assert urgent["final_classifications"] == []
    assert urgent["final_actions"] == []
    nonurgent = by_id["hpg-071-incomplete-entry-unknown"]["expected"]["evaluation"]
    assert nonurgent["urgent_action_required"] is False
    assert nonurgent["final_classifications"] == []
    assert nonurgent["final_actions"] == []


def test_explicit_negative_and_omission_remain_distinct(records: list[dict]) -> None:
    by_id = _by_id(records)
    complete = by_id["hpg-001-all-negative"]["expected"]["evaluation"]
    omitted = by_id["hpg-071-incomplete-entry-unknown"]["expected"]["evaluation"]
    assert complete["supported_encounter_complete"] is True
    assert omitted["supported_encounter_complete"] is False
    assert "patient_facts.has_diarrhoea" in omitted["missing_elements"]["supported_encounter"]


def test_out_of_scope_cases_are_schema_rejections(records: list[dict]) -> None:
    rejected = [record for record in records if "out_of_scope" in record["coverage"]]
    assert len(rejected) == 2
    assert all(record["expected"]["kind"] == "SCHEMA_REJECTION" for record in rejected)


def test_later_plan_reassessment_gap_is_resolved_by_versioned_product_scope() -> None:
    manifest = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
    artifact = load_scope_dispositions()
    assert manifest["known_coverage_gaps"] == []
    assert manifest["freeze_blockers"] == ["DOMAIN_REVIEW_PENDING"]
    assert manifest["scope_dispositions"] == artifact["dispositions"]
    disposition = artifact["dispositions"][0]
    assert disposition["gap_id"] == "HPG-GAP-REASSESS-001"
    assert disposition["status"] == "RESOLVED_BY_PRODUCT_SCOPE"
    assert disposition["rationale_type"] == "PRODUCT_SCOPE_DECISION"
    assert artifact["clinical_rule_change"] is False
    yaml_mirror = yaml.safe_load(DEFAULT_SCOPE_DISPOSITIONS_YAML_PATH.read_text(encoding="utf-8"))
    assert yaml_mirror == json.loads(DEFAULT_SCOPE_DISPOSITIONS_PATH.read_text(encoding="utf-8"))


def test_suite_contains_semantics_only_and_review_package_is_complete(records: list[dict]) -> None:
    serialized = DEFAULT_JSONL_PATH.read_text(encoding="utf-8")
    assert "conversation" not in serialized
    assert "rendering" not in serialized
    assert "assistant_message" not in serialized
    review = DEFAULT_REVIEW_PATH.read_text(encoding="utf-8")
    assert "not training data" in review.lower()
    assert "HPG-GAP-REASSESS-001" in review
    for record in records:
        assert f"`{record['golden_case_id']}`" in review
    assert not Path("data/train").exists()
    assert not Path("data/validation").exists()
