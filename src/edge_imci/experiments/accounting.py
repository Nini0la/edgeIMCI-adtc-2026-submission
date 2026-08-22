"""Versioned, decimal rate-card accounting derived from immutable raw usage."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Mapping

from edge_imci.experiments.provenance import atomic_write_json, hash_canonical
from edge_imci.experiments.registry import (
    SCHEMA_DIR,
    load_json_object,
    validate_against_schema,
)
from edge_imci.experiments.tracking import TERMINAL_STATUSES, validate_run_sidecar

CALCULATION_VERSION = "edgeimci-accounting-v1"
_DIVISORS = {
    "PER_UNIT": Decimal("1"),
    "PER_SECOND": Decimal("1"),
    "PER_1K": Decimal("1000"),
    "PER_1M": Decimal("1000000"),
}


def load_rate_card(path: str | Path) -> dict[str, Any]:
    card = load_json_object(path)
    validate_against_schema(card, SCHEMA_DIR / "rate_card.schema.json")
    metrics = [item["metric"] for item in card["unit_rates"]]
    if len(metrics) != len(set(metrics)):
        raise ValueError("rate card metrics must be unique")
    return card


def derive_cost(
    raw_metrics: Mapping[str, int | float | str | Decimal],
    rate_card: Mapping[str, Any],
    *,
    calculation_id: str,
    evidence_class: str | None = None,
    attempt_count: int | None = None,
    accepted_count: int | None = None,
    example_count: int | None = None,
) -> dict[str, Any]:
    """Calculate a reproducible cost record without mutating the raw usage."""
    validate_against_schema(dict(rate_card), SCHEMA_DIR / "rate_card.schema.json")
    lines: list[dict[str, str]] = []
    total = Decimal("0")
    for rate in rate_card["unit_rates"]:
        metric = rate["metric"]
        if metric not in raw_metrics:
            continue
        quantity = Decimal(str(raw_metrics[metric]))
        unit_price = Decimal(rate["price"])
        amount = quantity / _DIVISORS[rate["unit"]] * unit_price
        total += amount
        lines.append(
            {
                "metric": metric,
                "quantity": format(quantity, "f"),
                "unit": rate["unit"],
                "unit_price": format(unit_price, "f"),
                "amount": format(
                    amount.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_EVEN),
                    "f",
                ),
            }
        )
    rounded = total.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_EVEN)
    result: dict[str, Any] = {
        "calculation_id": calculation_id,
        "calculation_version": CALCULATION_VERSION,
        "evidence_class": evidence_class
        or ("ESTIMATE" if rate_card["rate_class"] == "ESTIMATE_RATE" else "ACTUAL"),
        "rate_card_id": rate_card["rate_card_id"],
        "rate_card_version": rate_card["version"],
        "rate_card_sha256": hash_canonical(dict(rate_card)),
        "currency": rate_card["currency"],
        "line_items": lines,
        "total": format(rounded, "f"),
    }
    for name, count in (
        ("cost_per_attempt", attempt_count),
        ("cost_per_accepted_example", accepted_count),
    ):
        if count is not None:
            if count <= 0:
                raise ValueError(f"{name} denominator must be positive")
            result[name] = format(
                (total / Decimal(count)).quantize(Decimal("0.00000001")), "f"
            )
    if example_count is not None:
        if example_count <= 0:
            raise ValueError("example_count must be positive")
        result["cost_per_1000_examples"] = format(
            (total * Decimal("1000") / Decimal(example_count)).quantize(
                Decimal("0.00000001")
            ),
            "f",
        )
    return result


def append_accounting_record(
    sidecar_path: str | Path,
    calculation: Mapping[str, Any],
    *,
    reconciled_from_id: str | None = None,
    actor: str,
    occurred_at: str | None = None,
) -> dict[str, Any]:
    """Explicit audited exception to terminal immutability for billing evidence only."""
    path = Path(sidecar_path)
    record = validate_run_sidecar(path)
    if record["status"] not in TERMINAL_STATUSES:
        raise ValueError("accounting reconciliation applies only to terminal runs")
    ids = {item["calculation_id"] for item in record["accounting"]}
    if calculation["calculation_id"] in ids:
        raise ValueError("accounting calculation_id already exists")
    if reconciled_from_id is not None and reconciled_from_id not in ids:
        raise ValueError(
            "reconciled_from_id does not identify preserved accounting evidence"
        )
    item = dict(calculation)
    if reconciled_from_id:
        item["reconciled_from_id"] = reconciled_from_id
    record["accounting"].append(item)
    record["accounting_audit"].append(
        {
            "event": "ACCOUNTING_EVIDENCE_APPENDED",
            "calculation_id": item["calculation_id"],
            "reconciled_from_id": reconciled_from_id,
            "actor": actor,
            "occurred_at": occurred_at
            or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    )
    atomic_write_json(path, record)
    return record


def combine_component_costs(
    calculations: list[Mapping[str, Any]],
    *,
    calculation_id: str,
) -> dict[str, Any]:
    if len(
        {(item["currency"], item["calculation_id"]) for item in calculations}
    ) != len(calculations):
        raise ValueError("component calculations must be unique")
    currencies = {item["currency"] for item in calculations}
    if len(currencies) != 1:
        raise ValueError("hybrid cost components must use one currency")
    total = sum((Decimal(item["total"]) for item in calculations), Decimal("0"))
    return {
        "calculation_id": calculation_id,
        "calculation_version": CALCULATION_VERSION,
        "evidence_class": "COMBINED",
        "currency": next(iter(currencies)),
        "component_calculation_ids": [item["calculation_id"] for item in calculations],
        "total": format(total.quantize(Decimal("0.00000001")), "f"),
    }
