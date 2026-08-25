"""Checksum-gated local Q8_0 extraction through llama.cpp."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
from threading import Lock
from typing import Any

from app.extractor.base import (
    AI_SERVICE_UNAVAILABLE_MESSAGE,
    INVALID_AI_INTERPRETATION_MESSAGE,
    ExtractionError,
    ExtractionResult,
)
from edge_imci.model_io.encounter import validate_model_facing_encounter


MODEL_FILENAME = "qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf"
MODEL_SHA256 = "26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2"
MODEL_SIZE_BYTES = 639_446_752
LLAMA_CPP_COMMIT = "aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3"
LLAMA_CPP_BUILD = "9637"
LLAMA_CPP_SHA256 = "a41d3d5fec1173afc89323a026a8f3612a9de2692a8c825223852627e8277641"
MAX_FINDINGS_CHARS = 2_000
SYSTEM_INSTRUCTION = (
    "Convert the PHC worker's findings into one JSON object matching the "
    "EdgeIMCI model-facing encounter schema. Preserve explicitly stated "
    "positives, negatives, measurements, durations, and qualifiers. Use null "
    "for UNKNOWN; never infer an unmentioned finding as negative. Output JSON only."
)
ROOT = Path(__file__).resolve().parents[2]
logger = logging.getLogger(__name__)
_INFERENCE_LOCK = Lock()


def _qwen3_prompt(free_text: str) -> str:
    """Render the frozen non-thinking Qwen3 chat prompt used during inference."""

    return (
        f"<|im_start|>system\n{SYSTEM_INSTRUCTION}<|im_end|>\n"
        f"<|im_start|>user\n{free_text}<|im_end|>\n"
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )


def _parse_json_object(raw_response: str) -> dict[str, Any]:
    """Parse exactly one strict JSON object and reject duplicate keys."""

    def pairs_to_dict(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number is not allowed: {value}")

    parsed = json.loads(
        raw_response,
        object_pairs_hook=pairs_to_dict,
        parse_constant=reject_constant,
    )
    if not isinstance(parsed, dict):
        raise ValueError("model target must be one JSON object")
    return parsed


class LlamaCppEncounterExtractor:
    """Run the selected GGUF locally and fail closed on invalid output."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        executable: str | None = None,
        *,
        max_tokens: int = 1200,
        context_size: int = 2048,
        threads: int | None = None,
        timeout_seconds: int = 180,
        invoke: Callable[[str], str] | None = None,
    ) -> None:
        self._max_tokens = max_tokens
        self._context_size = context_size
        self._threads = threads or int(os.environ.get("EDGEIMCI_THREADS", "2"))
        self._timeout_seconds = timeout_seconds
        self._invoke = invoke
        self._model_path = Path(
            model_path
            or os.environ.get("EDGEIMCI_MODEL_PATH", ROOT / "model" / MODEL_FILENAME)
        ).resolve()
        self._executable = executable or os.environ.get(
            "LLAMA_CPP_BIN", "llama-completion"
        )
        if invoke is None:
            self._verify_runtime()

    @property
    def mode_label(self) -> str:
        return "EdgeIMCI Qwen3-0.6B SFT / local Q8_0"

    def extract(self, free_text: str) -> ExtractionResult:
        text = free_text.strip()
        if not text:
            raise ExtractionError(
                "Enter the assessment findings before interpreting the encounter."
            )
        if len(text) > MAX_FINDINGS_CHARS:
            raise ExtractionError(
                "The assessment findings are too long for local interpretation."
            )
        if "<|im_start|>" in text or "<|im_end|>" in text:
            raise ExtractionError(INVALID_AI_INTERPRETATION_MESSAGE)

        try:
            with _INFERENCE_LOCK:
                raw_response = (
                    self._invoke(text)
                    if self._invoke is not None
                    else self._invoke_local(text)
                )
        except Exception as error:
            logger.exception("Local model inference request failed")
            raise ExtractionError(AI_SERVICE_UNAVAILABLE_MESSAGE) from error

        try:
            encounter = _parse_json_object(raw_response.strip())
            validate_model_facing_encounter(encounter)
        except Exception as error:
            logger.error("Local model output failed strict validation: %s", error)
            raise ExtractionError(INVALID_AI_INTERPRETATION_MESSAGE) from error

        return ExtractionResult(
            encounter=encounter,
            extraction_mode=self.mode_label,
            matched_case_id=None,
        )

    def _verify_runtime(self) -> None:
        if not self._model_path.is_file():
            raise FileNotFoundError(
                f"Model not found: {self._model_path}. Set EDGEIMCI_MODEL_PATH."
            )
        if self._model_path.stat().st_size != MODEL_SIZE_BYTES:
            raise ValueError(f"Model size does not match the selected artifact: {self._model_path}")

        digest = hashlib.sha256()
        with self._model_path.open("rb") as model_file:
            while chunk := model_file.read(1024 * 1024):
                digest.update(chunk)
        if digest.hexdigest() != MODEL_SHA256:
            raise ValueError(
                f"Model checksum does not match the selected artifact: {self._model_path}"
            )

        resolved_executable = shutil.which(self._executable)
        if resolved_executable is None:
            raise FileNotFoundError(
                f"llama.cpp executable not found: {self._executable}. Set LLAMA_CPP_BIN."
            )
        self._executable = resolved_executable

        executable_digest = hashlib.sha256()
        with Path(self._executable).open("rb") as executable_file:
            while chunk := executable_file.read(1024 * 1024):
                executable_digest.update(chunk)

        version = subprocess.run(
            [self._executable, "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
        version_output = f"{version.stdout}\n{version.stderr}"
        if (
            version.returncode != 0
            or LLAMA_CPP_COMMIT[:7] not in version_output
            or executable_digest.hexdigest() != LLAMA_CPP_SHA256
        ):
            raise ValueError(
                "llama.cpp executable is not the pinned b9637 target binary at "
                f"{LLAMA_CPP_COMMIT}"
            )

    def _invoke_local(self, free_text: str) -> str:
        completed = subprocess.run(
            [
                self._executable,
                "-m",
                str(self._model_path),
                "-p",
                _qwen3_prompt(free_text),
                "-n",
                str(self._max_tokens),
                "--temp",
                "0",
                "--seed",
                "0",
                "--no-display-prompt",
                "-no-cnv",
                "--simple-io",
                "--color",
                "off",
                "--offline",
                "--no-warmup",
                "-c",
                str(self._context_size),
                "-t",
                str(self._threads),
                "-tb",
                str(self._threads),
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=self._timeout_seconds,
        )
        if completed.returncode != 0:
            details = completed.stderr.strip().splitlines()
            reason = details[-1] if details else f"exit status {completed.returncode}"
            raise RuntimeError(f"llama.cpp inference failed: {reason}")
        response = completed.stdout.strip()
        terminal_marker = " [end of text]"
        if response.endswith(terminal_marker):
            response = response[: -len(terminal_marker)].rstrip()
        return response
