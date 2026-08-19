"""Deterministic demonstration splits and leakage checks for future post-training data."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

from edge_imci.generation.cases import GENERATOR_VERSION, generate_cases
from edge_imci.rules.loader import load_rule_set
from edge_imci.schemas.case import ClinicalCase

SPLITTER_VERSION = "edge-imci-splitter-v1"
MANIFEST_VERSION = "edge-imci-split-demo-v1"
SPLIT_SEED = 20260819
DEFAULT_CASES_PATH = Path(__file__).resolve().parents[3] / "data" / "generated" / "split_demo_v1.jsonl"
DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parents[3] / "data" / "generated" / "split_manifest_v1.json"
_PARTITIONS = ("training", "validation", "benchmark")


def build_demonstration_cases() -> list[ClinicalCase]:
    """Create versioned split examples without declaring them a final benchmark corpus."""
    result: list[ClinicalCase] = []
    for index, case in enumerate(generate_cases(), start=1):
        group_id = case.generation.counterfactual_group_id
        result.append(
            replace(
                case,
                case_id=f"split_demo_{index:03d}_{case.case_id}",
                generation=replace(
                    case.generation,
                    seed=SPLIT_SEED + index,
                    counterfactual_group_id=f"split-demo:{group_id}" if group_id else None,
                ),
            )
        )
    return result


def build_split_manifest(cases: list[ClinicalCase]) -> dict[str, Any]:
    if not cases:
        raise ValueError("split corpus is empty")
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("split corpus contains duplicate case IDs")

    iid = _iid_regime(cases)
    template = _template_shift_regime(cases)
    compositional = _compositional_regime(cases)
    challenge = _challenge_regime(cases)
    serialized = _serialize_cases(cases)
    manifest: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "artifact_kind": "split-machinery-demonstration-not-final-benchmark",
        "rule_set_version": load_rule_set().rule_set_id,
        "generator_version": GENERATOR_VERSION,
        "splitter_version": SPLITTER_VERSION,
        "split_seed": SPLIT_SEED,
        "generation_seeds": sorted(case.generation.seed for case in cases),
        "corpus_case_count": len(cases),
        "corpus_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        "source_regression_set": {
            "benchmark_version": "edge-imci-development-regression-v0",
            "case_count": 82,
            "role": "development regression and diagnostics only",
            "permitted_for_training": False,
        },
        "partition_policy": {
            "training": "future post-training data only",
            "validation": "future hyperparameter and checkpoint selection only",
            "benchmark": "evaluation only; never training or hyperparameter selection",
        },
        "regimes": {
            "iid_held_out": iid,
            "template_shift": template,
            "compositional_holdout": compositional,
            "counterfactual_boundary_challenge": challenge,
        },
    }
    findings = find_leakage(cases, manifest)
    if findings:
        raise ValueError(f"generated split manifest leaks: {findings}")
    manifest["leakage_checks"] = {"status": "passed", "finding_count": 0}
    return manifest


def write_split_artifacts(
    cases_path: str | Path = DEFAULT_CASES_PATH,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
) -> tuple[list[ClinicalCase], dict[str, Any]]:
    cases = build_demonstration_cases()
    manifest = build_split_manifest(cases)
    cases_output = Path(cases_path)
    manifest_output = Path(manifest_path)
    cases_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    cases_output.write_text(_serialize_cases(cases), encoding="utf-8")
    manifest_output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return cases, manifest


def find_leakage(cases: list[ClinicalCase], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Return mechanically detected train/validation/benchmark contamination."""
    findings: list[dict[str, Any]] = []
    case_by_id = {case.case_id: case for case in cases}
    expected_ids = set(case_by_id)
    for regime_name, regime in manifest["regimes"].items():
        partitions = {name: set(regime["partitions"][name]) for name in _PARTITIONS}
        assigned = set().union(*partitions.values())
        if assigned != expected_ids:
            findings.append(
                {
                    "regime": regime_name,
                    "kind": "incomplete_case_assignment",
                    "missing": sorted(expected_ids - assigned),
                    "unknown": sorted(assigned - expected_ids),
                }
            )
        for left_index, left in enumerate(_PARTITIONS):
            for right in _PARTITIONS[left_index + 1 :]:
                overlap = sorted(partitions[left] & partitions[right])
                if overlap:
                    findings.append(
                        {"regime": regime_name, "kind": "case_id_overlap", "partitions": [left, right], "values": overlap}
                    )
        known_partitions = {
            partition: [case_by_id[case_id] for case_id in ids if case_id in case_by_id]
            for partition, ids in partitions.items()
        }
        findings.extend(_cross_partition_key_findings(regime_name, known_partitions, "structured_case", normalized_case_hash))
        findings.extend(
            _cross_partition_key_findings(regime_name, known_partitions, "normalized_presentation", normalized_presentation)
        )
        findings.extend(
            _cross_partition_key_findings(
                regime_name,
                known_partitions,
                "counterfactual_group_id",
                lambda case: case.generation.counterfactual_group_id,
            )
        )
        train_cases = known_partitions["training"]
        for field, attribute, finding_kind in (
            ("held_out_template_families", "template_family", "heldout_template_in_training"),
            ("held_out_logic_signatures", "logic_signature", "heldout_logic_signature_in_training"),
            ("held_out_challenge_group_ids", "counterfactual_group_id", "challenge_group_in_training"),
        ):
            held_out = set(regime.get(field, []))
            leaked = sorted(
                held_out & {getattr(case.generation, attribute) for case in train_cases if getattr(case.generation, attribute)}
            )
            if leaked:
                findings.append({"regime": regime_name, "kind": finding_kind, "values": leaked})
    return findings


def normalized_case_hash(case: ClinicalCase) -> str:
    data = case.to_dict(include_expected=False)
    normalized = {
        "patient_facts": data["patient_facts"],
        "observations": data["observations"],
        "known_missing_information": data["known_missing_information"],
    }
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def normalized_presentation(case: ClinicalCase) -> str:
    return re.sub(r"[^a-z0-9]+", " ", case.presentation.lower()).strip()


def _iid_regime(cases: list[ClinicalCase]) -> dict[str, Any]:
    groups = _components(cases)
    partitions = _partition_three_ways(groups, "iid")
    return _regime(
        "IID over newly identified latent case groups; no row-level random split",
        partitions,
    )


def _template_shift_regime(cases: list[ClinicalCase]) -> dict[str, Any]:
    groups = _components(cases, "template_family")
    ordered = _ordered_groups(groups, "template")
    benchmark_groups = _take_target(ordered, max(1, round(len(cases) * 0.2)))
    remaining = [group for group in ordered if group not in benchmark_groups]
    training, validation = _training_validation(remaining, "template-validation")
    partitions = {"training": training, "validation": validation, "benchmark": _case_ids(benchmark_groups)}
    held_out = sorted({case.generation.template_family for group in benchmark_groups for case in group})
    return _regime(
        "Template-family holdout; wording robustness, explicitly not IID generalization",
        partitions,
        held_out_template_families=held_out,
    )


def _compositional_regime(cases: list[ClinicalCase]) -> dict[str, Any]:
    groups = _ordered_groups(_components(cases, "logic_signature"), "compositional")
    benchmark_groups: list[list[ClinicalCase]] = []
    for group in groups:
        held_out_signatures = {case.generation.logic_signature for case in group}
        held_out_rules = set().union(*(_signature_rules(signature) for signature in held_out_signatures))
        remaining = [candidate for candidate in groups if candidate is not group]
        remaining_rules = set().union(*(_case_rules(case) for candidate in remaining for case in candidate))
        if len(held_out_rules) >= 2 and held_out_rules <= remaining_rules:
            benchmark_groups = [group]
            break
    if not benchmark_groups:
        raise ValueError("no mechanically valid compositional holdout exists")
    remaining = [group for group in groups if group not in benchmark_groups]
    validation_group = _safe_validation_group(remaining, benchmark_groups)
    validation_groups = [validation_group] if validation_group else []
    training_groups = [group for group in remaining if group is not validation_group]
    held_out = sorted({case.generation.logic_signature for group in benchmark_groups for case in group})
    constituent_rules = sorted(set().union(*(_signature_rules(signature) for signature in held_out)))
    partitions = {
        "training": _case_ids(training_groups),
        "validation": _case_ids(validation_groups),
        "benchmark": _case_ids(benchmark_groups),
    }
    return _regime(
        "Exact valid logic combinations held out while constituent fired rules remain in training",
        partitions,
        held_out_logic_signatures=held_out,
        held_out_constituent_rule_ids=constituent_rules,
    )


def _challenge_regime(cases: list[ClinicalCase]) -> dict[str, Any]:
    groups = _ordered_groups(_components(cases), "challenge")
    benchmark_groups = [group for group in groups if any(case.generation.counterfactual_group_id for case in group)]
    remaining = [group for group in groups if group not in benchmark_groups]
    training, validation = _training_validation(remaining, "challenge-validation")
    held_out = sorted(
        {
            case.generation.counterfactual_group_id
            for group in benchmark_groups
            for case in group
            if case.generation.counterfactual_group_id
        }
    )
    partitions = {"training": training, "validation": validation, "benchmark": _case_ids(benchmark_groups)}
    return _regime(
        "Whole counterfactual and clinical-boundary families held out from training",
        partitions,
        held_out_challenge_group_ids=held_out,
    )


def _regime(description: str, partitions: dict[str, list[str]], **held_out: Any) -> dict[str, Any]:
    return {
        "description": description,
        "partitions": partitions,
        "counts": {name: len(partitions[name]) for name in _PARTITIONS},
        **held_out,
    }


def _components(cases: list[ClinicalCase], *additional_keys: str) -> list[list[ClinicalCase]]:
    parent = {case.case_id: case.case_id for case in cases}

    def find(case_id: str) -> str:
        while parent[case_id] != case_id:
            parent[case_id] = parent[parent[case_id]]
            case_id = parent[case_id]
        return case_id

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    key_functions = [normalized_case_hash, normalized_presentation]
    key_functions.append(lambda case: case.generation.counterfactual_group_id)
    for key_name in additional_keys:
        key_functions.append(lambda case, name=key_name: getattr(case.generation, name))
    for key_function in key_functions:
        first_by_key: dict[str, str] = {}
        for case in cases:
            key = key_function(case)
            if key is None:
                continue
            if key in first_by_key:
                union(first_by_key[key], case.case_id)
            else:
                first_by_key[key] = case.case_id
    grouped: dict[str, list[ClinicalCase]] = defaultdict(list)
    for case in cases:
        grouped[find(case.case_id)].append(case)
    return [sorted(group, key=lambda case: case.case_id) for group in grouped.values()]


def _partition_three_ways(groups: list[list[ClinicalCase]], salt: str) -> dict[str, list[str]]:
    ordered = _ordered_groups(groups, salt)
    training_groups = _take_target(ordered, max(1, round(sum(map(len, ordered)) * 0.7)))
    remaining = [group for group in ordered if group not in training_groups]
    validation_groups = _take_target(remaining, max(1, round(sum(map(len, ordered)) * 0.15)))
    benchmark_groups = [group for group in remaining if group not in validation_groups]
    if not benchmark_groups:
        benchmark_groups = [validation_groups.pop()]
    return {
        "training": _case_ids(training_groups),
        "validation": _case_ids(validation_groups),
        "benchmark": _case_ids(benchmark_groups),
    }


def _training_validation(groups: list[list[ClinicalCase]], salt: str) -> tuple[list[str], list[str]]:
    ordered = _ordered_groups(groups, salt)
    if len(ordered) < 2:
        return _case_ids(ordered), []
    validation_groups = _take_target(ordered, max(1, round(sum(map(len, ordered)) * 0.15)))
    training_groups = [group for group in ordered if group not in validation_groups]
    return _case_ids(training_groups), _case_ids(validation_groups)


def _safe_validation_group(
    candidates: list[list[ClinicalCase]], benchmark_groups: list[list[ClinicalCase]]
) -> list[ClinicalCase] | None:
    required_rules = set().union(*(_case_rules(case) for group in benchmark_groups for case in group))
    for candidate in _ordered_groups(candidates, "compositional-validation"):
        training_cases = [case for group in candidates if group is not candidate for case in group]
        if required_rules <= set().union(*(_case_rules(case) for case in training_cases)):
            return candidate
    return None


def _take_target(groups: list[list[ClinicalCase]], target_cases: int) -> list[list[ClinicalCase]]:
    selected: list[list[ClinicalCase]] = []
    count = 0
    for group in groups:
        if count >= target_cases:
            break
        selected.append(group)
        count += len(group)
    return selected


def _ordered_groups(groups: list[list[ClinicalCase]], salt: str) -> list[list[ClinicalCase]]:
    return sorted(
        groups,
        key=lambda group: hashlib.sha256(
            f"{SPLIT_SEED}:{salt}:{','.join(case.case_id for case in group)}".encode("utf-8")
        ).hexdigest(),
    )


def _case_ids(groups: Iterable[list[ClinicalCase]]) -> list[str]:
    return sorted(case.case_id for group in groups for case in group)


def _signature_rules(signature: str) -> set[str]:
    return set(json.loads(signature)["fired_rule_ids"])


def _case_rules(case: ClinicalCase) -> set[str]:
    return _signature_rules(case.generation.logic_signature)


def _cross_partition_key_findings(
    regime_name: str,
    partitions: dict[str, list[ClinicalCase]],
    kind: str,
    key_function,
) -> list[dict[str, Any]]:
    locations: dict[str, set[str]] = defaultdict(set)
    for partition, cases in partitions.items():
        for case in cases:
            value = key_function(case)
            if value:
                locations[value].add(partition)
    return [
        {"regime": regime_name, "kind": kind, "partitions": sorted(parts), "value": value}
        for value, parts in sorted(locations.items())
        if len(parts) > 1
    ]


def _serialize_cases(cases: list[ClinicalCase]) -> str:
    return "\n".join(json.dumps(case.to_dict(), sort_keys=True) for case in cases) + "\n"
