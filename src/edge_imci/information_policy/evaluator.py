"""Deterministic valid-completion information-policy evaluator.

This module owns information sufficiency and acquisition ordering. Clinical
classification and action semantics remain in ``evaluation.reference``.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable

from edge_imci.evaluation.reference import evaluate_case
from edge_imci.information_policy.artifacts import (
    CONSTRAINT_SET_ID,
    POLICY_ID,
    InformationPolicyArtifacts,
    load_information_policy_artifacts,
)
from edge_imci.rules.loader import Rule, load_rule_set
from edge_imci.schemas.case import (
    Action,
    Classification,
    ClinicalCase,
    ClinicalObservations,
    DehydrationObservations,
    DrinkingStatus,
    EvaluationResult,
    GenerationCategory,
    GenerationMetadata,
    GeneralDangerSignObservations,
    Pathway,
    PatientFacts,
    RespiratoryObservations,
    SkinPinch,
    SourceProvenance,
)
from edge_imci.schemas.trajectory import (
    CANONICAL_OBSERVATION_ORDER,
    AcquisitionMode,
    AcquisitionReason,
    AcquisitionRequest,
    BasisType,
    DecisionStatus,
    EntryStatus,
    EvidenceValidityStatus,
    InformationPolicyResult,
    KnowledgeState,
    ObservationEvidence,
    ObservationId,
    PartialCaseState,
    PathwayPolicyState,
    PolicyProvenance,
    ScopeStatus,
    acquisition_mode_for,
)

_INDEX = {item: index for index, item in enumerate(CANONICAL_OBSERVATION_ORDER)}
_PATHWAY_ORDER = (Pathway.GENERAL_DANGER_SIGNS, Pathway.RESPIRATORY, Pathway.DEHYDRATION)
_BOOLEAN_IDS = frozenset(
    {
        ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING,
        ObservationId.HAS_DIARRHOEA,
        ObservationId.DANGER_CONVULSING_NOW,
        ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS,
        ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED,
        ObservationId.DANGER_VOMITS_EVERYTHING,
        ObservationId.DANGER_HAD_CONVULSIONS,
        ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM,
        ObservationId.RESPIRATORY_CHEST_INDRAWING,
        ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE,
        ObservationId.DEHYDRATION_SUNKEN_EYES,
    }
)
_RESPIRATORY_IDS = frozenset(
    {
        ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM,
        ObservationId.RESPIRATORY_CHEST_INDRAWING,
        ObservationId.RESPIRATORY_RATE,
    }
)
_DEHYDRATION_IDS = frozenset(
    {
        ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE,
        ObservationId.DEHYDRATION_SUNKEN_EYES,
        ObservationId.DEHYDRATION_DRINKING_STATUS,
        ObservationId.DEHYDRATION_SKIN_PINCH,
    }
)
_DANGER_IDS = (
    ObservationId.DANGER_CONVULSING_NOW,
    ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS,
    ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED,
    ObservationId.DANGER_VOMITS_EVERYTHING,
    ObservationId.DANGER_HAD_CONVULSIONS,
)
_URGENT_OR_IMMEDIATE_ACTIONS = frozenset(
    {
        Action.URGENT_REFERRAL,
        Action.GIVE_DIAZEPAM_IF_CONVULSING_NOW,
        Action.GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC,
        Action.GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY,
    }
)
_EMPTY_PROVENANCE = SourceProvenance(
    document="WHO Integrated Management of Childhood Illness, Chart Booklet",
    edition="March 2014",
    source_pdf_pages=(),
    source_printed_pages=(),
    source_rule_ids=(),
)
_TEST_GENERATION = GenerationMetadata(
    generator_version="information-policy-valid-completion-v1",
    seed=0,
    categories=(GenerationCategory.MISSING_INFORMATION,),
    rule_family="information-policy",
    logic_signature="valid-completion",
    template_family="none",
)


@dataclass(frozen=True)
class _CompletionOutcome:
    values: tuple[Any, ...]
    scope_status: ScopeStatus
    result: EvaluationResult | None
    pathway_actions: tuple[frozenset[Action], ...]
    pathway_rule_ids: tuple[tuple[str, ...], ...]

    def value(self, observation_id: ObservationId) -> Any:
        return self.values[_INDEX[observation_id]]

    def classification(self, pathway: Pathway) -> Classification | None:
        return None if self.result is None else self.result.classifications.get(pathway)

    def actions_for(self, pathway: Pathway) -> frozenset[Action]:
        return self.pathway_actions[_PATHWAY_ORDER.index(pathway)]

    def rule_ids_for(self, pathway: Pathway) -> tuple[str, ...]:
        return self.pathway_rule_ids[_PATHWAY_ORDER.index(pathway)]

    @property
    def actions(self) -> frozenset[Action]:
        return frozenset() if self.result is None else frozenset(self.result.actions)

    @property
    def classification_signature(self) -> tuple[Any, ...]:
        classifications = tuple(self.classification(pathway) for pathway in _PATHWAY_ORDER)
        return (self.scope_status, classifications)


@dataclass(frozen=True)
class _Influence:
    can_change_classification: bool = False
    can_change_actions: bool = False
    can_trigger_or_add_urgent_action: bool = False
    classification_pathways: frozenset[Pathway] = frozenset()
    action_pathways: frozenset[Pathway] = frozenset()
    can_change_to_severe_dehydration: bool = False

    @property
    def decision_relevant(self) -> bool:
        return self.can_change_classification or self.can_change_actions or self.can_trigger_or_add_urgent_action


class InformationPolicyEvaluator:
    """Evaluate sufficiency and deterministic next acquisitions for one partial state."""

    def __init__(self, artifacts: InformationPolicyArtifacts | None = None) -> None:
        self.artifacts = artifacts or load_information_policy_artifacts()
        self._observation_artifacts = self.artifacts.observations

    def evaluate(self, state: PartialCaseState) -> InformationPolicyResult:
        records = {item.observation_id: item for item in state.observations}
        outcomes, pruned_coherence = _enumerate_outcomes(records)
        influences = {
            observation_id: _measure_influence(observation_id, outcomes)
            for observation_id, record in records.items()
            if record.knowledge_state is KnowledgeState.UNKNOWN
        }
        relevant_ids = {item for item, influence in influences.items() if influence.decision_relevant}
        unresolved_ids = self._unresolved_questions(records)
        blocked_ids = {
            item
            for item in relevant_ids
            if records[item].acquired
            and records[item].validity.status is EvidenceValidityStatus.UNRESOLVED
        }

        pathway_states = tuple(
            self._pathway_state(pathway, records, outcomes, influences, blocked_ids)
            for pathway in _PATHWAY_ORDER
        )
        known_actions = _ordered_actions(set.intersection(*(set(item.actions) for item in outcomes)))
        possible_actions = set.union(*(set(item.actions) for item in outcomes))
        possible_additional_actions = _ordered_actions(possible_actions - set(known_actions))
        urgent_action_required = bool(set(known_actions) & _URGENT_OR_IMMEDIATE_ACTIONS)
        supported_assessment_complete = self._supported_assessment_complete(records)

        if urgent_action_required and not supported_assessment_complete:
            unresolved_ids.add("IP-CQ-001")
        if Action.URGENT_REFERRAL in known_actions and Action.GIVE_FLUID_ZINC_AND_FOOD_PLAN_A in known_actions:
            unresolved_ids.add("IP-CQ-004")

        decision_requests = self._decision_requests(records, influences, known_actions)
        scheduled_decision_batch = _first_batch(decision_requests)
        assessment_requests = self._assessment_requests(records, relevant_ids)

        scope_status = _scope_status(records[ObservationId.AGE_MONTHS])
        if blocked_ids:
            supported_decision_status = DecisionStatus.BLOCKED
        elif scope_status is ScopeStatus.OUT_OF_SCOPE:
            supported_decision_status = DecisionStatus.SUFFICIENT
        elif scope_status is ScopeStatus.UNKNOWN:
            supported_decision_status = DecisionStatus.INSUFFICIENT
        else:
            supported_decision_status = (
                DecisionStatus.SUFFICIENT
                if all(item.decision_status is DecisionStatus.SUFFICIENT for item in pathway_states)
                and _entry_status(records[ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING]) is not EntryStatus.UNKNOWN
                and _entry_status(records[ObservationId.HAS_DIARRHOEA]) is not EntryStatus.UNKNOWN
                else DecisionStatus.INSUFFICIENT
            )

        supported_action_sufficient = len({item.actions for item in outcomes}) == 1
        applied_constraints = self._applied_constraints(records, pruned_coherence)
        return InformationPolicyResult(
            policy_id=POLICY_ID,
            constraint_set_id=CONSTRAINT_SET_ID,
            scope_status=scope_status,
            pathway_states=pathway_states,
            supported_encounter_decision_status=supported_decision_status,
            supported_encounter_action_set_sufficient=supported_action_sufficient,
            supported_encounter_assessment_complete=supported_assessment_complete,
            urgent_action_required=urgent_action_required,
            known_actions=known_actions,
            possible_additional_actions=possible_additional_actions,
            decision_directed_acquisitions=scheduled_decision_batch,
            assessment_completion_acquisitions=assessment_requests,
            applied_constraint_ids=applied_constraints,
            unresolved_question_ids=tuple(sorted(unresolved_ids)),
        )

    def _pathway_state(
        self,
        pathway: Pathway,
        records: dict[ObservationId, ObservationEvidence],
        outcomes: tuple[_CompletionOutcome, ...],
        influences: dict[ObservationId, _Influence],
        blocked_ids: set[ObservationId],
    ) -> PathwayPolicyState:
        classifications = {item.classification(pathway) for item in outcomes}
        actions = {item.actions_for(pathway) for item in outcomes}
        traces = {item.rule_ids_for(pathway) for item in outcomes}
        possible_classifications = tuple(sorted((item for item in classifications if item is not None), key=lambda item: item.value))
        possible_rule_ids = tuple(sorted({rule_id for trace in traces for rule_id in trace}))
        pathway_blocked = any(
            item in blocked_ids
            and (
                pathway in influences[item].classification_pathways
                or pathway in influences[item].action_pathways
            )
            for item in blocked_ids
        )
        if pathway_blocked:
            decision_status = DecisionStatus.BLOCKED
        else:
            decision_status = DecisionStatus.SUFFICIENT if len(classifications) == 1 else DecisionStatus.INSUFFICIENT

        if pathway is Pathway.GENERAL_DANGER_SIGNS:
            entry_status = EntryStatus.ACTIVE
            assessment_ids = set(_DANGER_IDS)
        elif pathway is Pathway.RESPIRATORY:
            entry_status = _entry_status(records[ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING])
            assessment_ids = set(_RESPIRATORY_IDS)
        else:
            entry_status = _entry_status(records[ObservationId.HAS_DIARRHOEA])
            assessment_ids = set(_DEHYDRATION_IDS)

        if entry_status is EntryStatus.NOT_APPLICABLE:
            assessment_complete = True
        elif entry_status is EntryStatus.UNKNOWN:
            assessment_complete = False
        else:
            assessment_complete = all(_is_known_valid(records[item]) for item in assessment_ids)

        return PathwayPolicyState(
            pathway=pathway,
            entry_status=entry_status,
            possible_classifications=possible_classifications,
            decision_status=decision_status,
            action_set_sufficient=len(actions) == 1,
            exact_rule_sufficient=len(traces) == 1 and len(possible_rule_ids) <= 1,
            possible_fired_rule_ids=possible_rule_ids,
            assessment_complete=assessment_complete,
        )

    def _decision_requests(
        self,
        records: dict[ObservationId, ObservationEvidence],
        influences: dict[ObservationId, _Influence],
        known_actions: tuple[Action, ...],
    ) -> tuple[AcquisitionRequest, ...]:
        requests: list[AcquisitionRequest] = []
        already_urgent = bool(set(known_actions) & _URGENT_OR_IMMEDIATE_ACTIONS)
        for observation_id, influence in influences.items():
            if not influence.decision_relevant:
                continue
            artifact = self._observation_artifacts[observation_id]
            if influence.can_trigger_or_add_urgent_action:
                reason = (
                    AcquisitionReason.CAN_ADD_IMMEDIATE_ACTION
                    if already_urgent
                    else AcquisitionReason.CAN_TRIGGER_URGENT_ACTION
                )
            elif influence.can_change_classification:
                reason = AcquisitionReason.CAN_CHANGE_CLASSIFICATION
            else:
                reason = AcquisitionReason.CAN_CHANGE_ACTION_BRANCH
            priority_band = artifact["default_priority_band"]
            if observation_id in _DEHYDRATION_IDS:
                priority_band = 4 if influence.can_change_to_severe_dehydration else 5
            requests.append(
                AcquisitionRequest(
                    observation_id=observation_id,
                    acquisition_mode=AcquisitionMode(artifact["acquisition_mode"]),
                    reason=reason,
                    priority_band=priority_band,
                    priority_order=_INDEX[observation_id],
                    provenance=self._provenance(observation_id, records[observation_id]),
                    can_change_classification=influence.can_change_classification,
                    can_change_actions=influence.can_change_actions,
                    can_trigger_or_add_urgent_action=influence.can_trigger_or_add_urgent_action,
                )
            )
        return tuple(sorted(requests, key=lambda item: (item.priority_band, item.priority_order)))

    def _assessment_requests(
        self,
        records: dict[ObservationId, ObservationEvidence],
        relevant_ids: set[ObservationId],
    ) -> tuple[AcquisitionRequest, ...]:
        required_ids = self._active_assessment_ids(records)
        requests = []
        for observation_id in CANONICAL_OBSERVATION_ORDER:
            if observation_id not in required_ids or observation_id in relevant_ids or _is_known_valid(records[observation_id]):
                continue
            artifact = self._observation_artifacts[observation_id]
            requests.append(
                AcquisitionRequest(
                    observation_id=observation_id,
                    acquisition_mode=acquisition_mode_for(observation_id),
                    reason=AcquisitionReason.ASSESSMENT_COMPLETION_ONLY,
                    priority_band=6,
                    priority_order=_INDEX[observation_id],
                    provenance=self._provenance(observation_id, records[observation_id]),
                )
            )
        return tuple(requests)

    def _active_assessment_ids(
        self,
        records: dict[ObservationId, ObservationEvidence],
    ) -> set[ObservationId]:
        age_status = _scope_status(records[ObservationId.AGE_MONTHS])
        if age_status is ScopeStatus.OUT_OF_SCOPE:
            return set()
        if age_status is ScopeStatus.UNKNOWN:
            return {ObservationId.AGE_MONTHS}
        required = {
            ObservationId.AGE_MONTHS,
            ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING,
            ObservationId.HAS_DIARRHOEA,
            *_DANGER_IDS,
        }
        if _known_value(records[ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING]) is True:
            required.update(_RESPIRATORY_IDS)
        if _known_value(records[ObservationId.HAS_DIARRHOEA]) is True:
            required.update(_DEHYDRATION_IDS)
        return required

    def _supported_assessment_complete(
        self,
        records: dict[ObservationId, ObservationEvidence],
    ) -> bool:
        return all(_is_known_valid(records[item]) for item in self._active_assessment_ids(records))

    def _provenance(
        self,
        observation_id: ObservationId,
        record: ObservationEvidence,
    ) -> PolicyProvenance:
        artifact = self._observation_artifacts[observation_id]
        unresolved = tuple(record.validity.unresolved_question_ids)
        basis = BasisType(artifact["basis"])
        if unresolved:
            basis = BasisType.UNRESOLVED_CLINICAL_AMBIGUITY
        return PolicyProvenance(
            basis=basis,
            source_rule_ids=tuple(artifact.get("source_rule_ids", [])),
            source_pdf_pages=tuple(artifact.get("source_pdf_pages", [])),
            source_printed_pages=tuple(artifact.get("source_printed_pages", [])),
            policy_rule_ids=tuple(artifact.get("policy_rule_ids", [])),
            unresolved_question_ids=unresolved,
        )

    def _unresolved_questions(
        self,
        records: dict[ObservationId, ObservationEvidence],
    ) -> set[str]:
        unresolved = {
            question_id
            for record in records.values()
            for question_id in record.validity.unresolved_question_ids
        }
        unable = records[ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED]
        drinking = records[ObservationId.DEHYDRATION_DRINKING_STATUS]
        if (unable.knowledge_state is KnowledgeState.UNKNOWN) != (drinking.knowledge_state is KnowledgeState.UNKNOWN):
            unresolved.add("IP-CQ-002")
        return unresolved

    @staticmethod
    def _applied_constraints(
        records: dict[ObservationId, ObservationEvidence],
        pruned_coherence: bool,
    ) -> tuple[str, ...]:
        applied = {
            "VC-SCOPE-001",
            "VC-DOMAIN-001",
            "VC-DOMAIN-002",
            "VC-DOMAIN-003",
            "VC-ENTRY-001",
            "VC-CONTAINER-001",
            "VC-COHERENCE-002",
        }
        if any(record.knowledge_state is KnowledgeState.UNKNOWN for record in records.values()):
            applied.add("VC-UNKNOWN-001")
        if pruned_coherence:
            applied.add("VC-COHERENCE-001")
        if any(record.acquired and record.knowledge_state is KnowledgeState.UNKNOWN for record in records.values()):
            applied.add("VC-EVIDENCE-001")
        return tuple(sorted(applied))


def evaluate_information_policy(
    state: PartialCaseState,
    artifacts: InformationPolicyArtifacts | None = None,
) -> InformationPolicyResult:
    """Convenience wrapper for deterministic policy evaluation."""

    return InformationPolicyEvaluator(artifacts).evaluate(state)


def _enumerate_outcomes(
    records: dict[ObservationId, ObservationEvidence],
) -> tuple[tuple[_CompletionOutcome, ...], bool]:
    age_record = records[ObservationId.AGE_MONTHS]
    known_age = _known_value(age_record)
    if known_age is not None and not 2 <= known_age < 60:
        values = tuple(
            known_age if item is ObservationId.AGE_MONTHS else _known_value(records[item]) or _default_value(item)
            for item in CANONICAL_OBSERVATION_ORDER
        )
        return (_out_of_scope_outcome(values),), False

    outcomes: list[_CompletionOutcome] = []
    values: list[Any] = [None] * len(CANONICAL_OBSERVATION_ORDER)
    pruned_coherence = False
    original_age_unknown = age_record.knowledge_state is KnowledgeState.UNKNOWN

    def visit(position: int) -> None:
        nonlocal pruned_coherence
        if position == len(CANONICAL_OBSERVATION_ORDER):
            if values[_INDEX[ObservationId.AGE_MONTHS]] == 60:
                outcomes.append(_out_of_scope_outcome(tuple(values)))
            else:
                outcomes.append(_evaluate_completion(tuple(values)))
            return
        observation_id = CANONICAL_OBSERVATION_ORDER[position]
        for value in _completion_domain(observation_id, records, values, original_age_unknown):
            values[position] = value
            if (
                values[_INDEX[ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS]] is True
                and values[_INDEX[ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE]] is True
            ):
                pruned_coherence = True
                continue
            visit(position + 1)
        values[position] = None

    visit(0)
    if not outcomes:
        raise ValueError("partial state has no valid completions")
    return tuple(outcomes), pruned_coherence


def _completion_domain(
    observation_id: ObservationId,
    records: dict[ObservationId, ObservationEvidence],
    values: list[Any],
    original_age_unknown: bool,
) -> tuple[Any, ...]:
    known = _known_value(records[observation_id])
    if known is not None:
        return (known,)
    if observation_id is ObservationId.AGE_MONTHS:
        return (2, 12, 60)
    if observation_id in _RESPIRATORY_IDS:
        entry = values[_INDEX[ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING]]
        if entry is not True:
            return (_default_value(observation_id),)
    if observation_id in _DEHYDRATION_IDS:
        entry = values[_INDEX[ObservationId.HAS_DIARRHOEA]]
        if entry is not True:
            return (_default_value(observation_id),)
    if observation_id in _BOOLEAN_IDS:
        return (False, True)
    if observation_id is ObservationId.DEHYDRATION_DRINKING_STATUS:
        return tuple(DrinkingStatus)
    if observation_id is ObservationId.DEHYDRATION_SKIN_PINCH:
        return tuple(SkinPinch)
    if observation_id is ObservationId.RESPIRATORY_RATE:
        if original_age_unknown:
            return (39, 40, 49, 50)
        age = values[_INDEX[ObservationId.AGE_MONTHS]]
        return (49, 50) if age < 12 else (39, 40)
    raise ValueError(f"no completion domain for {observation_id.value}")


def _default_value(observation_id: ObservationId) -> Any:
    if observation_id in _BOOLEAN_IDS:
        return False
    if observation_id is ObservationId.RESPIRATORY_RATE:
        return 0
    if observation_id is ObservationId.DEHYDRATION_DRINKING_STATUS:
        return DrinkingStatus.NORMAL
    if observation_id is ObservationId.DEHYDRATION_SKIN_PINCH:
        return SkinPinch.NORMAL
    if observation_id is ObservationId.AGE_MONTHS:
        return 60
    raise ValueError(f"no default for {observation_id.value}")


def _out_of_scope_outcome(values: tuple[Any, ...]) -> _CompletionOutcome:
    return _CompletionOutcome(
        values=values,
        scope_status=ScopeStatus.OUT_OF_SCOPE,
        result=None,
        pathway_actions=(frozenset(), frozenset(), frozenset()),
        pathway_rule_ids=((), (), ()),
    )


@lru_cache(maxsize=131072)
def _evaluate_completion(values: tuple[Any, ...]) -> _CompletionOutcome:
    result = evaluate_case(_clinical_case(values))
    pathway_actions = _pathway_actions(result)
    pathway_rule_ids = _pathway_rule_ids(result)
    return _CompletionOutcome(
        values=values,
        scope_status=ScopeStatus.IN_SCOPE,
        result=result,
        pathway_actions=tuple(pathway_actions[pathway] for pathway in _PATHWAY_ORDER),
        pathway_rule_ids=tuple(pathway_rule_ids[pathway] for pathway in _PATHWAY_ORDER),
    )


def _clinical_case(values: tuple[Any, ...]) -> ClinicalCase:
    def value(observation_id: ObservationId) -> Any:
        return values[_INDEX[observation_id]]

    danger = GeneralDangerSignObservations(
        unable_to_drink_or_breastfeed=value(ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED),
        vomits_everything=value(ObservationId.DANGER_VOMITS_EVERYTHING),
        had_convulsions=value(ObservationId.DANGER_HAD_CONVULSIONS),
        lethargic_or_unconscious=value(ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS),
        convulsing_now=value(ObservationId.DANGER_CONVULSING_NOW),
    )
    has_respiratory = value(ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING)
    has_diarrhoea = value(ObservationId.HAS_DIARRHOEA)
    respiratory = (
        RespiratoryObservations(
            respiratory_rate=value(ObservationId.RESPIRATORY_RATE),
            chest_indrawing=value(ObservationId.RESPIRATORY_CHEST_INDRAWING),
            stridor_when_calm=value(ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM),
        )
        if has_respiratory
        else None
    )
    dehydration = (
        DehydrationObservations(
            restless_or_irritable=value(ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE),
            sunken_eyes=value(ObservationId.DEHYDRATION_SUNKEN_EYES),
            drinking_status=value(ObservationId.DEHYDRATION_DRINKING_STATUS),
            skin_pinch=value(ObservationId.DEHYDRATION_SKIN_PINCH),
        )
        if has_diarrhoea
        else None
    )
    try:
        observations = ClinicalObservations(danger_signs=danger, respiratory=respiratory, dehydration=dehydration)
    except ValueError as error:
        if "UNABLE drinking status conflicts" not in str(error):
            raise
        # VC-COHERENCE-002 is explicitly input-validation-only. Hypothetical
        # completions must not infer or prune either drinking observation.
        observations = object.__new__(ClinicalObservations)
        object.__setattr__(observations, "danger_signs", danger)
        object.__setattr__(observations, "respiratory", respiratory)
        object.__setattr__(observations, "dehydration", dehydration)
    return ClinicalCase(
        case_id="information-policy-completion",
        patient_facts=PatientFacts(
            age_months=value(ObservationId.AGE_MONTHS),
            has_cough_or_difficult_breathing=has_respiratory,
            has_diarrhoea=has_diarrhoea,
        ),
        presentation="Machine-generated valid completion for policy evaluation.",
        observations=observations,
        known_missing_information=(),
        expected_result=None,
        provenance=_EMPTY_PROVENANCE,
        generation=_TEST_GENERATION,
    )


def _pathway_actions(result: EvaluationResult) -> dict[Pathway, frozenset[Action]]:
    rules = {rule.rule_id: rule for rule in load_rule_set().rules}
    actions: dict[Pathway, set[Action]] = {pathway: set() for pathway in _PATHWAY_ORDER}
    for rule_id in result.fired_rule_ids:
        rule = rules[rule_id]
        pathway = _pathway_for_rule(rule)
        if pathway is None:
            continue
        configured = _configured_actions(rule, result)
        actions[pathway].update(Action(item) for item in configured)
    return {pathway: frozenset(items) for pathway, items in actions.items()}


def _configured_actions(rule: Rule, result: EvaluationResult) -> Iterable[str]:
    if "actions" in rule.result:
        return rule.result["actions"]
    other_severe = bool(result.detected_danger_signs) or (
        result.classifications.get(Pathway.RESPIRATORY)
        is Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE
    )
    key = "actions_with_other_severe_classification" if other_severe else "actions_without_other_severe_classification"
    return rule.result[key]


def _pathway_rule_ids(result: EvaluationResult) -> dict[Pathway, tuple[str, ...]]:
    rules = {rule.rule_id: rule for rule in load_rule_set().rules}
    grouped: dict[Pathway, list[str]] = {pathway: [] for pathway in _PATHWAY_ORDER}
    for rule_id in result.fired_rule_ids:
        pathway = _pathway_for_rule(rules[rule_id])
        if pathway is not None and rules[rule_id].kind != "fast_breathing_threshold":
            grouped[pathway].append(rule_id)
    return {pathway: tuple(rule_ids) for pathway, rule_ids in grouped.items()}


def _pathway_for_rule(rule: Rule) -> Pathway | None:
    if rule.kind == "danger_sign":
        return Pathway.GENERAL_DANGER_SIGNS
    if rule.kind == "respiratory_classification":
        return Pathway.RESPIRATORY
    if rule.kind == "dehydration_classification":
        return Pathway.DEHYDRATION
    return None


def _measure_influence(
    observation_id: ObservationId,
    outcomes: tuple[_CompletionOutcome, ...],
) -> _Influence:
    index = _INDEX[observation_id]
    grouped: dict[tuple[Any, ...], list[_CompletionOutcome]] = defaultdict(list)
    for outcome in outcomes:
        key = outcome.values[:index] + outcome.values[index + 1 :]
        grouped[key].append(outcome)

    classification = False
    actions = False
    urgent = False
    severe_dehydration = False
    classification_pathways: set[Pathway] = set()
    action_pathways: set[Pathway] = set()
    for variants in grouped.values():
        if len({item.value(observation_id) for item in variants}) < 2:
            continue
        if len({item.classification_signature for item in variants}) > 1:
            classification = True
        if len({item.actions for item in variants}) > 1:
            actions = True
        if len({item.actions & _URGENT_OR_IMMEDIATE_ACTIONS for item in variants}) > 1:
            urgent = True
        dehydration_classes = {item.classification(Pathway.DEHYDRATION) for item in variants}
        if Classification.SEVERE_DEHYDRATION in dehydration_classes and len(dehydration_classes) > 1:
            severe_dehydration = True
        for pathway in _PATHWAY_ORDER:
            if len({item.classification(pathway) for item in variants}) > 1:
                classification_pathways.add(pathway)
            if len({item.actions_for(pathway) for item in variants}) > 1:
                action_pathways.add(pathway)

    return _Influence(
        can_change_classification=classification,
        can_change_actions=actions,
        can_trigger_or_add_urgent_action=urgent,
        classification_pathways=frozenset(classification_pathways),
        action_pathways=frozenset(action_pathways),
        can_change_to_severe_dehydration=severe_dehydration,
    )


def _first_batch(requests: tuple[AcquisitionRequest, ...]) -> tuple[AcquisitionRequest, ...]:
    if not requests:
        return ()
    first = requests[0]
    return tuple(
        item
        for item in requests
        if item.priority_band == first.priority_band and item.acquisition_mode is first.acquisition_mode
    )


def _scope_status(record: ObservationEvidence) -> ScopeStatus:
    age = _known_value(record)
    if age is None:
        return ScopeStatus.UNKNOWN
    return ScopeStatus.IN_SCOPE if 2 <= age < 60 else ScopeStatus.OUT_OF_SCOPE


def _entry_status(record: ObservationEvidence) -> EntryStatus:
    value = _known_value(record)
    if value is None:
        return EntryStatus.UNKNOWN
    return EntryStatus.ACTIVE if value else EntryStatus.NOT_APPLICABLE


def _known_value(record: ObservationEvidence) -> Any:
    return record.value if record.knowledge_state is not KnowledgeState.UNKNOWN else None


def _is_known_valid(record: ObservationEvidence) -> bool:
    return record.knowledge_state is not KnowledgeState.UNKNOWN and record.validity.status is EvidenceValidityStatus.VALID


def _ordered_actions(actions: Iterable[Action]) -> tuple[Action, ...]:
    return tuple(sorted(actions, key=lambda item: item.value))
