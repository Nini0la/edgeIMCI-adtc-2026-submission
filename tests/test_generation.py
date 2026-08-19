from __future__ import annotations

from edge_imci.evaluation.reference import evaluate_case
from edge_imci.generation.cases import generate_cases, load_benchmark, write_benchmark
from edge_imci.rules.loader import load_rule_set
from edge_imci.schemas.case import GenerationCategory


def test_rule_set_is_explicit_unique_and_provenanced():
    rule_set = load_rule_set()

    assert len(rule_set.rules) == 15
    assert len(rule_set.ids()) == 15
    assert all(rule.source["source_pdf_page"] in {5, 6, 7} for rule in rule_set.rules)
    assert all(rule.source["source_printed_page"] in {"1 of 76", "2 of 76", "3 of 76"} for rule in rule_set.rules)
    assert all(rule.source["section"] for rule in rule_set.rules)


def test_generation_is_deterministic_and_within_development_size():
    first = generate_cases(seed=20240301)
    second = generate_cases(seed=20240301)

    assert len(first) == 82
    assert [case.to_dict() for case in first] == [case.to_dict() for case in second]
    assert len({case.case_id for case in first}) == len(first)


def test_generated_labels_come_from_reference_evaluator():
    for case in generate_cases():
        assert case.expected_result == evaluate_case(case)
        assert case.known_missing_information == case.expected_result.missing_required_observations


def test_cases_preserve_valid_rule_provenance():
    rule_ids = load_rule_set().ids()

    for case in generate_cases():
        assert case.provenance.document
        assert case.provenance.edition == "March 2014"
        assert case.provenance.source_pdf_pages
        assert case.provenance.source_printed_pages
        assert case.provenance.source_rule_ids
        assert set(case.provenance.source_rule_ids) <= rule_ids
        assert set(case.expected_result.fired_rule_ids) <= set(case.provenance.source_rule_ids)


def test_benchmark_covers_required_generation_categories():
    categories = {category for case in generate_cases() for category in case.generation.categories}

    assert categories == set(GenerationCategory)


def test_jsonl_round_trip(tmp_path):
    path = tmp_path / "benchmark.jsonl"

    written = write_benchmark(path)
    loaded = load_benchmark(path)

    assert loaded == written
