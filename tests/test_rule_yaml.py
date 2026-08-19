from __future__ import annotations

import yaml

from edge_imci.evaluation.reference import evaluate_case
from edge_imci.generation.cases import load_benchmark
from edge_imci.rules.yaml_sync import (
    DEFAULT_YAML_RULE_PATH,
    load_canonical_rule_data,
    render_rule_yaml,
)


def test_generated_yaml_deserializes_to_canonical_json_rule_set():
    canonical = load_canonical_rule_data()
    yaml_text = DEFAULT_YAML_RULE_PATH.read_text(encoding="utf-8")

    assert yaml.safe_load(yaml_text) == canonical
    assert yaml_text == render_rule_yaml(canonical)


def test_yaml_mirror_preserves_all_committed_benchmark_oracle_outputs():
    cases = load_benchmark()

    assert len(cases) == 82
    for case in cases:
        assert case.expected_result is not None
        assert evaluate_case(case).to_dict() == case.expected_result.to_dict(), case.case_id
