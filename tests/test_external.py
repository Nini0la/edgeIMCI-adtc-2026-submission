from __future__ import annotations

import hashlib
import json

import pytest

from edge_imci.evaluation.external import (
    ExternalBenchmarkSpec,
    ExternalQuestion,
    fetch_external_benchmark,
    load_external_specs,
    parse_strict_external_answer,
    parse_upstream_compatible_answer,
    run_external_benchmark,
)
from edge_imci.inference.adapters import GenerationOutput


def _question(question_id: int, *, label: str = "cond_symp", correct: str = "A") -> ExternalQuestion:
    return ExternalQuestion(
        question_id=question_id,
        question="Which option is correct?",
        answer="alpha",
        label=label,
        options={"A": "alpha", "B": "beta", "C": "gamma", "D": "delta"},
        correct_answer=correct,
        template_id="template-1",
    )


def _spec(question_count: int) -> ExternalBenchmarkSpec:
    return ExternalBenchmarkSpec(
        benchmark_id="fixture",
        repository_url="https://github.com/example/repository",
        revision="a" * 40,
        questions_path="questions.json",
        questions_git_blob_oid="b" * 40,
        questions_sha256="unused-in-runner",
        questions_size_bytes=0,
        question_count=question_count,
        license_path="LICENSE",
        license_sha256="unused-in-runner",
        license_size_bytes=0,
        license_spdx="MIT",
        paper_url="https://example.test/paper",
        paper_license="CC-BY-4.0",
        paper_version="v1",
        status_note="fixture",
    )


class _SequenceAdapter:
    model_id = "sequence-test"
    model_metadata = {"model_id": model_id, "revision": "fixture"}
    runtime_metadata = {"backend": "test"}

    def __init__(self, outputs):
        self._outputs = iter(outputs)

    def generate(self, prompt: str) -> GenerationOutput:
        output = next(self._outputs)
        if isinstance(output, Exception):
            raise output
        return GenerationOutput(output, input_token_count=10, output_token_count=1, generation_seconds=0.5)


def test_pinned_specs_keep_current_and_historical_versions_separate():
    specs = load_external_specs()

    assert specs["lundin_current_07c6f0f"].question_count == 432
    assert specs["lundin_arxiv_v1_d153120"].question_count == 438
    assert specs["lundin_current_07c6f0f"].revision != specs["lundin_arxiv_v1_d153120"].revision
    assert specs["lundin_arxiv_v1_d153120"].paper_version == "v1"


@pytest.mark.parametrize("raw", ["A", " B ", "C\n"])
def test_strict_external_parser_accepts_only_one_uppercase_letter(raw):
    assert parse_strict_external_answer(raw).valid


@pytest.mark.parametrize("raw", ["a", "Answer: A", "AB", "", "```A```", "."])
def test_strict_external_parser_rejects_ambiguous_or_malformed_answers(raw):
    parsed = parse_strict_external_answer(raw)

    assert not parsed.valid
    assert parsed.answer is None


def test_upstream_compatible_parser_is_explicitly_permissive():
    assert parse_upstream_compatible_answer("THE ANSWER IS C").answer == "A"
    fallback = parse_upstream_compatible_answer("xyz")
    assert fallback.answer == "A"
    assert fallback.error == "upstream fallback-to-A applied"


def test_strict_runner_keeps_invalid_and_failed_generations_in_denominator(tmp_path):
    questions = [_question(index) for index in range(4)]
    adapter = _SequenceAdapter(["A", "Answer: A", "a", RuntimeError("offline")])

    artifact = run_external_benchmark(questions, _spec(4), adapter, tmp_path)

    assert artifact["evaluation_policy"] == "edge_imci_strict_external_eval"
    assert artifact["denominator"] == 4
    assert artifact["correct_count"] == 1
    assert artifact["accuracy"] == 0.25
    assert artifact["invalid_count"] == 3
    assert artifact["generation_failure_count"] == 1
    assert all(record["included_in_denominator"] for record in artifact["per_case"])
    assert json.loads((tmp_path / "strict_run.json").read_text()) == artifact


def test_upstream_compatible_runner_keeps_its_denominator_semantics_separate(tmp_path):
    questions = [_question(1), _question(2)]
    adapter = _SequenceAdapter(["xyz", RuntimeError("provider failure")])

    artifact = run_external_benchmark(
        questions,
        _spec(2),
        adapter,
        tmp_path,
        policy="lundin_upstream_compat_eval",
    )

    assert artifact["denominator"] == 1
    assert artifact["correct_count"] == 1
    assert artifact["accuracy"] == 1.0
    assert artifact["generation_failure_count"] == 1
    assert not artifact["per_case"][1]["included_in_denominator"]
    assert "not proven published-score reproduction" in artifact["policy_warning"]


def test_fetch_verifies_hash_size_count_and_preserves_license(tmp_path):
    question_data = [
        {
            "id": 1,
            "question": "Question?",
            "answer": "alpha",
            "label": "cond_symp",
            "options": {"A": "alpha", "B": "beta", "C": "gamma", "D": "delta"},
            "correct_answer": "A",
            "template_id": "template-1",
        }
    ]
    questions_bytes = json.dumps(question_data).encode()
    license_bytes = b"fixture license\n"
    config = {
        "fixture": {
            "repository_url": "https://github.com/example/repository",
            "revision": "a" * 40,
            "questions_path": "questions.json",
            "questions_git_blob_oid": "b" * 40,
            "questions_sha256": hashlib.sha256(questions_bytes).hexdigest(),
            "questions_size_bytes": len(questions_bytes),
            "question_count": 1,
            "license_path": "LICENSE",
            "license_sha256": hashlib.sha256(license_bytes).hexdigest(),
            "license_size_bytes": len(license_bytes),
            "license_spdx": "MIT",
            "paper_url": "https://example.test/paper",
            "paper_license": "CC-BY-4.0",
            "paper_version": "v1",
            "status_note": "fixture",
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    def fetcher(url: str) -> bytes:
        return license_bytes if url.endswith("/LICENSE") else questions_bytes

    spec, questions, destination = fetch_external_benchmark(
        "fixture",
        tmp_path / "cache",
        fetch_bytes=fetcher,
        config_path=config_path,
    )

    assert spec.revision == "a" * 40
    assert [question.question_id for question in questions] == [1]
    assert (destination / "LICENSE").read_bytes() == license_bytes
    assert json.loads((destination / "provenance.json").read_text())["questions_sha256"] == config["fixture"]["questions_sha256"]


def test_fetch_rejects_content_that_does_not_match_the_pin(tmp_path):
    config = {
        "fixture": {
            "repository_url": "https://github.com/example/repository",
            "revision": "a" * 40,
            "questions_path": "questions.json",
            "questions_git_blob_oid": "b" * 40,
            "questions_sha256": "0" * 64,
            "questions_size_bytes": 1,
            "question_count": 1,
            "license_path": "LICENSE",
            "license_sha256": "0" * 64,
            "license_size_bytes": 1,
            "license_spdx": "MIT",
            "paper_url": "https://example.test/paper",
            "paper_license": "CC-BY-4.0",
            "paper_version": "v1",
            "status_note": "fixture",
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    with pytest.raises(ValueError, match="integrity failure"):
        fetch_external_benchmark(
            "fixture",
            tmp_path / "cache",
            fetch_bytes=lambda _: b"x",
            config_path=config_path,
        )
