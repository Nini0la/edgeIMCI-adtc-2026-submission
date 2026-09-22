#!/usr/bin/env python3
"""Reconstruct the public dataset view from surviving training-source records."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

FREE_FORM_SYSTEM_PROMPT = (
    "Respond in clear natural language. Be accurate about EdgeIMCI, preserve "
    "uncertainty and negation, stay within supported scope, and never claim "
    "autonomous clinical authority."
)
EXPECTED_BASE_TRAIN_SHA256 = "952a785b478654097bff3d643ca743d2d5a078de4f2c2e5b125f87b47dbab367"
EXPECTED_ADDITIONS_SHA256 = "5cf220a66fa2b7e31400f556838afb52be6958c55739215d1dd39b1dd602d3c0"
EXPECTED_VALIDATION_SHA256 = "76dc64d51f52a8ffbb7a10c5fd10a3fff770a7ee6847cf7fb62c9a00568a58c5"
FROZEN_TRAINING_INPUT_SHA256 = "95945aa2e451f67348f4600e57c17e4a4acd278f285f2f1fbea9df4b633805f7"
FROZEN_DATASET_MANIFEST_SHA256 = "0820f092ed585a46182e075477f9246917629061b03a3f57d92cb1087e303706"
REVIEW_TAG = "AI_CURATED_CLINICAL_REVIEW_PENDING"

COMPONENT_BY_RUN_ID = {
    "edge-imci-alpha3-gpt54-expansion-v2": "alpha3_gpt54_expansion_v2",
    "edge-imci-delta1-expansion-v3": "delta1_expansion_v3",
    "edge-imci-delta2-expansion-v4": "delta2_expansion_v4",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
            handle.write("\n")


def write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    try:
        pa = importlib.import_module("pyarrow")
        pq = importlib.import_module("pyarrow.parquet")
    except ImportError as exc:
        raise RuntimeError(
            "Parquet publication requires pyarrow; run with `uv run --with pyarrow`."
        ) from exc

    schema = pa.schema(
        [
            pa.field("component_id", pa.string()),
            pa.field("evaluation_suite", pa.string()),
            pa.field("example_id", pa.string()),
            pa.field("expected_route", pa.string()),
            pa.field("leakage_group_id", pa.string()),
            pa.field("lineage_parent_ids", pa.list_(pa.string())),
            pa.field(
                "messages",
                pa.list_(
                    pa.struct(
                        [
                            pa.field("content", pa.string()),
                            pa.field("role", pa.string()),
                        ]
                    )
                ),
            ),
            pa.field("mode", pa.string()),
            pa.field("partition", pa.string()),
            pa.field("review_tag", pa.string()),
            pa.field("semantic_parent_id", pa.string()),
            pa.field("source_case_id", pa.string()),
            pa.field("validation_status", pa.string()),
        ]
    )
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, path, compression="zstd")



def normalize_candidate(record: dict[str, Any]) -> dict[str, Any]:
    generation = record["provenance"]["input_generation"]
    run_id = generation["run_id"]
    component_id = COMPONENT_BY_RUN_ID[run_id]
    settings = generation["settings"]
    source_case_id = settings.get("source_case_id", record["semantic_parent_id"])
    return {
        "component_id": component_id,
        "example_id": record["example_id"],
        "leakage_group_id": record["leakage_group_id"],
        "lineage_parent_ids": [record["semantic_parent_id"]],
        "messages": [
            {"content": FREE_FORM_SYSTEM_PROMPT, "role": "system"},
            {"content": record["input"]["content"], "role": "user"},
            {"content": record["target"], "role": "assistant"},
        ],
        "mode": record["mode"],
        "partition": record["partition"],
        "review_tag": REVIEW_TAG,
        "semantic_parent_id": record["semantic_parent_id"],
        "source_case_id": source_case_id,
    }


def normalize_train_schema(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["evaluation_suite"] = None
    normalized["expected_route"] = None
    normalized["validation_status"] = None
    return normalized


def checked_copy(source: Path, destination: Path) -> dict[str, Any]:
    shutil.copyfile(source, destination)
    return {
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_root = args.source_root.resolve()
    output = args.output.resolve()
    if output.is_relative_to(source_root) or source_root.is_relative_to(output):
        raise ValueError("output must not overlap the source tree")
    if args.output.is_symlink() or output.exists():
        raise FileExistsError("output must be a new directory; existing paths are never removed")
    baseline_dir = source_root / "beta0_1k_multitask_v1"
    expansion_dir = source_root / "expansion_20260922"

    baseline_train = baseline_dir / "train.jsonl"
    validation = baseline_dir / "validation.jsonl"
    additions = expansion_dir / "addition_candidates.jsonl"
    expected_hashes = {
        baseline_train: EXPECTED_BASE_TRAIN_SHA256,
        validation: EXPECTED_VALIDATION_SHA256,
        additions: EXPECTED_ADDITIONS_SHA256,
    }
    for path in (*expected_hashes, baseline_dir / "manifest.json", expansion_dir / "manifest.json"):
        if not path.is_file():
            raise FileNotFoundError(f"missing required source file: {path}")
    try:
        importlib.import_module("pyarrow")
        importlib.import_module("pyarrow.parquet")
    except ImportError as exc:
        raise RuntimeError(
            "Parquet publication requires pyarrow; run with `uv run --with pyarrow`."
        ) from exc
    for path, expected in expected_hashes.items():
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"unexpected source hash for {path}: {actual} != {expected}")

    baseline_rows = load_jsonl(baseline_train)
    addition_rows = load_jsonl(additions)
    normalized_additions = [normalize_candidate(row) for row in addition_rows]
    train_rows = [
        normalize_train_schema(row) for row in baseline_rows + normalized_additions
    ]
    validation_rows = load_jsonl(validation)

    if len(baseline_rows) != 1831 or len(normalized_additions) != 427:
        raise ValueError("unexpected training-source record count")
    if len(train_rows) != 2258 or len(validation_rows) != 139:
        raise ValueError("unexpected packaged split count")
    if any(row["partition"] != "TRAIN" for row in train_rows):
        raise ValueError("TRAIN package contains a non-TRAIN record")
    if any(row["partition"] != "VALIDATION" for row in validation_rows):
        raise ValueError("VALIDATION package contains a non-VALIDATION record")

    example_ids = [row["example_id"] for row in train_rows]
    if len(example_ids) != len(set(example_ids)):
        raise ValueError("duplicate TRAIN example_id")
    train_leakage_groups = {row["leakage_group_id"] for row in train_rows}
    validation_leakage_groups = {row["leakage_group_id"] for row in validation_rows}
    overlap = sorted(train_leakage_groups & validation_leakage_groups)
    if overlap:
        raise ValueError(f"TRAIN/VALIDATION leakage-group overlap: {overlap[:5]}")

    output.mkdir(parents=True, exist_ok=False)
    data_dir = output / "data"
    provenance_dir = output / "provenance"
    data_dir.mkdir()
    provenance_dir.mkdir()

    packaged_train = data_dir / "train.jsonl"
    packaged_validation = data_dir / "validation.jsonl"
    write_jsonl(packaged_train, train_rows)
    write_jsonl(packaged_validation, validation_rows)
    parquet_train = data_dir / "train-00000-of-00001.parquet"
    parquet_validation = data_dir / "validation-00000-of-00001.parquet"
    write_parquet(parquet_train, train_rows)
    write_parquet(parquet_validation, validation_rows)

    copied_sources = {
        "provenance/build_dataset_package.py": checked_copy(
            Path(__file__).resolve(), provenance_dir / "build_dataset_package.py"
        ),
        "provenance/addition_candidates.jsonl": checked_copy(
            additions, provenance_dir / "addition_candidates.jsonl"
        ),
        "provenance/baseline_manifest.json": checked_copy(
            baseline_dir / "manifest.json", provenance_dir / "baseline_manifest.json"
        ),
        "provenance/expansion_manifest.json": checked_copy(
            expansion_dir / "manifest.json", provenance_dir / "expansion_manifest.json"
        ),
    }

    modes = Counter(row["mode"] for row in train_rows)
    components = Counter(row["component_id"] for row in train_rows)
    manifest = {
        "schema_version": "1.0.0",
        "release_id": "beta0_1k_multitask_enriched_2258_v1",
        "selected_model": "4B-alpha-second",
        "publication_status": "PREPARED_FOR_PUBLICATION",
        "review_tag": REVIEW_TAG,
        "clinical_review_complete": False,
        "clinical_use_authorized": False,
        "promotion_authorized": False,
        "split_policy": "PRESERVE_FROZEN_TRAIN_AND_VALIDATION_NO_RESHUFFLE_NO_RESPLIT",
        "test_partition_used": False,
        "frozen_training_release": {
            "manifest_sha256": FROZEN_DATASET_MANIFEST_SHA256,
            "train_rows": 2258,
            "train_sha256": FROZEN_TRAINING_INPUT_SHA256,
            "validation_rows": 139,
            "validation_sha256": EXPECTED_VALIDATION_SHA256,
        },
        "publication_view": {
            "description": (
                "Message-normalized publication view reconstructed from the frozen 1,831-row "
                "base release and the 427-record enrichment source."
            ),
            "train": {
                "path": "data/train.jsonl",
                "rows": len(train_rows),
                "bytes": packaged_train.stat().st_size,
                "sha256": sha256(packaged_train),
                "parquet_path": "data/train-00000-of-00001.parquet",
                "parquet_bytes": parquet_train.stat().st_size,
                "parquet_sha256": sha256(parquet_train),
            },
            "validation": {
                "path": "data/validation.jsonl",
                "rows": len(validation_rows),
                "bytes": packaged_validation.stat().st_size,
                "sha256": sha256(packaged_validation),
                "byte_identical_to_frozen_training_release": (
                    sha256(packaged_validation) == EXPECTED_VALIDATION_SHA256
                ),
                "parquet_path": "data/validation-00000-of-00001.parquet",
                "parquet_bytes": parquet_validation.stat().st_size,
                "parquet_sha256": sha256(parquet_validation),
            },
        },
        "composition": {
            "train_modes": dict(sorted(modes.items())),
            "train_components": dict(sorted(components.items())),
            "baseline_rows": len(baseline_rows),
            "enrichment_rows": len(normalized_additions),
        },
        "source_artifacts": copied_sources,
        "normalization": {
            "content_change": "NONE_TO_USER_OR_ASSISTANT_MESSAGE_TEXT",
            "free_form_system_prompt": FREE_FORM_SYSTEM_PROMPT,
            "metadata_change": (
                "Candidate-schema enrichment records normalized to the same message schema as "
                "the frozen baseline. Original candidate records are retained under provenance/."
            ),
        },
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    checksum_paths = [
        packaged_train,
        packaged_validation,
        parquet_train,
        parquet_validation,
        manifest_path,
        *(output / relative for relative in sorted(copied_sources)),
    ]
    checksum_file = output / "checksums.sha256"
    checksum_file.write_text(
        "".join(f"{sha256(path)}  {path.relative_to(output)}\n" for path in checksum_paths),
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
