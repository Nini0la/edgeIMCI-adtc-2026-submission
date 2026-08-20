from __future__ import annotations

import hashlib
import json
from pathlib import Path

from edge_imci.generation.golden import DEFAULT_GOLDEN_PATH, load_golden_slice
from edge_imci.generation.rendering import (
    REFERENCE_STATUS,
    build_reference_rendering,
    build_teacher_prompt,
    compact_semantic_input,
    internal_term_hits,
)
from edge_imci.schemas.trajectory import ExpectedAssistantSemantics
from edge_imci.validation.rendering import NATURAL_VALIDATOR_ID, validate_natural_rendering

CONFIG_PATH = Path("configs/rendering/rendering_bakeoff_v1.json")
REFERENCE_PATH = Path("data/golden/golden_reference_renderings_v1.jsonl")
CANDIDATE_PATH = Path("experiments/rendering_bakeoff_v1/candidates.jsonl")
SUMMARY_PATH = Path("experiments/rendering_bakeoff_v1/summary.json")
REVIEW_PATH = Path("docs/rendering_bakeoff_review_v1.md")
CONTRACT_PATH = Path("docs/rendering_contract_v1.md")


def _jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_bakeoff_pins_the_fixed_golden_semantic_source() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    golden = load_golden_slice(DEFAULT_GOLDEN_PATH)
    source = config["semantic_source"]
    assert source["case_count"] == len(golden) == 14
    assert source["assistant_target_count"] == 16
    assert source["sha256"] == hashlib.sha256(DEFAULT_GOLDEN_PATH.read_bytes()).hexdigest()
    assert source["rule_set_id"] == "imci-selected-v0"
    assert source["information_policy_id"] == "imci-selected-v0-information-policy-v1"
    assert source["constraint_set_id"] == "imci-selected-v0-valid-completions-v1"


def test_bakeoff_uses_three_real_pinned_models_and_two_meaningful_prompts() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    teachers = config["teacher_models"]
    strategies = config["prompt_strategies"]
    assert len(teachers) == 3
    assert len(strategies) == 2
    assert len({item["model_id"] for item in teachers}) == 3
    assert all(len(item["revision"]) == 40 for item in teachers)
    assert {item["strategy_id"] for item in strategies} == {
        "strict-semantic-v1",
        "guided-conversational-v1",
    }
    assert config["generation"] == {
        "temperature": 0.0,
        "max_output_tokens": 512,
        "enable_thinking": False,
        "seed": 20260819,
        "variants_per_target": 1,
        "retry_policy": "one retry only for an empty output or runtime exception",
    }
    assert config["provider"]["api_cost"] is None


def test_all_fourteen_reference_renderings_are_proposed_and_reproducible() -> None:
    golden = load_golden_slice(DEFAULT_GOLDEN_PATH)
    committed = _jsonl(REFERENCE_PATH)
    regenerated = [build_reference_rendering(item).to_dict() for item in golden]
    assert len(committed) == 14
    for actual, reference in zip(committed, regenerated, strict=True):
        assert actual["golden_case_id"] == reference["golden_case_id"]
        assert actual["status"] == reference["status"] == REFERENCE_STATUS
        assert actual["renderer_id"] == reference["renderer_id"]
        assert actual["turns"] == reference["turns"]


def test_all_reference_assistant_targets_pass_deterministic_guards() -> None:
    references = _jsonl(REFERENCE_PATH)
    validations = [item for record in references for item in record["semantic_validations"]]
    assert len(validations) == 16
    for item in validations:
        validation = item["validation"]
        assert validation["validator_id"] == NATURAL_VALIDATOR_ID
        assert validation["semantic_pass"]
        assert all(validation["checks"].values())
        assert validation["missing_concepts"] == []
        assert validation["unexpected_concepts"] == []
        assert validation["acquisition_mode_errors"] == []
        assert validation["obvious_hallucinations"] == []


def test_reference_outputs_hide_internal_policy_and_schema_terms() -> None:
    for record in _jsonl(REFERENCE_PATH):
        for turn in record["turns"]:
            assert internal_term_hits(turn["text"]) == ()
            assert "IMCI-" not in turn["text"]
            assert "diagnosis:" not in turn["text"].lower()


def test_reference_user_turns_do_not_change_the_fixed_semantics() -> None:
    golden = load_golden_slice(DEFAULT_GOLDEN_PATH)
    references = {item["golden_case_id"]: item for item in _jsonl(REFERENCE_PATH)}
    for record in golden:
        source_turns = record["trajectory"]["interaction"]["turns"]
        rendered_turns = references[record["golden_case_id"]]["turns"]
        assert [item["turn_index"] for item in source_turns] == [item["turn_index"] for item in rendered_turns]
        assert [item["visible_message"]["role"] for item in source_turns] == [item["role"] for item in rendered_turns]
        assert [len(item["revealed_observations"]) for item in source_turns] == [
            len(source["revealed_observations"]) for source in source_turns
        ]


def test_teacher_prompts_receive_semantics_not_latent_truth() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    golden = load_golden_slice(DEFAULT_GOLDEN_PATH)[0]
    assistant_turn = next(
        item
        for item in golden["trajectory"]["interaction"]["turns"]
        if item["expected_assistant_semantics"] is not None
    )
    semantics = ExpectedAssistantSemantics.from_dict(assistant_turn["expected_assistant_semantics"])
    prompt = build_teacher_prompt(
        strategy=config["prompt_strategies"][0],
        golden_case_id=golden["golden_case_id"],
        turn_index=assistant_turn["turn_index"],
        conversation_so_far=({"role": "user", "text": "Visible presentation."},),
        semantics=semantics,
    )
    assert json.dumps(compact_semantic_input(semantics), sort_keys=True) in prompt
    assert "latent_truth" not in prompt
    assert "possible_fired_rule_ids" not in prompt
    assert "source_rule_ids" not in prompt


def test_bakeoff_contains_every_configuration_and_assistant_target() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    candidates = _jsonl(CANDIDATE_PATH)
    expected_configurations = {
        f"{teacher['teacher_id']}__{strategy['strategy_id']}"
        for teacher in config["teacher_models"]
        for strategy in config["prompt_strategies"]
    }
    assert len(candidates) == 3 * 2 * 16
    assert {item["configuration_id"] for item in candidates} == expected_configurations
    for configuration_id in expected_configurations:
        items = [item for item in candidates if item["configuration_id"] == configuration_id]
        assert len(items) == 16
        assert len({(item["golden_case_id"], item["assistant_turn_index"]) for item in items}) == 16


def test_candidate_validation_is_recomputed_from_fixed_semantics() -> None:
    golden = {item["golden_case_id"]: item for item in load_golden_slice(DEFAULT_GOLDEN_PATH)}
    references = {item["golden_case_id"]: item for item in _jsonl(REFERENCE_PATH)}
    candidates = _jsonl(CANDIDATE_PATH)
    candidate_index = {
        (item["configuration_id"], item["golden_case_id"], item["assistant_turn_index"]): item
        for item in candidates
    }
    for candidate in candidates:
        record = golden[candidate["golden_case_id"]]
        source_turn = next(
            item
            for item in record["trajectory"]["interaction"]["turns"]
            if item["turn_index"] == candidate["assistant_turn_index"]
        )
        semantics = ExpectedAssistantSemantics.from_dict(source_turn["expected_assistant_semantics"])
        reference_turns = references[candidate["golden_case_id"]]["turns"]
        visible_context_parts = []
        for item in reference_turns:
            if item["turn_index"] >= candidate["assistant_turn_index"]:
                break
            if item["role"] == "user":
                visible_context_parts.append(item["text"])
            else:
                visible_context_parts.append(
                    candidate_index[
                        (
                            candidate["configuration_id"],
                            candidate["golden_case_id"],
                            item["turn_index"],
                        )
                    ]["candidate_text"]
                )
        visible_context = "\n".join(visible_context_parts)
        recomputed = validate_natural_rendering(
            candidate["candidate_text"],
            semantics,
            visible_context=visible_context,
        )
        assert recomputed.to_dict() == candidate["validation"]


def test_summary_matches_candidate_results_and_records_no_fabricated_cost() -> None:
    candidates = _jsonl(CANDIDATE_PATH)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    assert summary["candidate_count"] == len(candidates) == 96
    assert summary["configuration_count"] == 6
    assert summary["bulk_generation_ready"] is False
    assert summary["recommendation"]["approval"] == "NO_CURRENT_CONFIGURATION_READY_TO_FREEZE"
    assert summary["recommendation"]["human_review_shortlist"] == [
        "qwen3-4b-4bit-local__strict-semantic-v1"
    ]
    for item in summary["configurations"]:
        candidates_for_config = [row for row in candidates if row["configuration_id"] == item["configuration_id"]]
        passes = sum(row["validation"]["semantic_pass"] for row in candidates_for_config)
        assert item["candidate_assistant_targets"] == 16
        assert item["semantic_pass_count"] == passes
        assert item["rejected_count"] == 16 - passes
        assert item["semantic_pass_rate"] == passes / 16
        assert item["actual_cost"] is None
        assert item["rough_naturalness_observation"]


def test_review_artifact_is_compact_and_has_human_fields() -> None:
    review = REVIEW_PATH.read_text(encoding="utf-8")
    for record in load_golden_slice(DEFAULT_GOLDEN_PATH):
        assert f"### {record['golden_case_id']}" in review
    assert "Semantic faithfulness" in review
    assert "Naturalness" in review
    assert "PHC suitability" in review
    assert "Preferred output" in review
    assert "not a model-performance benchmark" in review


def test_rendering_contract_defines_required_modes_and_non_goals() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    for heading in (
        "PHC case presentation",
        "Caregiver question",
        "Clinician observation request",
        "Measurement request",
        "Classification and action response",
        "Urgent escalation",
        "Multi-turn behavior",
    ):
        assert heading in contract
    assert "PROPOSED_FOR_HUMAN_REVIEW" in contract
    assert "not a model-performance benchmark" in contract.lower()
    assert "SFT corpus" in contract


def test_experiment_does_not_create_training_or_split_artifacts() -> None:
    assert not Path("data/train").exists()
    assert not Path("data/validation").exists()
    assert not Path("data/test").exists()
    assert not (Path("experiments/rendering_bakeoff_v1") / "splits.json").exists()
