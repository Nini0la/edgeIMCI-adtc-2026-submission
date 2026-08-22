"""Mechanical lifecycle guardrails for archived and active corpora."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any


class CorpusUse(str, Enum):
    COMPONENT_REGRESSION = "COMPONENT_REGRESSION"
    HISTORICAL_REPRODUCTION = "HISTORICAL_REPRODUCTION"
    HOLISTIC_GENERATION = "HOLISTIC_GENERATION"
    PRODUCT_EVALUATION = "PRODUCT_EVALUATION"
    TEACHER_BAKEOFF = "TEACHER_BAKEOFF"
    TRAINING = "TRAINING"


ROOT = Path(__file__).resolve().parents[2]
SELECTED_V0_ARCHIVE_MANIFEST = ROOT / "data" / "archive" / "selected_v0" / "archive_manifest.json"


def load_corpus_manifest(path: str | Path = SELECTED_V0_ARCHIVE_MANIFEST) -> dict[str, Any]:
    """Load a versioned corpus lifecycle manifest."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def assert_corpus_use_allowed(
    corpus_path: str | Path,
    use: CorpusUse,
    *,
    manifest_path: str | Path = SELECTED_V0_ARCHIVE_MANIFEST,
) -> None:
    """Reject a use that the corpus lifecycle manifest does not permit.

    This guard is intentionally deterministic. It does not infer eligibility from a
    filename, documentation prose, or the caller's intent.
    """

    manifest_file = Path(manifest_path).resolve()
    manifest = load_corpus_manifest(manifest_file)
    repository_root = manifest_file.parents[3]
    registered_assets = {(repository_root / item).resolve() for item in manifest["assets"]}
    requested_path = Path(corpus_path)
    requested_asset = (requested_path if requested_path.is_absolute() else repository_root / requested_path).resolve()
    if requested_asset not in registered_assets:
        raise ValueError(f"Corpus asset is not registered by {manifest['archive_id']}: {requested_asset}")
    if not manifest["eligibility"].get(use.value, False):
        raise ValueError(
            f"Corpus {manifest['archive_id']} is {manifest['lifecycle_status']} and is not eligible for {use.value}"
        )
