# Clinical questions

This file records source-dependent questions that must not be resolved from general medical knowledge. A proposed rule remains unimplemented until the decision is supplied by an appropriate IMCI domain expert and documented here.

Each question must identify the proposed rule ID, source location, a faithful summary of the source wording, the exact ambiguity, the expert decision required, and the blocked implementation.

## Open

### CQ-001 — Wheeze reassessment before respiratory classification

- **Proposed rule ID:** `IMCI-RESP-WHEEZE-REASSESS`
- **Source:** WHO *Integrated Management of Childhood Illness, Chart Booklet*, March 2014; “Cough or difficult breathing”; PDF page 6 (chart page 2 of 76).
- **Source wording, summarized:** When wheeze occurs with either fast breathing or chest indrawing, the chart directs a trial of rapid-acting inhaled bronchodilator up to three times, followed by another breath count and chest-indrawing assessment before classification.
- **Exact ambiguity:** The source is clear about the clinical sequence but does not define how a static benchmark case should represent the repeated observations, an incomplete bronchodilator trial, or a setting where reassessment is unavailable.
- **Decision needed:** A domain expert must define the admissible pre-treatment/post-treatment observation states and when the benchmark should require reassessment rather than emit a respiratory classification.
- **Blocked implementation:** Wheezing cases and bronchodilator-response rules are excluded from `imci-selected-v0`. Respiratory cases in this version do not assert wheeze.

## Resolved

None.
