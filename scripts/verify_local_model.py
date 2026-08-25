"""Exercise public prompts through local Q8_0 extraction and existing logic."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from app.extractor.llama_cpp import MODEL_FILENAME, MODEL_SHA256, SYSTEM_INSTRUCTION
from app.extractor.llama_cpp import LlamaCppEncounterExtractor
from app.extractor.base import ExtractionResult
from app.service.service import evaluate_extracted_findings, extract_freeform_findings


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    prompts = json.loads(
        (ROOT / "acceptance" / "public_prompts.json").read_text(encoding="utf-8")
    )
    extractor = LlamaCppEncounterExtractor()
    outcomes: list[dict[str, object]] = []

    for test_prompt in prompts:
        findings = test_prompt["prompt"]
        if SYSTEM_INSTRUCTION in findings:
            raise ValueError(
                f"{test_prompt['prompt_id']} embeds the internal system instruction"
            )

        extraction = extractor.extract(findings)
        if extraction.encounter != test_prompt["expected_target"]:
            raise RuntimeError(
                f"{test_prompt['prompt_id']} did not exactly preserve the public findings"
            )

        class CapturedExtractor:
            mode_label = extractor.mode_label

            def extract(self, _: str) -> ExtractionResult:
                return extraction

        preview = extract_freeform_findings(findings, extractor=CapturedExtractor())
        if preview.error or not preview.schema_valid:
            raise RuntimeError(
                f"{test_prompt['prompt_id']} extraction failed: {preview.error}"
            )
        result = evaluate_extracted_findings(preview)
        if result.error or result.outside_supported_scope:
            raise RuntimeError(
                f"{test_prompt['prompt_id']} downstream evaluation failed: {result.error}"
            )
        if result.state != test_prompt["expected_state"]:
            raise RuntimeError(
                f"{test_prompt['prompt_id']} produced state {result.state}, "
                f"expected {test_prompt['expected_state']}"
            )

        outcomes.append(
            {
                "prompt_id": test_prompt["prompt_id"],
                "schema_valid": result.schema_valid,
                "state": result.state,
                "is_complete": result.is_complete,
                "is_urgent": result.is_urgent,
                "classifications": result.classifications,
                "structured_encounter": result.structured_encounter,
                "pipeline_trace": [asdict(step) for step in result.pipeline_trace],
            }
        )

    print(
        json.dumps(
            {
                "status": "PASS",
                "scope": "real-q8_0-public-prompts-and-deterministic-pipeline",
                "model_file": MODEL_FILENAME,
                "model_sha256": MODEL_SHA256,
                "outcomes": outcomes,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
