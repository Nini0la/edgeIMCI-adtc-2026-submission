"""Pinned Lundin IMCI benchmark fetch, adaptation, and explicitly separated scoring policies."""

from __future__ import annotations

import hashlib
import json
import time
import ssl
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable
import certifi

from edge_imci.inference.adapters import ModelAdapter

DEFAULT_EXTERNAL_CONFIG = Path(__file__).resolve().parents[3] / "configs" / "external_benchmarks.json"
DEFAULT_EXTERNAL_CACHE = Path.home() / ".cache" / "edge-imci" / "external"
STRICT_PROMPT_VERSION = "edge-imci-external-mcq-strict-v1"
UPSTREAM_COMPAT_PROMPT_VERSION = "lundin-upstream-compatible-prompt-v1"
_STRICT_POLICY = "edge_imci_strict_external_eval"
_COMPAT_POLICY = "lundin_upstream_compat_eval"
_ANSWER_LETTERS = frozenset("ABCD")


@dataclass(frozen=True)
class ExternalBenchmarkSpec:
    benchmark_id: str
    repository_url: str
    revision: str
    questions_path: str
    questions_git_blob_oid: str
    questions_sha256: str
    questions_size_bytes: int
    question_count: int
    license_path: str
    license_sha256: str
    license_size_bytes: int
    license_spdx: str
    paper_url: str
    paper_license: str
    paper_version: str
    status_note: str

    @classmethod
    def from_dict(cls, benchmark_id: str, data: dict[str, Any]) -> "ExternalBenchmarkSpec":
        return cls(benchmark_id=benchmark_id, **data)

    def raw_url(self, path: str) -> str:
        repository = self.repository_url.removesuffix("/")
        owner_repo = repository.removeprefix("https://github.com/")
        return f"https://raw.githubusercontent.com/{owner_repo}/{self.revision}/{path}"


@dataclass(frozen=True)
class ExternalQuestion:
    question_id: int | str
    question: str
    answer: str
    label: str
    options: dict[str, str]
    correct_answer: str
    template_id: str
    graph_trace: Any = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExternalQuestion":
        required = {"id", "question", "answer", "label", "options", "correct_answer", "template_id"}
        missing = required - set(data)
        if missing:
            raise ValueError(f"external question missing fields: {sorted(missing)}")
        options = data["options"]
        if not isinstance(options, dict) or set(options) != _ANSWER_LETTERS:
            raise ValueError("external question options must contain exactly A, B, C, and D")
        if any(not isinstance(value, str) for value in options.values()):
            raise ValueError("external option values must be strings")
        correct_answer = data["correct_answer"]
        if correct_answer not in _ANSWER_LETTERS:
            raise ValueError(f"invalid external correct_answer: {correct_answer}")
        for field in ("question", "answer", "label", "template_id"):
            if not isinstance(data[field], str):
                raise ValueError(f"external question {field} must be a string")
        return cls(
            question_id=data["id"],
            question=data["question"],
            answer=data["answer"],
            label=data["label"],
            options={letter: options[letter] for letter in "ABCD"},
            correct_answer=correct_answer,
            template_id=data["template_id"],
            graph_trace=data.get("graph_trace"),
        )


@dataclass(frozen=True)
class ExternalAnswerParse:
    valid: bool
    answer: str | None
    error: str | None


def load_external_specs(path: str | Path = DEFAULT_EXTERNAL_CONFIG) -> dict[str, ExternalBenchmarkSpec]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {benchmark_id: ExternalBenchmarkSpec.from_dict(benchmark_id, data) for benchmark_id, data in raw.items()}


def fetch_external_benchmark(
    benchmark_id: str,
    cache_dir: str | Path = DEFAULT_EXTERNAL_CACHE,
    *,
    fetch_bytes: Callable[[str], bytes] | None = None,
    config_path: str | Path = DEFAULT_EXTERNAL_CONFIG,
) -> tuple[ExternalBenchmarkSpec, list[ExternalQuestion], Path]:
    specs = load_external_specs(config_path)
    try:
        spec = specs[benchmark_id]
    except KeyError as error:
        raise ValueError(f"unknown external benchmark: {benchmark_id}") from error
    downloader = fetch_bytes or _download
    destination = Path(cache_dir) / benchmark_id
    destination.mkdir(parents=True, exist_ok=True)
    questions_file = destination / "questions.json"
    license_file = destination / "LICENSE"
    questions_bytes = _cached_or_fetch(
        questions_file,
        spec.raw_url(spec.questions_path),
        spec.questions_sha256,
        spec.questions_size_bytes,
        downloader,
    )
    _cached_or_fetch(
        license_file,
        spec.raw_url(spec.license_path),
        spec.license_sha256,
        spec.license_size_bytes,
        downloader,
    )
    questions = load_external_questions(questions_bytes, expected_count=spec.question_count)
    (destination / "provenance.json").write_text(
        json.dumps(asdict(spec), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return spec, questions, destination


def load_external_questions(content: bytes, *, expected_count: int) -> list[ExternalQuestion]:
    try:
        raw = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"external questions are not valid UTF-8 JSON: {error}") from error
    if not isinstance(raw, list) or len(raw) != expected_count:
        actual = len(raw) if isinstance(raw, list) else "not-a-list"
        raise ValueError(f"external question count mismatch: expected {expected_count}, got {actual}")
    questions = [ExternalQuestion.from_dict(item) for item in raw]
    ids = [question.question_id for question in questions]
    if len(ids) != len(set(ids)):
        raise ValueError("external question IDs are not unique")
    return questions


def parse_strict_external_answer(raw_output: str) -> ExternalAnswerParse:
    stripped = raw_output.strip()
    if len(stripped) == 1 and stripped in _ANSWER_LETTERS:
        return ExternalAnswerParse(True, stripped, None)
    return ExternalAnswerParse(False, None, "expected exactly one uppercase letter A, B, C, or D")


def parse_upstream_compatible_answer(raw_output: str) -> ExternalAnswerParse:
    normalized = raw_output.strip().upper()
    for character in normalized:
        if character in _ANSWER_LETTERS:
            return ExternalAnswerParse(True, character, None)
    return ExternalAnswerParse(True, "A", "upstream fallback-to-A applied")


def build_external_prompt(question: ExternalQuestion, *, policy: str = _STRICT_POLICY) -> tuple[str, str]:
    options = "\n".join(f"{letter}) {question.options[letter]}" for letter in "ABCD")
    if policy == _STRICT_POLICY:
        prompt_version = STRICT_PROMPT_VERSION
        instruction = "Answer with exactly one uppercase letter: A, B, C, or D. Do not include explanation or punctuation."
    elif policy == _COMPAT_POLICY:
        prompt_version = UPSTREAM_COMPAT_PROMPT_VERSION
        instruction = "Please answer with only the letter (A, B, C, or D) that corresponds to the correct answer."
    else:
        raise ValueError(f"unknown external evaluation policy: {policy}")
    prompt = (
        "You are a medical expert answering questions about childhood illness management.\n\n"
        f"Question: {question.question}\n\n"
        f"Options:\n{options}\n\n"
        f"{instruction}\n\nAnswer:"
    )
    return prompt, prompt_version


def run_external_benchmark(
    questions: list[ExternalQuestion],
    spec: ExternalBenchmarkSpec,
    adapter: ModelAdapter,
    output_dir: str | Path,
    *,
    policy: str = _STRICT_POLICY,
) -> dict[str, Any]:
    if not questions:
        raise ValueError("external benchmark is empty")
    if policy not in {_STRICT_POLICY, _COMPAT_POLICY}:
        raise ValueError(f"unknown external evaluation policy: {policy}")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    per_case: list[dict[str, Any]] = []
    correct_count = 0
    denominator = 0
    invalid_count = 0
    generation_failure_count = 0
    total_latency_ms = 0.0
    label_totals: dict[str, dict[str, int]] = {}

    for question in questions:
        prompt, prompt_version = build_external_prompt(question, policy=policy)
        raw_output = ""
        parsed_answer: str | None = None
        parse_valid = False
        parse_error: str | None = None
        included_in_denominator = policy == _STRICT_POLICY
        input_token_count: int | None = None
        output_token_count: int | None = None
        throughput: float | None = None
        started = time.perf_counter_ns()
        try:
            generation = adapter.generate(prompt)
            raw_output = generation.text
            input_token_count = generation.input_token_count
            output_token_count = generation.output_token_count
            throughput = generation.tokens_per_second
            parsed = (
                parse_strict_external_answer(raw_output)
                if policy == _STRICT_POLICY
                else parse_upstream_compatible_answer(raw_output)
            )
            parse_valid = parsed.valid
            parsed_answer = parsed.answer
            parse_error = parsed.error
            included_in_denominator = True
            if not parsed.valid:
                invalid_count += 1
        except Exception as error:
            generation_failure_count += 1
            parse_error = f"{type(error).__name__}: {error}"
            if policy == _STRICT_POLICY:
                invalid_count += 1
        latency_ms = (time.perf_counter_ns() - started) / 1_000_000
        total_latency_ms += latency_ms
        is_correct = parse_valid and parsed_answer == question.correct_answer
        if included_in_denominator:
            denominator += 1
            correct_count += int(is_correct)
            label = label_totals.setdefault(question.label, {"correct": 0, "count": 0})
            label["count"] += 1
            label["correct"] += int(is_correct)
        per_case.append(
            {
                "question_id": question.question_id,
                "benchmark_id": spec.benchmark_id,
                "benchmark_revision": spec.revision,
                "evaluation_policy": policy,
                "prompt_version": prompt_version,
                "prompt": prompt,
                "raw_model_output": raw_output,
                "parsed_answer": parsed_answer,
                "parse_valid": parse_valid,
                "parse_error": parse_error,
                "expected_answer": question.correct_answer,
                "label": question.label,
                "template_id": question.template_id,
                "is_correct": is_correct,
                "included_in_denominator": included_in_denominator,
                "latency_ms": latency_ms,
                "input_token_count": input_token_count,
                "output_token_count": output_token_count,
                "generation_throughput_tokens_per_second": throughput,
            }
        )

    by_label = {
        label: {**counts, "accuracy": counts["correct"] / counts["count"]}
        for label, counts in sorted(label_totals.items())
    }
    prompt_version = STRICT_PROMPT_VERSION if policy == _STRICT_POLICY else UPSTREAM_COMPAT_PROMPT_VERSION
    artifact: dict[str, Any] = {
        "schema_version": "edge-imci-external-run-v1",
        "evaluation_kind": "external_mcqa",
        "evaluation_policy": policy,
        "policy_warning": (
            "EdgeIMCI strict scoring; not upstream or published-score reproduction"
            if policy == _STRICT_POLICY
            else "Upstream repository parser/denominator compatibility; not proven published-score reproduction"
        ),
        "benchmark_id": spec.benchmark_id,
        "benchmark_revision": spec.revision,
        "benchmark_questions_sha256": spec.questions_sha256,
        "question_count": len(questions),
        "model_identifier": adapter.model_id,
        "model_metadata": adapter.model_metadata,
        "runtime_metadata": adapter.runtime_metadata,
        "prompt_version": prompt_version,
        "correct_count": correct_count,
        "denominator": denominator,
        "accuracy": correct_count / denominator if denominator else None,
        "invalid_count": invalid_count,
        "invalid_rate": invalid_count / len(questions),
        "generation_failure_count": generation_failure_count,
        "by_label": by_label,
        "total_latency_ms": total_latency_ms,
        "per_case": per_case,
    }
    output_name = "strict_run.json" if policy == _STRICT_POLICY else "upstream_compat_run.json"
    (output_path / output_name).write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "edge-imci-benchmark-fetch/1"})
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=60, context=context) as response:
        return response.read()


def _cached_or_fetch(
    path: Path,
    url: str,
    expected_sha256: str,
    expected_size: int,
    fetch_bytes: Callable[[str], bytes],
) -> bytes:
    content = path.read_bytes() if path.exists() else fetch_bytes(url)
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if len(content) != expected_size or actual_sha256 != expected_sha256:
        raise ValueError(
            f"external asset integrity failure for {url}: expected size/sha256 "
            f"{expected_size}/{expected_sha256}, got {len(content)}/{actual_sha256}"
        )
    if not path.exists():
        path.write_bytes(content)
    return content
