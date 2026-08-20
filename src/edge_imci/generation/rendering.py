"""Proposed natural PHC renderings over fixed golden semantics.

This module realizes language only. Clinical and information-policy semantics
remain owned by the committed golden trajectories.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

from edge_imci.schemas.case import Action, Classification, DrinkingStatus, Pathway, SkinPinch
from edge_imci.schemas.trajectory import (
    AcquisitionMode,
    AcquisitionRequest,
    DecisionStatus,
    ExpectedAssistantSemantics,
    KnowledgeState,
    ObservationEvidence,
    ObservationId,
)

REFERENCE_RENDERER_ID = "edge-imci-phc-reference-renderer-v1"
REFERENCE_STATUS = "PROPOSED_FOR_HUMAN_REVIEW"

_CLASSIFICATION_LABELS = {
    (Pathway.GENERAL_DANGER_SIGNS, Classification.VERY_SEVERE_DISEASE): "Very severe disease",
    (Pathway.RESPIRATORY, Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE): "Severe pneumonia or very severe disease",
    (Pathway.RESPIRATORY, Classification.PNEUMONIA): "Pneumonia",
    (Pathway.RESPIRATORY, Classification.COUGH_OR_COLD): "Cough or cold",
    (Pathway.DEHYDRATION, Classification.SEVERE_DEHYDRATION): "Severe dehydration",
    (Pathway.DEHYDRATION, Classification.SOME_DEHYDRATION): "Some dehydration",
    (Pathway.DEHYDRATION, Classification.NO_DEHYDRATION): "No dehydration",
}

_ACTION_CLAUSES = {
    Action.COMPLETE_ASSESSMENT_QUICKLY: "complete the remaining assessment quickly",
    Action.GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY: "give the indicated pre-referral treatment immediately",
    Action.PREVENT_LOW_BLOOD_SUGAR: "prevent low blood sugar",
    Action.KEEP_WARM: "keep the child warm",
    Action.URGENT_REFERRAL: "arrange urgent referral",
    Action.GIVE_DIAZEPAM_IF_CONVULSING_NOW: "give diazepam because the child is convulsing now",
    Action.GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC: "give the first dose of an appropriate antibiotic",
    Action.GIVE_ORAL_AMOXICILLIN_5_DAYS: "give oral amoxicillin for 5 days",
    Action.SOOTHE_THROAT_AND_RELIEVE_COUGH: "soothe the throat and relieve the cough with a safe remedy",
    Action.ADVISE_WHEN_TO_RETURN_IMMEDIATELY: "advise the caregiver when to return immediately",
    Action.FOLLOW_UP_3_DAYS: "follow up in 3 days",
    Action.FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING: "follow up in 5 days if the child is not improving",
    Action.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C: "give Plan C fluid for severe dehydration",
    Action.GIVE_FLUID_ZINC_AND_FOOD_PLAN_B: "give Plan B fluid, zinc, and food",
    Action.GIVE_FLUID_ZINC_AND_FOOD_PLAN_A: "give Plan A fluid, zinc, and food",
    Action.FREQUENT_ORS_SIPS_DURING_REFERRAL: "give frequent sips of ORS during referral",
    Action.CONTINUE_BREASTFEEDING: "continue breastfeeding",
}

_ACTION_ORDER = (
    Action.GIVE_DIAZEPAM_IF_CONVULSING_NOW,
    Action.GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC,
    Action.GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY,
    Action.PREVENT_LOW_BLOOD_SUGAR,
    Action.KEEP_WARM,
    Action.FREQUENT_ORS_SIPS_DURING_REFERRAL,
    Action.CONTINUE_BREASTFEEDING,
    Action.URGENT_REFERRAL,
    Action.COMPLETE_ASSESSMENT_QUICKLY,
    Action.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C,
    Action.GIVE_FLUID_ZINC_AND_FOOD_PLAN_B,
    Action.GIVE_FLUID_ZINC_AND_FOOD_PLAN_A,
    Action.GIVE_ORAL_AMOXICILLIN_5_DAYS,
    Action.SOOTHE_THROAT_AND_RELIEVE_COUGH,
    Action.ADVISE_WHEN_TO_RETURN_IMMEDIATELY,
    Action.FOLLOW_UP_3_DAYS,
    Action.FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING,
)

_REQUEST_CLAUSES = {
    ObservationId.AGE_MONTHS: "confirm the child's age in completed months from the caregiver or record",
    ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: "ask the caregiver whether the child has cough or difficult breathing",
    ObservationId.HAS_DIARRHOEA: "ask the caregiver whether the child has diarrhoea",
    ObservationId.DANGER_CONVULSING_NOW: "check whether the child is convulsing now",
    ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS: "check whether the child is lethargic or unconscious",
    ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED: "ask the caregiver whether the child is able to drink or breastfeed",
    ObservationId.DANGER_VOMITS_EVERYTHING: "ask the caregiver whether the child vomits everything",
    ObservationId.DANGER_HAD_CONVULSIONS: "ask the caregiver whether the child has had convulsions during this illness",
    ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM: "check for stridor while the child is calm",
    ObservationId.RESPIRATORY_CHEST_INDRAWING: "check for chest indrawing while the child is calm",
    ObservationId.RESPIRATORY_RATE: "count the child's breaths for one full minute while the child is calm and report the respiratory rate",
    ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE: "check whether the child is restless or irritable",
    ObservationId.DEHYDRATION_SUNKEN_EYES: "check whether the child's eyes are sunken",
    ObservationId.DEHYDRATION_DRINKING_STATUS: "offer fluid and observe whether the child drinks normally, eagerly or thirstily, poorly, or is unable to drink",
    ObservationId.DEHYDRATION_SKIN_PINCH: "pinch the abdominal skin and observe how quickly it returns",
}

_INTERNAL_TERMS = (
    "decision_sufficient",
    "action_set_sufficient",
    "assessment_complete",
    "decision-directed",
    "assessment-completion",
    "information policy",
    "schema",
    "possible_fired_rule_ids",
    "exact_rule_sufficient",
    "decision: sufficient",
    "decision: insufficient",
    "decision requests",
    "remaining assessment requests",
    "sufficiency",
    "sufficient",
)


@dataclass(frozen=True)
class ProposedReferenceTurn:
    turn_index: int
    role: str
    text: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "role": self.role,
            "text": self.text,
            "note": self.note,
        }


@dataclass(frozen=True)
class ProposedReferenceRendering:
    golden_case_id: str
    status: str
    renderer_id: str
    turns: tuple[ProposedReferenceTurn, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "golden_case_id": self.golden_case_id,
            "status": self.status,
            "renderer_id": self.renderer_id,
            "turns": [item.to_dict() for item in self.turns],
        }


def render_user_presentation(evidence: Iterable[ObservationEvidence]) -> str:
    """Render only newly revealed evidence, grouping related facts naturally."""

    known = [item for item in evidence if item.knowledge_state is not KnowledgeState.UNKNOWN]
    by_id = {item.observation_id: item.value for item in known}
    parts: list[str] = []

    if ObservationId.AGE_MONTHS in by_id:
        parts.append(f"The child is {by_id.pop(ObservationId.AGE_MONTHS)} months old.")

    entries = []
    if ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING in by_id:
        value = by_id.pop(ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING)
        entries.append("cough or difficult breathing" if value else "no cough or difficult breathing")
    if ObservationId.HAS_DIARRHOEA in by_id:
        value = by_id.pop(ObservationId.HAS_DIARRHOEA)
        entries.append("diarrhoea" if value else "no diarrhoea")
    if entries:
        parts.append(f"The caregiver reports {_join_clauses(entries)}.")

    caregiver_findings = []
    for observation_id, positive, negative in (
        (ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED, "the child is unable to drink or breastfeed", "the child can drink or breastfeed"),
        (ObservationId.DANGER_VOMITS_EVERYTHING, "the child vomits everything", "the child does not vomit everything"),
        (ObservationId.DANGER_HAD_CONVULSIONS, "convulsions during this illness", "no convulsions during this illness"),
    ):
        if observation_id in by_id:
            caregiver_findings.append(positive if by_id.pop(observation_id) else negative)
    if caregiver_findings:
        parts.append(f"The caregiver also reports {_join_clauses(caregiver_findings)}.")

    observed_findings = []
    for observation_id, positive, negative in (
        (ObservationId.DANGER_CONVULSING_NOW, "the child is convulsing now", "the child is not convulsing now"),
        (ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS, "the child is lethargic or unconscious", "the child is alert and not lethargic or unconscious"),
        (ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM, "stridor is present while calm", "there is no stridor while calm"),
        (ObservationId.RESPIRATORY_CHEST_INDRAWING, "chest indrawing is present while calm", "there is no chest indrawing while calm"),
        (ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE, "the child is restless or irritable", "the child is not restless or irritable"),
        (ObservationId.DEHYDRATION_SUNKEN_EYES, "the eyes are sunken", "the eyes are not sunken"),
    ):
        if observation_id in by_id:
            observed_findings.append(positive if by_id.pop(observation_id) else negative)
    if observed_findings:
        parts.append(f"On examination, {_join_clauses(observed_findings)}.")

    if ObservationId.RESPIRATORY_RATE in by_id:
        rate = by_id.pop(ObservationId.RESPIRATORY_RATE)
        parts.append(f"With the child calm, the respiratory rate counted for one full minute is {rate} breaths per minute.")

    if ObservationId.DEHYDRATION_DRINKING_STATUS in by_id:
        drinking = by_id.pop(ObservationId.DEHYDRATION_DRINKING_STATUS)
        phrase = {
            DrinkingStatus.NORMAL: "drinks normally",
            DrinkingStatus.EAGER_OR_THIRSTY: "drinks eagerly and appears thirsty",
            DrinkingStatus.POORLY: "drinks poorly",
            DrinkingStatus.UNABLE: "is unable to drink",
        }[drinking]
        parts.append(f"When offered fluid, the child {phrase}.")

    if ObservationId.DEHYDRATION_SKIN_PINCH in by_id:
        skin_pinch = by_id.pop(ObservationId.DEHYDRATION_SKIN_PINCH)
        phrase = {
            SkinPinch.NORMAL: "normally",
            SkinPinch.SLOWLY: "slowly",
            SkinPinch.VERY_SLOWLY: "very slowly",
        }[skin_pinch]
        parts.append(f"The abdominal skin pinch returns {phrase}.")

    if by_id:
        raise ValueError(f"unrendered known observations: {sorted(item.value for item in by_id)}")
    return " ".join(parts)


def render_assistant_reference(semantics: ExpectedAssistantSemantics) -> str:
    """Render a concise proposed PHC response without policy/schema language."""

    blocks: list[str] = []
    if semantics.urgent_action_required:
        blocks.append("URGENT: Act now.")

    if semantics.classifications:
        labels = [
            (
                f"{_CLASSIFICATION_LABELS[(pathway, classification)]} ({pathway.value.replace('_', ' ')})"
                if len(semantics.classifications) > 1 or pathway is Pathway.GENERAL_DANGER_SIGNS
                else _CLASSIFICATION_LABELS[(pathway, classification)]
            )
            for pathway, classification in semantics.classifications.items()
        ]
        blocks.append("Classification: " + "; ".join(labels) + ".")

    ordered_actions = [item for item in _ACTION_ORDER if item in semantics.actions]
    if ordered_actions:
        action_text = _join_clauses([_ACTION_CLAUSES[item] for item in ordered_actions])
        blocks.append(action_text[0].upper() + action_text[1:] + ".")

    if semantics.decision_directed_acquisitions:
        requests = _render_request_group(semantics.decision_directed_acquisitions)
        prefix = "Before classifying, " if not semantics.classifications else "To complete the classification, "
        blocks.append(prefix + requests + ".")

    if semantics.assessment_completion_acquisitions:
        requests = _render_request_group(semantics.assessment_completion_acquisitions)
        if semantics.urgent_action_required:
            blocks.append("Do not delay urgent treatment or referral. While preparing referral, " + requests + ".")
        else:
            blocks.append("Also " + requests + ".")

    if semantics.decision_status is DecisionStatus.BLOCKED and not semantics.decision_directed_acquisitions:
        blocks.append("The classification cannot be completed until the unresolved clinical evidence is checked.")

    return "\n\n".join(blocks)


def proposed_reference_note(
    role: str,
    evidence: tuple[ObservationEvidence, ...] = (),
    semantics: ExpectedAssistantSemantics | None = None,
) -> str:
    if role == "user":
        modes = sorted({item.acquisition_mode.value for item in evidence if item.acquisition_mode is not None})
        return "Groups only newly revealed facts; retained acquisition sources: " + ", ".join(modes) + "."
    if semantics is None:
        raise ValueError("assistant note requires semantics")
    notes = ["Uses classification terminology and source-backed actions only."]
    if semantics.urgent_action_required:
        notes.append("Urgency is placed first.")
    if semantics.decision_directed_acquisitions:
        notes.append("Decision-directed requests are introduced as required before classification.")
    if semantics.assessment_completion_acquisitions:
        notes.append("Remaining assessment is separated from the already determined decision and actions.")
    return " ".join(notes)


def build_reference_rendering(golden_record: dict[str, Any]) -> ProposedReferenceRendering:
    trajectory = golden_record["trajectory"]
    turns = []
    for turn in trajectory["interaction"]["turns"]:
        if turn["visible_message"]["role"] == "user":
            evidence = tuple(ObservationEvidence.from_dict(item) for item in turn["revealed_observations"])
            turns.append(
                ProposedReferenceTurn(
                    turn_index=turn["turn_index"],
                    role="user",
                    text=render_user_presentation(evidence),
                    note=proposed_reference_note("user", evidence=evidence),
                )
            )
        else:
            semantics = ExpectedAssistantSemantics.from_dict(turn["expected_assistant_semantics"])
            turns.append(
                ProposedReferenceTurn(
                    turn_index=turn["turn_index"],
                    role="assistant",
                    text=render_assistant_reference(semantics),
                    note=proposed_reference_note("assistant", semantics=semantics),
                )
            )
    return ProposedReferenceRendering(
        golden_case_id=golden_record["golden_case_id"],
        status=REFERENCE_STATUS,
        renderer_id=REFERENCE_RENDERER_ID,
        turns=tuple(turns),
    )


def compact_semantic_input(semantics: ExpectedAssistantSemantics) -> dict[str, Any]:
    return {
        "decision": semantics.decision_status.value,
        "urgent": semantics.urgent_action_required,
        "classifications": [
            {"pathway": pathway.value, "label": _CLASSIFICATION_LABELS[(pathway, classification)]}
            for pathway, classification in semantics.classifications.items()
        ],
        "actions": [_ACTION_CLAUSES[item] for item in _ACTION_ORDER if item in semantics.actions],
        "decision_requests": [_request_spec(item) for item in semantics.decision_directed_acquisitions],
        "remaining_assessment_requests": [_request_spec(item) for item in semantics.assessment_completion_acquisitions],
        "detected_danger_signs": [item.value for item in semantics.detected_danger_signs],
    }


def build_teacher_prompt(
    *,
    strategy: dict[str, Any],
    golden_case_id: str,
    turn_index: int,
    conversation_so_far: tuple[dict[str, str], ...],
    semantics: ExpectedAssistantSemantics,
) -> str:
    context = "\n".join(f"{item['role'].upper()}: {item['text']}" for item in conversation_so_far)
    semantic_json = json.dumps(compact_semantic_input(semantics), sort_keys=True)
    return (
        f"CASE_ID: {golden_case_id}\n"
        f"ASSISTANT_TURN: {turn_index}\n"
        f"RENDERER: {strategy['strategy_id']}\n\n"
        "You render fixed EdgeIMCI semantics into concise language for a frontline PHC worker. "
        "Do not add, omit, infer, or change clinical facts, classifications, actions, urgency, or requests. "
        "Use classification, never diagnosis. Never expose schema, policy, sufficiency flags, rule IDs, or unknown hidden facts. "
        "Caregiver questions must say to ask the caregiver. Clinician observations must say check or observe. "
        "Respiratory-rate measurement must require counting breaths for one full minute while the child is calm. "
        "If urgent is true, start with a short urgent instruction. Do not classify when classifications is empty. "
        "Keep decision requests distinct from remaining-assessment requests. Return only the assistant's words; no JSON, labels about the task, or commentary.\n\n"
        f"STRATEGY:\n{strategy['instructions']}\n\n"
        f"CONVERSATION SO FAR:\n{context}\n\n"
        f"FIXED SEMANTICS:\n{semantic_json}\n\n"
        "ASSISTANT RESPONSE:"
    )


def internal_term_hits(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    return tuple(item for item in _INTERNAL_TERMS if item in lowered)


def normalize_teacher_output(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    cleaned = re.sub(r"^ASSISTANT(?: RESPONSE)?:\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _request_spec(request: AcquisitionRequest) -> dict[str, str]:
    return {
        "observation_id": request.observation_id.value,
        "mode": request.acquisition_mode.value,
        "instruction": _REQUEST_CLAUSES[request.observation_id],
        "channel": "decision" if request.reason.value != "ASSESSMENT_COMPLETION_ONLY" else "assessment_completion",
    }


def _render_request_group(requests: tuple[AcquisitionRequest, ...]) -> str:
    clauses = [_REQUEST_CLAUSES[item.observation_id] for item in requests]
    modes = {item.acquisition_mode for item in requests}
    if modes == {AcquisitionMode.CLINICIAN_OBSERVATION} and len(clauses) > 1:
        clauses = [item.removeprefix("check ") for item in clauses]
        return "check " + _join_clauses(clauses)
    return _join_clauses(clauses)


def _join_clauses(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"
