from __future__ import annotations

import copy
import json
from dataclasses import replace

from edge_imci.generation.splits import (
    DEFAULT_CASES_PATH,
    DEFAULT_MANIFEST_PATH,
    build_demonstration_cases,
    build_split_manifest,
    find_leakage,
)
from edge_imci.generation.cases import load_benchmark


def test_committed_split_artifacts_are_deterministic_and_leakage_free():
    cases = build_demonstration_cases()
    manifest = build_split_manifest(cases)

    assert manifest == build_split_manifest(build_demonstration_cases())
    assert manifest == json.loads(DEFAULT_MANIFEST_PATH.read_text())
    assert [case.to_dict() for case in cases] == [case.to_dict() for case in load_benchmark(DEFAULT_CASES_PATH)]
    assert not find_leakage(cases, manifest)
    assert len({case.case_id for case in cases}) == len(cases)
    assert len({case.generation.seed for case in cases}) == len(cases)
    for regime in manifest["regimes"].values():
        assert all(regime["counts"][partition] > 0 for partition in ("training", "validation", "benchmark"))
        assert sum(regime["counts"].values()) == len(cases)


def test_template_and_challenge_families_are_wholly_held_out():
    cases = build_demonstration_cases()
    manifest = build_split_manifest(cases)
    by_id = {case.case_id: case for case in cases}

    template = manifest["regimes"]["template_shift"]
    train_templates = {by_id[case_id].generation.template_family for case_id in template["partitions"]["training"]}
    assert set(template["held_out_template_families"]).isdisjoint(train_templates)

    challenge = manifest["regimes"]["counterfactual_boundary_challenge"]
    train_groups = {
        by_id[case_id].generation.counterfactual_group_id
        for case_id in challenge["partitions"]["training"]
        if by_id[case_id].generation.counterfactual_group_id
    }
    assert set(challenge["held_out_challenge_group_ids"]).isdisjoint(train_groups)


def test_compositional_constituents_remain_in_training_but_combination_does_not():
    cases = build_demonstration_cases()
    manifest = build_split_manifest(cases)
    by_id = {case.case_id: case for case in cases}
    regime = manifest["regimes"]["compositional_holdout"]
    training = [by_id[case_id] for case_id in regime["partitions"]["training"]]
    training_signatures = {case.generation.logic_signature for case in training}
    training_rule_ids = {
        rule_id
        for case in training
        for rule_id in json.loads(case.generation.logic_signature)["fired_rule_ids"]
    }

    assert set(regime["held_out_logic_signatures"]).isdisjoint(training_signatures)
    assert set(regime["held_out_constituent_rule_ids"]) <= training_rule_ids


def test_duplicate_structured_case_and_presentation_are_detected():
    cases = build_demonstration_cases()
    manifest = build_split_manifest(cases)
    iid = manifest["regimes"]["iid_held_out"]["partitions"]
    training_case = next(case for case in cases if case.case_id == iid["training"][0])
    benchmark_case = next(case for case in cases if case.case_id == iid["benchmark"][0])
    contaminated = [
        replace(
            case,
            patient_facts=training_case.patient_facts,
            observations=training_case.observations,
            known_missing_information=training_case.known_missing_information,
            presentation=training_case.presentation,
        )
        if case.case_id == benchmark_case.case_id
        else case
        for case in cases
    ]

    kinds = {finding["kind"] for finding in find_leakage(contaminated, manifest) if finding["regime"] == "iid_held_out"}

    assert "structured_case" in kinds
    assert "normalized_presentation" in kinds


def test_counterfactual_group_and_case_id_overlap_are_detected():
    cases = build_demonstration_cases()
    manifest = build_split_manifest(cases)
    challenge = manifest["regimes"]["counterfactual_boundary_challenge"]["partitions"]
    benchmark_case = next(case for case in cases if case.case_id == challenge["benchmark"][0])
    training_id = challenge["training"][0]
    contaminated_cases = [
        replace(
            case,
            generation=replace(
                case.generation,
                counterfactual_group_id=benchmark_case.generation.counterfactual_group_id,
            ),
        )
        if case.case_id == training_id
        else case
        for case in cases
    ]
    contaminated_manifest = copy.deepcopy(manifest)
    contaminated_manifest["regimes"]["iid_held_out"]["partitions"]["training"].append(
        contaminated_manifest["regimes"]["iid_held_out"]["partitions"]["benchmark"][0]
    )

    group_kinds = {
        finding["kind"]
        for finding in find_leakage(contaminated_cases, manifest)
        if finding["regime"] == "counterfactual_boundary_challenge"
    }
    overlap_kinds = {
        finding["kind"]
        for finding in find_leakage(cases, contaminated_manifest)
        if finding["regime"] == "iid_held_out"
    }

    assert "counterfactual_group_id" in group_kinds
    assert "challenge_group_in_training" in group_kinds
    assert "case_id_overlap" in overlap_kinds
