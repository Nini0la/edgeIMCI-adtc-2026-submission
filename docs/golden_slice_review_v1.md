# Archived selected-v0 component regression slice v1 — human/domain-expert review

**Status:** `ARCHIVED`. Historical/component-regression use only; not training data and ineligible for product evaluation, holistic generation, and teacher selection.

**Pinned IDs:** `imci-selected-v0` / `imci-selected-v0-information-policy-v1` / `imci-selected-v0-valid-completions-v1`

**Records:** 14. Deterministic renderer: `edge-imci-conservative-golden-renderer-v1`. Seed: `20260820`.

The deterministic round trip checks controlled language and structured correspondence. It is not independent clinical proof; every record remains marked for human review.

## Coverage summary

- `acquire_information`
- `age_boundary`
- `assessment_only`
- `canonical_order`
- `caregiver_vs_measurement`
- `clinician_observation`
- `complete_single_turn`
- `convulsing_now`
- `cough_cold`
- `cross_pathway_action`
- `danger_sign`
- `decision_sufficient_assessment_incomplete`
- `diazepam`
- `early_escalation`
- `exact_rule_unresolved`
- `fast_breathing`
- `measurement`
- `multi_turn`
- `no_dehydration`
- `partial`
- `plan_c`
- `pneumonia`
- `respiratory_severe`
- `rr_at_cutoff`
- `rr_below_cutoff`
- `severe_dehydration`
- `simultaneous_danger_signs`
- `some_dehydration`
- `two_of`
- `unknown_preserved`
- `urgent`
- `very_incomplete`

## Cases

### golden-complete-chest-pneumonia

**Why:** Complete single-turn respiratory case with chest-indrawing pneumonia and its full selected action block.

**Coverage:** `complete_single_turn`, `pneumonia`, `clinician_observation`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=18; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=True; patient_facts.has_diarrhoea=False; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=True; respiratory.respiratory_rate=35; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=False; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `respiratory=PNEUMONIA`. Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_3_DAYS, GIVE_ORAL_AMOXICILLIN_5_DAYS, SOOTHE_THROAT_AND_RELIEVE_COUGH`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 18 months old. On observation, the child is not convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child can drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports cough or difficult breathing. The caregiver reports no diarrhoea. When calm, the child has no stridor. When calm, chest indrawing is present. With the child calm, the respiratory rate counted for one full minute is 35 breaths per minute.
- **Turn 1 — ASSISTANT:** The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is complete. The supported respiratory classification is pneumonia. Advise the caregiver when to return immediately. Follow up in 3 days. Give oral amoxicillin for 5 days. Soothe the throat and relieve the cough with a safe remedy.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `True`; urgent `False`.
  - Classifications: `respiratory=PNEUMONIA`.
  - Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_3_DAYS, GIVE_ORAL_AMOXICILLIN_5_DAYS, SOOTHE_THROAT_AND_RELIEVE_COUGH`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-very-incomplete

**Why:** Very incomplete presentation that must acquire clinician-observed danger signs before lower-priority information.

**Coverage:** `very_incomplete`, `acquire_information`, `canonical_order`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=20; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=False; patient_facts.has_diarrhoea=False; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=False; respiratory.respiratory_rate=30; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=False; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `none`. Actions: `none`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 20 months old.
- **Turn 1 — ASSISTANT:** More information is needed before the supported classification decision is determined. The complete supported action set is not yet determined. The supported assessment is not yet complete. Acquire next: Observe whether the child is convulsing now. Observe whether the child is lethargic or unconscious.
  - Policy: decision `INSUFFICIENT`; actions sufficient `False`; assessment complete `False`; urgent `False`.
  - Classifications: `none`.
  - Actions: `none`.
  - Decision acquisitions: `danger_signs.convulsing_now, danger_signs.lethargic_or_unconscious`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-partial-needs-respiratory-measurement

**Why:** Partially complete respiratory assessment where only a valid one-minute respiratory-rate measurement can decide pneumonia versus cough/cold.

**Coverage:** `partial`, `measurement`, `caregiver_vs_measurement`, `unknown_preserved`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=18; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=True; patient_facts.has_diarrhoea=False; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=False; respiratory.respiratory_rate=45; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=False; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `respiratory=PNEUMONIA`. Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_3_DAYS, GIVE_ORAL_AMOXICILLIN_5_DAYS, SOOTHE_THROAT_AND_RELIEVE_COUGH`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 18 months old. On observation, the child is not convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child can drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports cough or difficult breathing. The caregiver reports no diarrhoea. When calm, the child has no stridor. When calm, chest indrawing is absent.
- **Turn 1 — ASSISTANT:** More information is needed before the supported classification decision is determined. The complete supported action set is not yet determined. The supported assessment is not yet complete. Advise the caregiver when to return immediately. Soothe the throat and relieve the cough with a safe remedy. Acquire next: When the child is calm, count breaths for one full minute and report the respiratory rate.
  - Policy: decision `INSUFFICIENT`; actions sufficient `False`; assessment complete `False`; urgent `False`.
  - Classifications: `none`.
  - Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, SOOTHE_THROAT_AND_RELIEVE_COUGH`.
  - Decision acquisitions: `respiratory.respiratory_rate`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-multiturn-age12-rr40

**Why:** Multi-turn progression across the exact older-band threshold: measurement at 40 produces pneumonia.

**Coverage:** `multi_turn`, `age_boundary`, `fast_breathing`, `rr_at_cutoff`, `pneumonia`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=12; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=True; patient_facts.has_diarrhoea=False; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=False; respiratory.respiratory_rate=40; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=False; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `respiratory=PNEUMONIA`. Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_3_DAYS, GIVE_ORAL_AMOXICILLIN_5_DAYS, SOOTHE_THROAT_AND_RELIEVE_COUGH`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 12 months old. On observation, the child is not convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child can drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports cough or difficult breathing. The caregiver reports no diarrhoea. When calm, the child has no stridor. When calm, chest indrawing is absent.
- **Turn 1 — ASSISTANT:** More information is needed before the supported classification decision is determined. The complete supported action set is not yet determined. The supported assessment is not yet complete. Advise the caregiver when to return immediately. Soothe the throat and relieve the cough with a safe remedy. Acquire next: When the child is calm, count breaths for one full minute and report the respiratory rate.
  - Policy: decision `INSUFFICIENT`; actions sufficient `False`; assessment complete `False`; urgent `False`.
  - Classifications: `none`.
  - Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, SOOTHE_THROAT_AND_RELIEVE_COUGH`.
  - Decision acquisitions: `respiratory.respiratory_rate`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.
- **Turn 2 — USER:** With the child calm, the respiratory rate counted for one full minute is 40 breaths per minute.
- **Turn 3 — ASSISTANT:** The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is complete. The supported respiratory classification is pneumonia. Advise the caregiver when to return immediately. Follow up in 3 days. Give oral amoxicillin for 5 days. Soothe the throat and relieve the cough with a safe remedy.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `True`; urgent `False`.
  - Classifications: `respiratory=PNEUMONIA`.
  - Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_3_DAYS, GIVE_ORAL_AMOXICILLIN_5_DAYS, SOOTHE_THROAT_AND_RELIEVE_COUGH`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-age11-rr49-cough-cold

**Why:** Younger-band respiratory rate immediately below 50 verifies justified cough/cold fallback.

**Coverage:** `age_boundary`, `rr_below_cutoff`, `cough_cold`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=11; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=True; patient_facts.has_diarrhoea=False; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=False; respiratory.respiratory_rate=49; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=False; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `respiratory=COUGH_OR_COLD`. Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING, SOOTHE_THROAT_AND_RELIEVE_COUGH`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 11 months old. On observation, the child is not convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child can drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports cough or difficult breathing. The caregiver reports no diarrhoea. When calm, the child has no stridor. When calm, chest indrawing is absent. With the child calm, the respiratory rate counted for one full minute is 49 breaths per minute.
- **Turn 1 — ASSISTANT:** The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is complete. The supported respiratory classification is cough or cold. Advise the caregiver when to return immediately. Follow up in 5 days if the child is not improving. Soothe the throat and relieve the cough with a safe remedy.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `True`; urgent `False`.
  - Classifications: `respiratory=COUGH_OR_COLD`.
  - Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING, SOOTHE_THROAT_AND_RELIEVE_COUGH`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-age11-rr50-pneumonia

**Why:** Younger-band respiratory rate exactly at 50 verifies fast-breathing pneumonia.

**Coverage:** `age_boundary`, `rr_at_cutoff`, `fast_breathing`, `pneumonia`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=11; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=True; patient_facts.has_diarrhoea=False; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=False; respiratory.respiratory_rate=50; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=False; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `respiratory=PNEUMONIA`. Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_3_DAYS, GIVE_ORAL_AMOXICILLIN_5_DAYS, SOOTHE_THROAT_AND_RELIEVE_COUGH`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 11 months old. On observation, the child is not convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child can drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports cough or difficult breathing. The caregiver reports no diarrhoea. When calm, the child has no stridor. When calm, chest indrawing is absent. With the child calm, the respiratory rate counted for one full minute is 50 breaths per minute.
- **Turn 1 — ASSISTANT:** The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is complete. The supported respiratory classification is pneumonia. Advise the caregiver when to return immediately. Follow up in 3 days. Give oral amoxicillin for 5 days. Soothe the throat and relieve the cough with a safe remedy.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `True`; urgent `False`.
  - Classifications: `respiratory=PNEUMONIA`.
  - Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_3_DAYS, GIVE_ORAL_AMOXICILLIN_5_DAYS, SOOTHE_THROAT_AND_RELIEVE_COUGH`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-age12-rr39-cough-cold

**Why:** Older-band respiratory rate immediately below 40 verifies the age-band transition and justified fallback.

**Coverage:** `age_boundary`, `rr_below_cutoff`, `cough_cold`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=12; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=True; patient_facts.has_diarrhoea=False; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=False; respiratory.respiratory_rate=39; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=False; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `respiratory=COUGH_OR_COLD`. Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING, SOOTHE_THROAT_AND_RELIEVE_COUGH`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 12 months old. On observation, the child is not convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child can drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports cough or difficult breathing. The caregiver reports no diarrhoea. When calm, the child has no stridor. When calm, chest indrawing is absent. With the child calm, the respiratory rate counted for one full minute is 39 breaths per minute.
- **Turn 1 — ASSISTANT:** The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is complete. The supported respiratory classification is cough or cold. Advise the caregiver when to return immediately. Follow up in 5 days if the child is not improving. Soothe the throat and relieve the cough with a safe remedy.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `True`; urgent `False`.
  - Classifications: `respiratory=COUGH_OR_COLD`.
  - Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING, SOOTHE_THROAT_AND_RELIEVE_COUGH`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-danger-sign-early-escalation

**Why:** Known vomiting-everything danger sign fixes severe classifications and urgent actions before the supported assessment is complete.

**Coverage:** `danger_sign`, `early_escalation`, `urgent`, `decision_sufficient_assessment_incomplete`

**Flags:** `HUMAN_REVIEW_REQUIRED`, `UNRESOLVED:IP-CQ-001`

**Latent clinical truth:**

`patient_facts.age_months=30; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=True; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=True; patient_facts.has_diarrhoea=False; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=False; respiratory.respiratory_rate=30; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=False; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `general_danger_signs=VERY_SEVERE_DISEASE, respiratory=SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE`. Actions: `COMPLETE_ASSESSMENT_QUICKLY, GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC, GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY, KEEP_WARM, PREVENT_LOW_BLOOD_SUGAR, URGENT_REFERRAL`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 30 months old. On observation, the child is not convulsing now. The caregiver says the child vomits everything. The caregiver reports cough or difficult breathing. The caregiver reports no diarrhoea.
- **Turn 1 — ASSISTANT:** Urgent action is required now. The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is not yet complete. The supported general danger-sign classification is very severe disease. The supported respiratory classification is severe pneumonia or very severe disease. Complete the supported assessment quickly. Give the first dose of an appropriate antibiotic. Give the indicated pre-referral treatment immediately. Keep the child warm. Prevent low blood sugar. Arrange urgent referral. Assessment still to complete: Observe whether the child is lethargic or unconscious. Ask the caregiver whether the child is unable to drink or breastfeed. Ask the caregiver whether the child has had convulsions during this illness. When the child is calm, observe whether stridor is present. When the child is calm, observe whether chest indrawing is present. When the child is calm, count breaths for one full minute and report the respiratory rate. Do not delay the urgent actions while the supported assessment remains incomplete.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `False`; urgent `True`.
  - Classifications: `general_danger_signs=VERY_SEVERE_DISEASE, respiratory=SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE`.
  - Actions: `COMPLETE_ASSESSMENT_QUICKLY, GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC, GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY, KEEP_WARM, PREVENT_LOW_BLOOD_SUGAR, URGENT_REFERRAL`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `danger_signs.lethargic_or_unconscious, danger_signs.unable_to_drink_or_breastfeed, danger_signs.had_convulsions, respiratory.stridor_when_calm, respiratory.chest_indrawing, respiratory.respiratory_rate`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-simultaneous-danger-diazepam

**Why:** Simultaneous unable-to-drink and convulsing-now rules must retain both signs and the additional diazepam action.

**Coverage:** `simultaneous_danger_signs`, `convulsing_now`, `diazepam`, `urgent`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=24; danger_signs.convulsing_now=True; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=True; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=False; patient_facts.has_diarrhoea=False; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=False; respiratory.respiratory_rate=30; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=False; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `general_danger_signs=VERY_SEVERE_DISEASE`. Actions: `COMPLETE_ASSESSMENT_QUICKLY, GIVE_DIAZEPAM_IF_CONVULSING_NOW, GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY, KEEP_WARM, PREVENT_LOW_BLOOD_SUGAR, URGENT_REFERRAL`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 24 months old. On observation, the child is convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child is unable to drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports no cough or difficult breathing. The caregiver reports no diarrhoea.
- **Turn 1 — ASSISTANT:** Urgent action is required now. The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is complete. The supported general danger-sign classification is very severe disease. Complete the supported assessment quickly. Give diazepam because the child is convulsing now. Give the indicated pre-referral treatment immediately. Keep the child warm. Prevent low blood sugar. Arrange urgent referral.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `True`; urgent `True`.
  - Classifications: `general_danger_signs=VERY_SEVERE_DISEASE`.
  - Actions: `COMPLETE_ASSESSMENT_QUICKLY, GIVE_DIAZEPAM_IF_CONVULSING_NOW, GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY, KEEP_WARM, PREVENT_LOW_BLOOD_SUGAR, URGENT_REFERRAL`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-severe-dehydration-plan-c

**Why:** Two severe dehydration signs with no other severe classification select severe dehydration and Plan C.

**Coverage:** `severe_dehydration`, `two_of`, `plan_c`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=18; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=False; patient_facts.has_diarrhoea=True; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=False; respiratory.respiratory_rate=30; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=True; dehydration.drinking_status=POORLY; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `dehydration=SEVERE_DEHYDRATION`. Actions: `GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 18 months old. On observation, the child is not convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child can drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports no cough or difficult breathing. The caregiver reports diarrhoea. The child is not restless or irritable. The child's eyes are sunken. When offered fluid, the child drinks poorly. The abdominal skin pinch returns normally.
- **Turn 1 — ASSISTANT:** The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is complete. The supported dehydration classification is severe dehydration. Give Plan C fluid for severe dehydration.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `True`; urgent `False`.
  - Classifications: `dehydration=SEVERE_DEHYDRATION`.
  - Actions: `GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-multiturn-some-dehydration

**Why:** Multi-turn clinician observation of sunken eyes resolves an insufficient dehydration decision to some dehydration with two signs.

**Coverage:** `multi_turn`, `some_dehydration`, `two_of`, `clinician_observation`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=18; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=False; patient_facts.has_diarrhoea=True; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=False; respiratory.respiratory_rate=30; dehydration.restless_or_irritable=True; dehydration.sunken_eyes=True; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `dehydration=SOME_DEHYDRATION`. Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING, GIVE_FLUID_ZINC_AND_FOOD_PLAN_B`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 18 months old. On observation, the child is not convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child can drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports no cough or difficult breathing. The caregiver reports diarrhoea. The child is restless or irritable. When offered fluid, the child drinks normally. The abdominal skin pinch returns normally.
- **Turn 1 — ASSISTANT:** More information is needed before the supported classification decision is determined. The complete supported action set is not yet determined. The supported assessment is not yet complete. Advise the caregiver when to return immediately. Follow up in 5 days if the child is not improving. Acquire next: Observe whether the child's eyes are sunken.
  - Policy: decision `INSUFFICIENT`; actions sufficient `False`; assessment complete `False`; urgent `False`.
  - Classifications: `none`.
  - Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING`.
  - Decision acquisitions: `dehydration.sunken_eyes`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.
- **Turn 2 — USER:** The child's eyes are sunken.
- **Turn 3 — ASSISTANT:** The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is complete. The supported dehydration classification is some dehydration. Advise the caregiver when to return immediately. Follow up in 5 days if the child is not improving. Give Plan B fluid, zinc, and food.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `True`; urgent `False`.
  - Classifications: `dehydration=SOME_DEHYDRATION`.
  - Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING, GIVE_FLUID_ZINC_AND_FOOD_PLAN_B`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-no-dehydration-invariant

**Why:** No dehydration is already invariant while the skin-pinch observation remains assessment-only.

**Coverage:** `no_dehydration`, `decision_sufficient_assessment_incomplete`, `assessment_only`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=18; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=False; patient_facts.has_diarrhoea=True; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=False; respiratory.respiratory_rate=30; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=False; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `dehydration=NO_DEHYDRATION`. Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING, GIVE_FLUID_ZINC_AND_FOOD_PLAN_A`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 18 months old. On observation, the child is not convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child can drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports no cough or difficult breathing. The caregiver reports diarrhoea. The child is not restless or irritable. The child's eyes are not sunken. When offered fluid, the child drinks normally.
- **Turn 1 — ASSISTANT:** The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is not yet complete. The supported dehydration classification is no dehydration. Advise the caregiver when to return immediately. Follow up in 5 days if the child is not improving. Give Plan A fluid, zinc, and food. Assessment still to complete: Pinch the abdominal skin and observe how quickly it returns.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `False`; urgent `False`.
  - Classifications: `dehydration=NO_DEHYDRATION`.
  - Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING, GIVE_FLUID_ZINC_AND_FOOD_PLAN_A`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `dehydration.skin_pinch`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-dehydration-cross-severe-referral

**Why:** Severe dehydration classification remains fixed while severe respiratory classification selects the referral/ORS/breastfeeding branch instead of Plan C.

**Coverage:** `severe_dehydration`, `cross_pathway_action`, `respiratory_severe`, `urgent`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=18; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=True; patient_facts.has_diarrhoea=True; respiratory.stridor_when_calm=True; respiratory.chest_indrawing=False; respiratory.respiratory_rate=30; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=True; dehydration.drinking_status=POORLY; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `respiratory=SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE, dehydration=SEVERE_DEHYDRATION`. Actions: `CONTINUE_BREASTFEEDING, FREQUENT_ORS_SIPS_DURING_REFERRAL, GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC, URGENT_REFERRAL`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 18 months old. On observation, the child is not convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child can drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports cough or difficult breathing. The caregiver reports diarrhoea. When calm, the child has stridor. When calm, chest indrawing is absent. With the child calm, the respiratory rate counted for one full minute is 30 breaths per minute. The child is not restless or irritable. The child's eyes are sunken. When offered fluid, the child drinks poorly. The abdominal skin pinch returns normally.
- **Turn 1 — ASSISTANT:** Urgent action is required now. The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is complete. The supported respiratory classification is severe pneumonia or very severe disease. The supported dehydration classification is severe dehydration. Continue breastfeeding. Give frequent sips of ORS during referral. Give the first dose of an appropriate antibiotic. Arrange urgent referral.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `True`; urgent `True`.
  - Classifications: `respiratory=SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE, dehydration=SEVERE_DEHYDRATION`.
  - Actions: `CONTINUE_BREASTFEEDING, FREQUENT_ORS_SIPS_DURING_REFERRAL, GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC, URGENT_REFERRAL`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `none`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

### golden-pneumonia-exact-rule-unresolved

**Why:** Fast breathing fixes pneumonia and its actions while unknown chest indrawing leaves exact rule identity and assessment completion unresolved.

**Coverage:** `pneumonia`, `exact_rule_unresolved`, `decision_sufficient_assessment_incomplete`, `fast_breathing`

**Flags:** `HUMAN_REVIEW_REQUIRED`

**Latent clinical truth:**

`patient_facts.age_months=24; danger_signs.convulsing_now=False; danger_signs.lethargic_or_unconscious=False; danger_signs.unable_to_drink_or_breastfeed=False; danger_signs.vomits_everything=False; danger_signs.had_convulsions=False; patient_facts.has_cough_or_difficult_breathing=True; patient_facts.has_diarrhoea=False; respiratory.stridor_when_calm=False; respiratory.chest_indrawing=True; respiratory.respiratory_rate=45; dehydration.restless_or_irritable=False; dehydration.sunken_eyes=False; dehydration.drinking_status=NORMAL; dehydration.skin_pinch=NORMAL`  
Oracle classifications: `respiratory=PNEUMONIA`. Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_3_DAYS, GIVE_ORAL_AMOXICILLIN_5_DAYS, SOOTHE_THROAT_AND_RELIEVE_COUGH`.

**Model-visible interaction and structured targets:**

- **Turn 0 — USER:** The child is 24 months old. On observation, the child is not convulsing now. On observation, the child is alert and not lethargic or unconscious. The caregiver says the child can drink or breastfeed. The caregiver says the child does not vomit everything. The caregiver reports no convulsions during this illness. The caregiver reports cough or difficult breathing. The caregiver reports no diarrhoea. When calm, the child has no stridor. With the child calm, the respiratory rate counted for one full minute is 45 breaths per minute.
- **Turn 1 — ASSISTANT:** The available information is sufficient to determine the supported classification decision. The supported action set is determined. The supported assessment is not yet complete. The supported respiratory classification is pneumonia. Advise the caregiver when to return immediately. Follow up in 3 days. Give oral amoxicillin for 5 days. Soothe the throat and relieve the cough with a safe remedy. Assessment still to complete: When the child is calm, observe whether chest indrawing is present.
  - Policy: decision `SUFFICIENT`; actions sufficient `True`; assessment complete `False`; urgent `False`.
  - Classifications: `respiratory=PNEUMONIA`.
  - Actions: `ADVISE_WHEN_TO_RETURN_IMMEDIATELY, FOLLOW_UP_3_DAYS, GIVE_ORAL_AMOXICILLIN_5_DAYS, SOOTHE_THROAT_AND_RELIEVE_COUGH`.
  - Decision acquisitions: `none`.
  - Assessment acquisitions: `respiratory.chest_indrawing`.
  - Round trip: `PASS` via `golden-controlled-language-roundtrip-v1`; human review required `True`.

---

## Review disposition

All controlled-language round trips pass deterministically. No external LLM extractor was used. Domain-expert review should confirm naturalness, action phrasing, and that the controlled targets preserve the intended selected-scope meaning before controlled bulk generation.
