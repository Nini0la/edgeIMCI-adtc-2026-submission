"""Deterministic factory for the first tiny EdgeIMCI golden conversion slice."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from edge_imci.evaluation.reference import evaluate_case
from edge_imci.information_policy import (
    CONSTRAINT_SET_ID,
    POLICY_ID,
    evaluate_information_policy_observations,
    load_information_policy_artifacts,
)
from edge_imci.rules.loader import load_rule_set
from edge_imci.schemas.case import (
    Action,
    Classification,
    ClinicalCase,
    ClinicalObservations,
    DangerSign,
    DehydrationObservations,
    DrinkingStatus,
    GenerationCategory,
    GenerationMetadata,
    GeneralDangerSignObservations,
    Pathway,
    PatientFacts,
    ReferralRequirement,
    RespiratoryObservations,
    SkinPinch,
    SourceProvenance,
)
from edge_imci.schemas.trajectory import (
    CANONICAL_OBSERVATION_ORDER,
    TRAJECTORY_SCHEMA_VERSION,
    AssistantBehavior,
    BasisType,
    ClinicalTrajectory,
    ConversationRole,
    ConversationTurn,
    CorpusRole,
    DecisionStatus,
    EntryStatus,
    EvidenceValidityStatus,
    ExpectedAssistantSemantics,
    InformationPolicyResult,
    LatentClinicalCase,
    LatentObservation,
    ModelVisibleMessage,
    ObservationEvidence,
    ObservationId,
    ObservationValidity,
    PartialCaseState,
    PolicyProvenance,
    ScopeStatus,
    TrajectoryInteraction,
    TrajectoryMetadata,
)
from edge_imci.validation.golden import RoundTripValidation, validate_target_round_trip

GOLDEN_GENERATOR_VERSION = "golden-conversion-slice-v1"
GOLDEN_SEED = 20260820
DEFAULT_GOLDEN_PATH = Path(__file__).resolve().parents[3] / "data" / "golden" / "golden_conversion_slice_v1.jsonl"
DEFAULT_GOLDEN_YAML_PATH = Path(__file__).resolve().parents[3] / "data" / "golden" / "golden_conversion_slice_v1.yaml"
DEFAULT_REVIEW_PATH = Path(__file__).resolve().parents[3] / "docs" / "golden_slice_review_v1.md"

_DANGER_IDS = (
    ObservationId.DANGER_CONVULSING_NOW,
    ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS,
    ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED,
    ObservationId.DANGER_VOMITS_EVERYTHING,
    ObservationId.DANGER_HAD_CONVULSIONS,
)
_RESPIRATORY_IDS = (
    ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM,
    ObservationId.RESPIRATORY_CHEST_INDRAWING,
    ObservationId.RESPIRATORY_RATE,
)
_DEHYDRATION_IDS = (
    ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE,
    ObservationId.DEHYDRATION_SUNKEN_EYES,
    ObservationId.DEHYDRATION_DRINKING_STATUS,
    ObservationId.DEHYDRATION_SKIN_PINCH,
)
_BASELINE_IDS = (
    ObservationId.AGE_MONTHS,
    *_DANGER_IDS,
    ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING,
    ObservationId.HAS_DIARRHOEA,
)
_DANGER_ENUMS = {
    ObservationId.DANGER_CONVULSING_NOW: DangerSign.CONVULSING_NOW,
    ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS: DangerSign.LETHARGIC_OR_UNCONSCIOUS,
    ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED: DangerSign.UNABLE_TO_DRINK_OR_BREASTFEED,
    ObservationId.DANGER_VOMITS_EVERYTHING: DangerSign.VOMITS_EVERYTHING,
    ObservationId.DANGER_HAD_CONVULSIONS: DangerSign.HAD_CONVULSIONS,
}

_CLASSIFICATION_PHRASES = {
    (Pathway.GENERAL_DANGER_SIGNS, Classification.VERY_SEVERE_DISEASE): "The supported general danger-sign classification is very severe disease.",
    (Pathway.RESPIRATORY, Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE): "The supported respiratory classification is severe pneumonia or very severe disease.",
    (Pathway.RESPIRATORY, Classification.PNEUMONIA): "The supported respiratory classification is pneumonia.",
    (Pathway.RESPIRATORY, Classification.COUGH_OR_COLD): "The supported respiratory classification is cough or cold.",
    (Pathway.DEHYDRATION, Classification.SEVERE_DEHYDRATION): "The supported dehydration classification is severe dehydration.",
    (Pathway.DEHYDRATION, Classification.SOME_DEHYDRATION): "The supported dehydration classification is some dehydration.",
    (Pathway.DEHYDRATION, Classification.NO_DEHYDRATION): "The supported dehydration classification is no dehydration.",
}
_ACTION_PHRASES = {
    Action.COMPLETE_ASSESSMENT_QUICKLY: "Complete the supported assessment quickly.",
    Action.GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY: "Give the indicated pre-referral treatment immediately.",
    Action.PREVENT_LOW_BLOOD_SUGAR: "Prevent low blood sugar.",
    Action.KEEP_WARM: "Keep the child warm.",
    Action.URGENT_REFERRAL: "Arrange urgent referral.",
    Action.GIVE_DIAZEPAM_IF_CONVULSING_NOW: "Give diazepam because the child is convulsing now.",
    Action.GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC: "Give the first dose of an appropriate antibiotic.",
    Action.GIVE_ORAL_AMOXICILLIN_5_DAYS: "Give oral amoxicillin for 5 days.",
    Action.SOOTHE_THROAT_AND_RELIEVE_COUGH: "Soothe the throat and relieve the cough with a safe remedy.",
    Action.ADVISE_WHEN_TO_RETURN_IMMEDIATELY: "Advise the caregiver when to return immediately.",
    Action.FOLLOW_UP_3_DAYS: "Follow up in 3 days.",
    Action.FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING: "Follow up in 5 days if the child is not improving.",
    Action.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C: "Give Plan C fluid for severe dehydration.",
    Action.GIVE_FLUID_ZINC_AND_FOOD_PLAN_B: "Give Plan B fluid, zinc, and food.",
    Action.GIVE_FLUID_ZINC_AND_FOOD_PLAN_A: "Give Plan A fluid, zinc, and food.",
    Action.FREQUENT_ORS_SIPS_DURING_REFERRAL: "Give frequent sips of ORS during referral.",
    Action.CONTINUE_BREASTFEEDING: "Continue breastfeeding.",
}
_ACQUISITION_PHRASES = {
    ObservationId.AGE_MONTHS: "Confirm the child's age in completed months from the caregiver or record.",
    ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: "Ask the caregiver whether the child has cough or difficult breathing.",
    ObservationId.HAS_DIARRHOEA: "Ask the caregiver whether the child has diarrhoea.",
    ObservationId.DANGER_CONVULSING_NOW: "Observe whether the child is convulsing now.",
    ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS: "Observe whether the child is lethargic or unconscious.",
    ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED: "Ask the caregiver whether the child is unable to drink or breastfeed.",
    ObservationId.DANGER_VOMITS_EVERYTHING: "Ask the caregiver whether the child vomits everything.",
    ObservationId.DANGER_HAD_CONVULSIONS: "Ask the caregiver whether the child has had convulsions during this illness.",
    ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM: "When the child is calm, observe whether stridor is present.",
    ObservationId.RESPIRATORY_CHEST_INDRAWING: "When the child is calm, observe whether chest indrawing is present.",
    ObservationId.RESPIRATORY_RATE: "When the child is calm, count breaths for one full minute and report the respiratory rate.",
    ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE: "Observe whether the child is restless or irritable.",
    ObservationId.DEHYDRATION_SUNKEN_EYES: "Observe whether the child's eyes are sunken.",
    ObservationId.DEHYDRATION_DRINKING_STATUS: "Offer fluid and observe whether the child drinks normally, eagerly or thirstily, poorly, or is unable to drink.",
    ObservationId.DEHYDRATION_SKIN_PINCH: "Pinch the abdominal skin and observe how quickly it returns.",
}


@dataclass(frozen=True)
class GoldenCaseSpec:
    case_id: str
    why: str
    coverage: tuple[str, ...]
    latent_values: dict[ObservationId, Any]
    reveal_stages: tuple[tuple[ObservationId, ...], ...]
    template_family: str


@dataclass(frozen=True)
class AssistantTargetValidation:
    turn_index: int
    round_trip: RoundTripValidation

    def to_dict(self) -> dict[str, Any]:
        return {"turn_index": self.turn_index, "round_trip": self.round_trip.to_dict()}


@dataclass(frozen=True)
class GoldenRecord:
    golden_case_id: str
    why: str
    coverage: tuple[str, ...]
    trajectory: ClinicalTrajectory
    assistant_target_validations: tuple[AssistantTargetValidation, ...]
    review_flags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "golden_case_id": self.golden_case_id,
            "why": self.why,
            "coverage": list(self.coverage),
            "trajectory": self.trajectory.to_dict(),
            "assistant_target_validations": [item.to_dict() for item in self.assistant_target_validations],
            "review_flags": list(self.review_flags),
        }


class ConservativeGoldenRenderer:
    """Small controlled renderer with no paraphrase sampling."""

    renderer_id = "edge-imci-conservative-golden-renderer-v1"

    def render_reveal(self, evidence: tuple[ObservationEvidence, ...]) -> str:
        return " ".join(_reveal_sentence(item) for item in evidence)

    def render_assistant_target(self, semantics: ExpectedAssistantSemantics) -> str:
        sentences = []
        if semantics.urgent_action_required:
            sentences.append("Urgent action is required now.")
        sentences.append(
            {
                DecisionStatus.SUFFICIENT: "The available information is sufficient to determine the supported classification decision.",
                DecisionStatus.INSUFFICIENT: "More information is needed before the supported classification decision is determined.",
                DecisionStatus.BLOCKED: "The supported classification decision is blocked by unresolved evidence.",
            }[semantics.decision_status]
        )
        sentences.append(
            "The supported action set is determined."
            if semantics.action_set_sufficient
            else "The complete supported action set is not yet determined."
        )
        sentences.append(
            "The supported assessment is complete."
            if semantics.assessment_complete
            else "The supported assessment is not yet complete."
        )
        sentences.extend(_CLASSIFICATION_PHRASES[item] for item in semantics.classifications.items())
        sentences.extend(_ACTION_PHRASES[item] for item in semantics.actions)
        if semantics.decision_directed_acquisitions:
            requests = " ".join(_ACQUISITION_PHRASES[item.observation_id] for item in semantics.decision_directed_acquisitions)
            sentences.append(f"Acquire next: {requests}")
        if semantics.assessment_completion_acquisitions:
            requests = " ".join(_ACQUISITION_PHRASES[item.observation_id] for item in semantics.assessment_completion_acquisitions)
            sentences.append(f"Assessment still to complete: {requests}")
        if semantics.urgent_action_required and not semantics.assessment_complete:
            sentences.append("Do not delay the urgent actions while the supported assessment remains incomplete.")
        return " ".join(sentences)


def generate_golden_slice(seed: int = GOLDEN_SEED) -> list[GoldenRecord]:
    renderer = ConservativeGoldenRenderer()
    return [_build_record(spec, renderer, seed) for spec in _golden_specs()]

def write_golden_slice(
    output_path: str | Path = DEFAULT_GOLDEN_PATH,
    review_path: str | Path = DEFAULT_REVIEW_PATH,
    seed: int = GOLDEN_SEED,
    yaml_path: str | Path = DEFAULT_GOLDEN_YAML_PATH,
) -> list[GoldenRecord]:
    records = generate_golden_slice(seed)
    serialized_records = [record.to_dict() for record in records]
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in serialized_records),
        encoding="utf-8",
    )
    yaml_destination = Path(yaml_path)
    yaml_destination.parent.mkdir(parents=True, exist_ok=True)
    yaml_destination.write_text(
        yaml.safe_dump(serialized_records, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    review_destination = Path(review_path)
    review_destination.parent.mkdir(parents=True, exist_ok=True)
    review_destination.write_text(render_golden_review(records), encoding="utf-8")
    return records


def load_golden_slice(path: str | Path = DEFAULT_GOLDEN_PATH) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def render_golden_review(records: list[GoldenRecord]) -> str:
    lines = [
        "# EdgeIMCI golden conversion slice v1 — human/domain-expert review",
        "",
        "**Status:** Validation artifacts only. Not training data, not a benchmark, and not a bulk corpus.",
        "",
        f"**Pinned IDs:** `imci-selected-v0` / `{POLICY_ID}` / `{CONSTRAINT_SET_ID}`",
        "",
        f"**Records:** {len(records)}. Deterministic renderer: `{ConservativeGoldenRenderer.renderer_id}`. Seed: `{records[0].trajectory.metadata.generation_seed}`.",
        "",
        "The deterministic round trip checks controlled language and structured correspondence. It is not independent clinical proof; every record remains marked for human review.",
        "",
        "## Coverage summary",
        "",
    ]
    coverage = sorted({tag for record in records for tag in record.coverage})
    lines.extend(f"- `{item}`" for item in coverage)
    lines.extend(["", "## Cases", ""])
    for record in records:
        trajectory = record.trajectory
        lines.extend(
            [
                f"### {record.golden_case_id}",
                "",
                f"**Why:** {record.why}",
                "",
                f"**Coverage:** {', '.join(f'`{item}`' for item in record.coverage)}",
                "",
                f"**Flags:** {', '.join(f'`{item}`' for item in record.review_flags) or 'None'}",
                "",
                "**Latent clinical truth:**",
                "",
                _latent_summary(trajectory.latent_truth),
                "",
                "**Model-visible interaction and structured targets:**",
                "",
            ]
        )
        validations = {item.turn_index: item.round_trip for item in record.assistant_target_validations}
        states = {item.state_id: item for item in trajectory.states}
        for turn in trajectory.interaction.turns:
            role = turn.visible_message.role.value.upper()
            lines.extend([f"- **Turn {turn.turn_index} — {role}:** {turn.visible_message.content}"])
            if turn.expected_assistant_semantics is not None:
                semantics = turn.expected_assistant_semantics
                policy = states[turn.state_after_turn_id].policy_result
                validation = validations[turn.turn_index]
                lines.extend(
                    [
                        f"  - Policy: decision `{policy.supported_encounter_decision_status.value}`; actions sufficient `{policy.supported_encounter_action_set_sufficient}`; assessment complete `{policy.supported_encounter_assessment_complete}`; urgent `{policy.urgent_action_required}`.",
                        f"  - Classifications: `{_enum_mapping(semantics.classifications) or 'none'}`.",
                        f"  - Actions: `{', '.join(item.value for item in semantics.actions) or 'none'}`.",
                        f"  - Decision acquisitions: `{', '.join(item.observation_id.value for item in semantics.decision_directed_acquisitions) or 'none'}`.",
                        f"  - Assessment acquisitions: `{', '.join(item.observation_id.value for item in semantics.assessment_completion_acquisitions) or 'none'}`.",
                        f"  - Round trip: `{'PASS' if validation.deterministic_match else 'FAIL'}` via `{validation.validator_id}`; human review required `{validation.human_review_required}`.",
                    ]
                )
        lines.extend(["", "---", ""])
    lines.extend(
        [
            "## Review disposition",
            "",
            "All controlled-language round trips pass deterministically. No external LLM extractor was used. Domain-expert review should confirm naturalness, action phrasing, and that the controlled targets preserve the intended selected-scope meaning before controlled bulk generation.",
            "",
        ]
    )
    return "\n".join(lines)


def _build_record(
    spec: GoldenCaseSpec,
    renderer: ConservativeGoldenRenderer,
    seed: int,
) -> GoldenRecord:
    latent = _latent_case(spec)
    acquired: dict[ObservationId, ObservationEvidence] = {}
    states = []
    turns = []
    validations = []
    for stage_index, reveal_ids in enumerate(spec.reveal_stages):
        stage_evidence = tuple(_evidence(item, spec.latent_values[item]) for item in reveal_ids)
        for item in stage_evidence:
            acquired[item.observation_id] = item
        policy_result = evaluate_information_policy_observations(tuple(acquired.values()))
        state_id = f"{spec.case_id}-state-{stage_index}"
        state = PartialCaseState.from_observations(state_id, tuple(acquired.values()), policy_result)
        states.append(state)
        user_turn_index = len(turns)
        turns.append(
            ConversationTurn(
                turn_index=user_turn_index,
                visible_message=ModelVisibleMessage(
                    role=ConversationRole.USER,
                    content=renderer.render_reveal(stage_evidence),
                ),
                state_after_turn_id=state_id,
                revealed_observations=stage_evidence,
            )
        )
        semantics = _assistant_semantics(state)
        assistant_text = renderer.render_assistant_target(semantics)
        assistant_turn_index = len(turns)
        turns.append(
            ConversationTurn(
                turn_index=assistant_turn_index,
                visible_message=ModelVisibleMessage(
                    role=ConversationRole.ASSISTANT,
                    content=assistant_text,
                ),
                state_after_turn_id=state_id,
                expected_assistant_semantics=semantics,
            )
        )
        validations.append(
            AssistantTargetValidation(
                turn_index=assistant_turn_index,
                round_trip=validate_target_round_trip(assistant_text, semantics),
            )
        )
    final_semantics = turns[-1].expected_assistant_semantics
    terminal_state_id = states[-1].state_id if final_semantics and not (
        final_semantics.decision_directed_acquisitions or final_semantics.assessment_completion_acquisitions
    ) else None
    logic_signature = json.dumps(latent.oracle_result.to_dict(), sort_keys=True, separators=(",", ":"))
    trajectory = ClinicalTrajectory(
        trajectory_id=spec.case_id,
        latent_truth=latent,
        states=tuple(states),
        interaction=TrajectoryInteraction(turns=tuple(turns)),
        initial_state_id=states[0].state_id,
        terminal_state_id=terminal_state_id,
        metadata=TrajectoryMetadata(
            schema_version=TRAJECTORY_SCHEMA_VERSION,
            rule_set_id="imci-selected-v0",
            information_policy_id=POLICY_ID,
            constraint_set_id=CONSTRAINT_SET_ID,
            generator_version=GOLDEN_GENERATOR_VERSION,
            generation_seed=seed,
            rule_family=_rule_family(latent.oracle_result.classifications),
            logic_signature=logic_signature,
            template_family=spec.template_family,
            corpus_role=CorpusRole.GOLDEN_CONVERSION_SLICE,
        ),
    )
    unresolved = sorted(
        {
            question_id
            for state in states
            for question_id in state.policy_result.unresolved_question_ids
        }
    )
    flags = ["HUMAN_REVIEW_REQUIRED"]
    flags.extend(f"UNRESOLVED:{item}" for item in unresolved)
    if any(not item.round_trip.deterministic_match for item in validations):
        flags.append("ROUND_TRIP_FAILURE")
    return GoldenRecord(
        golden_case_id=spec.case_id,
        why=spec.why,
        coverage=spec.coverage,
        trajectory=trajectory,
        assistant_target_validations=tuple(validations),
        review_flags=tuple(flags),
    )


def _assistant_semantics(state: PartialCaseState) -> ExpectedAssistantSemantics:
    policy = state.policy_result
    classifications = {}
    possible_classifications = {}
    possible_rule_ids = set()
    exact_rule_sufficient = True
    for pathway_state in policy.pathway_states:
        if pathway_state.possible_classifications:
            possible_classifications[pathway_state.pathway] = pathway_state.possible_classifications
        if pathway_state.decision_status is DecisionStatus.SUFFICIENT and len(pathway_state.possible_classifications) == 1:
            classifications[pathway_state.pathway] = pathway_state.possible_classifications[0]
        possible_rule_ids.update(pathway_state.possible_fired_rule_ids)
        exact_rule_sufficient = exact_rule_sufficient and pathway_state.exact_rule_sufficient

    actions = policy.known_actions
    blocked_ids = tuple(
        item.observation_id
        for item in state.observations
        if item.acquired
        and item.validity.status is EvidenceValidityStatus.UNRESOLVED
        and item.observation_id in {request.observation_id for request in policy.decision_directed_acquisitions}
    )
    behaviors = []
    if policy.decision_directed_acquisitions or policy.assessment_completion_acquisitions:
        behaviors.append(AssistantBehavior.REQUEST_INFORMATION)
    if policy.urgent_action_required:
        behaviors.append(AssistantBehavior.EMIT_URGENT_ACTION)
    if classifications:
        behaviors.append(AssistantBehavior.EMIT_CLASSIFICATION)
    if actions:
        behaviors.append(AssistantBehavior.EMIT_ACTIONS)
    if policy.scope_status is ScopeStatus.OUT_OF_SCOPE:
        behaviors.append(AssistantBehavior.REPORT_OUT_OF_SCOPE)
    if policy.supported_encounter_decision_status is DecisionStatus.BLOCKED or blocked_ids:
        behaviors.append(AssistantBehavior.REPORT_BLOCKED)

    detected_danger_signs = tuple(
        _DANGER_ENUMS[item.observation_id]
        for item in state.observations
        if item.observation_id in _DANGER_ENUMS and item.knowledge_state.name == "KNOWN_PRESENT"
    )
    return ExpectedAssistantSemantics(
        behaviors=tuple(behaviors),
        scope_status=policy.scope_status,
        decision_status=policy.supported_encounter_decision_status,
        action_set_sufficient=policy.supported_encounter_action_set_sufficient,
        assessment_complete=policy.supported_encounter_assessment_complete,
        urgent_action_required=policy.urgent_action_required,
        exact_rule_sufficient=exact_rule_sufficient,
        detected_danger_signs=detected_danger_signs,
        classifications=classifications,
        possible_classifications=possible_classifications,
        referral=ReferralRequirement.URGENT if Action.URGENT_REFERRAL in actions else ReferralRequirement.NONE,
        actions=actions,
        possible_fired_rule_ids=tuple(sorted(possible_rule_ids)),
        decision_directed_acquisitions=policy.decision_directed_acquisitions,
        assessment_completion_acquisitions=policy.assessment_completion_acquisitions,
        blocked_observation_ids=blocked_ids,
        unresolved_question_ids=policy.unresolved_question_ids,
    )


def _evidence(observation_id: ObservationId, value: Any) -> ObservationEvidence:
    artifact = load_information_policy_artifacts().observations[observation_id]
    validity = ObservationValidity(
        status=EvidenceValidityStatus.VALID,
        child_calm=True if observation_id in _RESPIRATORY_IDS else None,
        counted_for_one_minute=True if observation_id is ObservationId.RESPIRATORY_RATE else None,
    )
    provenance = PolicyProvenance(
        basis=BasisType(artifact["basis"]),
        source_rule_ids=tuple(artifact.get("source_rule_ids", [])),
        source_pdf_pages=tuple(artifact.get("source_pdf_pages", [])),
        source_printed_pages=tuple(artifact.get("source_printed_pages", [])),
        policy_rule_ids=tuple(artifact.get("policy_rule_ids", [])),
    )
    return ObservationEvidence.known(observation_id, value, validity=validity, provenance=provenance)


def _latent_case(spec: GoldenCaseSpec) -> LatentClinicalCase:
    clinical_case = _clinical_case(spec.case_id, spec.latent_values)
    oracle_result = evaluate_case(clinical_case)
    rule_set = load_rule_set()
    source_rules = tuple(oracle_result.fired_rule_ids)
    source_pdf_pages = tuple(sorted({rule.source["source_pdf_page"] for rule in rule_set.rules if rule.rule_id in source_rules}))
    source_printed_pages = tuple(
        sorted({rule.source["source_printed_page"] for rule in rule_set.rules if rule.rule_id in source_rules})
    )
    return LatentClinicalCase(
        latent_case_id=f"latent-{spec.case_id}",
        observations=tuple(LatentObservation(item, spec.latent_values[item]) for item in CANONICAL_OBSERVATION_ORDER),
        scope_status=ScopeStatus.IN_SCOPE,
        oracle_result=oracle_result,
        provenance=SourceProvenance(
            document=rule_set.document,
            edition=rule_set.edition,
            source_pdf_pages=source_pdf_pages,
            source_printed_pages=source_printed_pages,
            source_rule_ids=source_rules,
        ),
    )


def _clinical_case(case_id: str, values: dict[ObservationId, Any]) -> ClinicalCase:
    has_respiratory = values[ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING]
    has_diarrhoea = values[ObservationId.HAS_DIARRHOEA]
    return ClinicalCase(
        case_id=case_id,
        patient_facts=PatientFacts(
            age_months=values[ObservationId.AGE_MONTHS],
            has_cough_or_difficult_breathing=has_respiratory,
            has_diarrhoea=has_diarrhoea,
        ),
        presentation="Structured golden latent truth.",
        observations=ClinicalObservations(
            danger_signs=GeneralDangerSignObservations(
                unable_to_drink_or_breastfeed=values[ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED],
                vomits_everything=values[ObservationId.DANGER_VOMITS_EVERYTHING],
                had_convulsions=values[ObservationId.DANGER_HAD_CONVULSIONS],
                lethargic_or_unconscious=values[ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS],
                convulsing_now=values[ObservationId.DANGER_CONVULSING_NOW],
            ),
            respiratory=RespiratoryObservations(
                respiratory_rate=values[ObservationId.RESPIRATORY_RATE],
                chest_indrawing=values[ObservationId.RESPIRATORY_CHEST_INDRAWING],
                stridor_when_calm=values[ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM],
            ) if has_respiratory else None,
            dehydration=DehydrationObservations(
                restless_or_irritable=values[ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE],
                sunken_eyes=values[ObservationId.DEHYDRATION_SUNKEN_EYES],
                drinking_status=values[ObservationId.DEHYDRATION_DRINKING_STATUS],
                skin_pinch=values[ObservationId.DEHYDRATION_SKIN_PINCH],
            ) if has_diarrhoea else None,
        ),
        known_missing_information=(),
        expected_result=None,
        provenance=SourceProvenance(
            document="WHO Integrated Management of Childhood Illness, Chart Booklet",
            edition="March 2014",
            source_pdf_pages=(),
            source_printed_pages=(),
            source_rule_ids=(),
        ),
        generation=GenerationMetadata(
            generator_version=GOLDEN_GENERATOR_VERSION,
            seed=GOLDEN_SEED,
            categories=(GenerationCategory.NORMAL,),
            rule_family="golden",
            logic_signature=case_id,
            template_family="structured-first",
        ),
    )


def _reveal_sentence(record: ObservationEvidence) -> str:
    observation_id = record.observation_id
    value = record.value
    if observation_id is ObservationId.AGE_MONTHS:
        return f"The child is {value} months old."
    if observation_id is ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING:
        return "The caregiver reports cough or difficult breathing." if value else "The caregiver reports no cough or difficult breathing."
    if observation_id is ObservationId.HAS_DIARRHOEA:
        return "The caregiver reports diarrhoea." if value else "The caregiver reports no diarrhoea."
    if observation_id is ObservationId.DANGER_CONVULSING_NOW:
        return "On observation, the child is convulsing now." if value else "On observation, the child is not convulsing now."
    if observation_id is ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS:
        return "On observation, the child is lethargic or unconscious." if value else "On observation, the child is alert and not lethargic or unconscious."
    if observation_id is ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED:
        return "The caregiver says the child is unable to drink or breastfeed." if value else "The caregiver says the child can drink or breastfeed."
    if observation_id is ObservationId.DANGER_VOMITS_EVERYTHING:
        return "The caregiver says the child vomits everything." if value else "The caregiver says the child does not vomit everything."
    if observation_id is ObservationId.DANGER_HAD_CONVULSIONS:
        return "The caregiver reports convulsions during this illness." if value else "The caregiver reports no convulsions during this illness."
    if observation_id is ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM:
        return "When calm, the child has stridor." if value else "When calm, the child has no stridor."
    if observation_id is ObservationId.RESPIRATORY_CHEST_INDRAWING:
        return "When calm, chest indrawing is present." if value else "When calm, chest indrawing is absent."
    if observation_id is ObservationId.RESPIRATORY_RATE:
        return f"With the child calm, the respiratory rate counted for one full minute is {value} breaths per minute."
    if observation_id is ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE:
        return "The child is restless or irritable." if value else "The child is not restless or irritable."
    if observation_id is ObservationId.DEHYDRATION_SUNKEN_EYES:
        return "The child's eyes are sunken." if value else "The child's eyes are not sunken."
    if observation_id is ObservationId.DEHYDRATION_DRINKING_STATUS:
        return {
            DrinkingStatus.NORMAL: "When offered fluid, the child drinks normally.",
            DrinkingStatus.EAGER_OR_THIRSTY: "When offered fluid, the child drinks eagerly and appears thirsty.",
            DrinkingStatus.POORLY: "When offered fluid, the child drinks poorly.",
            DrinkingStatus.UNABLE: "When offered fluid, the child is unable to drink.",
        }[value]
    if observation_id is ObservationId.DEHYDRATION_SKIN_PINCH:
        return {
            SkinPinch.NORMAL: "The abdominal skin pinch returns normally.",
            SkinPinch.SLOWLY: "The abdominal skin pinch returns slowly.",
            SkinPinch.VERY_SLOWLY: "The abdominal skin pinch returns very slowly.",
        }[value]
    raise ValueError(f"unsupported reveal observation: {observation_id.value}")


def _base_values(**overrides: Any) -> dict[ObservationId, Any]:
    values = {
        ObservationId.AGE_MONTHS: 18,
        ObservationId.DANGER_CONVULSING_NOW: False,
        ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS: False,
        ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED: False,
        ObservationId.DANGER_VOMITS_EVERYTHING: False,
        ObservationId.DANGER_HAD_CONVULSIONS: False,
        ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: False,
        ObservationId.HAS_DIARRHOEA: False,
        ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM: False,
        ObservationId.RESPIRATORY_CHEST_INDRAWING: False,
        ObservationId.RESPIRATORY_RATE: 30,
        ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE: False,
        ObservationId.DEHYDRATION_SUNKEN_EYES: False,
        ObservationId.DEHYDRATION_DRINKING_STATUS: DrinkingStatus.NORMAL,
        ObservationId.DEHYDRATION_SKIN_PINCH: SkinPinch.NORMAL,
    }
    values.update(overrides)
    return values


def _golden_specs() -> tuple[GoldenCaseSpec, ...]:
    respiratory_complete = (*_BASELINE_IDS, *_RESPIRATORY_IDS)
    dehydration_complete = (*_BASELINE_IDS, *_DEHYDRATION_IDS)
    return (
        GoldenCaseSpec(
            "golden-complete-chest-pneumonia",
            "Complete single-turn respiratory case with chest-indrawing pneumonia and its full selected action block.",
            ("complete_single_turn", "pneumonia", "clinician_observation"),
            _base_values(**{ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True, ObservationId.RESPIRATORY_CHEST_INDRAWING: True, ObservationId.RESPIRATORY_RATE: 35}),
            (respiratory_complete,),
            "complete-respiratory",
        ),
        GoldenCaseSpec(
            "golden-very-incomplete",
            "Very incomplete presentation that must acquire clinician-observed danger signs before lower-priority information.",
            ("very_incomplete", "acquire_information", "canonical_order"),
            _base_values(**{ObservationId.AGE_MONTHS: 20}),
            ((ObservationId.AGE_MONTHS,),),
            "minimal-presentation",
        ),
        GoldenCaseSpec(
            "golden-partial-needs-respiratory-measurement",
            "Partially complete respiratory assessment where only a valid one-minute respiratory-rate measurement can decide pneumonia versus cough/cold.",
            ("partial", "measurement", "caregiver_vs_measurement", "unknown_preserved"),
            _base_values(**{ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True, ObservationId.RESPIRATORY_RATE: 45}),
            ((*_BASELINE_IDS, ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM, ObservationId.RESPIRATORY_CHEST_INDRAWING),),
            "respiratory-measurement-request",
        ),
        GoldenCaseSpec(
            "golden-multiturn-age12-rr40",
            "Multi-turn progression across the exact older-band threshold: measurement at 40 produces pneumonia.",
            ("multi_turn", "age_boundary", "fast_breathing", "rr_at_cutoff", "pneumonia"),
            _base_values(**{ObservationId.AGE_MONTHS: 12, ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True, ObservationId.RESPIRATORY_RATE: 40}),
            ((*_BASELINE_IDS, ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM, ObservationId.RESPIRATORY_CHEST_INDRAWING), (ObservationId.RESPIRATORY_RATE,)),
            "respiratory-measurement-multiturn",
        ),
        GoldenCaseSpec(
            "golden-age11-rr49-cough-cold",
            "Younger-band respiratory rate immediately below 50 verifies justified cough/cold fallback.",
            ("age_boundary", "rr_below_cutoff", "cough_cold"),
            _base_values(**{ObservationId.AGE_MONTHS: 11, ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True, ObservationId.RESPIRATORY_RATE: 49}),
            (respiratory_complete,),
            "respiratory-boundary-complete",
        ),
        GoldenCaseSpec(
            "golden-age11-rr50-pneumonia",
            "Younger-band respiratory rate exactly at 50 verifies fast-breathing pneumonia.",
            ("age_boundary", "rr_at_cutoff", "fast_breathing", "pneumonia"),
            _base_values(**{ObservationId.AGE_MONTHS: 11, ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True, ObservationId.RESPIRATORY_RATE: 50}),
            (respiratory_complete,),
            "respiratory-boundary-complete",
        ),
        GoldenCaseSpec(
            "golden-age12-rr39-cough-cold",
            "Older-band respiratory rate immediately below 40 verifies the age-band transition and justified fallback.",
            ("age_boundary", "rr_below_cutoff", "cough_cold"),
            _base_values(**{ObservationId.AGE_MONTHS: 12, ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True, ObservationId.RESPIRATORY_RATE: 39}),
            (respiratory_complete,),
            "respiratory-boundary-complete",
        ),
        GoldenCaseSpec(
            "golden-danger-sign-early-escalation",
            "Known vomiting-everything danger sign fixes severe classifications and urgent actions before the supported assessment is complete.",
            ("danger_sign", "early_escalation", "urgent", "decision_sufficient_assessment_incomplete"),
            _base_values(**{ObservationId.AGE_MONTHS: 30, ObservationId.DANGER_VOMITS_EVERYTHING: True, ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True}),
            ((ObservationId.AGE_MONTHS, ObservationId.DANGER_CONVULSING_NOW, ObservationId.DANGER_VOMITS_EVERYTHING, ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING, ObservationId.HAS_DIARRHOEA),),
            "urgent-partial",
        ),
        GoldenCaseSpec(
            "golden-simultaneous-danger-diazepam",
            "Simultaneous unable-to-drink and convulsing-now rules must retain both signs and the additional diazepam action.",
            ("simultaneous_danger_signs", "convulsing_now", "diazepam", "urgent"),
            _base_values(**{ObservationId.AGE_MONTHS: 24, ObservationId.DANGER_CONVULSING_NOW: True, ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED: True}),
            (_BASELINE_IDS,),
            "complete-danger",
        ),
        GoldenCaseSpec(
            "golden-severe-dehydration-plan-c",
            "Two severe dehydration signs with no other severe classification select severe dehydration and Plan C.",
            ("severe_dehydration", "two_of", "plan_c"),
            _base_values(**{ObservationId.HAS_DIARRHOEA: True, ObservationId.DEHYDRATION_SUNKEN_EYES: True, ObservationId.DEHYDRATION_DRINKING_STATUS: DrinkingStatus.POORLY}),
            (dehydration_complete,),
            "complete-dehydration",
        ),
        GoldenCaseSpec(
            "golden-multiturn-some-dehydration",
            "Multi-turn clinician observation of sunken eyes resolves an insufficient dehydration decision to some dehydration with two signs.",
            ("multi_turn", "some_dehydration", "two_of", "clinician_observation"),
            _base_values(**{ObservationId.HAS_DIARRHOEA: True, ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE: True, ObservationId.DEHYDRATION_SUNKEN_EYES: True}),
            ((*_BASELINE_IDS, ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE, ObservationId.DEHYDRATION_DRINKING_STATUS, ObservationId.DEHYDRATION_SKIN_PINCH), (ObservationId.DEHYDRATION_SUNKEN_EYES,)),
            "dehydration-observation-multiturn",
        ),
        GoldenCaseSpec(
            "golden-no-dehydration-invariant",
            "No dehydration is already invariant while the skin-pinch observation remains assessment-only.",
            ("no_dehydration", "decision_sufficient_assessment_incomplete", "assessment_only"),
            _base_values(**{ObservationId.HAS_DIARRHOEA: True}),
            ((*_BASELINE_IDS, ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE, ObservationId.DEHYDRATION_SUNKEN_EYES, ObservationId.DEHYDRATION_DRINKING_STATUS),),
            "dehydration-invariant-partial",
        ),
        GoldenCaseSpec(
            "golden-dehydration-cross-severe-referral",
            "Severe dehydration classification remains fixed while severe respiratory classification selects the referral/ORS/breastfeeding branch instead of Plan C.",
            ("severe_dehydration", "cross_pathway_action", "respiratory_severe", "urgent"),
            _base_values(**{ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True, ObservationId.HAS_DIARRHOEA: True, ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM: True, ObservationId.DEHYDRATION_SUNKEN_EYES: True, ObservationId.DEHYDRATION_DRINKING_STATUS: DrinkingStatus.POORLY}),
            ((*_BASELINE_IDS, *_RESPIRATORY_IDS, *_DEHYDRATION_IDS),),
            "complete-cross-pathway",
        ),
        GoldenCaseSpec(
            "golden-pneumonia-exact-rule-unresolved",
            "Fast breathing fixes pneumonia and its actions while unknown chest indrawing leaves exact rule identity and assessment completion unresolved.",
            ("pneumonia", "exact_rule_unresolved", "decision_sufficient_assessment_incomplete", "fast_breathing"),
            _base_values(**{ObservationId.AGE_MONTHS: 24, ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True, ObservationId.RESPIRATORY_CHEST_INDRAWING: True, ObservationId.RESPIRATORY_RATE: 45}),
            ((*_BASELINE_IDS, ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM, ObservationId.RESPIRATORY_RATE),),
            "respiratory-rule-invariant-partial",
        ),
    )


def _rule_family(classifications: dict[Pathway, Classification]) -> str:
    return "+".join(pathway.value for pathway in classifications) or "danger-assessment"


def _latent_summary(latent: LatentClinicalCase) -> str:
    values = "; ".join(f"{item.observation_id.value}={item.value.value if hasattr(item.value, 'value') else item.value}" for item in latent.observations)
    oracle = latent.oracle_result
    return (
        f"`{values}`  \n"
        f"Oracle classifications: `{_enum_mapping(oracle.classifications) or 'none'}`. "
        f"Actions: `{', '.join(item.value for item in oracle.actions) or 'none'}`."
    )


def _enum_mapping(values: dict[Any, Any]) -> str:
    return ", ".join(f"{key.value}={value.value}" for key, value in values.items())
