"""Typed schemas for future conversational IMCI dataset trajectories.

This module is deliberately separate from ``ClinicalCase``.  It represents
partial knowledge, model-visible messages, and expected assistant semantics
without changing the frozen complete-case benchmark contract.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, TypeAlias

from edge_imci.schemas.case import (
    Action,
    Classification,
    DangerSign,
    DrinkingStatus,
    EvaluationResult,
    Pathway,
    ReferralRequirement,
    SkinPinch,
    SourceProvenance,
    StringEnum,
)

TRAJECTORY_SCHEMA_VERSION = "edge-imci-trajectory-v1"


class ObservationId(StringEnum):
    AGE_MONTHS = "patient_facts.age_months"
    HAS_COUGH_OR_DIFFICULT_BREATHING = "patient_facts.has_cough_or_difficult_breathing"
    HAS_DIARRHOEA = "patient_facts.has_diarrhoea"
    DANGER_CONVULSING_NOW = "danger_signs.convulsing_now"
    DANGER_LETHARGIC_OR_UNCONSCIOUS = "danger_signs.lethargic_or_unconscious"
    DANGER_UNABLE_TO_DRINK_OR_BREASTFEED = "danger_signs.unable_to_drink_or_breastfeed"
    DANGER_VOMITS_EVERYTHING = "danger_signs.vomits_everything"
    DANGER_HAD_CONVULSIONS = "danger_signs.had_convulsions"
    RESPIRATORY_STRIDOR_WHEN_CALM = "respiratory.stridor_when_calm"
    RESPIRATORY_CHEST_INDRAWING = "respiratory.chest_indrawing"
    RESPIRATORY_RATE = "respiratory.respiratory_rate"
    DEHYDRATION_RESTLESS_OR_IRRITABLE = "dehydration.restless_or_irritable"
    DEHYDRATION_SUNKEN_EYES = "dehydration.sunken_eyes"
    DEHYDRATION_DRINKING_STATUS = "dehydration.drinking_status"
    DEHYDRATION_SKIN_PINCH = "dehydration.skin_pinch"


CANONICAL_OBSERVATION_ORDER = (
    ObservationId.AGE_MONTHS,
    ObservationId.DANGER_CONVULSING_NOW,
    ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS,
    ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED,
    ObservationId.DANGER_VOMITS_EVERYTHING,
    ObservationId.DANGER_HAD_CONVULSIONS,
    ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING,
    ObservationId.HAS_DIARRHOEA,
    ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM,
    ObservationId.RESPIRATORY_CHEST_INDRAWING,
    ObservationId.RESPIRATORY_RATE,
    ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE,
    ObservationId.DEHYDRATION_SUNKEN_EYES,
    ObservationId.DEHYDRATION_DRINKING_STATUS,
    ObservationId.DEHYDRATION_SKIN_PINCH,
)


class KnowledgeState(StringEnum):
    UNKNOWN = "UNKNOWN"
    KNOWN_PRESENT = "KNOWN_PRESENT"
    KNOWN_ABSENT = "KNOWN_ABSENT"
    KNOWN_VALUE = "KNOWN_VALUE"


class AcquisitionMode(StringEnum):
    CAREGIVER_QUESTION = "CAREGIVER_QUESTION"
    CLINICIAN_OBSERVATION = "CLINICIAN_OBSERVATION"
    MEASUREMENT = "MEASUREMENT"
    HISTORY_OR_RECORD = "HISTORY_OR_RECORD"


class EvidenceValidityStatus(StringEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    VALID = "VALID"
    INVALID = "INVALID"
    UNRESOLVED = "UNRESOLVED"


class AcquisitionReason(StringEnum):
    CAN_TRIGGER_URGENT_ACTION = "CAN_TRIGGER_URGENT_ACTION"
    CAN_CHANGE_CLASSIFICATION = "CAN_CHANGE_CLASSIFICATION"
    CAN_CHANGE_ACTION_BRANCH = "CAN_CHANGE_ACTION_BRANCH"
    CAN_ADD_IMMEDIATE_ACTION = "CAN_ADD_IMMEDIATE_ACTION"
    ASSESSMENT_COMPLETION_ONLY = "ASSESSMENT_COMPLETION_ONLY"


class BasisType(StringEnum):
    DIRECT_SOURCE_DERIVED = "DIRECT_SOURCE_DERIVED"
    INTERACTION_POLICY = "INTERACTION_POLICY"
    UNRESOLVED_CLINICAL_AMBIGUITY = "UNRESOLVED_CLINICAL_AMBIGUITY"


class ScopeStatus(StringEnum):
    IN_SCOPE = "IN_SCOPE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNKNOWN = "UNKNOWN"


class EntryStatus(StringEnum):
    ACTIVE = "ACTIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class DecisionStatus(StringEnum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    BLOCKED = "BLOCKED"


class AssistantBehavior(StringEnum):
    REQUEST_INFORMATION = "REQUEST_INFORMATION"
    EMIT_URGENT_ACTION = "EMIT_URGENT_ACTION"
    EMIT_CLASSIFICATION = "EMIT_CLASSIFICATION"
    EMIT_ACTIONS = "EMIT_ACTIONS"
    REPORT_NOT_APPLICABLE = "REPORT_NOT_APPLICABLE"
    REPORT_OUT_OF_SCOPE = "REPORT_OUT_OF_SCOPE"
    REPORT_BLOCKED = "REPORT_BLOCKED"


class ConversationRole(StringEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class CorpusRole(StringEnum):
    UNASSIGNED = "UNASSIGNED"
    TRAINING = "TRAINING"
    VALIDATION = "VALIDATION"
    BENCHMARK = "BENCHMARK"
    ILLUSTRATIVE_FIXTURE = "ILLUSTRATIVE_FIXTURE"


ClinicalValue: TypeAlias = bool | int | DrinkingStatus | SkinPinch

_BOOLEAN_OBSERVATIONS = frozenset(
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

_ACQUISITION_MODES = {
    ObservationId.AGE_MONTHS: AcquisitionMode.HISTORY_OR_RECORD,
    ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: AcquisitionMode.CAREGIVER_QUESTION,
    ObservationId.HAS_DIARRHOEA: AcquisitionMode.CAREGIVER_QUESTION,
    ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED: AcquisitionMode.CAREGIVER_QUESTION,
    ObservationId.DANGER_VOMITS_EVERYTHING: AcquisitionMode.CAREGIVER_QUESTION,
    ObservationId.DANGER_HAD_CONVULSIONS: AcquisitionMode.CAREGIVER_QUESTION,
    ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS: AcquisitionMode.CLINICIAN_OBSERVATION,
    ObservationId.DANGER_CONVULSING_NOW: AcquisitionMode.CLINICIAN_OBSERVATION,
    ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM: AcquisitionMode.CLINICIAN_OBSERVATION,
    ObservationId.RESPIRATORY_CHEST_INDRAWING: AcquisitionMode.CLINICIAN_OBSERVATION,
    ObservationId.RESPIRATORY_RATE: AcquisitionMode.MEASUREMENT,
    ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE: AcquisitionMode.CLINICIAN_OBSERVATION,
    ObservationId.DEHYDRATION_SUNKEN_EYES: AcquisitionMode.CLINICIAN_OBSERVATION,
    ObservationId.DEHYDRATION_DRINKING_STATUS: AcquisitionMode.CLINICIAN_OBSERVATION,
    ObservationId.DEHYDRATION_SKIN_PINCH: AcquisitionMode.CLINICIAN_OBSERVATION,
}

_CLASSIFICATIONS_BY_PATHWAY = {
    Pathway.GENERAL_DANGER_SIGNS: frozenset({Classification.VERY_SEVERE_DISEASE}),
    Pathway.RESPIRATORY: frozenset(
        {
            Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE,
            Classification.PNEUMONIA,
            Classification.COUGH_OR_COLD,
        }
    ),
    Pathway.DEHYDRATION: frozenset(
        {
            Classification.SEVERE_DEHYDRATION,
            Classification.SOME_DEHYDRATION,
            Classification.NO_DEHYDRATION,
        }
    ),
}


def acquisition_mode_for(observation_id: ObservationId) -> AcquisitionMode:
    """Return the approved v1 acquisition mode for an observation."""

    return _ACQUISITION_MODES[observation_id]


@dataclass(frozen=True)
class PolicyProvenance:
    basis: BasisType
    source_rule_ids: tuple[str, ...] = ()
    source_pdf_pages: tuple[int, ...] = ()
    source_printed_pages: tuple[str, ...] = ()
    policy_rule_ids: tuple[str, ...] = ()
    unresolved_question_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_unique(self.source_rule_ids, "source_rule_ids")
        _require_unique(self.source_pdf_pages, "source_pdf_pages")
        _require_unique(self.source_printed_pages, "source_printed_pages")
        _require_unique(self.policy_rule_ids, "policy_rule_ids")
        _require_unique(self.unresolved_question_ids, "unresolved_question_ids")
        if self.basis is BasisType.UNRESOLVED_CLINICAL_AMBIGUITY and not self.unresolved_question_ids:
            raise ValueError("unresolved clinical provenance requires an unresolved question ID")

    def to_dict(self) -> dict[str, Any]:
        return {
            "basis": self.basis.value,
            "source_rule_ids": list(self.source_rule_ids),
            "source_pdf_pages": list(self.source_pdf_pages),
            "source_printed_pages": list(self.source_printed_pages),
            "policy_rule_ids": list(self.policy_rule_ids),
            "unresolved_question_ids": list(self.unresolved_question_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyProvenance":
        return cls(
            basis=BasisType(data["basis"]),
            source_rule_ids=tuple(data.get("source_rule_ids", [])),
            source_pdf_pages=tuple(data.get("source_pdf_pages", [])),
            source_printed_pages=tuple(data.get("source_printed_pages", [])),
            policy_rule_ids=tuple(data.get("policy_rule_ids", [])),
            unresolved_question_ids=tuple(data.get("unresolved_question_ids", [])),
        )


@dataclass(frozen=True)
class ObservationValidity:
    status: EvidenceValidityStatus = EvidenceValidityStatus.NOT_ASSESSED
    child_calm: bool | None = None
    counted_for_one_minute: bool | None = None
    unresolved_question_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_unique(self.unresolved_question_ids, "unresolved_question_ids")
        if self.status is EvidenceValidityStatus.NOT_ASSESSED:
            if self.child_calm is not None or self.counted_for_one_minute is not None or self.unresolved_question_ids:
                raise ValueError("NOT_ASSESSED validity cannot contain method findings or unresolved questions")
        elif self.status is EvidenceValidityStatus.UNRESOLVED:
            if not self.unresolved_question_ids:
                raise ValueError("UNRESOLVED validity requires an unresolved question ID")
        elif self.unresolved_question_ids:
            raise ValueError("only UNRESOLVED validity may carry unresolved question IDs")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "child_calm": self.child_calm,
            "counted_for_one_minute": self.counted_for_one_minute,
            "unresolved_question_ids": list(self.unresolved_question_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObservationValidity":
        return cls(
            status=EvidenceValidityStatus(data["status"]),
            child_calm=data.get("child_calm"),
            counted_for_one_minute=data.get("counted_for_one_minute"),
            unresolved_question_ids=tuple(data.get("unresolved_question_ids", [])),
        )


@dataclass(frozen=True)
class LatentObservation:
    observation_id: ObservationId
    value: ClinicalValue

    def __post_init__(self) -> None:
        _validate_value(self.observation_id, self.value)

    def to_dict(self) -> dict[str, Any]:
        return {"observation_id": self.observation_id.value, "value": _serialize_value(self.value)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LatentObservation":
        observation_id = ObservationId(data["observation_id"])
        return cls(observation_id=observation_id, value=_deserialize_value(observation_id, data["value"]))


@dataclass(frozen=True)
class LatentClinicalCase:
    latent_case_id: str
    observations: tuple[LatentObservation, ...]
    scope_status: ScopeStatus
    oracle_result: EvaluationResult | None
    provenance: SourceProvenance

    def __post_init__(self) -> None:
        if not self.latent_case_id:
            raise ValueError("latent_case_id is required")
        _require_complete_catalog(self.observations, "latent observations")
        by_id = {item.observation_id: item for item in self.observations}
        object.__setattr__(self, "observations", tuple(by_id[item] for item in CANONICAL_OBSERVATION_ORDER))
        age = self.observation(ObservationId.AGE_MONTHS).value
        if type(age) is not int:
            raise ValueError("latent age must be an integer")
        expected_scope = ScopeStatus.IN_SCOPE if 2 <= age < 60 else ScopeStatus.OUT_OF_SCOPE
        if self.scope_status is not expected_scope:
            raise ValueError("scope_status contradicts latent age")
        if self.scope_status is ScopeStatus.IN_SCOPE:
            if self.oracle_result is None:
                raise ValueError("an in-scope latent case requires an oracle result")
            if self.oracle_result.missing_required_observations:
                raise ValueError("a complete latent case cannot have missing oracle observations")
        elif self.oracle_result is not None:
            raise ValueError("an out-of-scope latent case cannot have a clinical oracle result")

    def observation(self, observation_id: ObservationId) -> LatentObservation:
        return next(item for item in self.observations if item.observation_id is observation_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "latent_case_id": self.latent_case_id,
            "observations": [self.observation(item).to_dict() for item in CANONICAL_OBSERVATION_ORDER],
            "scope_status": self.scope_status.value,
            "oracle_result": self.oracle_result.to_dict() if self.oracle_result else None,
            "provenance": _source_provenance_to_dict(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LatentClinicalCase":
        return cls(
            latent_case_id=data["latent_case_id"],
            observations=tuple(LatentObservation.from_dict(item) for item in data["observations"]),
            scope_status=ScopeStatus(data["scope_status"]),
            oracle_result=EvaluationResult.from_dict(data["oracle_result"]) if data.get("oracle_result") else None,
            provenance=_source_provenance_from_dict(data["provenance"]),
        )


@dataclass(frozen=True)
class ObservationEvidence:
    observation_id: ObservationId
    knowledge_state: KnowledgeState = KnowledgeState.UNKNOWN
    value: ClinicalValue | None = None
    acquired: bool = False
    acquisition_mode: AcquisitionMode | None = None
    validity: ObservationValidity = field(default_factory=ObservationValidity)
    provenance: PolicyProvenance | None = None

    def __post_init__(self) -> None:
        if self.value is not None:
            _validate_value(self.observation_id, self.value)
        if not self.acquired:
            if self.knowledge_state is not KnowledgeState.UNKNOWN or self.value is not None:
                raise ValueError("an unacquired observation must remain UNKNOWN without a value")
            if self.acquisition_mode is not None or self.validity.status is not EvidenceValidityStatus.NOT_ASSESSED:
                raise ValueError("an unacquired observation cannot have an acquisition mode or validity result")
            if self.provenance is not None:
                raise ValueError("an unacquired observation cannot carry evidence provenance")
            return
        if self.acquisition_mode is not acquisition_mode_for(self.observation_id):
            raise ValueError(f"{self.observation_id.value} requires {acquisition_mode_for(self.observation_id).value}")
        if self.knowledge_state is KnowledgeState.UNKNOWN:
            if self.validity.status not in {EvidenceValidityStatus.INVALID, EvidenceValidityStatus.UNRESOLVED}:
                raise ValueError("acquired UNKNOWN evidence must be invalid or unresolved")
            return
        if self.value is None:
            raise ValueError("known evidence requires a value")
        if self.validity.status is not EvidenceValidityStatus.VALID:
            raise ValueError("known evidence requires VALID acquisition validity")
        expected_state = _knowledge_state_for(self.value)
        if self.knowledge_state is not expected_state:
            raise ValueError(f"knowledge_state must be {expected_state.value} for value {self.value!r}")

    @classmethod
    def unknown(cls, observation_id: ObservationId) -> "ObservationEvidence":
        return cls(observation_id=observation_id)

    @classmethod
    def known(
        cls,
        observation_id: ObservationId,
        value: ClinicalValue,
        *,
        validity: ObservationValidity | None = None,
        provenance: PolicyProvenance | None = None,
    ) -> "ObservationEvidence":
        return cls(
            observation_id=observation_id,
            knowledge_state=_knowledge_state_for(value),
            value=value,
            acquired=True,
            acquisition_mode=acquisition_mode_for(observation_id),
            validity=validity or ObservationValidity(EvidenceValidityStatus.VALID),
            provenance=provenance,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id.value,
            "knowledge_state": self.knowledge_state.value,
            "value": _serialize_value(self.value),
            "acquired": self.acquired,
            "acquisition_mode": self.acquisition_mode.value if self.acquisition_mode else None,
            "validity": self.validity.to_dict(),
            "provenance": self.provenance.to_dict() if self.provenance else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObservationEvidence":
        observation_id = ObservationId(data["observation_id"])
        raw_value = data.get("value")
        return cls(
            observation_id=observation_id,
            knowledge_state=KnowledgeState(data["knowledge_state"]),
            value=_deserialize_value(observation_id, raw_value) if raw_value is not None else None,
            acquired=data["acquired"],
            acquisition_mode=AcquisitionMode(data["acquisition_mode"]) if data.get("acquisition_mode") else None,
            validity=ObservationValidity.from_dict(data["validity"]),
            provenance=PolicyProvenance.from_dict(data["provenance"]) if data.get("provenance") else None,
        )


@dataclass(frozen=True)
class AcquisitionRequest:
    observation_id: ObservationId
    acquisition_mode: AcquisitionMode
    reason: AcquisitionReason
    priority_band: int
    priority_order: int
    provenance: PolicyProvenance
    can_change_classification: bool = False
    can_change_actions: bool = False
    can_trigger_or_add_urgent_action: bool = False

    def __post_init__(self) -> None:
        if self.acquisition_mode is not acquisition_mode_for(self.observation_id):
            raise ValueError(f"acquisition mode contradicts observation catalog for {self.observation_id.value}")
        if self.priority_band < 1 or self.priority_order < 0:
            raise ValueError("acquisition priorities must be positive-band and non-negative-order")
        if self.reason is AcquisitionReason.ASSESSMENT_COMPLETION_ONLY:
            if self.can_change_classification or self.can_change_actions or self.can_trigger_or_add_urgent_action:
                raise ValueError("assessment-only acquisition cannot carry decision-changing flags")
        elif not (self.can_change_classification or self.can_change_actions or self.can_trigger_or_add_urgent_action):
            raise ValueError("decision-directed acquisition requires a decision-changing flag")
        if self.reason is AcquisitionReason.CAN_CHANGE_CLASSIFICATION and not self.can_change_classification:
            raise ValueError("classification reason requires can_change_classification")
        if self.reason is AcquisitionReason.CAN_CHANGE_ACTION_BRANCH and not self.can_change_actions:
            raise ValueError("action reason requires can_change_actions")
        if self.reason in {
            AcquisitionReason.CAN_TRIGGER_URGENT_ACTION,
            AcquisitionReason.CAN_ADD_IMMEDIATE_ACTION,
        } and not self.can_trigger_or_add_urgent_action:
            raise ValueError("urgent-action reason requires can_trigger_or_add_urgent_action")

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id.value,
            "acquisition_mode": self.acquisition_mode.value,
            "reason": self.reason.value,
            "priority_band": self.priority_band,
            "priority_order": self.priority_order,
            "provenance": self.provenance.to_dict(),
            "can_change_classification": self.can_change_classification,
            "can_change_actions": self.can_change_actions,
            "can_trigger_or_add_urgent_action": self.can_trigger_or_add_urgent_action,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AcquisitionRequest":
        return cls(
            observation_id=ObservationId(data["observation_id"]),
            acquisition_mode=AcquisitionMode(data["acquisition_mode"]),
            reason=AcquisitionReason(data["reason"]),
            priority_band=data["priority_band"],
            priority_order=data["priority_order"],
            provenance=PolicyProvenance.from_dict(data["provenance"]),
            can_change_classification=data.get("can_change_classification", False),
            can_change_actions=data.get("can_change_actions", False),
            can_trigger_or_add_urgent_action=data.get("can_trigger_or_add_urgent_action", False),
        )


@dataclass(frozen=True)
class PathwayPolicyState:
    pathway: Pathway
    entry_status: EntryStatus
    possible_classifications: tuple[Classification, ...]
    decision_status: DecisionStatus
    action_set_sufficient: bool
    exact_rule_sufficient: bool
    possible_fired_rule_ids: tuple[str, ...]
    assessment_complete: bool

    def __post_init__(self) -> None:
        _require_unique(self.possible_classifications, "possible_classifications")
        _require_unique(self.possible_fired_rule_ids, "possible_fired_rule_ids")
        for classification in self.possible_classifications:
            if classification not in _CLASSIFICATIONS_BY_PATHWAY[self.pathway]:
                raise ValueError(f"classification {classification.value} is invalid for {self.pathway.value}")
        if self.entry_status is EntryStatus.NOT_APPLICABLE and self.possible_classifications:
            raise ValueError("a not-applicable pathway cannot have possible classifications")
        if self.exact_rule_sufficient and len(self.possible_fired_rule_ids) > 1:
            raise ValueError("exact-rule sufficiency cannot have multiple possible fired rules")

    def to_dict(self) -> dict[str, Any]:
        return {
            "pathway": self.pathway.value,
            "entry_status": self.entry_status.value,
            "possible_classifications": [item.value for item in self.possible_classifications],
            "decision_status": self.decision_status.value,
            "action_set_sufficient": self.action_set_sufficient,
            "exact_rule_sufficient": self.exact_rule_sufficient,
            "possible_fired_rule_ids": list(self.possible_fired_rule_ids),
            "assessment_complete": self.assessment_complete,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PathwayPolicyState":
        return cls(
            pathway=Pathway(data["pathway"]),
            entry_status=EntryStatus(data["entry_status"]),
            possible_classifications=tuple(Classification(item) for item in data.get("possible_classifications", [])),
            decision_status=DecisionStatus(data["decision_status"]),
            action_set_sufficient=data["action_set_sufficient"],
            exact_rule_sufficient=data["exact_rule_sufficient"],
            possible_fired_rule_ids=tuple(data.get("possible_fired_rule_ids", [])),
            assessment_complete=data["assessment_complete"],
        )


@dataclass(frozen=True)
class InformationPolicyResult:
    policy_id: str
    constraint_set_id: str
    scope_status: ScopeStatus
    pathway_states: tuple[PathwayPolicyState, ...]
    supported_encounter_decision_status: DecisionStatus
    supported_encounter_action_set_sufficient: bool
    supported_encounter_assessment_complete: bool
    urgent_action_required: bool
    known_actions: tuple[Action, ...] = ()
    possible_additional_actions: tuple[Action, ...] = ()
    decision_directed_acquisitions: tuple[AcquisitionRequest, ...] = ()
    assessment_completion_acquisitions: tuple[AcquisitionRequest, ...] = ()
    applied_constraint_ids: tuple[str, ...] = ()
    unresolved_question_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.policy_id or not self.constraint_set_id:
            raise ValueError("policy_id and constraint_set_id are required")
        _require_unique(tuple(item.pathway for item in self.pathway_states), "pathway_states")
        _require_unique(self.known_actions, "known_actions")
        _require_unique(self.possible_additional_actions, "possible_additional_actions")
        _require_unique(self.applied_constraint_ids, "applied_constraint_ids")
        _require_unique(self.unresolved_question_ids, "unresolved_question_ids")
        if set(self.known_actions) & set(self.possible_additional_actions):
            raise ValueError("known and possible additional actions must be disjoint")
        _validate_acquisition_channels(
            self.decision_directed_acquisitions,
            self.assessment_completion_acquisitions,
        )
        if self.urgent_action_required and not self.known_actions:
            raise ValueError("urgent_action_required needs at least one known action")
        if self.supported_encounter_assessment_complete and self.assessment_completion_acquisitions:
            raise ValueError("assessment-complete state cannot retain assessment acquisitions")

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "constraint_set_id": self.constraint_set_id,
            "scope_status": self.scope_status.value,
            "pathway_states": [item.to_dict() for item in self.pathway_states],
            "supported_encounter_decision_status": self.supported_encounter_decision_status.value,
            "supported_encounter_action_set_sufficient": self.supported_encounter_action_set_sufficient,
            "supported_encounter_assessment_complete": self.supported_encounter_assessment_complete,
            "urgent_action_required": self.urgent_action_required,
            "known_actions": [item.value for item in self.known_actions],
            "possible_additional_actions": [item.value for item in self.possible_additional_actions],
            "decision_directed_acquisitions": [item.to_dict() for item in self.decision_directed_acquisitions],
            "assessment_completion_acquisitions": [item.to_dict() for item in self.assessment_completion_acquisitions],
            "applied_constraint_ids": list(self.applied_constraint_ids),
            "unresolved_question_ids": list(self.unresolved_question_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InformationPolicyResult":
        return cls(
            policy_id=data["policy_id"],
            constraint_set_id=data["constraint_set_id"],
            scope_status=ScopeStatus(data["scope_status"]),
            pathway_states=tuple(PathwayPolicyState.from_dict(item) for item in data.get("pathway_states", [])),
            supported_encounter_decision_status=DecisionStatus(data["supported_encounter_decision_status"]),
            supported_encounter_action_set_sufficient=data["supported_encounter_action_set_sufficient"],
            supported_encounter_assessment_complete=data["supported_encounter_assessment_complete"],
            urgent_action_required=data["urgent_action_required"],
            known_actions=tuple(Action(item) for item in data.get("known_actions", [])),
            possible_additional_actions=tuple(Action(item) for item in data.get("possible_additional_actions", [])),
            decision_directed_acquisitions=tuple(
                AcquisitionRequest.from_dict(item) for item in data.get("decision_directed_acquisitions", [])
            ),
            assessment_completion_acquisitions=tuple(
                AcquisitionRequest.from_dict(item) for item in data.get("assessment_completion_acquisitions", [])
            ),
            applied_constraint_ids=tuple(data.get("applied_constraint_ids", [])),
            unresolved_question_ids=tuple(data.get("unresolved_question_ids", [])),
        )


@dataclass(frozen=True)
class PartialCaseState:
    state_id: str
    observations: tuple[ObservationEvidence, ...]
    policy_result: InformationPolicyResult

    def __post_init__(self) -> None:
        if not self.state_id:
            raise ValueError("state_id is required")
        _require_complete_catalog(self.observations, "partial-state observations")
        by_id = {item.observation_id: item for item in self.observations}
        object.__setattr__(self, "observations", tuple(by_id[item] for item in CANONICAL_OBSERVATION_ORDER))
        self._validate_approved_constraints()

    def _validate_approved_constraints(self) -> None:
        lethargic = self.observation(ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS)
        restless = self.observation(ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE)
        if _known_value(lethargic) is True and _known_value(restless) is True:
            raise ValueError("a child cannot be both lethargic/unconscious and restless/irritable")
        unable = self.observation(ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED)
        drinking = self.observation(ObservationId.DEHYDRATION_DRINKING_STATUS)
        if _known_value(unable) is False and _known_value(drinking) is DrinkingStatus.UNABLE:
            raise ValueError("UNABLE drinking status conflicts with a negative general danger sign")

    @classmethod
    def from_observations(
        cls,
        state_id: str,
        known_or_acquired: tuple[ObservationEvidence, ...],
        policy_result: InformationPolicyResult,
    ) -> "PartialCaseState":
        _require_unique(tuple(item.observation_id for item in known_or_acquired), "known_or_acquired")
        by_id = {item.observation_id: item for item in known_or_acquired}
        observations = tuple(by_id.get(item, ObservationEvidence.unknown(item)) for item in CANONICAL_OBSERVATION_ORDER)
        return cls(state_id=state_id, observations=observations, policy_result=policy_result)

    def observation(self, observation_id: ObservationId) -> ObservationEvidence:
        return next(item for item in self.observations if item.observation_id is observation_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_id": self.state_id,
            "observations": [self.observation(item).to_dict() for item in CANONICAL_OBSERVATION_ORDER],
            "policy_result": self.policy_result.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PartialCaseState":
        return cls(
            state_id=data["state_id"],
            observations=tuple(ObservationEvidence.from_dict(item) for item in data["observations"]),
            policy_result=InformationPolicyResult.from_dict(data["policy_result"]),
        )


@dataclass(frozen=True)
class ExpectedAssistantSemantics:
    behaviors: tuple[AssistantBehavior, ...]
    scope_status: ScopeStatus
    decision_status: DecisionStatus
    action_set_sufficient: bool
    assessment_complete: bool
    urgent_action_required: bool
    exact_rule_sufficient: bool
    detected_danger_signs: tuple[DangerSign, ...] = ()
    classifications: dict[Pathway, Classification] = field(default_factory=dict)
    possible_classifications: dict[Pathway, tuple[Classification, ...]] = field(default_factory=dict)
    referral: ReferralRequirement = ReferralRequirement.NONE
    actions: tuple[Action, ...] = ()
    possible_fired_rule_ids: tuple[str, ...] = ()
    decision_directed_acquisitions: tuple[AcquisitionRequest, ...] = ()
    assessment_completion_acquisitions: tuple[AcquisitionRequest, ...] = ()
    not_applicable_pathways: tuple[Pathway, ...] = ()
    blocked_observation_ids: tuple[ObservationId, ...] = ()
    unresolved_question_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_unique(self.behaviors, "behaviors")
        _require_unique(self.detected_danger_signs, "detected_danger_signs")
        _require_unique(self.actions, "actions")
        _require_unique(self.possible_fired_rule_ids, "possible_fired_rule_ids")
        _require_unique(self.not_applicable_pathways, "not_applicable_pathways")
        _require_unique(self.blocked_observation_ids, "blocked_observation_ids")
        _require_unique(self.unresolved_question_ids, "unresolved_question_ids")
        _validate_classifications(self.classifications)
        for pathway, possibilities in self.possible_classifications.items():
            _require_unique(possibilities, f"possible_classifications.{pathway.value}")
            _validate_classifications({pathway: item for item in possibilities})
        _validate_acquisition_channels(
            self.decision_directed_acquisitions,
            self.assessment_completion_acquisitions,
        )
        has_acquisitions = bool(self.decision_directed_acquisitions or self.assessment_completion_acquisitions)
        if (AssistantBehavior.REQUEST_INFORMATION in self.behaviors) != has_acquisitions:
            raise ValueError("REQUEST_INFORMATION must match acquisition requests")
        if (AssistantBehavior.EMIT_CLASSIFICATION in self.behaviors) != bool(self.classifications):
            raise ValueError("EMIT_CLASSIFICATION must match emitted classifications")
        if (AssistantBehavior.EMIT_ACTIONS in self.behaviors) != bool(self.actions):
            raise ValueError("EMIT_ACTIONS must match emitted actions")
        if (AssistantBehavior.EMIT_URGENT_ACTION in self.behaviors) != self.urgent_action_required:
            raise ValueError("EMIT_URGENT_ACTION must match urgent_action_required")
        if self.urgent_action_required and not self.actions:
            raise ValueError("urgent assistant behavior requires source-backed actions")
        if (AssistantBehavior.REPORT_NOT_APPLICABLE in self.behaviors) != bool(self.not_applicable_pathways):
            raise ValueError("REPORT_NOT_APPLICABLE must match not_applicable_pathways")
        if (AssistantBehavior.REPORT_OUT_OF_SCOPE in self.behaviors) != (self.scope_status is ScopeStatus.OUT_OF_SCOPE):
            raise ValueError("REPORT_OUT_OF_SCOPE must match scope_status")
        blocked = self.decision_status is DecisionStatus.BLOCKED or bool(self.blocked_observation_ids)
        if (AssistantBehavior.REPORT_BLOCKED in self.behaviors) != blocked:
            raise ValueError("REPORT_BLOCKED must match blocked decision state")
        if self.exact_rule_sufficient and len(self.possible_fired_rule_ids) > 1:
            raise ValueError("exact-rule sufficiency cannot have multiple possible fired rules")

    def to_dict(self) -> dict[str, Any]:
        return {
            "behaviors": [item.value for item in self.behaviors],
            "scope_status": self.scope_status.value,
            "decision_status": self.decision_status.value,
            "action_set_sufficient": self.action_set_sufficient,
            "assessment_complete": self.assessment_complete,
            "urgent_action_required": self.urgent_action_required,
            "exact_rule_sufficient": self.exact_rule_sufficient,
            "detected_danger_signs": [item.value for item in self.detected_danger_signs],
            "classifications": {key.value: value.value for key, value in self.classifications.items()},
            "possible_classifications": {
                key.value: [item.value for item in value] for key, value in self.possible_classifications.items()
            },
            "referral": self.referral.value,
            "actions": [item.value for item in self.actions],
            "possible_fired_rule_ids": list(self.possible_fired_rule_ids),
            "decision_directed_acquisitions": [item.to_dict() for item in self.decision_directed_acquisitions],
            "assessment_completion_acquisitions": [item.to_dict() for item in self.assessment_completion_acquisitions],
            "not_applicable_pathways": [item.value for item in self.not_applicable_pathways],
            "blocked_observation_ids": [item.value for item in self.blocked_observation_ids],
            "unresolved_question_ids": list(self.unresolved_question_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpectedAssistantSemantics":
        return cls(
            behaviors=tuple(AssistantBehavior(item) for item in data["behaviors"]),
            scope_status=ScopeStatus(data["scope_status"]),
            decision_status=DecisionStatus(data["decision_status"]),
            action_set_sufficient=data["action_set_sufficient"],
            assessment_complete=data["assessment_complete"],
            urgent_action_required=data["urgent_action_required"],
            exact_rule_sufficient=data["exact_rule_sufficient"],
            detected_danger_signs=tuple(DangerSign(item) for item in data.get("detected_danger_signs", [])),
            classifications={Pathway(key): Classification(value) for key, value in data.get("classifications", {}).items()},
            possible_classifications={
                Pathway(key): tuple(Classification(item) for item in value)
                for key, value in data.get("possible_classifications", {}).items()
            },
            referral=ReferralRequirement(data.get("referral", "NONE")),
            actions=tuple(Action(item) for item in data.get("actions", [])),
            possible_fired_rule_ids=tuple(data.get("possible_fired_rule_ids", [])),
            decision_directed_acquisitions=tuple(
                AcquisitionRequest.from_dict(item) for item in data.get("decision_directed_acquisitions", [])
            ),
            assessment_completion_acquisitions=tuple(
                AcquisitionRequest.from_dict(item) for item in data.get("assessment_completion_acquisitions", [])
            ),
            not_applicable_pathways=tuple(Pathway(item) for item in data.get("not_applicable_pathways", [])),
            blocked_observation_ids=tuple(ObservationId(item) for item in data.get("blocked_observation_ids", [])),
            unresolved_question_ids=tuple(data.get("unresolved_question_ids", [])),
        )


@dataclass(frozen=True)
class ModelVisibleMessage:
    role: ConversationRole
    content: str

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("model-visible message content is required")

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role.value, "content": self.content}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelVisibleMessage":
        return cls(role=ConversationRole(data["role"]), content=data["content"])


@dataclass(frozen=True)
class ConversationTurn:
    turn_index: int
    visible_message: ModelVisibleMessage
    state_after_turn_id: str
    revealed_observations: tuple[ObservationEvidence, ...] = ()
    expected_assistant_semantics: ExpectedAssistantSemantics | None = None

    def __post_init__(self) -> None:
        if self.turn_index < 0 or not self.state_after_turn_id:
            raise ValueError("turn index and state_after_turn_id are required")
        _require_unique(tuple(item.observation_id for item in self.revealed_observations), "revealed_observations")
        if any(not item.acquired for item in self.revealed_observations):
            raise ValueError("revealed observations must represent an acquisition")
        if self.visible_message.role is ConversationRole.ASSISTANT:
            if self.expected_assistant_semantics is None:
                raise ValueError("assistant natural-language target requires structured semantics")
            if self.revealed_observations:
                raise ValueError("assistant turns cannot reveal acquired user/worker observations")
        elif self.expected_assistant_semantics is not None:
            raise ValueError("only assistant turns may contain expected assistant semantics")

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "visible_message": self.visible_message.to_dict(),
            "state_after_turn_id": self.state_after_turn_id,
            "revealed_observations": [item.to_dict() for item in self.revealed_observations],
            "expected_assistant_semantics": (
                self.expected_assistant_semantics.to_dict() if self.expected_assistant_semantics else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationTurn":
        return cls(
            turn_index=data["turn_index"],
            visible_message=ModelVisibleMessage.from_dict(data["visible_message"]),
            state_after_turn_id=data["state_after_turn_id"],
            revealed_observations=tuple(
                ObservationEvidence.from_dict(item) for item in data.get("revealed_observations", [])
            ),
            expected_assistant_semantics=(
                ExpectedAssistantSemantics.from_dict(data["expected_assistant_semantics"])
                if data.get("expected_assistant_semantics")
                else None
            ),
        )


@dataclass(frozen=True)
class TrajectoryInteraction:
    turns: tuple[ConversationTurn, ...]

    def __post_init__(self) -> None:
        if not self.turns:
            raise ValueError("a trajectory interaction requires at least one turn")
        if tuple(item.turn_index for item in self.turns) != tuple(range(len(self.turns))):
            raise ValueError("turn indices must be contiguous and start at zero")

    def model_visible_messages(self) -> list[dict[str, str]]:
        """Return only role/content pairs; no latent values or semantic labels."""

        return [turn.visible_message.to_dict() for turn in self.turns]

    def prompt_before_assistant(self, turn_index: int) -> list[dict[str, str]]:
        """Return the model-visible prompt preceding one assistant target."""

        turn = self.turns[turn_index]
        if turn.visible_message.role is not ConversationRole.ASSISTANT:
            raise ValueError("prompt target turn must be an assistant turn")
        return [item.visible_message.to_dict() for item in self.turns[:turn_index]]

    def to_dict(self) -> dict[str, Any]:
        return {"turns": [item.to_dict() for item in self.turns]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrajectoryInteraction":
        return cls(turns=tuple(ConversationTurn.from_dict(item) for item in data["turns"]))


@dataclass(frozen=True)
class TrajectoryMetadata:
    schema_version: str
    rule_set_id: str
    information_policy_id: str
    constraint_set_id: str
    generator_version: str
    generation_seed: int
    rule_family: str
    logic_signature: str
    template_family: str
    corpus_role: CorpusRole = CorpusRole.UNASSIGNED
    counterfactual_group_id: str | None = None
    split_group_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != TRAJECTORY_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {TRAJECTORY_SCHEMA_VERSION}")
        required = {
            "rule_set_id": self.rule_set_id,
            "information_policy_id": self.information_policy_id,
            "constraint_set_id": self.constraint_set_id,
            "generator_version": self.generator_version,
            "rule_family": self.rule_family,
            "logic_signature": self.logic_signature,
            "template_family": self.template_family,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"trajectory metadata is missing values: {missing}")
        _require_unique(self.split_group_ids, "split_group_ids")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "rule_set_id": self.rule_set_id,
            "information_policy_id": self.information_policy_id,
            "constraint_set_id": self.constraint_set_id,
            "generator_version": self.generator_version,
            "generation_seed": self.generation_seed,
            "rule_family": self.rule_family,
            "logic_signature": self.logic_signature,
            "template_family": self.template_family,
            "corpus_role": self.corpus_role.value,
            "counterfactual_group_id": self.counterfactual_group_id,
            "split_group_ids": list(self.split_group_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrajectoryMetadata":
        return cls(
            schema_version=data["schema_version"],
            rule_set_id=data["rule_set_id"],
            information_policy_id=data["information_policy_id"],
            constraint_set_id=data["constraint_set_id"],
            generator_version=data["generator_version"],
            generation_seed=data["generation_seed"],
            rule_family=data["rule_family"],
            logic_signature=data["logic_signature"],
            template_family=data["template_family"],
            corpus_role=CorpusRole(data.get("corpus_role", "UNASSIGNED")),
            counterfactual_group_id=data.get("counterfactual_group_id"),
            split_group_ids=tuple(data.get("split_group_ids", [])),
        )


@dataclass(frozen=True)
class ClinicalTrajectory:
    trajectory_id: str
    latent_truth: LatentClinicalCase
    states: tuple[PartialCaseState, ...]
    interaction: TrajectoryInteraction
    initial_state_id: str
    terminal_state_id: str | None
    metadata: TrajectoryMetadata

    def __post_init__(self) -> None:
        if not self.trajectory_id:
            raise ValueError("trajectory_id is required")
        state_ids = tuple(item.state_id for item in self.states)
        _require_unique(state_ids, "state IDs")
        if self.initial_state_id not in state_ids:
            raise ValueError("initial_state_id does not reference a state")
        if self.terminal_state_id is not None and self.terminal_state_id not in state_ids:
            raise ValueError("terminal_state_id does not reference a state")
        if self.interaction.turns[0].state_after_turn_id != self.initial_state_id:
            raise ValueError("the first visible turn must establish initial_state_id")
        if self.terminal_state_id is not None:
            if self.interaction.turns[-1].state_after_turn_id != self.terminal_state_id:
                raise ValueError("terminal_state_id must be the state after the final turn")
        by_state = {item.state_id: item for item in self.states}
        if any(turn.state_after_turn_id not in by_state for turn in self.interaction.turns):
            raise ValueError("every turn must reference a known partial state")
        if self.latent_truth.scope_status is ScopeStatus.IN_SCOPE and self.metadata.rule_set_id == "":
            raise ValueError("in-scope trajectories require a rule-set identity")
        self._validate_reveals(by_state)

    def _validate_reveals(self, by_state: dict[str, PartialCaseState]) -> None:
        revealed: dict[ObservationId, ObservationEvidence] = {}
        for turn in self.interaction.turns:
            for item in turn.revealed_observations:
                latent_value = self.latent_truth.observation(item.observation_id).value
                if item.knowledge_state is not KnowledgeState.UNKNOWN and item.value != latent_value:
                    raise ValueError(f"revealed value contradicts latent truth for {item.observation_id.value}")
                previous = revealed.get(item.observation_id)
                if previous is not None and previous.knowledge_state is not KnowledgeState.UNKNOWN:
                    if item != previous:
                        raise ValueError(f"known observation changed across turns: {item.observation_id.value}")
                revealed[item.observation_id] = item
            state = by_state[turn.state_after_turn_id]
            for record in state.observations:
                if record.acquired and revealed.get(record.observation_id) != record:
                    raise ValueError(
                        f"state {state.state_id} contains evidence not revealed to the interaction: "
                        f"{record.observation_id.value}"
                    )
                previous = revealed.get(record.observation_id)
                if previous is not None and previous.knowledge_state is not KnowledgeState.UNKNOWN:
                    if record.knowledge_state is KnowledgeState.UNKNOWN or record.value != previous.value:
                        raise ValueError(f"known state regressed for {record.observation_id.value}")

    def model_visible_messages(self) -> list[dict[str, str]]:
        return self.interaction.model_visible_messages()

    def to_dict(self) -> dict[str, Any]:
        return {
            "trajectory_id": self.trajectory_id,
            "latent_truth": self.latent_truth.to_dict(),
            "states": [item.to_dict() for item in self.states],
            "interaction": self.interaction.to_dict(),
            "initial_state_id": self.initial_state_id,
            "terminal_state_id": self.terminal_state_id,
            "metadata": self.metadata.to_dict(),
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + ("\n" if indent is not None else "")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClinicalTrajectory":
        return cls(
            trajectory_id=data["trajectory_id"],
            latent_truth=LatentClinicalCase.from_dict(data["latent_truth"]),
            states=tuple(PartialCaseState.from_dict(item) for item in data["states"]),
            interaction=TrajectoryInteraction.from_dict(data["interaction"]),
            initial_state_id=data["initial_state_id"],
            terminal_state_id=data.get("terminal_state_id"),
            metadata=TrajectoryMetadata.from_dict(data["metadata"]),
        )

    @classmethod
    def from_json(cls, content: str) -> "ClinicalTrajectory":
        return cls.from_dict(json.loads(content))


def _validate_acquisition_channels(
    decision_directed: tuple[AcquisitionRequest, ...],
    assessment_completion: tuple[AcquisitionRequest, ...],
) -> None:
    decision_ids = tuple(item.observation_id for item in decision_directed)
    assessment_ids = tuple(item.observation_id for item in assessment_completion)
    _require_unique(decision_ids, "decision_directed_acquisitions")
    _require_unique(assessment_ids, "assessment_completion_acquisitions")
    overlap = set(decision_ids) & set(assessment_ids)
    if overlap:
        raise ValueError(f"acquisition channels overlap: {sorted(item.value for item in overlap)}")
    if any(item.reason is AcquisitionReason.ASSESSMENT_COMPLETION_ONLY for item in decision_directed):
        raise ValueError("decision-directed channel cannot contain assessment-only acquisitions")
    if any(item.reason is not AcquisitionReason.ASSESSMENT_COMPLETION_ONLY for item in assessment_completion):
        raise ValueError("assessment-completion channel requires assessment-only reasons")


def _validate_classifications(classifications: dict[Pathway, Classification]) -> None:
    for pathway, classification in classifications.items():
        if classification not in _CLASSIFICATIONS_BY_PATHWAY[pathway]:
            raise ValueError(f"classification {classification.value} is invalid for {pathway.value}")


def _require_complete_catalog(items: tuple[Any, ...], field_name: str) -> None:
    observation_ids = tuple(item.observation_id for item in items)
    _require_unique(observation_ids, field_name)
    if set(observation_ids) != set(CANONICAL_OBSERVATION_ORDER):
        missing = set(CANONICAL_OBSERVATION_ORDER) - set(observation_ids)
        extra = set(observation_ids) - set(CANONICAL_OBSERVATION_ORDER)
        raise ValueError(
            f"{field_name} must contain the full observation catalog; "
            f"missing={sorted(item.value for item in missing)}, extra={sorted(item.value for item in extra)}"
        )


def _validate_value(observation_id: ObservationId, value: ClinicalValue) -> None:
    if observation_id is ObservationId.AGE_MONTHS:
        if type(value) is not int or value < 0:
            raise ValueError("age_months must be a non-negative integer")
    elif observation_id in _BOOLEAN_OBSERVATIONS:
        if type(value) is not bool:
            raise ValueError(f"{observation_id.value} must be boolean")
    elif observation_id is ObservationId.RESPIRATORY_RATE:
        if type(value) is not int or value < 0:
            raise ValueError("respiratory_rate must be a non-negative integer")
    elif observation_id is ObservationId.DEHYDRATION_DRINKING_STATUS:
        if not isinstance(value, DrinkingStatus):
            raise ValueError("drinking_status must be a DrinkingStatus")
    elif observation_id is ObservationId.DEHYDRATION_SKIN_PINCH:
        if not isinstance(value, SkinPinch):
            raise ValueError("skin_pinch must be a SkinPinch")
    else:  # pragma: no cover - exhaustive ObservationId guard
        raise ValueError(f"unsupported observation: {observation_id.value}")


def _knowledge_state_for(value: ClinicalValue) -> KnowledgeState:
    if type(value) is bool:
        return KnowledgeState.KNOWN_PRESENT if value else KnowledgeState.KNOWN_ABSENT
    return KnowledgeState.KNOWN_VALUE


def _known_value(record: ObservationEvidence) -> ClinicalValue | None:
    return record.value if record.knowledge_state is not KnowledgeState.UNKNOWN else None


def _serialize_value(value: ClinicalValue | None) -> bool | int | str | None:
    return value.value if isinstance(value, StringEnum) else value


def _deserialize_value(observation_id: ObservationId, value: Any) -> ClinicalValue:
    if observation_id is ObservationId.DEHYDRATION_DRINKING_STATUS:
        return DrinkingStatus(value)
    if observation_id is ObservationId.DEHYDRATION_SKIN_PINCH:
        return SkinPinch(value)
    return value


def _source_provenance_to_dict(provenance: SourceProvenance) -> dict[str, Any]:
    return {
        "document": provenance.document,
        "edition": provenance.edition,
        "source_pdf_pages": list(provenance.source_pdf_pages),
        "source_printed_pages": list(provenance.source_printed_pages),
        "source_rule_ids": list(provenance.source_rule_ids),
    }


def _source_provenance_from_dict(data: dict[str, Any]) -> SourceProvenance:
    return SourceProvenance(
        document=data["document"],
        edition=data["edition"],
        source_pdf_pages=tuple(data.get("source_pdf_pages", [])),
        source_printed_pages=tuple(data.get("source_printed_pages", [])),
        source_rule_ids=tuple(data.get("source_rule_ids", [])),
    )


def _require_unique(values: tuple[Any, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} cannot contain duplicates")
