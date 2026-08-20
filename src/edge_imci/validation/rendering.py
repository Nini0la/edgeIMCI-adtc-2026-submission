"""Deterministic lexical guards for natural EdgeIMCI rendering candidates.

The guards reject missing or additional structured concepts and acquisition-mode
errors. They do not claim to understand arbitrary prose; human review remains
mandatory for naturalness and subtle invented observations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from edge_imci.generation.rendering import compact_semantic_input, internal_term_hits
from edge_imci.schemas.trajectory import AcquisitionMode, ExpectedAssistantSemantics

NATURAL_VALIDATOR_ID = "edge-imci-natural-rendering-lexical-guards-v1"

_CLASSIFICATION_PATTERNS = {
    "Very severe disease": r"\bvery severe disease\b",
    "Severe pneumonia or very severe disease": r"\bsevere pneumonia\s*(?:/|or)\s*very severe disease\b",
    "Pneumonia": r"\bpneumonia\b",
    "Cough or cold": r"\bcough\s+or\s+cold\b",
    "Severe dehydration": r"\bsevere dehydration\b",
    "Some dehydration": r"\bsome dehydration\b",
    "No dehydration": r"\bno dehydration\b",
}

_ACTION_PATTERNS = {
    "complete the remaining assessment quickly": r"\bcomplete\b.{0,40}\bassessment\b.{0,20}\bquickly\b",
    "give the indicated pre-referral treatment immediately": r"\b(?:give|provide)\b.{0,35}\bpre-referral treatment\b.{0,25}\bimmediately\b",
    "prevent low blood sugar": r"\bprevent\b.{0,15}\blow blood sugar\b",
    "keep the child warm": r"\bkeep\b.{0,15}\bchild\b.{0,10}\bwarm\b",
    "arrange urgent referral": r"\b(?:arrange|make|refer)\b.{0,20}\burgent referral\b",
    "give diazepam because the child is convulsing now": r"\b(?:give|administer)\b.{0,15}\bdiazepam\b",
    "give the first dose of an appropriate antibiotic": r"\b(?:give|administer)\b.{0,20}\bfirst dose\b.{0,25}\b(?:appropriate )?antibiotic\b",
    "give oral amoxicillin for 5 days": r"\b(?:give|start|administer)\b.{0,15}\boral amoxicillin\b.{0,20}\b5 days\b",
    "soothe the throat and relieve the cough with a safe remedy": r"\bsoothe\b.{0,20}\bthroat\b.{0,30}\brelieve\b.{0,20}\bcough\b.{0,30}\bsafe remedy\b",
    "advise the caregiver when to return immediately": r"\badvise\b.{0,25}\bcaregiver\b.{0,30}\breturn immediately\b",
    "follow up in 3 days": r"\bfollow[- ]?up\b.{0,15}\b3 days\b",
    "follow up in 5 days if the child is not improving": r"\bfollow[- ]?up\b.{0,15}\b5 days\b.{0,35}\bnot improving\b",
    "give Plan C fluid for severe dehydration": r"\b(?:give|start)\b.{0,15}\bplan c\b.{0,20}\bfluid",
    "give Plan B fluid, zinc, and food": r"\b(?:give|start)\b.{0,15}\bplan b\b.{0,40}\bzinc\b.{0,25}\bfood\b",
    "give Plan A fluid, zinc, and food": r"\b(?:give|start)\b.{0,15}\bplan a\b.{0,40}\bzinc\b.{0,25}\bfood\b",
    "give frequent sips of ORS during referral": r"\b(?:give|offer)\b.{0,20}\bfrequent sips\b.{0,15}\bors\b.{0,25}\breferral\b",
    "continue breastfeeding": r"\bcontinue\b.{0,10}\bbreastfeeding\b",
}

_OBSERVATION_PATTERNS = {
    "patient_facts.age_months": r"\bage\b.{0,25}\bmonths\b",
    "patient_facts.has_cough_or_difficult_breathing": r"\bcough\b.{0,15}\bdifficult breathing\b",
    "patient_facts.has_diarrhoea": r"\bdiarrh(?:oea|ea)\b",
    "danger_signs.convulsing_now": r"\bconvuls(?:ing|ion)\b.{0,20}\bnow\b",
    "danger_signs.lethargic_or_unconscious": r"\blethargic\b.{0,15}\bunconscious\b",
    "danger_signs.unable_to_drink_or_breastfeed": r"\b(?:able|unable)\b.{0,20}\bdrink\b.{0,20}\bbreastfeed\b",
    "danger_signs.vomits_everything": r"\bvomit(?:s)?\b.{0,15}\beverything\b",
    "danger_signs.had_convulsions": r"\b(?:had|history of|during this illness)\b.{0,30}\bconvulsions?\b|\bconvulsions?\b.{0,30}\bduring this illness\b",
    "respiratory.stridor_when_calm": r"\bstridor\b.{0,25}\bcalm\b|\bcalm\b.{0,25}\bstridor\b",
    "respiratory.chest_indrawing": r"\bchest indrawing\b.{0,25}\bcalm\b|\bcalm\b.{0,25}\bchest indrawing\b",
    "respiratory.respiratory_rate": r"\b(?:respiratory rate|breaths?)\b",
    "dehydration.restless_or_irritable": r"\brestless\b.{0,15}\birritable\b",
    "dehydration.sunken_eyes": r"\bsunken eyes\b|\beyes\b.{0,15}\bsunken\b",
    "dehydration.drinking_status": r"\boffer\b.{0,15}\bfluid\b.{0,40}\bdrink",
    "dehydration.skin_pinch": r"\bskin pinch\b|\bpinch\b.{0,20}\babdominal skin\b",
}


@dataclass(frozen=True)
class NaturalSemanticValidation:
    validator_id: str
    semantic_pass: bool
    checks: dict[str, bool]
    missing_concepts: tuple[str, ...]
    unexpected_concepts: tuple[str, ...]
    acquisition_mode_errors: tuple[str, ...]
    internal_terms: tuple[str, ...]
    obvious_hallucinations: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "validator_id": self.validator_id,
            "semantic_pass": self.semantic_pass,
            "checks": self.checks,
            "missing_concepts": list(self.missing_concepts),
            "unexpected_concepts": list(self.unexpected_concepts),
            "acquisition_mode_errors": list(self.acquisition_mode_errors),
            "internal_terms": list(self.internal_terms),
            "obvious_hallucinations": list(self.obvious_hallucinations),
            "limitations": list(self.limitations),
        }


def validate_natural_rendering(
    text: str,
    semantics: ExpectedAssistantSemantics,
    *,
    visible_context: str,
) -> NaturalSemanticValidation:
    expected = compact_semantic_input(semantics)
    lowered = _normalized(text)
    missing: list[str] = []
    unexpected: list[str] = []
    mode_errors: list[str] = []

    expected_classifications = {item["label"] for item in expected["classifications"]}
    detected_classifications = _detect_classifications(lowered)
    missing.extend(f"classification:{item}" for item in sorted(expected_classifications - detected_classifications))
    unexpected.extend(f"classification:{item}" for item in sorted(detected_classifications - expected_classifications))

    expected_actions = set(expected["actions"])
    detected_actions = {name for name, pattern in _ACTION_PATTERNS.items() if re.search(pattern, lowered, re.DOTALL)}
    missing.extend(f"action:{item}" for item in sorted(expected_actions - detected_actions))
    unexpected.extend(f"action:{item}" for item in sorted(detected_actions - expected_actions))

    requests = expected["decision_requests"] + expected["remaining_assessment_requests"]
    expected_request_ids = {item["observation_id"] for item in requests}
    for request in requests:
        observation_id = request["observation_id"]
        if not re.search(_OBSERVATION_PATTERNS[observation_id], lowered, re.DOTALL):
            missing.append(f"acquisition:{observation_id}")
            continue
        mode_error = _mode_error(lowered, request["mode"], observation_id)
        if mode_error:
            mode_errors.append(mode_error)

    if expected["urgent"]:
        urgency_ok = bool(re.search(r"\b(?:urgent|act now|immediately)\b", lowered[:180]))
    else:
        urgency_ok = not bool(re.search(r"\burgent:\s*act now\b", lowered[:180]))

    internal = internal_term_hits(text)
    if re.search(r"\bdiagnos(?:is|e|ed|tic)\b", lowered):
        unexpected.append("terminology:diagnosis")
    obvious_hallucinations = _obvious_hallucinations(
        lowered,
        visible_context=visible_context,
        expected_request_ids=expected_request_ids,
    )
    classification_cue = bool(re.search(r"\bclassif(?:ication|ied|y)\b", lowered))
    checks = {
        "classification_preserved": not any(item.startswith("classification:") for item in missing + unexpected),
        "actions_preserved": not any(item.startswith("action:") for item in missing + unexpected),
        "urgency_preserved": urgency_ok,
        "acquisitions_preserved": not any(item.startswith("acquisition:") for item in missing),
        "acquisition_modes_preserved": not mode_errors,
        "classification_terminology": not expected_classifications or classification_cue,
        "no_premature_classification": bool(expected_classifications) or not (detected_classifications or classification_cue),
        "no_internal_terminology": not internal,
        "classification_not_diagnosis": "terminology:diagnosis" not in unexpected,
        "no_obvious_hallucination": not obvious_hallucinations,
        "nonempty": bool(text.strip()),
    }
    semantic_pass = all(checks.values())
    return NaturalSemanticValidation(
        validator_id=NATURAL_VALIDATOR_ID,
        semantic_pass=semantic_pass,
        checks=checks,
        missing_concepts=tuple(missing),
        unexpected_concepts=tuple(unexpected),
        acquisition_mode_errors=tuple(mode_errors),
        internal_terms=internal,
        obvious_hallucinations=obvious_hallucinations,
        limitations=(
            "Lexical guards verify explicit selected-scope concepts and acquisition-mode cues, not unrestricted natural-language entailment.",
            "Subtle invented observations, negation errors, clinical clarity, and PHC suitability still require human/domain-expert review.",
            "A semantic pass is acceptance-experiment evidence, not approval for training-corpus use.",
        ),
    )


def _detect_classifications(text: str) -> set[str]:
    detected = set()
    severe_respiratory = bool(re.search(_CLASSIFICATION_PATTERNS["Severe pneumonia or very severe disease"], text))
    for name, pattern in _CLASSIFICATION_PATTERNS.items():
        if re.search(pattern, text):
            detected.add(name)
    if severe_respiratory:
        detected.discard("Pneumonia")
        # Count GDS only when the shared phrase also appears outside the severe
        # respiratory label, or is explicitly tied to general danger signs.
        without_respiratory_label = re.sub(
            _CLASSIFICATION_PATTERNS["Severe pneumonia or very severe disease"],
            "",
            text,
        )
        has_separate_gds = bool(
            re.search(_CLASSIFICATION_PATTERNS["Very severe disease"], without_respiratory_label)
            or re.search(r"(?:danger sign|general).*very severe disease|very severe disease.*(?:danger sign|general)", text)
        )
        if not has_separate_gds:
            detected.discard("Very severe disease")
    if "Severe dehydration" in detected:
        detected.discard("No dehydration")
    return detected


def _mode_error(text: str, mode: str, observation_id: str) -> str | None:
    if mode == AcquisitionMode.CAREGIVER_QUESTION.value:
        if not re.search(r"\bask\b.{0,35}\bcaregiver\b|\bcaregiver\b.{0,35}\bask\b", text):
            return f"{observation_id}: caregiver question lacks ask-caregiver cue"
    elif mode == AcquisitionMode.CLINICIAN_OBSERVATION.value:
        if not re.search(r"\b(?:check|observe|look for|assess)\b", text):
            return f"{observation_id}: clinician observation lacks check/observe cue"
    elif mode == AcquisitionMode.MEASUREMENT.value:
        required = (
            re.search(r"\bcount\b.{0,25}\bbreaths?\b", text)
            and "one full minute" in text
            and "calm" in text
        )
        if not required:
            return f"{observation_id}: measurement lacks count/one-full-minute/calm cues"
    elif mode == AcquisitionMode.HISTORY_OR_RECORD.value:
        if not re.search(r"\b(?:caregiver|record)\b", text):
            return f"{observation_id}: history/record acquisition lacks source cue"
    return None


def _obvious_hallucinations(
    text: str,
    *,
    visible_context: str,
    expected_request_ids: set[str],
) -> tuple[str, ...]:
    allowed_numbers = set(re.findall(r"\b\d+\b", visible_context)) | {"3", "5"}
    found_numbers = set(re.findall(r"\b\d+\b", text))
    errors = [f"unsupported_number:{item}" for item in sorted(found_numbers - allowed_numbers)]

    # A requested unknown observation may appear only with an acquisition cue. Assertions
    # without ask/check/observe/count language are mechanically suspicious.
    for observation_id in expected_request_ids:
        pattern = _OBSERVATION_PATTERNS[observation_id]
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            if re.search(pattern, sentence) and not re.search(
                r"\b(?:ask|check|observe|count|confirm|offer|pinch|assess|look for|complete)\b",
                sentence,
            ):
                errors.append(f"requested_unknown_asserted:{observation_id}")
                break
    return tuple(errors)


def _normalized(text: str) -> str:
    return " ".join(text.lower().replace("’", "'").split())
