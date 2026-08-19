"""Deterministic generation of controlled IMCI benchmark cases."""

from __future__ import annotations

import json
import random
from dataclasses import replace
from pathlib import Path
from typing import Any

from edge_imci.evaluation.reference import evaluate_case
from edge_imci.rules.loader import RuleSet, load_rule_set
from edge_imci.schemas.case import (
    ClinicalCase,
    ClinicalObservations,
    DehydrationObservations,
    DrinkingStatus,
    GeneralDangerSignObservations,
    GenerationCategory,
    GenerationMetadata,
    PatientFacts,
    RespiratoryObservations,
    SkinPinch,
    SourceProvenance,
)

GENERATOR_VERSION = "imci-generator-v0"
DEFAULT_SEED = 20240301
DEFAULT_BENCHMARK_PATH = Path(__file__).resolve().parents[3] / "data" / "benchmark" / "imci_v0.jsonl"

_DANGER_FIELDS = (
    "unable_to_drink_or_breastfeed",
    "vomits_everything",
    "had_convulsions",
    "lethargic_or_unconscious",
    "convulsing_now",
)


def complete_danger_signs(**overrides: bool | None) -> GeneralDangerSignObservations:
    values: dict[str, bool | None] = {field_name: False for field_name in _DANGER_FIELDS}
    values.update(overrides)
    return GeneralDangerSignObservations(**values)


def generate_cases(seed: int = DEFAULT_SEED, rule_set: RuleSet | None = None) -> list[ClinicalCase]:
    selected_rules = rule_set or load_rule_set()
    rng = random.Random(seed)
    cases: list[ClinicalCase] = []

    def add(
        case_id: str,
        *,
        age_months: int = 18,
        presentation: str,
        danger: GeneralDangerSignObservations | None = None,
        respiratory: RespiratoryObservations | None = None,
        dehydration: DehydrationObservations | None = None,
        categories: tuple[GenerationCategory, ...] = (GenerationCategory.NORMAL,),
        template_id: str,
        counterfactual_group: str | None = None,
    ) -> None:
        patient_facts = PatientFacts(
            age_months=age_months,
            has_cough_or_difficult_breathing=respiratory is not None,
            has_diarrhoea=dehydration is not None,
        )
        provisional = ClinicalCase(
            case_id=case_id,
            patient_facts=patient_facts,
            presentation=presentation,
            observations=ClinicalObservations(
                danger_signs=danger or complete_danger_signs(),
                respiratory=respiratory,
                dehydration=dehydration,
            ),
            known_missing_information=(),
            expected_result=None,
            provenance=SourceProvenance(
                document=selected_rules.document,
                edition=selected_rules.edition,
                source_pdf_pages=(),
                source_printed_pages=(),
                source_rule_ids=(),
            ),
            generation=GenerationMetadata(
                generator_version=GENERATOR_VERSION,
                seed=seed,
                categories=categories,
                template_id=template_id,
                counterfactual_group=counterfactual_group,
            ),
        )
        result = evaluate_case(provisional, selected_rules)
        relevant_rules = _relevant_rule_ids(provisional, result.fired_rule_ids, selected_rules)
        source_by_id = {rule.rule_id: rule.source for rule in selected_rules.rules}
        source_pdf_pages = tuple(sorted({source_by_id[rule_id]["source_pdf_page"] for rule_id in relevant_rules}))
        source_printed_pages = tuple(
            sorted(
                {source_by_id[rule_id]["source_printed_page"] for rule_id in relevant_rules},
                key=lambda page: int(page.split()[0]),
            )
        )
        cases.append(
            replace(
                provisional,
                known_missing_information=result.missing_required_observations,
                expected_result=result,
                provenance=SourceProvenance(
                    document=selected_rules.document,
                    edition=selected_rules.edition,
                    source_pdf_pages=source_pdf_pages,
                    source_printed_pages=source_printed_pages,
                    source_rule_ids=relevant_rules,
                ),
            )
        )

    for index, field_name in enumerate(_DANGER_FIELDS, start=1):
        twin = f"general-danger-{field_name}"
        add(
            f"gds_{index:02d}_base",
            presentation="A caregiver brings the child for assessment; no general danger sign is reported or observed.",
            categories=(GenerationCategory.NORMAL, GenerationCategory.COUNTERFACTUAL_TWIN),
            template_id="general-danger-base",
            counterfactual_group=twin,
        )
        add(
            f"gds_{index:02d}_positive",
            presentation=f"A caregiver brings the child for assessment; {field_name.replace('_', ' ')} is present.",
            danger=complete_danger_signs(**{field_name: True}),
            categories=(GenerationCategory.DANGER_SIGN, GenerationCategory.COUNTERFACTUAL_TWIN),
            template_id="general-danger-positive",
            counterfactual_group=twin,
        )

    threshold_rules = selected_rules.by_kind("fast_breathing_threshold")
    if len(threshold_rules) != 2:
        raise ValueError("imci-selected-v0 must define exactly two respiratory age thresholds")
    for threshold_rule in threshold_rules:
        age_range = threshold_rule.conditions["age_months"]
        age = age_range["gte"] + (age_range["lt"] - age_range["gte"]) // 2
        threshold = threshold_rule.conditions["respiratory_rate"]["gte"]
        for rate in (threshold - 1, threshold, threshold + 1):
            add(
                f"resp_boundary_{age:02d}m_{rate:02d}",
                age_months=age,
                presentation=f"The caregiver reports cough for three days. Respiratory rate is {rate} breaths per minute while calm.",
                respiratory=_resp(rate),
                categories=(GenerationCategory.BOUNDARY, GenerationCategory.COUNTERFACTUAL_TWIN),
                template_id="respiratory-threshold",
                counterfactual_group=f"resp-threshold-{age}m",
            )

    younger_rule, older_rule = sorted(threshold_rules, key=lambda rule: rule.conditions["age_months"]["gte"])
    transition_ages = (younger_rule.conditions["age_months"]["lt"] - 1, older_rule.conditions["age_months"]["gte"])
    transition_rate = (
        younger_rule.conditions["respiratory_rate"]["gte"] + older_rule.conditions["respiratory_rate"]["gte"]
    ) // 2
    for age in transition_ages:
        add(
            f"resp_age_transition_{age:02d}m",
            age_months=age,
            presentation=f"The caregiver reports cough for two days. Respiratory rate is {transition_rate} breaths per minute while calm.",
            respiratory=_resp(transition_rate),
            categories=(GenerationCategory.BOUNDARY, GenerationCategory.COUNTERFACTUAL_TWIN),
            template_id="respiratory-age-transition",
            counterfactual_group="resp-age-threshold-transition",
        )

    for chest_indrawing in (False, True):
        add(
            f"resp_chest_{str(chest_indrawing).lower()}",
            presentation="The child has cough and is calm during assessment.",
            respiratory=_resp(34, chest_indrawing=chest_indrawing),
            categories=(GenerationCategory.NORMAL, GenerationCategory.COUNTERFACTUAL_TWIN),
            template_id="respiratory-chest-indrawing",
            counterfactual_group="resp-chest-indrawing",
        )

    for stridor in (False, True):
        add(
            f"resp_stridor_{str(stridor).lower()}",
            presentation="The child has difficult breathing and is calm during assessment.",
            respiratory=_resp(34, stridor_when_calm=stridor),
            categories=(GenerationCategory.NORMAL, GenerationCategory.COUNTERFACTUAL_TWIN),
            template_id="respiratory-stridor",
            counterfactual_group="resp-stridor",
        )

    for case_id, age, rate, chest in (
        ("resp_normal_cold_infant", 4, 32, False),
        ("resp_normal_cold_child", 36, 34, False),
        ("resp_normal_fast_infant", 6, 55, False),
        ("resp_normal_chest_child", 30, 34, True),
    ):
        add(
            case_id,
            age_months=age,
            presentation="The caregiver reports cough. The child was calm for the respiratory assessment.",
            respiratory=_resp(rate, chest_indrawing=chest),
            template_id="respiratory-normal",
        )

    for index, field_name in enumerate(_DANGER_FIELDS, start=1):
        twin = f"resp-danger-{field_name}"
        add(
            f"resp_danger_{index:02d}_base",
            presentation="The child has cough and a respiratory rate of 34 breaths per minute while calm.",
            respiratory=_resp(34),
            categories=(GenerationCategory.NORMAL, GenerationCategory.COUNTERFACTUAL_TWIN),
            template_id="respiratory-danger-base",
            counterfactual_group=twin,
        )
        add(
            f"resp_danger_{index:02d}_positive",
            presentation=f"The child has cough; {field_name.replace('_', ' ')} is present.",
            danger=complete_danger_signs(**{field_name: True}),
            respiratory=_resp(34),
            categories=(GenerationCategory.DANGER_SIGN, GenerationCategory.COUNTERFACTUAL_TWIN),
            template_id="respiratory-danger-positive",
            counterfactual_group=twin,
        )

    respiratory_missing = (
        ("rate", RespiratoryObservations(None, False, False), complete_danger_signs()),
        ("chest", RespiratoryObservations(34, None, False), complete_danger_signs()),
        ("stridor", RespiratoryObservations(34, False, None), complete_danger_signs()),
        ("danger", _resp(34), complete_danger_signs(vomits_everything=None)),
    )
    for name, observations, danger in respiratory_missing:
        add(
            f"resp_missing_{name}",
            presentation="The child has cough, but a required assessment item was not recorded.",
            danger=danger,
            respiratory=observations,
            categories=(GenerationCategory.MISSING_INFORMATION,),
            template_id="respiratory-missing",
        )

    distractors = [
        "The family walked to the clinic this morning.",
        "The child is wearing a blue shirt.",
        "A sibling accompanied the caregiver.",
        "The caregiver brought the paper health card.",
    ]
    for index in range(4):
        detail = rng.choice(distractors)
        add(
            f"resp_distractor_{index + 1:02d}",
            age_months=8 if index % 2 == 0 else 24,
            presentation=f"The caregiver reports cough for three days. {detail}",
            respiratory=_resp(52 if index % 2 == 0 else 35),
            categories=(GenerationCategory.DISTRACTOR,),
            template_id="respiratory-distractor",
        )

    severe_variants = (
        (False, True, DrinkingStatus.POORLY, SkinPinch.NORMAL),
        (False, True, DrinkingStatus.NORMAL, SkinPinch.VERY_SLOWLY),
        (False, False, DrinkingStatus.POORLY, SkinPinch.VERY_SLOWLY),
        (True, True, DrinkingStatus.NORMAL, SkinPinch.NORMAL),
    )
    for index, (lethargic, sunken, drinking, pinch) in enumerate(severe_variants, start=1):
        add(
            f"dehyd_severe_{index:02d}",
            presentation="The caregiver reports diarrhoea. The dehydration assessment was completed.",
            danger=complete_danger_signs(lethargic_or_unconscious=lethargic),
            dehydration=_dehyd(False, sunken, drinking, pinch),
            template_id="dehydration-severe",
        )

    some_variants = (
        (True, True, DrinkingStatus.NORMAL, SkinPinch.NORMAL),
        (True, False, DrinkingStatus.EAGER_OR_THIRSTY, SkinPinch.NORMAL),
        (False, True, DrinkingStatus.NORMAL, SkinPinch.SLOWLY),
        (True, True, DrinkingStatus.EAGER_OR_THIRSTY, SkinPinch.SLOWLY),
    )
    for index, variant in enumerate(some_variants, start=1):
        add(
            f"dehyd_some_{index:02d}",
            presentation="The caregiver reports diarrhoea. The child was offered fluid during assessment.",
            dehydration=_dehyd(*variant),
            template_id="dehydration-some",
        )

    no_variants = (
        (False, False, DrinkingStatus.NORMAL, SkinPinch.NORMAL),
        (False, True, DrinkingStatus.NORMAL, SkinPinch.NORMAL),
        (True, False, DrinkingStatus.NORMAL, SkinPinch.NORMAL),
        (True, False, DrinkingStatus.POORLY, SkinPinch.NORMAL),
    )
    for index, variant in enumerate(no_variants, start=1):
        add(
            f"dehyd_none_{index:02d}",
            presentation="The caregiver reports diarrhoea. Fewer than two qualifying dehydration signs are present.",
            dehydration=_dehyd(*variant),
            template_id="dehydration-none",
        )

    dehydration_twins = (
        ("severe", _dehyd(False, True, DrinkingStatus.NORMAL, SkinPinch.NORMAL), _dehyd(False, True, DrinkingStatus.POORLY, SkinPinch.NORMAL)),
        ("some", _dehyd(True, False, DrinkingStatus.NORMAL, SkinPinch.NORMAL), _dehyd(True, False, DrinkingStatus.EAGER_OR_THIRSTY, SkinPinch.NORMAL)),
        ("drinking-switch", _dehyd(False, True, DrinkingStatus.EAGER_OR_THIRSTY, SkinPinch.NORMAL), _dehyd(False, True, DrinkingStatus.POORLY, SkinPinch.NORMAL)),
    )
    for name, first, second in dehydration_twins:
        for side, observations in (("a", first), ("b", second)):
            add(
                f"dehyd_twin_{name}_{side}",
                presentation="The caregiver reports diarrhoea. One dehydration observation differs from the paired case.",
                dehydration=observations,
                categories=(GenerationCategory.BOUNDARY, GenerationCategory.COUNTERFACTUAL_TWIN),
                template_id="dehydration-counterfactual",
                counterfactual_group=f"dehydration-{name}",
            )

    for index, field_name in enumerate(_DANGER_FIELDS, start=1):
        twin = f"dehydration-danger-{field_name}"
        add(
            f"dehyd_danger_{index:02d}_base",
            presentation="The caregiver reports diarrhoea. No dehydration signs or general danger signs are present.",
            dehydration=_dehyd(False, False, DrinkingStatus.NORMAL, SkinPinch.NORMAL),
            categories=(GenerationCategory.NORMAL, GenerationCategory.COUNTERFACTUAL_TWIN),
            template_id="dehydration-danger-base",
            counterfactual_group=twin,
        )
        drinking = DrinkingStatus.UNABLE if field_name == "unable_to_drink_or_breastfeed" else DrinkingStatus.NORMAL
        add(
            f"dehyd_danger_{index:02d}_positive",
            presentation=f"The caregiver reports diarrhoea; {field_name.replace('_', ' ')} is present.",
            danger=complete_danger_signs(**{field_name: True}),
            dehydration=_dehyd(False, False, drinking, SkinPinch.NORMAL),
            categories=(GenerationCategory.DANGER_SIGN, GenerationCategory.COUNTERFACTUAL_TWIN),
            template_id="dehydration-danger-positive",
            counterfactual_group=twin,
        )

    missing_variants = (
        ("severe_drinking", complete_danger_signs(), _dehyd(False, True, None, SkinPinch.NORMAL)),
        ("severe_skin", complete_danger_signs(lethargic_or_unconscious=True), _dehyd(False, False, DrinkingStatus.NORMAL, None)),
        ("some_eyes", complete_danger_signs(), _dehyd(True, None, DrinkingStatus.NORMAL, SkinPinch.NORMAL)),
        ("some_skin", complete_danger_signs(), _dehyd(False, False, DrinkingStatus.EAGER_OR_THIRSTY, None)),
        ("two_unknown", complete_danger_signs(), _dehyd(False, None, None, SkinPinch.NORMAL)),
        ("danger", complete_danger_signs(vomits_everything=None), _dehyd(False, False, DrinkingStatus.NORMAL, SkinPinch.NORMAL)),
    )
    for name, danger, observations in missing_variants:
        add(
            f"dehyd_missing_{name}",
            presentation="The caregiver reports diarrhoea, but a required assessment item was not recorded.",
            danger=danger,
            dehydration=observations,
            categories=(GenerationCategory.MISSING_INFORMATION,),
            template_id="dehydration-missing",
        )

    for index in range(4):
        detail = rng.choice(distractors)
        observations = severe_variants[0] if index % 2 == 0 else some_variants[0]
        add(
            f"dehyd_distractor_{index + 1:02d}",
            presentation=f"The caregiver reports diarrhoea. {detail}",
            danger=complete_danger_signs(lethargic_or_unconscious=observations[0] if index % 2 == 0 else False),
            dehydration=_dehyd(*observations),
            categories=(GenerationCategory.DISTRACTOR,),
            template_id="dehydration-distractor",
        )

    if not 50 <= len(cases) <= 100:
        raise AssertionError(f"development benchmark size must be 50–100, got {len(cases)}")
    if len({case.case_id for case in cases}) != len(cases):
        raise AssertionError("generated case IDs must be unique")
    return cases


def write_benchmark(path: str | Path = DEFAULT_BENCHMARK_PATH, seed: int = DEFAULT_SEED) -> list[ClinicalCase]:
    cases = generate_cases(seed)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(json.dumps(case.to_dict(), sort_keys=True) for case in cases) + "\n"
    output_path.write_text(content, encoding="utf-8")
    return cases


def load_benchmark(path: str | Path = DEFAULT_BENCHMARK_PATH) -> list[ClinicalCase]:
    with Path(path).open(encoding="utf-8") as handle:
        return [ClinicalCase.from_dict(json.loads(line)) for line in handle if line.strip()]


def _resp(
    respiratory_rate: int | None,
    chest_indrawing: bool | None = False,
    stridor_when_calm: bool | None = False,
) -> RespiratoryObservations:
    return RespiratoryObservations(respiratory_rate, chest_indrawing, stridor_when_calm)


def _dehyd(
    restless_or_irritable: bool | None,
    sunken_eyes: bool | None,
    drinking_status: DrinkingStatus | None,
    skin_pinch: SkinPinch | None,
) -> DehydrationObservations:
    return DehydrationObservations(restless_or_irritable, sunken_eyes, drinking_status, skin_pinch)


def _relevant_rule_ids(case: ClinicalCase, fired_rule_ids: tuple[str, ...], rule_set: RuleSet) -> tuple[str, ...]:
    if fired_rule_ids:
        return fired_rule_ids
    kinds: set[str] = {"danger_sign"}
    if case.patient_facts.has_cough_or_difficult_breathing:
        kinds.update({"fast_breathing_threshold", "respiratory_classification"})
    if case.patient_facts.has_diarrhoea:
        kinds.add("dehydration_classification")
    return tuple(rule.rule_id for rule in rule_set.rules if rule.kind in kinds)
