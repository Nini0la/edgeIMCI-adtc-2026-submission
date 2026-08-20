# EdgeIMCI rendering bake-off v1 — human review

**Status:** `PROPOSED_FOR_HUMAN_REVIEW`

These are conversion-acceptance cases, not a model-performance benchmark or SFT corpus. Structured golden trajectories remain the semantic source of truth.

## Configuration summary

| Configuration | Targets | Semantic pass | Rejected | Retries | Hallucination flags | Mode errors | Premature classification | Mean words | Generation seconds | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `qwen3-0.6b-local__guided-conversational-v1` | 16 | 0/16 (0.0%) | 16 | 0 | 0 | 0 | 0 | 21.9 | 4.20 | not measured (local inference) |
| `qwen3-0.6b-local__strict-semantic-v1` | 16 | 2/16 (12.5%) | 14 | 0 | 0 | 0 | 4 | 48.0 | 11.62 | not measured (local inference) |
| `qwen3-1.7b-local__guided-conversational-v1` | 16 | 1/16 (6.2%) | 15 | 0 | 1 | 2 | 0 | 32.0 | 14.63 | not measured (local inference) |
| `qwen3-1.7b-local__strict-semantic-v1` | 16 | 6/16 (37.5%) | 10 | 0 | 2 | 2 | 4 | 40.8 | 22.59 | not measured (local inference) |
| `qwen3-4b-4bit-local__guided-conversational-v1` | 16 | 3/16 (18.8%) | 13 | 0 | 0 | 0 | 0 | 55.6 | 22.49 | not measured (local inference) |
| `qwen3-4b-4bit-local__strict-semantic-v1` | 16 | 10/16 (62.5%) | 6 | 0 | 0 | 0 | 4 | 55.0 | 23.94 | not measured (local inference) |

### Rough naturalness observations

- `qwen3-0.6b-local__guided-conversational-v1`: Short but frequently omits classifications and actions or restates facts incorrectly; not PHC-ready.
- `qwen3-0.6b-local__strict-semantic-v1`: Mechanical list formatting, internal-state leakage, and frequent omissions; not PHC-ready.
- `qwen3-1.7b-local__guided-conversational-v1`: Often fluent and concise, but routinely omits explicit classification terminology and required content.
- `qwen3-1.7b-local__strict-semantic-v1`: More structured, but still awkward and inconsistent, with measurement-mode and unknown-evidence errors.
- `qwen3-4b-4bit-local__guided-conversational-v1`: Generally fluent, but repeats the case presentation and often omits explicit classifications or invariant actions.
- `qwen3-4b-4bit-local__strict-semantic-v1`: Best semantic retention, but mechanical; repeats known evidence and mishandles insufficient and urgent response framing.

### Recommendation

**Current approval decision:** `NO_CURRENT_CONFIGURATION_READY_TO_FREEZE`

**Human-review shortlist:** `qwen3-4b-4bit-local__strict-semantic-v1`

The shortlisted configuration had the highest deterministic semantic pass rate, but still failed insufficient-state content and urgent-first framing.

**Next step:** Refine a single prompt combining strict semantic coverage with the PHC reference format, then rerun the same 14 cases before any controlled corpus generation.

## Side-by-side cases

### golden-complete-chest-pneumonia

**Why:** Complete single-turn respiratory case with chest-indrawing pneumonia and its full selected action block.

**Proposed user turn 0:** The child is 18 months old. The caregiver reports cough or difficult breathing and no diarrhoea. The caregiver also reports the child can drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is not convulsing now, the child is alert and not lethargic or unconscious, there is no stridor while calm, and chest indrawing is present while calm. With the child calm, the respiratory rate counted for one full minute is 35 breaths per minute.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD, MEASUREMENT.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["give oral amoxicillin for 5 days", "soothe the throat and relieve the cough with a safe remedy", "advise the caregiver when to return immediately", "follow up in 3 days"], "classifications": [{"label": "Pneumonia", "pathway": "respiratory"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": false}`

**Proposed reference:** Classification: Pneumonia.

Give oral amoxicillin for 5 days, soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, and follow up in 3 days.

*Language note:* Uses classification terminology and source-backed actions only.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** The child is 18 months old, alert, and not convulsing. Chest indrawing is present while calm, and the respiratory rate is 35 breaths per minute. No cough or difficulty breathing, no vomiting, and no convulsions. The caregiver should return immediately if symptoms worsen. Follow up in 3 days.

Validation notes: `classification:Pneumonia; action:advise the caregiver when to return immediately; action:give oral amoxicillin for 5 days; action:soothe the throat and relieve the cough with a safe remedy`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: Pneumonia  
Classification:  
- Pneumonia  
- Respiratory  
- Sufficient  
- Decision: SUFFICIENT  
- Decision Requests: []  
- Observations:  
  - Child is alert and not lethargic or unconscious  
  - Chest indrawing is present while calm  
  - Respiratory rate: 35 breaths per minute  
- Actions:  
  - give oral amoxicillin for 5 days  
  - soothe the throat and relieve the cough with a safe remedy  
  - advise the caregiver when to return immediately  
  - follow up in 3 days

Validation notes: `none`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Give oral amoxicillin for 5 days. Soothe the throat and relieve the cough with a safe remedy. Advise the caregiver when to return immediately. Follow up in 3 days.

Validation notes: `classification:Pneumonia`

**qwen3-1.7b-local__strict-semantic-v1 — PASS:** Classification: Pneumonia (respiratory)  
Give oral amoxicillin for 5 days  
Soothe the throat and relieve the cough with a safe remedy  
Advise the caregiver when to return immediately  
Follow up in 3 days

Validation notes: `none`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child has pneumonia. Give oral amoxicillin for 5 days. Soothe the throat and relieve the cough with a safe remedy. Advise the caregiver to return immediately if the child's condition worsens. Follow up in 3 days.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — PASS:** Classification: Pneumonia  
Actions: give oral amoxicillin for 5 days, soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, follow up in 3 days  
Respiratory-rate measurement: count breaths for one full minute while the child is calm  
Check: chest indrawing while calm  
Observe: no stridor while calm, child is alert and not lethargic or unconscious, child can drink or breastfeed, no vomiting, no convulsions during this illness

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-very-incomplete

**Why:** Very incomplete presentation that must acquire clinician-observed danger signs before lower-priority information.

**Proposed user turn 0:** The child is 20 months old.

*Language note:* Groups only newly revealed facts; retained acquisition sources: HISTORY_OR_RECORD.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": [], "classifications": [], "decision": "INSUFFICIENT", "decision_requests": [{"channel": "decision", "instruction": "check whether the child is convulsing now", "mode": "CLINICIAN_OBSERVATION", "observation_id": "danger_signs.convulsing_now"}, {"channel": "decision", "instruction": "check whether the child is lethargic or unconscious", "mode": "CLINICIAN_OBSERVATION", "observation_id": "danger_signs.lethargic_or_unconscious"}], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": false}`

**Proposed reference:** Before classifying, check whether the child is convulsing now and whether the child is lethargic or unconscious.

*Language note:* Uses classification terminology and source-backed actions only. Decision-directed requests are introduced as required before classification.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** check whether the child is convulsing now

Validation notes: `acquisition:danger_signs.lethargic_or_unconscious`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: The child is 20 months old.

Validation notes: `acquisition:danger_signs.convulsing_now; acquisition:danger_signs.lethargic_or_unconscious`

**qwen3-1.7b-local__guided-conversational-v1 — PASS:** Check whether the child is convulsing now. Check whether the child is lethargic or unconscious.

Validation notes: `none`

**qwen3-1.7b-local__strict-semantic-v1 — REJECT:** Classification: Check whether the child is convulsing now  
Classification: Check whether the child is lethargic or unconscious

Validation notes: `none`

**qwen3-4b-4bit-local__guided-conversational-v1 — PASS:** The child is 20 months old. Check whether the child is convulsing now. Check whether the child is lethargic or unconscious.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — REJECT:** Classification: Child is 20 months old.  
Decision: INSUFFICIENT  
Decision Request: check whether the child is convulsing now  
Decision Request: check whether the child is lethargic or unconscious

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-partial-needs-respiratory-measurement

**Why:** Partially complete respiratory assessment where only a valid one-minute respiratory-rate measurement can decide pneumonia versus cough/cold.

**Proposed user turn 0:** The child is 18 months old. The caregiver reports cough or difficult breathing and no diarrhoea. The caregiver also reports the child can drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is not convulsing now, the child is alert and not lethargic or unconscious, there is no stridor while calm, and there is no chest indrawing while calm.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["soothe the throat and relieve the cough with a safe remedy", "advise the caregiver when to return immediately"], "classifications": [], "decision": "INSUFFICIENT", "decision_requests": [{"channel": "decision", "instruction": "count the child's breaths for one full minute while the child is calm and report the respiratory rate", "mode": "MEASUREMENT", "observation_id": "respiratory.respiratory_rate"}], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": false}`

**Proposed reference:** Soothe the throat and relieve the cough with a safe remedy and advise the caregiver when to return immediately.

Before classifying, count the child's breaths for one full minute while the child is calm and report the respiratory rate.

*Language note:* Uses classification terminology and source-backed actions only. Decision-directed requests are introduced as required before classification.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** soothe the throat and relieve the cough with a safe remedy  
advise the caregiver when to return immediately

Validation notes: `acquisition:respiratory.respiratory_rate`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: soothe the throat and relieve the cough with a safe remedy  
Classification: advise the caregiver when to return immediately  
Classification: INSUFFICIENT  
Classification: count the child's breaths for one full minute while the child is calm and report the respiratory rate  
Classification: observe the child's respiratory rate

Validation notes: `none`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Soothe the throat and relieve the cough with a safe remedy. Check the child's respiratory rate by counting breaths for one full minute while the child is calm. If the respiratory rate is abnormal, advise the caregiver when to return immediately.

Validation notes: `respiratory.respiratory_rate: measurement lacks count/one-full-minute/calm cues; requested_unknown_asserted:respiratory.respiratory_rate`

**qwen3-1.7b-local__strict-semantic-v1 — REJECT:** Classification: Soothe the throat and relieve the cough with a safe remedy  
Classification: Advise the caregiver when to return immediately  
Observation: Respiratory rate measured by counting breaths for one full minute while the child is calm

Validation notes: `respiratory.respiratory_rate: measurement lacks count/one-full-minute/calm cues; requested_unknown_asserted:respiratory.respiratory_rate`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child is 18 months old. The caregiver reports cough or difficult breathing and no diarrhoea. The child can drink or breastfeed, does not vomit everything, and has no convulsions. On examination, the child is not convulsing, is alert, not lethargic or unconscious, has no stridor while calm, and no chest indrawing while calm. Count the child's breaths for one full minute while the child is calm and report the respiratory rate. Advise the caregiver when to return immediately.

Validation notes: `action:soothe the throat and relieve the cough with a safe remedy`

**qwen3-4b-4bit-local__strict-semantic-v1 — REJECT:** Classification:  
Count the child's breaths for one full minute while the child is calm and report the respiratory rate.

Validation notes: `action:advise the caregiver when to return immediately; action:soothe the throat and relieve the cough with a safe remedy`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-multiturn-age12-rr40

**Why:** Multi-turn progression across the exact older-band threshold: measurement at 40 produces pneumonia.

**Proposed user turn 0:** The child is 12 months old. The caregiver reports cough or difficult breathing and no diarrhoea. The caregiver also reports the child can drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is not convulsing now, the child is alert and not lethargic or unconscious, there is no stridor while calm, and there is no chest indrawing while calm.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["soothe the throat and relieve the cough with a safe remedy", "advise the caregiver when to return immediately"], "classifications": [], "decision": "INSUFFICIENT", "decision_requests": [{"channel": "decision", "instruction": "count the child's breaths for one full minute while the child is calm and report the respiratory rate", "mode": "MEASUREMENT", "observation_id": "respiratory.respiratory_rate"}], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": false}`

**Proposed reference:** Soothe the throat and relieve the cough with a safe remedy and advise the caregiver when to return immediately.

Before classifying, count the child's breaths for one full minute while the child is calm and report the respiratory rate.

*Language note:* Uses classification terminology and source-backed actions only. Decision-directed requests are introduced as required before classification.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** soothe the throat and relieve the cough with a safe remedy  
advise the caregiver when to return immediately

Validation notes: `acquisition:respiratory.respiratory_rate`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: soothe the throat and relieve the cough with a safe remedy  
Classification: advise the caregiver when to return immediately

Validation notes: `acquisition:respiratory.respiratory_rate`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Soothe the throat and relieve the cough with a safe remedy. Advise the caregiver when to return immediately. Check respiratory rate by counting breaths for one full minute while the child is calm.

Validation notes: `respiratory.respiratory_rate: measurement lacks count/one-full-minute/calm cues`

**qwen3-1.7b-local__strict-semantic-v1 — REJECT:** Classification: Soothe the throat and relieve the cough with a safe remedy  
Classification: Advise the caregiver when to return immediately  
Observation: Respiratory rate measured by counting breaths for one full minute while the child is calm.

Validation notes: `respiratory.respiratory_rate: measurement lacks count/one-full-minute/calm cues; requested_unknown_asserted:respiratory.respiratory_rate`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child is 12 months old. The caregiver reports cough or difficult breathing and no diarrhoea. The child can drink or breastfeed, does not vomit everything, and has no convulsions. On examination, the child is not convulsing, is alert, not lethargic or unconscious, has no stridor while calm, and no chest indrawing while calm. Count the child's breaths for one full minute while the child is calm and report the respiratory rate. Advise the caregiver when to return immediately.

Validation notes: `action:soothe the throat and relieve the cough with a safe remedy`

**qwen3-4b-4bit-local__strict-semantic-v1 — REJECT:** Classification:  
soothe the throat and relieve the cough with a safe remedy  
advise the caregiver when to return immediately  

decision: INSUFFICIENT  

decision_requests: count the child's breaths for one full minute while the child is calm and report the respiratory rate  

remaining_assessment_requests: []

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

**Proposed user turn 2:** With the child calm, the respiratory rate counted for one full minute is 40 breaths per minute.

*Language note:* Groups only newly revealed facts; retained acquisition sources: MEASUREMENT.

#### Assistant turn 3

**Structured expected behavior:** `{"actions": ["give oral amoxicillin for 5 days", "soothe the throat and relieve the cough with a safe remedy", "advise the caregiver when to return immediately", "follow up in 3 days"], "classifications": [{"label": "Pneumonia", "pathway": "respiratory"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": false}`

**Proposed reference:** Classification: Pneumonia.

Give oral amoxicillin for 5 days, soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, and follow up in 3 days.

*Language note:* Uses classification terminology and source-backed actions only.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** soothe the throat and relieve the cough with a safe remedy  
advise the caregiver when to return immediately

Validation notes: `classification:Pneumonia; action:follow up in 3 days; action:give oral amoxicillin for 5 days`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: soothe the throat and relieve the cough with a safe remedy  
Classification: advise the caregiver when to return immediately  
Classification: follow up in 3 days

Validation notes: `classification:Pneumonia; action:give oral amoxicillin for 5 days`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Soothe the throat and relieve the cough with a safe remedy. Advise the caregiver when to return immediately. Give oral amoxicillin for 5 days. Follow up in 3 days.

Validation notes: `classification:Pneumonia`

**qwen3-1.7b-local__strict-semantic-v1 — REJECT:** Classification: Give oral amoxicillin for 5 days  
Classification: Soothe the throat and relieve the cough with a safe remedy  
Classification: Advise the caregiver when to return immediately  
Classification: Follow up in 3 days

Validation notes: `classification:Pneumonia`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child is 12 months old. The caregiver reports cough or difficult breathing and no diarrhoea. The child can drink or breastfeed, does not vomit everything, and has no convulsions. On examination, the child is not convulsing, is alert, not lethargic or unconscious, has no stridor while calm, and no chest indrawing while calm. Count the child's breaths for one full minute while the child is calm and report the respiratory rate. Give oral amoxicillin for 5 days. Soothe the throat and relieve the cough with a safe remedy. Follow up in 3 days. Advise the caregiver when to return immediately.

Validation notes: `classification:Pneumonia`

**qwen3-4b-4bit-local__strict-semantic-v1 — PASS:** Classification: Pneumonia  
Classification:  
soothe the throat and relieve the cough with a safe remedy  
advise the caregiver when to return immediately  
follow up in 3 days  
give oral amoxicillin for 5 days

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-age11-rr49-cough-cold

**Why:** Younger-band respiratory rate immediately below 50 verifies justified cough/cold fallback.

**Proposed user turn 0:** The child is 11 months old. The caregiver reports cough or difficult breathing and no diarrhoea. The caregiver also reports the child can drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is not convulsing now, the child is alert and not lethargic or unconscious, there is no stridor while calm, and there is no chest indrawing while calm. With the child calm, the respiratory rate counted for one full minute is 49 breaths per minute.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD, MEASUREMENT.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["soothe the throat and relieve the cough with a safe remedy", "advise the caregiver when to return immediately", "follow up in 5 days if the child is not improving"], "classifications": [{"label": "Cough or cold", "pathway": "respiratory"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": false}`

**Proposed reference:** Classification: Cough or cold.

Soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, and follow up in 5 days if the child is not improving.

*Language note:* Uses classification terminology and source-backed actions only.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** soothe the throat and relieve the cough with a safe remedy  
advise the caregiver when to return immediately  
follow up in 5 days if the child is not improving

Validation notes: `classification:Cough or cold`

**qwen3-0.6b-local__strict-semantic-v1 — PASS:** Classification: Cough or cold  
soothe the throat and relieve the cough with a safe remedy  
advise the caregiver when to return immediately  
follow up in 5 days if the child is not improving

Validation notes: `none`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Soothe the throat and relieve the cough with a safe remedy. Advise the caregiver when to return immediately. Follow up in 5 days if the child is not improving.

Validation notes: `classification:Cough or cold`

**qwen3-1.7b-local__strict-semantic-v1 — PASS:** Classification: Cough or cold  
Soothe the throat and relieve the cough with a safe remedy  
Advise the caregiver when to return immediately  
Follow up in 5 days if the child is not improving

Validation notes: `none`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child has a cough or cold. Soothe the throat and relieve the cough with a safe remedy. Advise the caregiver to return immediately if the child's condition worsens. Follow up in 5 days if the child is not improving.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — PASS:** Classification: Cough or cold  
Actions: soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, follow up in 5 days if the child is not improving  
Respiratory-rate measurement: count breaths for one full minute while the child is calm  
Caregiver questions: ask the caregiver if the child is coughing or has difficulty breathing  
Clinician observations: check if the child is alert and not lethargic or unconscious, observe for stridor while calm, observe for chest indrawing while calm

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-age11-rr50-pneumonia

**Why:** Younger-band respiratory rate exactly at 50 verifies fast-breathing pneumonia.

**Proposed user turn 0:** The child is 11 months old. The caregiver reports cough or difficult breathing and no diarrhoea. The caregiver also reports the child can drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is not convulsing now, the child is alert and not lethargic or unconscious, there is no stridor while calm, and there is no chest indrawing while calm. With the child calm, the respiratory rate counted for one full minute is 50 breaths per minute.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD, MEASUREMENT.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["give oral amoxicillin for 5 days", "soothe the throat and relieve the cough with a safe remedy", "advise the caregiver when to return immediately", "follow up in 3 days"], "classifications": [{"label": "Pneumonia", "pathway": "respiratory"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": false}`

**Proposed reference:** Classification: Pneumonia.

Give oral amoxicillin for 5 days, soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, and follow up in 3 days.

*Language note:* Uses classification terminology and source-backed actions only.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** give oral amoxicillin for 5 days  
soothe the throat and relieve the cough with a safe remedy  
advise the caregiver when to return immediately  
follow up in 3 days

Validation notes: `classification:Pneumonia`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: give oral amoxicillin for 5 days  
Classification: soothe the throat and relieve the cough with a safe remedy  
Classification: advise the caregiver when to return immediately  
Classification: follow up in 3 days

Validation notes: `classification:Pneumonia`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Give oral amoxicillin for 5 days. Soothe the throat and relieve the cough with a safe remedy. Advise the caregiver when to return immediately. Follow up in 3 days.

Validation notes: `classification:Pneumonia`

**qwen3-1.7b-local__strict-semantic-v1 — PASS:** Classification: Pneumonia (respiratory)  
Action: Give oral amoxicillin for 5 days  
Action: Soothe the throat and relieve the cough with a safe remedy  
Action: Advise the caregiver when to return immediately  
Action: Follow up in 3 days

Validation notes: `none`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child has pneumonia. Give oral amoxicillin for 5 days. Soothe the throat and relieve the cough with a safe remedy. Advise the caregiver to return immediately if the child's condition worsens. Follow up in 3 days.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — PASS:** Classification: Pneumonia  
Actions: give oral amoxicillin for 5 days, soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, follow up in 3 days  
Respiratory-rate measurement: count breaths for one full minute while the child is calm  
Caregiver questions: ask the caregiver if the child is coughing or has difficulty breathing  
Clinician observations: check if the child is alert and not lethargic or unconscious, observe for stridor while calm, observe for chest indrawing while calm

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-age12-rr39-cough-cold

**Why:** Older-band respiratory rate immediately below 40 verifies the age-band transition and justified fallback.

**Proposed user turn 0:** The child is 12 months old. The caregiver reports cough or difficult breathing and no diarrhoea. The caregiver also reports the child can drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is not convulsing now, the child is alert and not lethargic or unconscious, there is no stridor while calm, and there is no chest indrawing while calm. With the child calm, the respiratory rate counted for one full minute is 39 breaths per minute.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD, MEASUREMENT.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["soothe the throat and relieve the cough with a safe remedy", "advise the caregiver when to return immediately", "follow up in 5 days if the child is not improving"], "classifications": [{"label": "Cough or cold", "pathway": "respiratory"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": false}`

**Proposed reference:** Classification: Cough or cold.

Soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, and follow up in 5 days if the child is not improving.

*Language note:* Uses classification terminology and source-backed actions only.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** soothe the throat and relieve the cough with a safe remedy  
advise the caregiver when to return immediately  
follow up in 5 days if the child is not improving

Validation notes: `classification:Cough or cold`

**qwen3-0.6b-local__strict-semantic-v1 — PASS:** Classification: Cough or cold  
Classification:  
- soothe the throat and relieve the cough with a safe remedy  
- advise the caregiver when to return immediately  
- follow up in 5 days if the child is not improving

Validation notes: `none`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Soothe the throat and relieve the cough with a safe remedy. Advise the caregiver when to return immediately. Follow up in 5 days if the child is not improving.

Validation notes: `classification:Cough or cold`

**qwen3-1.7b-local__strict-semantic-v1 — PASS:** Classification: Cough or cold  
Soothe the throat and relieve the cough with a safe remedy  
Advise the caregiver when to return immediately  
Follow up in 5 days if the child is not improving

Validation notes: `none`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child has a cough or cold. Soothe the throat and relieve the cough with a safe remedy. Advise the caregiver to return immediately if the child's condition worsens. Follow up in 5 days if the child is not improving.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — PASS:** Classification: Cough or cold  
Actions: soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, follow up in 5 days if the child is not improving  
Respiratory-rate measurement: count breaths for one full minute while the child is calm  
Check: child is alert and not lethargic or unconscious, no stridor while calm, no chest indrawing while calm, child can drink or breastfeed, no vomiting, no convulsions during this illness

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-danger-sign-early-escalation

**Why:** Known vomiting-everything danger sign fixes severe classifications and urgent actions before the supported assessment is complete.

**Proposed user turn 0:** The child is 30 months old. The caregiver reports cough or difficult breathing and no diarrhoea. The caregiver also reports the child vomits everything. On examination, the child is not convulsing now.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["give the first dose of an appropriate antibiotic", "give the indicated pre-referral treatment immediately", "prevent low blood sugar", "keep the child warm", "arrange urgent referral", "complete the remaining assessment quickly"], "classifications": [{"label": "Very severe disease", "pathway": "general_danger_signs"}, {"label": "Severe pneumonia or very severe disease", "pathway": "respiratory"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": ["VOMITS_EVERYTHING"], "remaining_assessment_requests": [{"channel": "assessment_completion", "instruction": "check whether the child is lethargic or unconscious", "mode": "CLINICIAN_OBSERVATION", "observation_id": "danger_signs.lethargic_or_unconscious"}, {"channel": "assessment_completion", "instruction": "ask the caregiver whether the child is able to drink or breastfeed", "mode": "CAREGIVER_QUESTION", "observation_id": "danger_signs.unable_to_drink_or_breastfeed"}, {"channel": "assessment_completion", "instruction": "ask the caregiver whether the child has had convulsions during this illness", "mode": "CAREGIVER_QUESTION", "observation_id": "danger_signs.had_convulsions"}, {"channel": "assessment_completion", "instruction": "check for stridor while the child is calm", "mode": "CLINICIAN_OBSERVATION", "observation_id": "respiratory.stridor_when_calm"}, {"channel": "assessment_completion", "instruction": "check for chest indrawing while the child is calm", "mode": "CLINICIAN_OBSERVATION", "observation_id": "respiratory.chest_indrawing"}, {"channel": "assessment_completion", "instruction": "count the child's breaths for one full minute while the child is calm and report the respiratory rate", "mode": "MEASUREMENT", "observation_id": "respiratory.respiratory_rate"}], "urgent": true}`

**Proposed reference:** URGENT: Act now.

Classification: Very severe disease (general danger signs); Severe pneumonia or very severe disease (respiratory).

Give the first dose of an appropriate antibiotic, give the indicated pre-referral treatment immediately, prevent low blood sugar, keep the child warm, arrange urgent referral, and complete the remaining assessment quickly.

Do not delay urgent treatment or referral. While preparing referral, check whether the child is lethargic or unconscious, ask the caregiver whether the child is able to drink or breastfeed, ask the caregiver whether the child has had convulsions during this illness, check for stridor while the child is calm, check for chest indrawing while the child is calm, and count the child's breaths for one full minute while the child is calm and report the respiratory rate.

*Language note:* Uses classification terminology and source-backed actions only. Urgency is placed first. Remaining assessment is separated from the already determined decision and actions.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** give the first dose of an appropriate antibiotic  
prevent low blood sugar  
keep the child warm  
arrange urgent referral  
complete the remaining assessment quickly

Validation notes: `classification:Severe pneumonia or very severe disease; classification:Very severe disease; action:give the indicated pre-referral treatment immediately; acquisition:danger_signs.lethargic_or_unconscious; acquisition:danger_signs.unable_to_drink_or_breastfeed; acquisition:danger_signs.had_convulsions; acquisition:respiratory.stridor_when_calm; acquisition:respiratory.chest_indrawing; acquisition:respiratory.respiratory_rate`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: VOMITS_EVERYTHING  
Classification: RESPIRATORY  
Decision: SUFFICIENT

Validation notes: `classification:Severe pneumonia or very severe disease; classification:Very severe disease; action:arrange urgent referral; action:complete the remaining assessment quickly; action:give the first dose of an appropriate antibiotic; action:give the indicated pre-referral treatment immediately; action:keep the child warm; action:prevent low blood sugar; acquisition:danger_signs.lethargic_or_unconscious; acquisition:danger_signs.unable_to_drink_or_breastfeed; acquisition:danger_signs.had_convulsions; acquisition:respiratory.stridor_when_calm; acquisition:respiratory.chest_indrawing; acquisition:respiratory.respiratory_rate`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Give the first dose of an appropriate antibiotic, give the indicated pre-referral treatment immediately, prevent low blood sugar, keep the child warm, and arrange urgent referral. Check if the child is lethargic or unconscious. Ask the caregiver if the child is able to drink or breastfeed. Ask if the child has had convulsions during this illness. Check for stridor while the child is calm. Check for chest indrawing while the child is calm. Count the child's breaths for one full minute while the child is calm and report the respiratory rate.

Validation notes: `classification:Severe pneumonia or very severe disease; classification:Very severe disease; action:complete the remaining assessment quickly`

**qwen3-1.7b-local__strict-semantic-v1 — REJECT:** Classification: Very severe disease  
Action: give the first dose of an appropriate antibiotic  
Classification: Severe pneumonia or very severe disease  
Action: give the indicated pre-referral treatment immediately  
Classification: Prevent low blood sugar  
Action: prevent low blood sugar  
Classification: Keep the child warm  
Action: keep the child warm  
Classification: Arrange urgent referral  
Action: arrange urgent referral  
Classification: Complete the remaining assessment quickly  
Action: complete the remaining assessment quickly  
Classification: VOMITS_EVERYTHING  
Action: give the first dose of an appropriate antibiotic  
Classification: LETHARGIC_OR_UNCONSCIOUS  
Action: check whether the child is lethargic or unconscious  
Classification: UNABLE_TO_DRINK_OR_BREASTFEED  
Action: ask the caregiver whether the child is able to drink or breastfeed  
Classification: HAD_CONVULSIONS_DURING_THIS_ILLNESS  
Action: ask the caregiver whether the child has had convulsions during this illness  
Classification: STRIDOR_WHILE_THE_CHILD_IS_CALM  
Action: check for stridor while the child is calm  
Classification: CHEST_INDRAWING_WHILE_THE_CHILD_IS_CALM  
Action: check for chest indrawing while the child is calm  
Classification: RESPIRATORY_RATE  
Action: count the child's breaths for one full minute while the child is calm and report the respiratory rate

Validation notes: `none`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child is showing a very severe disease and severe pneumonia or very severe disease. Give the first dose of an appropriate antibiotic. Give the indicated pre-referral treatment immediately. Prevent low blood sugar. Keep the child warm. Arrange urgent referral. Complete the remaining assessment quickly.

Check whether the child is lethargic or unconscious. Ask the caregiver whether the child is able to drink or breastfeed. Ask the caregiver whether the child has had convulsions during this illness. Check for stridor while the child is calm. Check for chest indrawing while the child is calm. Count the child's breaths for one full minute while the child is calm and report the respiratory rate.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — REJECT:** Classification: Very severe disease  
Classification: Severe pneumonia or very severe disease  
Action: give the first dose of an appropriate antibiotic  
Action: give the indicated pre-referral treatment immediately  
Action: prevent low blood sugar  
Action: keep the child warm  
Action: arrange urgent referral  
Action: complete the remaining assessment quickly  

Check whether the child is lethargic or unconscious  
Ask the caregiver whether the child is able to drink or breastfeed  
Ask the caregiver whether the child has had convulsions during this illness  
Check for stridor while the child is calm  
Check for chest indrawing while the child is calm  
Count the child's breaths for one full minute while the child is calm and report the respiratory rate

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-simultaneous-danger-diazepam

**Why:** Simultaneous unable-to-drink and convulsing-now rules must retain both signs and the additional diazepam action.

**Proposed user turn 0:** The child is 24 months old. The caregiver reports no cough or difficult breathing and no diarrhoea. The caregiver also reports the child is unable to drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is convulsing now and the child is alert and not lethargic or unconscious.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["give diazepam because the child is convulsing now", "give the indicated pre-referral treatment immediately", "prevent low blood sugar", "keep the child warm", "arrange urgent referral", "complete the remaining assessment quickly"], "classifications": [{"label": "Very severe disease", "pathway": "general_danger_signs"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": ["CONVULSING_NOW", "UNABLE_TO_DRINK_OR_BREASTFEED"], "remaining_assessment_requests": [], "urgent": true}`

**Proposed reference:** URGENT: Act now.

Classification: Very severe disease (general danger signs).

Give diazepam because the child is convulsing now, give the indicated pre-referral treatment immediately, prevent low blood sugar, keep the child warm, arrange urgent referral, and complete the remaining assessment quickly.

*Language note:* Uses classification terminology and source-backed actions only. Urgency is placed first.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** give diazepam because the child is convulsing now  
keep the child warm  
prevent low blood sugar  
arrange urgent referral  
complete the remaining assessment quickly

Validation notes: `classification:Very severe disease; action:give the indicated pre-referral treatment immediately`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: CONVULSING_NOW  
Classification: UNABLE_TO_DRINK_OR_BREASTFEED  
Classification: VERY_SEVERE_DISEASE  
Classification: PREVENT_LOW_BLOOD_SUGAR  
Classification: KEEP_CHILD_WARM  
Classification: ARRANGE_URGE_REFERRAL  
Classification: COMPLETE_REMAINING_ASSessment  
Decision: SUFFICIENT

Validation notes: `classification:Very severe disease; action:arrange urgent referral; action:complete the remaining assessment quickly; action:give diazepam because the child is convulsing now; action:give the indicated pre-referral treatment immediately; action:keep the child warm; action:prevent low blood sugar`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Give diazepam now because the child is convulsing. Arrange urgent referral. Keep the child warm and prevent low blood sugar.

Validation notes: `classification:Very severe disease; action:complete the remaining assessment quickly; action:give the indicated pre-referral treatment immediately`

**qwen3-1.7b-local__strict-semantic-v1 — REJECT:** Classification: Very severe disease  
Classification: CONVULSING_NOW  
Classification: UNABLE_TO_DRINK_OR_BREASTFEED  
Action: give diazepam because the child is convulsing now  
Action: give the indicated pre-referral treatment immediately  
Action: prevent low blood sugar  
Action: keep the child warm  
Action: arrange urgent referral  
Action: complete the remaining assessment quickly

Validation notes: `none`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child is convulsing now. Give diazepam because the child is convulsing now. Arrange urgent referral. Complete the remaining assessment quickly. Give the indicated pre-referral treatment immediately. Prevent low blood sugar. Keep the child warm.

Validation notes: `classification:Very severe disease`

**qwen3-4b-4bit-local__strict-semantic-v1 — PASS:** Classification: Very severe disease  
Action: give diazepam because the child is convulsing now  
Action: give the indicated pre-referral treatment immediately  
Action: prevent low blood sugar  
Action: keep the child warm  
Action: arrange urgent referral  
Action: complete the remaining assessment quickly  
Check: respiratory rate  
Observe: alertness  
Observe: feeding ability  
Observe: convulsing now  
Observe: unable to drink or breastfeed

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-severe-dehydration-plan-c

**Why:** Two severe dehydration signs with no other severe classification select severe dehydration and Plan C.

**Proposed user turn 0:** The child is 18 months old. The caregiver reports no cough or difficult breathing and diarrhoea. The caregiver also reports the child can drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is not convulsing now, the child is alert and not lethargic or unconscious, the child is not restless or irritable, and the eyes are sunken. When offered fluid, the child drinks poorly. The abdominal skin pinch returns normally.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["give Plan C fluid for severe dehydration"], "classifications": [{"label": "Severe dehydration", "pathway": "dehydration"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": false}`

**Proposed reference:** Classification: Severe dehydration.

Give Plan C fluid for severe dehydration.

*Language note:* Uses classification terminology and source-backed actions only.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** give Plan C fluid for severe dehydration

Validation notes: `none`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: Severe dehydration  
Classification:  
- Severe dehydration  
- Decision: SUFFICIENT  
- Observation: Child is alert, not convulsing, not lethargic, not restless, eyes are sunken.  
- Action: Give Plan C fluid for severe dehydration.

Validation notes: `none`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Give Plan C fluid for severe dehydration. Check the child's vital signs and abdominal skin pinch. If the child drinks poorly, continue to offer fluids.

Validation notes: `none`

**qwen3-1.7b-local__strict-semantic-v1 — PASS:** Classification: Severe dehydration  
Action: Give Plan C fluid for severe dehydration

Validation notes: `none`

**qwen3-4b-4bit-local__guided-conversational-v1 — PASS:** The child is classified as severe dehydration. Give Plan C fluid for severe dehydration. The child is alert, not lethargic or unconscious, and not restless or irritable. Eyes are sunken. The child drinks poorly when offered fluid. Check for any other signs of dehydration. Observe the child's response to fluids and overall condition.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — PASS:** Classification: Severe dehydration  
Action: give Plan C fluid for severe dehydration  
Check: respiratory rate  
Observe: eyes, alertness, thirst  
Assess: fluid intake, skin turgor  
Give: Plan C fluid for severe dehydration

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-multiturn-some-dehydration

**Why:** Multi-turn clinician observation of sunken eyes resolves an insufficient dehydration decision to some dehydration with two signs.

**Proposed user turn 0:** The child is 18 months old. The caregiver reports no cough or difficult breathing and diarrhoea. The caregiver also reports the child can drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is not convulsing now, the child is alert and not lethargic or unconscious, and the child is restless or irritable. When offered fluid, the child drinks normally. The abdominal skin pinch returns normally.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["advise the caregiver when to return immediately", "follow up in 5 days if the child is not improving"], "classifications": [], "decision": "INSUFFICIENT", "decision_requests": [{"channel": "decision", "instruction": "check whether the child's eyes are sunken", "mode": "CLINICIAN_OBSERVATION", "observation_id": "dehydration.sunken_eyes"}], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": false}`

**Proposed reference:** Advise the caregiver when to return immediately and follow up in 5 days if the child is not improving.

Before classifying, check whether the child's eyes are sunken.

*Language note:* Uses classification terminology and source-backed actions only. Decision-directed requests are introduced as required before classification.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** check whether the child's eyes are sunken

Validation notes: `action:advise the caregiver when to return immediately; action:follow up in 5 days if the child is not improving`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: advises the caregiver when to return immediately  
Classification: follow up in 5 days if the child is not improving

Validation notes: `action:advise the caregiver when to return immediately; acquisition:dehydration.sunken_eyes`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Check whether the child's eyes are sunken.

Validation notes: `action:advise the caregiver when to return immediately; action:follow up in 5 days if the child is not improving`

**qwen3-1.7b-local__strict-semantic-v1 — REJECT:** Classification: Check whether the child's eyes are sunken  
Action: advise the caregiver when to return immediately  
Action: follow up in 5 days if the child is not improving

Validation notes: `none`

**qwen3-4b-4bit-local__guided-conversational-v1 — PASS:** The child is 18 months old. The caregiver reports no cough or difficult breathing and diarrhoea. The child can drink or breastfeed, does not vomit everything, and has no convulsions. On examination, the child is not convulsing, is alert, not lethargic or unconscious, and is restless or irritable. When offered fluid, the child drinks normally. The abdominal skin pinch returns normally.

Check whether the child's eyes are sunken. Follow up in 5 days if the child is not improving. Advise the caregiver to return immediately if there are any changes.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — REJECT:** Classification: check whether the child's eyes are sunken  
Decision: INSUFFICIENT  
Action: advise the caregiver when to return immediately  
Action: follow up in 5 days if the child is not improving

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

**Proposed user turn 2:** On examination, the eyes are sunken.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CLINICIAN_OBSERVATION.

#### Assistant turn 3

**Structured expected behavior:** `{"actions": ["give Plan B fluid, zinc, and food", "advise the caregiver when to return immediately", "follow up in 5 days if the child is not improving"], "classifications": [{"label": "Some dehydration", "pathway": "dehydration"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": false}`

**Proposed reference:** Classification: Some dehydration.

Give Plan B fluid, zinc, and food, advise the caregiver when to return immediately, and follow up in 5 days if the child is not improving.

*Language note:* Uses classification terminology and source-backed actions only.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** check whether the child's eyes are sunken

Validation notes: `classification:Some dehydration; action:advise the caregiver when to return immediately; action:follow up in 5 days if the child is not improving; action:give Plan B fluid, zinc, and food`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: advises the caregiver when to return immediately  
Classification: follow up in 5 days if the child is not improving

Validation notes: `classification:Some dehydration; action:advise the caregiver when to return immediately; action:give Plan B fluid, zinc, and food`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Give Plan B fluid, zinc, and food. Advise the caregiver when to return immediately. Follow up in 5 days if the child is not improving.

Validation notes: `classification:Some dehydration`

**qwen3-1.7b-local__strict-semantic-v1 — REJECT:** Classification: Check whether the child's eyes are sunken  
Action: give Plan B fluid, zinc, and food  
Action: advise the caregiver when to return immediately  
Action: follow up in 5 days if the child is not improving

Validation notes: `classification:Some dehydration`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child has some dehydration. Give Plan B fluid, zinc, and food. Advise the caregiver to return immediately if there are any changes. Follow up in 5 days if the child is not improving. Check whether the child's eyes are sunken.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — PASS:** Classification: some dehydration  
Action: give Plan B fluid, zinc, and food  
Action: advise the caregiver when to return immediately  
Action: follow up in 5 days if the child is not improving

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-no-dehydration-invariant

**Why:** No dehydration is already invariant while the skin-pinch observation remains assessment-only.

**Proposed user turn 0:** The child is 18 months old. The caregiver reports no cough or difficult breathing and diarrhoea. The caregiver also reports the child can drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is not convulsing now, the child is alert and not lethargic or unconscious, the child is not restless or irritable, and the eyes are not sunken. When offered fluid, the child drinks normally.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["give Plan A fluid, zinc, and food", "advise the caregiver when to return immediately", "follow up in 5 days if the child is not improving"], "classifications": [{"label": "No dehydration", "pathway": "dehydration"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": [], "remaining_assessment_requests": [{"channel": "assessment_completion", "instruction": "pinch the abdominal skin and observe how quickly it returns", "mode": "CLINICIAN_OBSERVATION", "observation_id": "dehydration.skin_pinch"}], "urgent": false}`

**Proposed reference:** Classification: No dehydration.

Give Plan A fluid, zinc, and food, advise the caregiver when to return immediately, and follow up in 5 days if the child is not improving.

Also pinch the abdominal skin and observe how quickly it returns.

*Language note:* Uses classification terminology and source-backed actions only. Remaining assessment is separated from the already determined decision and actions.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** The child is 18 months old, alert, and not showing signs of dehydration. They are drinking and breastfeeding normally, and no vomiting or convulsions have occurred. The abdominal skin is not sunken, and the child is not restless or irritable. The assessment is complete.

Validation notes: `classification:No dehydration; action:advise the caregiver when to return immediately; action:follow up in 5 days if the child is not improving; action:give Plan A fluid, zinc, and food; acquisition:dehydration.skin_pinch`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification: No dehydration  
Classification:

Validation notes: `action:advise the caregiver when to return immediately; action:follow up in 5 days if the child is not improving; action:give Plan A fluid, zinc, and food; acquisition:dehydration.skin_pinch`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Give Plan A fluid, zinc, and food. Advise the caregiver when to return immediately. Follow up in 5 days if the child is not improving. Check dehydration by pinching the abdominal skin and observing how quickly it returns.

Validation notes: `classification:No dehydration; acquisition:dehydration.skin_pinch`

**qwen3-1.7b-local__strict-semantic-v1 — REJECT:** Classification: No dehydration  
Action: Give Plan A fluid, zinc, and food  
Action: Advise the caregiver when to return immediately  
Action: Follow up in 5 days if the child is not improving

Validation notes: `acquisition:dehydration.skin_pinch`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child has no dehydration. Give Plan A fluid, zinc, and food. Advise the caregiver to return immediately if the child shows any signs of worsening. Follow up in 5 days if the child is not improving. Pinch the abdominal skin and observe how quickly it returns.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — PASS:** Classification: No dehydration  
Actions: give Plan A fluid, zinc, and food; advise the caregiver when to return immediately; follow up in 5 days if the child is not improving  
Remaining assessment request: pinch the abdominal skin and observe how quickly it returns

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-dehydration-cross-severe-referral

**Why:** Severe dehydration classification remains fixed while severe respiratory classification selects the referral/ORS/breastfeeding branch instead of Plan C.

**Proposed user turn 0:** The child is 18 months old. The caregiver reports cough or difficult breathing and diarrhoea. The caregiver also reports the child can drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is not convulsing now, the child is alert and not lethargic or unconscious, stridor is present while calm, there is no chest indrawing while calm, the child is not restless or irritable, and the eyes are sunken. With the child calm, the respiratory rate counted for one full minute is 30 breaths per minute. When offered fluid, the child drinks poorly. The abdominal skin pinch returns normally.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD, MEASUREMENT.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["give the first dose of an appropriate antibiotic", "give frequent sips of ORS during referral", "continue breastfeeding", "arrange urgent referral"], "classifications": [{"label": "Severe dehydration", "pathway": "dehydration"}, {"label": "Severe pneumonia or very severe disease", "pathway": "respiratory"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": [], "remaining_assessment_requests": [], "urgent": true}`

**Proposed reference:** URGENT: Act now.

Classification: Severe dehydration (dehydration); Severe pneumonia or very severe disease (respiratory).

Give the first dose of an appropriate antibiotic, give frequent sips of ORS during referral, continue breastfeeding, and arrange urgent referral.

*Language note:* Uses classification terminology and source-backed actions only. Urgency is placed first.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** give the first dose of an appropriate antibiotic  
continue breastfeeding  
arrange urgent referral

Validation notes: `classification:Severe dehydration; classification:Severe pneumonia or very severe disease; action:give frequent sips of ORS during referral`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: Severe dehydration  
Classification: Severe pneumonia or very severe disease  

give the first dose of an appropriate antibiotic  
give frequent sips of ORS during referral  
continue breastfeeding  
arrange urgent referral

Validation notes: `none`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Give the first dose of an appropriate antibiotic, give frequent sips of ORS during referral, continue breastfeeding, and arrange urgent referral. The child has severe dehydration and severe pneumonia or very severe disease.

Validation notes: `none`

**qwen3-1.7b-local__strict-semantic-v1 — REJECT:** Classification: Severe dehydration, Pathway: dehydration  
Classification: Severe pneumonia or very severe disease, Pathway: respiratory  
Action: Give the first dose of an appropriate antibiotic  
Action: Give frequent sips of ORS during referral  
Action: Continue breastfeeding  
Action: Arrange urgent referral

Validation notes: `none`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child has severe dehydration and severe pneumonia or very severe disease. Give the first dose of an appropriate antibiotic. Give frequent sips of ORS during referral. Continue breastfeeding. Arrange urgent referral.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — REJECT:** Classification: Severe dehydration  
Classification: Severe pneumonia or very severe disease  
Action: give the first dose of an appropriate antibiotic  
Action: give frequent sips of ORS during referral  
Action: continue breastfeeding  
Action: arrange urgent referral  
Respiratory-rate measurement: count breaths for one full minute while the child is calm  
Check: child can drink or breastfeed  
Check: abdominal skin pinch returns normally  
Observe: eyes are sunken  
Observe: stridor is present while calm  
Observe: no chest indrawing while calm  
Observe: child is alert and not lethargic or unconscious  
Observe: child is not restless or irritable

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

### golden-pneumonia-exact-rule-unresolved

**Why:** Fast breathing fixes pneumonia and its actions while unknown chest indrawing leaves exact rule identity and assessment completion unresolved.

**Proposed user turn 0:** The child is 24 months old. The caregiver reports cough or difficult breathing and no diarrhoea. The caregiver also reports the child can drink or breastfeed, the child does not vomit everything, and no convulsions during this illness. On examination, the child is not convulsing now, the child is alert and not lethargic or unconscious, and there is no stridor while calm. With the child calm, the respiratory rate counted for one full minute is 45 breaths per minute.

*Language note:* Groups only newly revealed facts; retained acquisition sources: CAREGIVER_QUESTION, CLINICIAN_OBSERVATION, HISTORY_OR_RECORD, MEASUREMENT.

#### Assistant turn 1

**Structured expected behavior:** `{"actions": ["give oral amoxicillin for 5 days", "soothe the throat and relieve the cough with a safe remedy", "advise the caregiver when to return immediately", "follow up in 3 days"], "classifications": [{"label": "Pneumonia", "pathway": "respiratory"}], "decision": "SUFFICIENT", "decision_requests": [], "detected_danger_signs": [], "remaining_assessment_requests": [{"channel": "assessment_completion", "instruction": "check for chest indrawing while the child is calm", "mode": "CLINICIAN_OBSERVATION", "observation_id": "respiratory.chest_indrawing"}], "urgent": false}`

**Proposed reference:** Classification: Pneumonia.

Give oral amoxicillin for 5 days, soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, and follow up in 3 days.

Also check for chest indrawing while the child is calm.

*Language note:* Uses classification terminology and source-backed actions only. Remaining assessment is separated from the already determined decision and actions.

**qwen3-0.6b-local__guided-conversational-v1 — REJECT:** give oral amoxicillin for 5 days  
soothe the throat and relieve the cough with a safe remedy  
advise the caregiver when to return immediately  
follow up in 3 days

Validation notes: `classification:Pneumonia; acquisition:respiratory.chest_indrawing`

**qwen3-0.6b-local__strict-semantic-v1 — REJECT:** Classification: Pneumonia  
Classification:  
- Pneumonia  
- Respiratory  
- Sufficient  
- Observation: Respiratory rate is 45 breaths per minute.  
- Action: Give oral amoxicillin for 5 days.  
- Action: Soothe the throat and relieve the cough with a safe remedy.  
- Action: Follow up in 3 days.  
- Action: Check for chest indrawing while the child is calm.

Validation notes: `action:advise the caregiver when to return immediately`

**qwen3-1.7b-local__guided-conversational-v1 — REJECT:** Give oral amoxicillin for 5 days, soothe the throat and relieve the cough with a safe remedy, and advise the caregiver when to return immediately. Follow up in 3 days. Check for chest indrawing while the child is calm.

Validation notes: `classification:Pneumonia`

**qwen3-1.7b-local__strict-semantic-v1 — PASS:** Classification: Pneumonia (respiratory)  
Action: Give oral amoxicillin for 5 days  
Action: Soothe the throat and relieve the cough with a safe remedy  
Action: Advise the caregiver when to return immediately  
Action: Follow up in 3 days  
Observation: Check for chest indrawing while the child is calm

Validation notes: `none`

**qwen3-4b-4bit-local__guided-conversational-v1 — REJECT:** The child has pneumonia. Give oral amoxicillin for 5 days. Soothe the throat and relieve the cough with a safe remedy. Follow up in 3 days. Check for chest indrawing while the child is calm. Advise the caregiver to return immediately if the child's condition worsens.

Validation notes: `none`

**qwen3-4b-4bit-local__strict-semantic-v1 — PASS:** Classification: Pneumonia (respiratory)  
Actions: give oral amoxicillin for 5 days, soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, follow up in 3 days  
Remaining assessment request: check for chest indrawing while the child is calm

Validation notes: `none`

**Human-review fields**

- Semantic faithfulness: `[ ] pass  [ ] issue`
- Naturalness: `[ ] good  [ ] revise`
- PHC suitability: `[ ] suitable  [ ] revise`
- Preferred output: `________________`
- Comments: `________________`

---

## Decision

No configuration is approved automatically. Reviewers should use the deterministic verdicts as rejection guards, then judge naturalness and PHC suitability. Bulk generation remains blocked pending this review.
