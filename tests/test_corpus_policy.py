from __future__ import annotations

import pytest

from edge_imci.corpus_policy import (
    SELECTED_V0_ARCHIVE_MANIFEST,
    CorpusUse,
    assert_corpus_use_allowed,
    load_corpus_manifest,
)
from edge_imci.generation.golden import DEFAULT_GOLDEN_PATH
from edge_imci.generation.golden import load_golden_slice
from edge_imci.schemas.trajectory import CorpusRole


def test_selected_v0_archive_is_explicit_and_all_assets_exist() -> None:
    manifest = load_corpus_manifest()
    assert manifest["archive_id"] == "selected-v0-component-regression-archive-v1"
    assert manifest["lifecycle_status"] == "ARCHIVED"
    assert manifest["corpus_role"] == CorpusRole.LEGACY_SELECTED_V0_COMPONENT_REGRESSION.value
    root = SELECTED_V0_ARCHIVE_MANIFEST.resolve().parents[3]
    assert all((root / asset).is_file() for asset in manifest["assets"])
    assert not (root / "data" / "golden" / "golden_conversion_slice_v1.jsonl").exists()
    assert not (root / "data" / "golden" / "golden_conversion_slice_v1.yaml").exists()
    assert not (root / "data" / "golden" / "golden_reference_renderings_v1.jsonl").exists()


@pytest.mark.parametrize(
    "use",
    [
        CorpusUse.HOLISTIC_GENERATION,
        CorpusUse.PRODUCT_EVALUATION,
        CorpusUse.TEACHER_BAKEOFF,
        CorpusUse.TRAINING,
    ],
)
def test_selected_v0_archive_rejects_product_and_training_uses(use: CorpusUse) -> None:
    with pytest.raises(ValueError, match="is not eligible"):
        assert_corpus_use_allowed(DEFAULT_GOLDEN_PATH, use)
    with pytest.raises(ValueError, match="is not eligible"):
        load_golden_slice(corpus_use=use)


@pytest.mark.parametrize(
    "use",
    [CorpusUse.COMPONENT_REGRESSION, CorpusUse.HISTORICAL_REPRODUCTION],
)
def test_selected_v0_archive_allows_only_explicit_legacy_uses(use: CorpusUse) -> None:
    assert_corpus_use_allowed(DEFAULT_GOLDEN_PATH, use)


def test_product_golden_role_is_distinct_from_legacy_role() -> None:
    assert CorpusRole.HOLISTIC_PRODUCT_GOLDEN is not CorpusRole.LEGACY_SELECTED_V0_COMPONENT_REGRESSION
