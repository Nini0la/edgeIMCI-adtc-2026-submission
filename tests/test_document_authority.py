from __future__ import annotations

from pathlib import Path


DOCS = Path("docs")


def test_every_markdown_document_declares_authority_near_its_title() -> None:
    markdown_files = sorted(DOCS.glob("*.md"))
    assert markdown_files
    for path in markdown_files:
        opening = "\n".join(path.read_text(encoding="utf-8").splitlines()[:8])
        assert "**Authority:**" in opening, path
        assert "**Lifecycle:**" in opening, path


def test_document_control_index_defines_precedence_and_sync_relationships() -> None:
    index = (DOCS / "README.md").read_text(encoding="utf-8")
    for authority in (
        "NORMATIVE_CLINICAL_ARTIFACT",
        "APPROVED_DECISION_ARTIFACT",
        "APPROVED_PRODUCT_POLICY",
        "REVIEW_RECORD",
        "IMPLEMENTATION_REFERENCE",
        "WORKING_PLAN",
        "EXPLORATORY_NOTES",
        "HISTORICAL_ARCHIVE",
    ):
        assert authority in index
    assert "editing and synchronization—not clinical authority" in index
    assert "generated mirror" in index


def test_working_plans_notes_and_history_are_not_conflated() -> None:
    for name in (
        "experiment_operations_and_tracking_plan.md",
        "experimental_campaign_map.md",
        "synthetic_data_generation_experiment_plan.md",
    ):
        opening = (DOCS / name).read_text(encoding="utf-8").splitlines()[:8]
        assert "`WORKING_PLAN`" in "\n".join(opening)
    notes = (DOCS / "synthetic_data_generation_experiment_notes.md").read_text(encoding="utf-8")
    assert "`EXPLORATORY_NOTES`" in "\n".join(notes.splitlines()[:8])
    archived = (DOCS / "golden_slice_review_v1.md").read_text(encoding="utf-8")
    assert "`HISTORICAL_ARCHIVE`" in "\n".join(archived.splitlines()[:8])
