#!/usr/bin/env python
"""Generate human-readable crosscheck sheets for IMCI domain expert review.

Produces:
  - docs/rules_crosscheck.md  — one row per rule, plain clinical language
  - docs/cases_crosscheck.md  — one row per benchmark case, vignette + expected outcome
  - docs/rules_crosscheck.csv — same as rules table, Excel-friendly
  - docs/cases_crosscheck.csv — same as cases table, Excel-friendly
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = REPO_ROOT / "data" / "rules" / "imci_selected_v0.json"
BENCHMARK_PATH = REPO_ROOT / "data" / "benchmark" / "imci_v0.jsonl"
DOCS_DIR = REPO_ROOT / "docs"

# ── helpers ────────────────────────────────────────────────────────────

KIND_LABELS = {
    "danger_sign": "General danger signs",
    "fast_breathing_threshold": "Cough or difficult breathing",
    "respiratory_classification": "Cough or difficult breathing",
    "dehydration_classification": "Diarrhoea dehydration",
}

CLASSIFICATION_LABELS = {
    "VERY_SEVERE_DISEASE": "Very severe disease",
    "SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE": "Severe pneumonia or very severe disease",
    "PNEUMONIA": "Pneumonia",
    "COUGH_OR_COLD": "Cough or cold",
    "SEVERE_DEHYDRATION": "Severe dehydration",
    "SOME_DEHYDRATION": "Some dehydration",
    "NO_DEHYDRATION": "No dehydration",
}

ACTION_LABELS = {
    "COMPLETE_ASSESSMENT_QUICKLY": "Complete assessment quickly",
    "GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY": "Give pre-referral treatment immediately",
    "PREVENT_LOW_BLOOD_SUGAR": "Prevent low blood sugar",
    "KEEP_WARM": "Keep warm",
    "URGENT_REFERRAL": "Urgent referral",
    "GIVE_DIAZEPAM_IF_CONVULSING_NOW": "Give diazepam (if convulsing now)",
    "GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC": "Give first dose of appropriate antibiotic",
    "GIVE_ORAL_AMOXICILLIN_5_DAYS": "Give oral amoxicillin for 5 days",
    "SOOTHE_THROAT_AND_RELIEVE_COUGH": "Soothe throat and relieve cough",
    "ADVISE_WHEN_TO_RETURN_IMMEDIATELY": "Advise when to return immediately",
    "FOLLOW_UP_3_DAYS": "Follow up in 3 days",
    "FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING": "Follow up in 5 days if not improving",
    "GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C": "Give fluid for severe dehydration (Plan C)",
    "GIVE_FLUID_ZINC_AND_FOOD_PLAN_B": "Give fluid, zinc and food (Plan B)",
    "GIVE_FLUID_ZINC_AND_FOOD_PLAN_A": "Give fluid, zinc and food (Plan A)",
    "FREQUENT_ORS_SIPS_DURING_REFERRAL": "Frequent ORS sips during referral",
    "CONTINUE_BREASTFEEDING": "Continue breastfeeding",
}

DANGER_SIGN_LABELS = {
    "UNABLE_TO_DRINK_OR_BREASTFEED": "Unable to drink or breastfeed",
    "VOMITS_EVERYTHING": "Vomits everything",
    "HAD_CONVULSIONS": "Had convulsions",
    "LETHARGIC_OR_UNCONSCIOUS": "Lethargic or unconscious",
    "CONVULSING_NOW": "Convulsing now",
}

DRINKING_LABELS = {
    "NORMAL": "Drinking normally",
    "EAGER_OR_THIRSTY": "Drinks eagerly / thirsty",
    "POORLY": "Drinks poorly",
    "UNABLE": "Unable to drink",
}

SKIN_PINCH_LABELS = {
    "NORMAL": "Goes back quickly",
    "SLOWLY": "Goes back slowly",
    "VERY_SLOWLY": "Goes back very slowly",
}


def humanize_enum(value: str | None, mapping: dict[str, str]) -> str:
    if value is None:
        return "—"
    return mapping.get(value, value.replace("_", " ").title())


def humanize_actions(actions: list[str]) -> str:
    if not actions:
        return "—"
    return "; ".join(ACTION_LABELS.get(a, a.replace("_", " ").title()) for a in actions)


def humanize_classifications(classifications: dict[str, str]) -> str:
    if not classifications:
        return "—"
    parts = []
    for pathway, cls in classifications.items():
        label = CLASSIFICATION_LABELS.get(cls, cls.replace("_", " ").title())
        area = {"general_danger_signs": "Danger signs", "respiratory": "Respiratory", "dehydration": "Dehydration"}.get(pathway, pathway)
        parts.append(f"{area}: {label}")
    return "; ".join(parts)


def humanize_danger_signs(signs: list[str]) -> str:
    if not signs:
        return "None"
    return ", ".join(DANGER_SIGN_LABELS.get(s, s.replace("_", " ").title()) for s in signs)


def age_label(months: int) -> str:
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''}"
    years = months // 12
    rem = months % 12
    if rem == 0:
        return f"{years} year{'s' if years != 1 else ''}"
    return f"{years}y {rem}m"


def conditions_to_plain(rule: dict) -> str:
    """Translate rule conditions dict into a plain-English clinical statement."""
    conds = rule["conditions"]
    kind = rule["kind"]

    if conds.get("fallback"):
        return "None of the above conditions met (fallback)"

    if kind == "danger_sign":
        field = conds.get("field", "")
        sign_name = field.split(".")[-1].replace("_", " ")
        return f"Child has: {sign_name}"

    if kind == "fast_breathing_threshold":
        age = conds.get("age_months", {})
        rr = conds.get("respiratory_rate", {})
        age_str = f"age {age.get('gte', '?')}–{age.get('lt', '?')} months"
        rr_str = f"respiratory rate ≥ {rr.get('gte', '?')}"
        return f"Child aged {age.get('gte', '?')} to {age.get('lt', '?')} months with respiratory rate ≥ {rr.get('gte', '?')} breaths/min"

    if kind == "respiratory_classification":
        if conds.get("any_general_danger_sign"):
            return "Any general danger sign is present"
        field = conds.get("field", "")
        if field:
            sign_name = field.split(".")[-1].replace("_", " ")
            return f"Child has: {sign_name}"
        if conds.get("fast_breathing"):
            return "Fast breathing detected (threshold met)"
        return json.dumps(conds)

    if kind == "dehydration_classification":
        min_count = conds.get("minimum_count", 2)
        signs = conds.get("signs", [])
        sign_parts = []
        for sign in signs:
            field = sign.get("field", "")
            field_name = field.split(".")[-1].replace("_", " ")
            if "equals" in sign:
                val = sign["equals"]
                if isinstance(val, bool):
                    sign_parts.append(f"{field_name} = {'yes' if val else 'no'}")
                else:
                    sign_parts.append(f"{field_name} = {humanize_enum(val, {**DRINKING_LABELS, **SKIN_PINCH_LABELS})}")
            elif "in" in sign:
                vals = [humanize_enum(v, {**DRINKING_LABELS, **SKIN_PINCH_LABELS}) for v in sign["in"]]
                sign_parts.append(f"{field_name} in ({', '.join(vals)})")
        return f"At least {min_count} of: {'; '.join(sign_parts)}"

    return json.dumps(conds)


def observations_to_plain(observations: dict) -> str:
    """Turn a case's observations into a compact clinical summary."""
    parts = []

    ds = observations.get("danger_signs")
    if ds:
        present = [k.replace("_", " ") for k, v in ds.items() if v is True]
        if present:
            parts.append("Danger signs: " + ", ".join(present))

    resp = observations.get("respiratory")
    if resp:
        rr = resp.get("respiratory_rate")
        if rr is not None:
            parts.append(f"RR = {rr}/min")
        if resp.get("chest_indrawing"):
            parts.append("Chest indrawing")
        if resp.get("stridor_when_calm"):
            parts.append("Stridor when calm")

    dehyd = observations.get("dehydration")
    if dehyd:
        if dehyd.get("restless_or_irritable"):
            parts.append("Restless/irritable")
        if dehyd.get("sunken_eyes"):
            parts.append("Sunken eyes")
        ds_status = dehyd.get("drinking_status")
        if ds_status:
            parts.append(f"Drinking: {humanize_enum(ds_status, DRINKING_LABELS)}")
        sp = dehyd.get("skin_pinch")
        if sp:
            parts.append(f"Skin pinch: {humanize_enum(sp, SKIN_PINCH_LABELS)}")

    return "; ".join(parts) if parts else "No abnormal observations"


# ── rules crosscheck ───────────────────────────────────────────────────

def generate_rules_crosscheck(rules_data: dict) -> tuple[str, list[list[str]]]:
    headers = [
        "Rule ID", "Clinical Area", "If (condition)", "Then", "Actions / Note", "WHO page", "Correct?",
    ]
    rows = []

    for rule in rules_data["rules"]:
        kind = rule["kind"]
        area = KIND_LABELS.get(kind, kind)
        condition = conditions_to_plain(rule)
        result = rule["result"]
        source = rule.get("source", {})
        who_page = f"p.{source.get('source_pdf_page', '?')} (chart {source.get('source_printed_page', '?')})"

        if kind == "fast_breathing_threshold":
            # Threshold rules don't classify directly — they set a flag used by later rules
            classification = f"Sets: fast breathing = yes (used by rule IMCI-RESP-PNEUMONIA-FAST-BREATHING)"
            actions = "Not a classification rule — this is a threshold check that feeds the respiratory classification rules below"
        elif "classification" in result:
            classification = humanize_enum(result.get("classification"), CLASSIFICATION_LABELS)
            # Handle dehydration rules with conditional actions
            if "actions_without_other_severe_classification" in result:
                actions = (
                    "If no other severe classification: "
                    + humanize_actions(result.get("actions_without_other_severe_classification", []))
                    + "\n\nIf other severe classification present: "
                    + humanize_actions(result.get("actions_with_other_severe_classification", []))
                )
            else:
                actions = humanize_actions(result.get("actions", []))
        else:
            classification = "—"
            actions = "—"

        rows.append([
            rule["rule_id"],
            area,
            condition,
            classification,
            actions,
            who_page,
            "☐",
        ])

    # Build markdown
    md = "# `imci-selected-v0` machine-readable rule set — Domain Expert Crosscheck\n\n"
    md += f"**Source:** Derived from {rules_data['document']}, {rules_data['edition']}\n\n"
    md += f"**Population:** Children aged {rules_data['population']['age_months']['gte']} to {rules_data['population']['age_months']['lt'] - 1} months\n\n"
    md += "Review each EdgeIMCI-encoded rule derived from the WHO IMCI chart: does its condition, classification, and action set preserve the selected source logic?\n"
    md += "These are not WHO-authored machine-readable rules and do not represent complete IMCI. Tick the box in the last column if correct, or write a note if something is wrong.\n\n"
    md += "| " + " | ".join(headers) + " |\n"
    md += "|" + "|".join(["---"] * len(headers)) + "|\n"
    for row in rows:
        # Escape pipes in cell content
        escaped = [cell.replace("|", "\\|").replace("\n", "<br>") for cell in row]
        md += "| " + " | ".join(escaped) + " |\n"

    csv_rows = [headers] + rows
    return md, csv_rows


# ── cases crosscheck ───────────────────────────────────────────────────

def generate_cases_crosscheck(benchmark_path: Path) -> tuple[str, list[list[str]]]:
    headers = [
        "Case ID", "Age", "Presentation", "Key observations",
        "Expected classification", "Expected actions", "Referral", "Correct?",
    ]
    rows = []

    with benchmark_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            case = json.loads(line)

            age = age_label(case["patient_facts"]["age_months"])
            presentation = case.get("presentation", "—")
            obs = observations_to_plain(case.get("observations", {}))

            expected = case.get("expected_result", {})
            classification = humanize_classifications(expected.get("classifications", {}))
            actions = humanize_actions(expected.get("actions", []))
            referral = expected.get("referral", "NONE")
            referral_label = {"NONE": "None", "URGENT": "Urgent"}.get(referral, referral)

            rows.append([
                case["case_id"],
                age,
                presentation,
                obs,
                classification,
                actions,
                referral_label,
                "☐",
            ])

    md = "# `imci-selected-v0` benchmark cases — Domain Expert Crosscheck\n\n"
    md += "Review each selected-scope case: given the patient presentation and observations, is the expected classification and action correct under the EdgeIMCI machine-readable rule set derived from WHO IMCI 2014?\n"
    md += "These cases do not represent a complete IMCI encounter. Tick the box in the last column if correct, or write a note if something is wrong.\n\n"
    md += "| " + " | ".join(headers) + " |\n"
    md += "|" + "|".join(["---"] * len(headers)) + "|\n"
    for row in rows:
        escaped = [cell.replace("|", "\\|").replace("\n", "<br>") for cell in row]
        md += "| " + " | ".join(escaped) + " |\n"

    csv_rows = [headers] + rows
    return md, csv_rows


# ── main ──────────────────────────────────────────────────────────────

def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Rules
    with RULES_PATH.open(encoding="utf-8") as f:
        rules_data = json.load(f)
    rules_md, rules_csv = generate_rules_crosscheck(rules_data)

    rules_md_path = DOCS_DIR / "rules_crosscheck.md"
    rules_csv_path = DOCS_DIR / "rules_crosscheck.csv"
    rules_md_path.write_text(rules_md, encoding="utf-8")
    with rules_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rules_csv)

    # Cases
    cases_md, cases_csv = generate_cases_crosscheck(BENCHMARK_PATH)

    cases_md_path = DOCS_DIR / "cases_crosscheck.md"
    cases_csv_path = DOCS_DIR / "cases_crosscheck.csv"
    cases_md_path.write_text(cases_md, encoding="utf-8")
    with cases_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(cases_csv)

    print(f"Generated:")
    print(f"  {rules_md_path}")
    print(f"  {rules_csv_path}")
    print(f"  {cases_md_path}")
    print(f"  {cases_csv_path}")
    print(f"  Rules: {len(rules_csv) - 1} rows")
    print(f"  Cases: {len(cases_csv) - 1} rows")


if __name__ == "__main__":
    main()
