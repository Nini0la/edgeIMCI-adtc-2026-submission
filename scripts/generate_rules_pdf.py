#!/usr/bin/env python
"""Render the IMCI rules crosscheck Markdown table into a polished PDF.

Uses reportlab Platypus with landscape A4 to fit the wide table.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = REPO_ROOT / "data" / "rules" / "imci_selected_v0.json"
OUTPUT_PATH = REPO_ROOT / "docs" / "rules_crosscheck.pdf"

# ── label maps (same as generate_crosscheck.py) ────────────────────────

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


def humanize_enum(value, mapping):
    if value is None:
        return "—"
    return mapping.get(value, value.replace("_", " ").title())


def humanize_actions(actions):
    if not actions:
        return "—"
    return "; ".join(ACTION_LABELS.get(a, a.replace("_", " ").title()) for a in actions)


def conditions_to_plain(rule):
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
        return f"Child aged {age.get('gte', '?')} to {age.get('lt', '?')} months with respiratory rate >= {rr.get('gte', '?')} breaths/min"

    if kind == "respiratory_classification":
        if conds.get("any_general_danger_sign"):
            return "Any general danger sign is present"
        field = conds.get("field", "")
        if field:
            sign_name = field.split(".")[-1].replace("_", " ")
            return f"Child has: {sign_name}"
        if conds.get("fast_breathing"):
            return "Fast breathing detected (threshold met)"
        return str(conds)

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

    return str(conds)


def build_pdf():
    with RULES_PATH.open(encoding="utf-8") as f:
        rules_data = json.load(f)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=16,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=4,
    )
    intro_style = ParagraphStyle(
        "Intro",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#444444"),
        spaceAfter=12,
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=cell_style,
        fontName="Helvetica-Bold",
    )
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=landscape(A4),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    story = []

    story.append(Paragraph("IMCI Rules - Domain Expert Crosscheck", title_style))
    story.append(Paragraph(
        f"Source: {rules_data['document']}, {rules_data['edition']}",
        subtitle_style,
    ))
    pop = rules_data["population"]["age_months"]
    story.append(Paragraph(
        f"Population: Children aged {pop['gte']} to {pop['lt'] - 1} months",
        subtitle_style,
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Review each rule: does the condition, classification, and actions match the WHO IMCI chart? "
        "Tick the box in the last column if correct, or write a note if something is wrong.",
        intro_style,
    ))

    # Table data
    headers = ["Rule ID", "Clinical Area", "If (condition)", "Then", "Actions / Note", "WHO page", "Correct?"]
    header_row = [Paragraph(h, header_style) for h in headers]

    data = [header_row]

    for rule in rules_data["rules"]:
        kind = rule["kind"]
        area = KIND_LABELS.get(kind, kind)
        condition = conditions_to_plain(rule)
        result = rule["result"]
        source = rule.get("source", {})
        who_page = f"p.{source.get('pdf_page', '?')} (chart {source.get('chart_page', '?')})"

        if kind == "fast_breathing_threshold":
            then_text = "Sets: fast breathing = yes (used by rule IMCI-RESP-PNEUMONIA-FAST-BREATHING)"
            actions_text = "Not a classification rule - threshold check that feeds the respiratory classification rules below"
        elif "classification" in result:
            then_text = humanize_enum(result.get("classification"), CLASSIFICATION_LABELS)
            if "actions_without_other_severe_classification" in result:
                actions_text = (
                    "If no other severe classification: "
                    + humanize_actions(result.get("actions_without_other_severe_classification", []))
                    + "<br/><br/>If other severe classification present: "
                    + humanize_actions(result.get("actions_with_other_severe_classification", []))
                )
            else:
                actions_text = humanize_actions(result.get("actions", []))
        else:
            then_text = "—"
            actions_text = "—"

        row = [
            Paragraph(rule["rule_id"], cell_bold),
            Paragraph(area, cell_style),
            Paragraph(condition, cell_style),
            Paragraph(then_text, cell_style),
            Paragraph(actions_text, cell_style),
            Paragraph(who_page, cell_style),
            Paragraph("[ &nbsp; ]", ParagraphStyle("Checkbox", parent=cell_style, alignment=1)),  # printable checkbox
        ]
        data.append(row)

    # Column widths (total ~267mm for landscape A4 with 30mm margins)
    col_widths = [42*mm, 28*mm, 45*mm, 35*mm, 70*mm, 25*mm, 22*mm]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Body
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        # Alternating row colors
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
    ]))

    story.append(table)

    doc.build(story)
    print(f"Generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
