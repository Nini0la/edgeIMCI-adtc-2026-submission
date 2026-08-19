from __future__ import annotations

from edge_imci.generation.cases import complete_danger_signs
from edge_imci.schemas.case import (
    ClinicalCase,
    ClinicalObservations,
    DehydrationObservations,
    GenerationCategory,
    GenerationMetadata,
    GeneralDangerSignObservations,
    PatientFacts,
    RespiratoryObservations,
    SourceProvenance,
)


def make_case(
    *,
    age_months: int = 18,
    danger: GeneralDangerSignObservations | None = None,
    respiratory: RespiratoryObservations | None = None,
    dehydration: DehydrationObservations | None = None,
) -> ClinicalCase:
    return ClinicalCase(
        case_id="test-case",
        patient_facts=PatientFacts(
            age_months=age_months,
            has_cough_or_difficult_breathing=respiratory is not None,
            has_diarrhoea=dehydration is not None,
        ),
        presentation="Structured test case.",
        observations=ClinicalObservations(
            danger_signs=danger or complete_danger_signs(),
            respiratory=respiratory,
            dehydration=dehydration,
        ),
        known_missing_information=(),
        expected_result=None,
        provenance=SourceProvenance("WHO IMCI Chart Booklet", "March 2014", (), (), ()),
        generation=GenerationMetadata("test", 0, (GenerationCategory.NORMAL,), "test"),
    )
