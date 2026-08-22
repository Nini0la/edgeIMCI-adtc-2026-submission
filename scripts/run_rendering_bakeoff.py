#!/usr/bin/env python3
"""Reproduce the historical selected-v0 rendering experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from edge_imci.corpus_policy import CorpusUse, assert_corpus_use_allowed
from edge_imci.generation.golden import DEFAULT_GOLDEN_PATH, load_golden_slice
from edge_imci.generation.rendering import (
    build_reference_rendering,
    build_teacher_prompt,
    compact_semantic_input,
    normalize_teacher_output,
)
from edge_imci.inference.mlx_adapter import MlxModelAdapter
from edge_imci.schemas.trajectory import ExpectedAssistantSemantics
from edge_imci.validation.rendering import validate_natural_rendering

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT / "configs" / "rendering" / "rendering_bakeoff_v1.json"
DEFAULT_REFERENCE_PATH = ROOT / "data" / "archive" / "selected_v0" / "golden" / "golden_reference_renderings_v1.jsonl"
DEFAULT_RUN_DIR = ROOT / "experiments" / "rendering_bakeoff_v1"
DEFAULT_CANDIDATE_PATH = DEFAULT_RUN_DIR / "candidates.jsonl"
DEFAULT_SUMMARY_PATH = DEFAULT_RUN_DIR / "summary.json"
DEFAULT_REVIEW_PATH = ROOT / "docs" / "rendering_bakeoff_review_v1.md"
_NATURALNESS_OBSERVATIONS = {
    "qwen3-0.6b-local__strict-semantic-v1": "Mechanical list formatting, internal-state leakage, and frequent omissions; not PHC-ready.",
    "qwen3-0.6b-local__guided-conversational-v1": "Short but frequently omits classifications and actions or restates facts incorrectly; not PHC-ready.",
    "qwen3-1.7b-local__strict-semantic-v1": "More structured, but still awkward and inconsistent, with measurement-mode and unknown-evidence errors.",
    "qwen3-1.7b-local__guided-conversational-v1": "Often fluent and concise, but routinely omits explicit classification terminology and required content.",
    "qwen3-4b-4bit-local__strict-semantic-v1": "Best semantic retention, but mechanical; repeats known evidence and mishandles insufficient and urgent response framing.",
    "qwen3-4b-4bit-local__guided-conversational-v1": "Generally fluent, but repeats the case presentation and often omits explicit classifications or invariant actions.",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--revalidate-only", action="store_true")
    parser.add_argument("--reference-only", action="store_true")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    assert_corpus_use_allowed(DEFAULT_GOLDEN_PATH, CorpusUse.HISTORICAL_REPRODUCTION)
    golden = load_golden_slice(DEFAULT_GOLDEN_PATH, corpus_use=CorpusUse.HISTORICAL_REPRODUCTION)
    _validate_fixed_source(config, golden)
    references = _write_references(golden)
    if args.reference_only:
        print(f"wrote {len(references)} proposed reference renderings to {DEFAULT_REFERENCE_PATH}")
        return
    if args.revalidate_only:
        candidates = _revalidate_candidates(_load_jsonl(DEFAULT_CANDIDATE_PATH), golden, references)
        prior_summary = json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8"))
        summary = _summarize(config, candidates, prior_summary["runtime_by_teacher"])
        _write_experiment_artifacts(config, golden, references, candidates, summary)
        print(f"revalidated {len(candidates)} teacher candidates")
        return

    candidates, runtime_by_teacher = _run_candidates(config, golden, references)
    summary = _summarize(config, candidates, runtime_by_teacher)
    _write_experiment_artifacts(config, golden, references, candidates, summary)
    print(f"wrote {len(references)} proposed reference renderings to {DEFAULT_REFERENCE_PATH}")
    print(f"wrote {len(candidates)} teacher candidates to {DEFAULT_CANDIDATE_PATH}")
    print(f"wrote configuration summary to {DEFAULT_SUMMARY_PATH}")
    print(f"wrote human review package to {DEFAULT_REVIEW_PATH}")


def _write_experiment_artifacts(
    config: dict[str, Any],
    golden: list[dict[str, Any]],
    references: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    DEFAULT_RUN_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_CANDIDATE_PATH.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in candidates),
        encoding="utf-8",
    )
    DEFAULT_SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DEFAULT_REVIEW_PATH.write_text(
        _render_review(config, golden, references, candidates, summary),
        encoding="utf-8",
    )


def _write_references(golden: list[dict[str, Any]]) -> list[dict[str, Any]]:
    references = []
    for record in golden:
        rendering = build_reference_rendering(record)
        assistant_semantics = {
            str(turn["turn_index"]): compact_semantic_input(
                ExpectedAssistantSemantics.from_dict(turn["expected_assistant_semantics"])
            )
            for turn in record["trajectory"]["interaction"]["turns"]
            if turn["expected_assistant_semantics"] is not None
        }
        validations = []
        rendered_turns = {item.turn_index: item for item in rendering.turns}
        context = []
        for turn in record["trajectory"]["interaction"]["turns"]:
            reference_turn = rendered_turns[turn["turn_index"]]
            if reference_turn.role == "assistant":
                semantics = ExpectedAssistantSemantics.from_dict(turn["expected_assistant_semantics"])
                validation = validate_natural_rendering(
                    reference_turn.text,
                    semantics,
                    visible_context="\n".join(item["text"] for item in context),
                )
                validations.append({"turn_index": turn["turn_index"], "validation": validation.to_dict()})
            context.append({"role": reference_turn.role, "text": reference_turn.text})
        references.append(
            {
                "golden_case_id": record["golden_case_id"],
                "why": record["why"],
                "status": rendering.status,
                "renderer_id": rendering.renderer_id,
                "structured_expected_behavior": assistant_semantics,
                "turns": [item.to_dict() for item in rendering.turns],
                "semantic_validations": validations,
            }
        )
    DEFAULT_REFERENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REFERENCE_PATH.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in references),
        encoding="utf-8",
    )
    return references


def _run_candidates(
    config: dict[str, Any],
    golden: list[dict[str, Any]],
    references: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    reference_by_id = {item["golden_case_id"]: item for item in references}
    candidates: list[dict[str, Any]] = []
    runtime_by_teacher = {}
    for teacher in config["teacher_models"]:
        adapter = _adapter(teacher, config["generation"])
        _validate_adapter_identity(adapter, teacher)
        runtime_by_teacher[teacher["teacher_id"]] = {
            "model": adapter.model_metadata,
            "runtime": adapter.runtime_metadata,
        }
        for strategy in config["prompt_strategies"]:
            configuration_id = f"{teacher['teacher_id']}__{strategy['strategy_id']}"
            for record in golden:
                reference = reference_by_id[record["golden_case_id"]]
                reference_turns = {item["turn_index"]: item for item in reference["turns"]}
                conversation: list[dict[str, str]] = []
                for turn in record["trajectory"]["interaction"]["turns"]:
                    turn_index = turn["turn_index"]
                    if turn["visible_message"]["role"] == "user":
                        conversation.append({"role": "user", "text": reference_turns[turn_index]["text"]})
                        continue
                    semantics = ExpectedAssistantSemantics.from_dict(turn["expected_assistant_semantics"])
                    prompt = build_teacher_prompt(
                        strategy=strategy,
                        golden_case_id=record["golden_case_id"],
                        turn_index=turn_index,
                        conversation_so_far=tuple(conversation),
                        semantics=semantics,
                    )
                    output, retries, error, wall_seconds = _generate_with_one_empty_retry(adapter, prompt)
                    normalized = normalize_teacher_output(output.text) if output is not None else ""
                    validation = validate_natural_rendering(
                        normalized,
                        semantics,
                        visible_context="\n".join(item["text"] for item in conversation),
                    )
                    candidate = {
                        "candidate_id": f"{configuration_id}__{record['golden_case_id']}__turn-{turn_index}",
                        "configuration_id": configuration_id,
                        "teacher_id": teacher["teacher_id"],
                        "prompt_strategy_id": strategy["strategy_id"],
                        "golden_case_id": record["golden_case_id"],
                        "assistant_turn_index": turn_index,
                        "status": "PROPOSED_FOR_HUMAN_REVIEW" if validation.semantic_pass else "REJECTED_BY_DETERMINISTIC_VALIDATION",
                        "semantic_input": compact_semantic_input(semantics),
                        "prompt_sha256": _sha256(prompt),
                        "raw_output": output.text if output is not None else "",
                        "candidate_text": normalized,
                        "validation": validation.to_dict(),
                        "metrics": {
                            "input_tokens": output.input_token_count if output is not None else None,
                            "output_tokens": output.output_token_count if output is not None else None,
                            "generation_seconds": output.generation_seconds if output is not None else None,
                            "wall_seconds": wall_seconds,
                            "tokens_per_second": output.tokens_per_second if output is not None else None,
                            "retries": retries,
                            "error": error,
                            "actual_cost": None,
                        },
                    }
                    candidates.append(candidate)
                    conversation.append({"role": "assistant", "text": normalized})
    return candidates, runtime_by_teacher


def _adapter(teacher: dict[str, Any], generation: dict[str, Any]) -> MlxModelAdapter:
    return MlxModelAdapter(
        model_id=teacher["model_id"],
        revision=teacher["revision"],
        tokenizer_revision=teacher["tokenizer_revision"],
        base_or_instruct="post-trained chat/instruct",
        parameter_count_billions=teacher["parameter_count_billions"],
        context_length=40960,
        weights_modified=False,
        checkpoint_selection="none; pinned before rendering bake-off",
        max_tokens=generation["max_output_tokens"],
        temperature=generation["temperature"],
        enable_thinking=generation["enable_thinking"],
        seed=generation["seed"],
        dtype=teacher["dtype"],
        quantization=teacher["quantization"],
    )


def _revalidate_candidates(
    candidates: list[dict[str, Any]],
    golden: list[dict[str, Any]],
    references: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    golden_by_id = {item["golden_case_id"]: item for item in golden}
    reference_by_id = {item["golden_case_id"]: item for item in references}
    candidate_index = {
        (item["configuration_id"], item["golden_case_id"], item["assistant_turn_index"]): item
        for item in candidates
    }
    revalidated = []
    for candidate in candidates:
        case_id = candidate["golden_case_id"]
        turn_index = candidate["assistant_turn_index"]
        source_turn = next(
            item
            for item in golden_by_id[case_id]["trajectory"]["interaction"]["turns"]
            if item["turn_index"] == turn_index
        )
        semantics = ExpectedAssistantSemantics.from_dict(source_turn["expected_assistant_semantics"])
        context = []
        for turn in reference_by_id[case_id]["turns"]:
            if turn["turn_index"] >= turn_index:
                break
            if turn["role"] == "user":
                context.append({"role": "user", "text": turn["text"]})
            else:
                earlier = candidate_index[(candidate["configuration_id"], case_id, turn["turn_index"])]
                context.append({"role": "assistant", "text": earlier["candidate_text"]})
        validation = validate_natural_rendering(
            candidate["candidate_text"],
            semantics,
            visible_context="\n".join(item["text"] for item in context),
        )
        updated = dict(candidate)
        updated["validation"] = validation.to_dict()
        updated["status"] = (
            "PROPOSED_FOR_HUMAN_REVIEW"
            if validation.semantic_pass
            else "REJECTED_BY_DETERMINISTIC_VALIDATION"
        )
        revalidated.append(updated)
    return revalidated


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _generate_with_one_empty_retry(adapter: MlxModelAdapter, prompt: str):
    retries = 0
    error = None
    started = time.perf_counter()
    output = None
    for attempt in range(2):
        try:
            output = adapter.generate(prompt)
            if output.text.strip():
                break
            error = "empty output"
        except Exception as exc:  # pragma: no cover - hardware/runtime evidence path
            error = f"{type(exc).__name__}: {exc}"
        if attempt == 0:
            retries = 1
    wall_seconds = time.perf_counter() - started
    return output, retries, error, wall_seconds


def _summarize(
    config: dict[str, Any],
    candidates: list[dict[str, Any]],
    runtime_by_teacher: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    configurations = []
    configuration_ids = sorted({item["configuration_id"] for item in candidates})
    for configuration_id in configuration_ids:
        items = [item for item in candidates if item["configuration_id"] == configuration_id]
        passed = [item for item in items if item["validation"]["semantic_pass"]]
        total_input = sum(item["metrics"]["input_tokens"] or 0 for item in items)
        total_output = sum(item["metrics"]["output_tokens"] or 0 for item in items)
        total_seconds = sum(item["metrics"]["generation_seconds"] or 0 for item in items)
        word_counts = [len(item["candidate_text"].split()) for item in items]
        configurations.append(
            {
                "configuration_id": configuration_id,
                "teacher_id": items[0]["teacher_id"],
                "prompt_strategy_id": items[0]["prompt_strategy_id"],
                "candidate_assistant_targets": len(items),
                "semantic_pass_count": len(passed),
                "semantic_pass_rate": len(passed) / len(items),
                "rejected_count": len(items) - len(passed),
                "retry_count": sum(item["metrics"]["retries"] for item in items),
                "obvious_hallucination_count": sum(bool(item["validation"]["obvious_hallucinations"]) for item in items),
                "acquisition_mode_error_count": sum(bool(item["validation"]["acquisition_mode_errors"]) for item in items),
                "premature_classification_count": sum(not item["validation"]["checks"]["no_premature_classification"] for item in items),
                "internal_terminology_count": sum(bool(item["validation"]["internal_terms"]) for item in items),
                "input_tokens": total_input,
                "output_tokens": total_output,
                "generation_seconds": total_seconds,
                "mean_generation_tokens_per_second": total_output / total_seconds if total_seconds else None,
                "mean_output_words": sum(word_counts) / len(word_counts),
                "actual_cost": None,
                "cost_note": config["provider"]["api_cost_note"],
                "naturalness_assessment": "REQUIRES_HUMAN_REVIEW",
                "rough_naturalness_observation": _NATURALNESS_OBSERVATIONS[configuration_id],
            }
        )
    return {
        "experiment_id": config["experiment_id"],
        "status": "PROPOSED_FOR_HUMAN_REVIEW",
        "semantic_source": config["semantic_source"],
        "configuration_count": len(configurations),
        "candidate_count": len(candidates),
        "runtime_by_teacher": runtime_by_teacher,
        "configurations": configurations,
        "recommendation": {
            "human_review_shortlist": ["qwen3-4b-4bit-local__strict-semantic-v1"],
            "approval": "NO_CURRENT_CONFIGURATION_READY_TO_FREEZE",
            "reason": "The shortlisted configuration had the highest deterministic semantic pass rate, but still failed insufficient-state content and urgent-first framing.",
            "next_step": "Refine a single prompt combining strict semantic coverage with the PHC reference format, then rerun the same 14 cases before any controlled corpus generation.",
        },
        "bulk_generation_ready": False,
        "cost_note": config["provider"]["api_cost_note"],
    }


def _render_review(
    config: dict[str, Any],
    golden: list[dict[str, Any]],
    references: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    reference_by_id = {item["golden_case_id"]: item for item in references}
    configuration_ids = [item["configuration_id"] for item in summary["configurations"]]
    lines = [
        "# EdgeIMCI rendering bake-off v1 — human review",
        "",
        "**Status:** `PROPOSED_FOR_HUMAN_REVIEW`",
        "",
        "These are conversion-acceptance cases, not a model-performance benchmark or SFT corpus. Structured golden trajectories remain the semantic source of truth.",
        "",
        "## Configuration summary",
        "",
        "| Configuration | Targets | Semantic pass | Rejected | Retries | Hallucination flags | Mode errors | Premature classification | Mean words | Generation seconds | Cost |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in summary["configurations"]:
        lines.append(
            f"| `{item['configuration_id']}` | {item['candidate_assistant_targets']} | "
            f"{item['semantic_pass_count']}/{item['candidate_assistant_targets']} ({item['semantic_pass_rate']:.1%}) | "
            f"{item['rejected_count']} | {item['retry_count']} | {item['obvious_hallucination_count']} | "
            f"{item['acquisition_mode_error_count']} | {item['premature_classification_count']} | "
            f"{item['mean_output_words']:.1f} | {item['generation_seconds']:.2f} | not measured (local inference) |"
        )
    lines.extend(["", "### Rough naturalness observations", ""])
    for item in summary["configurations"]:
        lines.append(f"- `{item['configuration_id']}`: {item['rough_naturalness_observation']}")
    recommendation = summary["recommendation"]
    lines.extend(
        [
            "",
            "### Recommendation",
            "",
            f"**Current approval decision:** `{recommendation['approval']}`",
            "",
            f"**Human-review shortlist:** `{', '.join(recommendation['human_review_shortlist'])}`",
            "",
            recommendation["reason"],
            "",
            f"**Next step:** {recommendation['next_step']}",
            "",
            "## Side-by-side cases",
            "",
        ]
    )
    for record in golden:
        case_id = record["golden_case_id"]
        reference = reference_by_id[case_id]
        reference_turns = {item["turn_index"]: item for item in reference["turns"]}
        lines.extend([f"### {case_id}", "", f"**Why:** {record['why']}", ""])
        for turn in record["trajectory"]["interaction"]["turns"]:
            turn_index = turn["turn_index"]
            if turn["visible_message"]["role"] == "user":
                lines.extend(
                    [
                        f"**Proposed user turn {turn_index}:** {reference_turns[turn_index]['text']}",
                        "",
                        f"*Language note:* {reference_turns[turn_index]['note']}",
                        "",
                    ]
                )
                continue
            structured = reference["structured_expected_behavior"][str(turn_index)]
            lines.extend(
                [
                    f"#### Assistant turn {turn_index}",
                    "",
                    f"**Structured expected behavior:** `{json.dumps(structured, sort_keys=True)}`",
                    "",
                    f"**Proposed reference:** {reference_turns[turn_index]['text']}",
                    "",
                    f"*Language note:* {reference_turns[turn_index]['note']}",
                    "",
                ]
            )
            for configuration_id in configuration_ids:
                candidate = next(
                    item
                    for item in candidates
                    if item["configuration_id"] == configuration_id
                    and item["golden_case_id"] == case_id
                    and item["assistant_turn_index"] == turn_index
                )
                verdict = "PASS" if candidate["validation"]["semantic_pass"] else "REJECT"
                errors = candidate["validation"]["missing_concepts"] + candidate["validation"]["unexpected_concepts"] + candidate["validation"]["acquisition_mode_errors"] + candidate["validation"]["obvious_hallucinations"]
                lines.extend(
                    [
                        f"**{configuration_id} — {verdict}:** {candidate['candidate_text'] or '[no output]' }",
                        "",
                        f"Validation notes: `{'; '.join(errors) if errors else 'none'}`",
                        "",
                    ]
                )
            lines.extend(
                [
                    "**Human-review fields**",
                    "",
                    "- Semantic faithfulness: `[ ] pass  [ ] issue`",
                    "- Naturalness: `[ ] good  [ ] revise`",
                    "- PHC suitability: `[ ] suitable  [ ] revise`",
                    "- Preferred output: `________________`",
                    "- Comments: `________________`",
                    "",
                ]
            )
        lines.extend(["---", ""])
    lines.extend(
        [
            "## Decision",
            "",
            "No configuration is approved automatically. Reviewers should use the deterministic verdicts as rejection guards, then judge naturalness and PHC suitability. Bulk generation remains blocked pending this review.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_fixed_source(config: dict[str, Any], golden: list[dict[str, Any]]) -> None:
    expected = config["semantic_source"]
    actual_sha256 = hashlib.sha256(DEFAULT_GOLDEN_PATH.read_bytes()).hexdigest()
    if actual_sha256 != expected["sha256"]:
        raise ValueError("golden semantic source checksum does not match pinned bake-off configuration")
    assistant_targets = sum(
        turn["expected_assistant_semantics"] is not None
        for record in golden
        for turn in record["trajectory"]["interaction"]["turns"]
    )
    if len(golden) != expected["case_count"] or assistant_targets != expected["assistant_target_count"]:
        raise ValueError("golden semantic source count does not match pinned bake-off configuration")
    for record in golden:
        metadata = record["trajectory"]["metadata"]
        for field in ("rule_set_id", "information_policy_id", "constraint_set_id"):
            if metadata[field] != expected[field]:
                raise ValueError(f"golden semantic source {field} drift")


def _validate_adapter_identity(adapter: MlxModelAdapter, teacher: dict[str, Any]) -> None:
    metadata = adapter.model_metadata
    for field, expected in (
        ("model_id", teacher["model_id"]),
        ("model_revision", teacher["revision"]),
        ("tokenizer_revision", teacher["tokenizer_revision"]),
        ("quantization", teacher["quantization"]),
    ):
        if metadata[field] != expected:
            raise ValueError(f"loaded teacher {field} does not match pinned configuration")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    main()
