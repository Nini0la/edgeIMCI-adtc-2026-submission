"""Deterministic reference evaluator for the selected IMCI pathways."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from edge_imci.rules.loader import Rule, RuleSet, load_rule_set
from edge_imci.schemas.case import (
    Action,
    Classification,
    ClinicalCase,
    DangerSign,
    EvaluationResult,
    Pathway,
    ReferralRequirement,
)


def evaluate_case(case: ClinicalCase, rule_set: RuleSet | None = None) -> EvaluationResult:
    """Evaluate a structured case without an LLM or probabilistic behavior."""
    selected_rules = rule_set or load_rule_set()
    classifications: dict[Pathway, Classification] = {}
    actions: set[Action] = set()
    fired_rule_ids: list[str] = []
    missing: set[str] = set()

    danger_signs, danger_missing, danger_rules = _evaluate_danger_signs(case, selected_rules)
    missing.update(danger_missing)
    for rule in danger_rules:
        fired_rule_ids.append(rule.rule_id)
        actions.update(Action(item) for item in rule.result["actions"])
    if danger_signs:
        classifications[Pathway.GENERAL_DANGER_SIGNS] = Classification.VERY_SEVERE_DISEASE

    if case.patient_facts.has_cough_or_difficult_breathing:
        respiratory = _evaluate_respiratory(case, selected_rules, danger_signs, danger_missing)
        if respiratory[0] is not None:
            rule, threshold_rule = respiratory[0]
            classifications[Pathway.RESPIRATORY] = Classification(rule.result["classification"])
            actions.update(Action(item) for item in rule.result["actions"])
            if threshold_rule is not None:
                fired_rule_ids.append(threshold_rule.rule_id)
            fired_rule_ids.append(rule.rule_id)
        missing.update(respiratory[1])

    if case.patient_facts.has_diarrhoea:
        dehydration = _evaluate_dehydration(case, selected_rules)
        if dehydration[0] is not None:
            rule = dehydration[0]
            classifications[Pathway.DEHYDRATION] = Classification(rule.result["classification"])
            other_severe = bool(danger_signs) or classifications.get(Pathway.RESPIRATORY) is Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE
            if "actions" in rule.result:
                configured_actions = rule.result["actions"]
            elif other_severe:
                configured_actions = rule.result["actions_with_other_severe_classification"]
            else:
                configured_actions = rule.result["actions_without_other_severe_classification"]
            actions.update(Action(item) for item in configured_actions)
            fired_rule_ids.append(rule.rule_id)
        missing.update(dehydration[1])

    ordered_actions = tuple(sorted(actions, key=lambda item: item.value))
    return EvaluationResult(
        detected_danger_signs=tuple(sorted(danger_signs, key=lambda item: item.value)),
        classifications=classifications,
        referral=ReferralRequirement.URGENT if Action.URGENT_REFERRAL in actions else ReferralRequirement.NONE,
        actions=ordered_actions,
        missing_required_observations=tuple(sorted(missing)),
        fired_rule_ids=tuple(dict.fromkeys(fired_rule_ids)),
    )


def _evaluate_danger_signs(
    case: ClinicalCase,
    rule_set: RuleSet,
) -> tuple[set[DangerSign], set[str], list[Rule]]:
    detected: set[DangerSign] = set()
    missing: set[str] = set()
    fired: list[Rule] = []
    for rule in rule_set.by_kind("danger_sign"):
        field_name = rule.conditions["field"]
        value = _field_value(case, field_name)
        if value is None:
            missing.add(field_name)
        elif value is rule.conditions["equals"]:
            detected.add(DangerSign(rule.result["danger_sign"]))
            fired.append(rule)
    return detected, missing, fired


def _evaluate_respiratory(
    case: ClinicalCase,
    rule_set: RuleSet,
    danger_signs: set[DangerSign],
    danger_missing: set[str],
) -> tuple[tuple[Rule, Rule | None] | None, set[str]]:
    respiratory = case.observations.respiratory
    if respiratory is None:
        return None, {"respiratory.respiratory_rate", "respiratory.chest_indrawing", "respiratory.stridor_when_calm"}

    classification_rules = rule_set.by_kind("respiratory_classification")
    if danger_signs:
        return (next(rule for rule in classification_rules if rule.conditions.get("any_general_danger_sign")), None), set()
    if danger_missing:
        return None, set(danger_missing)

    if respiratory.stridor_when_calm is None:
        return None, {"respiratory.stridor_when_calm"}
    if respiratory.stridor_when_calm:
        return (next(rule for rule in classification_rules if rule.conditions.get("field") == "respiratory.stridor_when_calm"), None), set()

    if respiratory.chest_indrawing is None:
        return None, {"respiratory.chest_indrawing"}
    if respiratory.chest_indrawing:
        return (next(rule for rule in classification_rules if rule.conditions.get("field") == "respiratory.chest_indrawing"), None), set()

    if respiratory.respiratory_rate is None:
        return None, {"respiratory.respiratory_rate"}
    threshold_rule = _fast_breathing_rule(case.patient_facts.age_months, rule_set)
    threshold = threshold_rule.conditions["respiratory_rate"]["gte"]
    if respiratory.respiratory_rate >= threshold:
        rule = next(rule for rule in classification_rules if rule.conditions.get("fast_breathing"))
        return (rule, threshold_rule), set()
    fallback = next(rule for rule in classification_rules if rule.conditions.get("fallback"))
    return (fallback, None), set()


def _fast_breathing_rule(age_months: int, rule_set: RuleSet) -> Rule:
    for rule in rule_set.by_kind("fast_breathing_threshold"):
        age = rule.conditions["age_months"]
        if age["gte"] <= age_months < age["lt"]:
            return rule
    raise ValueError(f"no respiratory threshold for age {age_months}")


def _evaluate_dehydration(case: ClinicalCase, rule_set: RuleSet) -> tuple[Rule | None, set[str]]:
    if case.observations.dehydration is None:
        return None, {
            "dehydration.restless_or_irritable",
            "dehydration.sunken_eyes",
            "dehydration.drinking_status",
            "dehydration.skin_pinch",
        }

    rules = rule_set.by_kind("dehydration_classification")
    for rule in rules:
        if rule.conditions.get("fallback"):
            return rule, set()
        states = [(sign["field"], _condition_state(case, sign)) for sign in rule.conditions["signs"]]
        true_count = sum(state is True for _, state in states)
        unknown_fields = {field_name for field_name, state in states if state is None}
        minimum_count = rule.conditions["minimum_count"]
        if true_count >= minimum_count:
            return rule, set()
        if true_count + len(unknown_fields) >= minimum_count:
            return None, unknown_fields
    raise ValueError("dehydration rule set has no fallback")


def _condition_state(case: ClinicalCase, condition: dict[str, Any]) -> bool | None:
    value = _field_value(case, condition["field"])
    if value is None:
        return None
    comparable = value.value if hasattr(value, "value") else value
    if "equals" in condition:
        return comparable == condition["equals"]
    return comparable in condition["in"]


def _field_value(case: ClinicalCase, field_name: str) -> Any:
    group, attribute = field_name.split(".", 1)
    if group == "danger_signs":
        target = case.observations.danger_signs
    elif group == "respiratory":
        target = case.observations.respiratory
    elif group == "dehydration":
        target = case.observations.dehydration
    else:
        raise ValueError(f"unsupported condition group: {group}")
    return None if target is None else getattr(target, attribute)


def referenced_rule_ids(results: Iterable[EvaluationResult]) -> set[str]:
    return {rule_id for result in results for rule_id in result.fired_rule_ids}
