from __future__ import annotations

import json
from pathlib import Path

from edge_imci.evaluation.reporting import build_results_index


RESULTS_INDEX = Path("experiments/baselines/results_index.json")


def test_committed_real_results_index_is_deterministic_and_separated():
    committed = json.loads(RESULTS_INDEX.read_text())
    run_paths = [
        item["artifact_path"]
        for section in committed["sections"].values()
        for item in section
    ]

    assert build_results_index(run_paths) == committed
    assert committed["aggregation_policy"] == "sections are intentionally separate; no cross-benchmark overall score"
    assert "edge_imci_v0_development_regression" in committed["sections"]
    assert "lundin_current_07c6f0f::edge_imci_strict_external_eval" in committed["sections"]
    assert len(committed["sections"]) == 2
