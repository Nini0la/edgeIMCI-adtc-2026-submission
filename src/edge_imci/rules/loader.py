"""Load and minimally validate the selected IMCI rule set."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_RULE_PATH = Path(__file__).resolve().parents[3] / "data" / "rules" / "imci_selected_v0.json"


@dataclass(frozen=True)
class Rule:
    rule_id: str
    kind: str
    source: dict[str, Any]
    conditions: dict[str, Any]
    result: dict[str, Any]
    priority: int = 0


@dataclass(frozen=True)
class RuleSet:
    rule_set_id: str
    document: str
    edition: str
    rules: tuple[Rule, ...]

    def by_kind(self, kind: str) -> tuple[Rule, ...]:
        return tuple(sorted((rule for rule in self.rules if rule.kind == kind), key=lambda rule: rule.priority))

    def ids(self) -> frozenset[str]:
        return frozenset(rule.rule_id for rule in self.rules)


@lru_cache(maxsize=4)
def load_rule_set(path: str | Path = DEFAULT_RULE_PATH) -> RuleSet:
    rule_path = Path(path)
    with rule_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    required_top_level = {"rule_set_id", "document", "edition", "population", "rules"}
    missing = required_top_level - raw.keys()
    if missing:
        raise ValueError(f"rule set is missing keys: {sorted(missing)}")

    population = raw["population"]["age_months"]
    if population != {"gte": 2, "lt": 60}:
        raise ValueError("this evaluator only supports children aged 2 to under 60 months")

    rules: list[Rule] = []
    seen_ids: set[str] = set()
    for item in raw["rules"]:
        required = {"rule_id", "kind", "source", "conditions", "result"}
        missing = required - item.keys()
        if missing:
            raise ValueError(f"rule is missing keys: {sorted(missing)}")
        rule_id = item["rule_id"]
        if rule_id in seen_ids:
            raise ValueError(f"duplicate rule_id: {rule_id}")
        seen_ids.add(rule_id)
        source = item["source"]
        if not {"section", "source_pdf_page", "source_printed_page"} <= source.keys():
            raise ValueError(f"rule {rule_id} has incomplete provenance")
        rules.append(
            Rule(
                rule_id=rule_id,
                kind=item["kind"],
                source=source,
                conditions=item["conditions"],
                result=item["result"],
                priority=item.get("priority", 0),
            )
        )

    return RuleSet(
        rule_set_id=raw["rule_set_id"],
        document=raw["document"],
        edition=raw["edition"],
        rules=tuple(rules),
    )
