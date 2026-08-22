from __future__ import annotations

import json
from pathlib import Path

import pytest

from edge_imci.experiments.accounting import (
    append_accounting_record,
    combine_component_costs,
    derive_cost,
    load_rate_card,
)
from edge_imci.experiments.tracking import validate_run_sidecar
from tests.test_experiment_tracking import config, local_execution, tracker


def fictional_rate_card(tmp_path: Path, rate_class: str = "ESTIMATE_RATE") -> dict:
    card = {
        "schema_version": "1.0.0",
        "rate_card_id": "fictional-test-card",
        "version": "1.0.0",
        "provider": "fixture-provider",
        "service": "fixture-api",
        "currency": "USD",
        "effective_from": "2026-01-01",
        "effective_to": None,
        "region": "test",
        "deployment": "fake",
        "pricing_mode": "STANDARD",
        "rate_class": rate_class,
        "unit_rates": [
            {"metric": "input_tokens", "unit": "PER_1M", "price": "2.00"},
            {"metric": "output_tokens", "unit": "PER_1M", "price": "4.00"},
        ],
        "source": {"uri": "fixture://rate-card", "retrieved_at": "2026-01-01T00:00:00Z", "verified": True},
    }
    path = tmp_path / f"{rate_class}.json"
    path.write_text(json.dumps(card), encoding="utf-8")
    return load_rate_card(path)


def test_decimal_cost_and_normalized_api_reporting(tmp_path: Path) -> None:
    cost = derive_cost(
        {"input_tokens": 1_000_000, "output_tokens": 500_000},
        fictional_rate_card(tmp_path),
        calculation_id="estimate-v1",
        attempt_count=4,
        accepted_count=2,
    )
    assert cost["total"] == "4.00000000"
    assert cost["cost_per_attempt"] == "1.00000000"
    assert cost["cost_per_accepted_example"] == "2.00000000"
    assert cost["evidence_class"] == "ESTIMATE"


def test_accounting_reconciliation_appends_without_erasing_estimate(tmp_path: Path) -> None:
    output = tmp_path / "runs" / "accounting"
    with tracker(tmp_path).start(
        experiment_id="fake-ready-v1", output_dir=output, config=config(), execution=local_execution()
    ):
        pass
    sidecar = output / "edgeimci_run.json"
    estimate = derive_cost(
        {"input_tokens": 100}, fictional_rate_card(tmp_path), calculation_id="estimate-v1"
    )
    append_accounting_record(sidecar, estimate, actor="fixture-reviewer", occurred_at="2026-01-01T00:00:00Z")
    actual = derive_cost(
        {"input_tokens": 90},
        fictional_rate_card(tmp_path, "ACTUAL_RATE"),
        calculation_id="actual-v1",
    )
    append_accounting_record(
        sidecar,
        actual,
        reconciled_from_id="estimate-v1",
        actor="fixture-billing",
        occurred_at="2026-01-02T00:00:00Z",
    )
    record = validate_run_sidecar(sidecar)
    assert [item["calculation_id"] for item in record["accounting"]] == ["estimate-v1", "actual-v1"]
    assert record["accounting"][1]["reconciled_from_id"] == "estimate-v1"
    assert len(record["accounting_audit"]) == 2


def test_hybrid_cost_combines_each_component_once(tmp_path: Path) -> None:
    card = fictional_rate_card(tmp_path)
    api = derive_cost({"input_tokens": 1_000_000}, card, calculation_id="api")
    modal = derive_cost({"output_tokens": 1_000_000}, card, calculation_id="modal")
    combined = combine_component_costs([api, modal], calculation_id="hybrid")
    assert combined["total"] == "6.00000000"
    assert combined["component_calculation_ids"] == ["api", "modal"]
    with pytest.raises(ValueError, match="unique"):
        combine_component_costs([api, api], calculation_id="bad")
