# EdgeIMCI Interaction Design — Holistic Assessment, Completeness, and Clinical Synthesis

## Status and purpose

This note supersedes the earlier framing of EdgeIMCI as primarily a system for progressive conversational acquisition, assessment bundles, or retrieval of local decision cards.

Those interaction patterns remain useful, but they are secondary. The default product workflow should reflect how IMCI is intended to be practised: the frontline primary healthcare (PHC) worker completes the major assessment areas before classification and treatment are synthesized.

The central product task is therefore:

> **Given the findings from a completed, holistic IMCI assessment, produce the correct integrated classifications and treatment or management plan.**

EdgeIMCI is not primarily a diagnostic chatbot and should not recreate the paper checklist as a long chat. Its main value is to make the completed IMCI assessment executable: verify that the required evidence is present, apply the relevant logic, and synthesize the resulting classifications and actions across the encounter.

---

## Product definition

### Primary user

The primary user is a frontline PHC worker who has assessed the child using the supported IMCI workflow.

### Default input

The worker enters the completed assessment findings in free-form text. Free-form entry should let the worker report findings naturally and efficiently without forcing them through a large digital form or a sequence of one-question-at-a-time exchanges.

Possible later input channels, such as voice transcription or a structured form, may feed the same canonical encounter representation. They do not change the core workflow.

### Output guarantee

For a complete supported encounter, EdgeIMCI should provide:

- the full set of applicable IMCI classifications;
- an integrated treatment and management synthesis;
- referral, urgency, treatment, counselling, and follow-up actions as applicable;
- a clear explanation or presentation suitable for the PHC worker.

“Integrated” is essential. The product is not a collection of isolated pneumonia, diarrhoea, fever, ear, nutrition, or other classifiers whose outputs are merely concatenated. It must account for simultaneous classifications, precedence, urgent-referral rules, treatment interactions, and the combined management implications of the whole encounter.

### Product boundary

EdgeIMCI supports classification and treatment synthesis from findings gathered by a trained worker. It does not replace the worker’s physical assessment, invent unreported observations, or treat silence as evidence that a sign is absent.

---

## Default interaction flow

```text
PHC worker completes the major IMCI assessment
                    ↓
enters the encounter findings in free-form text
                    ↓
EdgeIMCI checks whether the supported assessment is complete
              ┌─────┴─────┐
              │           │
          complete     incomplete
              │           │
              ↓           ↓
integrated classification  missing-elements report
and treatment synthesis    + final synthesis withheld
                              │
                              ↓
                   worker supplies omissions
                              │
                              └──→ completeness check
```

The common successful interaction should be short:

1. The PHC worker completes the assessment.
2. The worker enters all findings together in free-form text.
3. EdgeIMCI confirms completeness.
4. EdgeIMCI produces the integrated classifications and management plan.

If the submission is incomplete, the next interaction should normally request all relevant omissions together, not begin an unnecessarily long question-by-question dialogue.

---

## Information policy: missing means unknown

The core safety rule is:

> **Not mentioned means UNKNOWN, never negative.**

`UNKNOWN` and `KNOWN_ABSENT` are distinct clinical states.

For example, if a worker submits:

> “14-month-old child. Cough for three days. Respiratory rate 48. No chest indrawing. Drinking well.”

EdgeIMCI must not silently infer that there is no diarrhoea, fever, ear problem, danger sign, nutrition problem, or other unmentioned finding. Those findings remain unknown until explicitly supplied or otherwise established by an authorized input mechanism.

### Complete submission

When every finding required to determine the supported holistic classifications and actions is known, EdgeIMCI may produce the final integrated synthesis.

### Incomplete submission

When required findings are unknown, EdgeIMCI should:

- state that the assessment is incomplete;
- identify the missing assessment elements concisely and specifically;
- group related omissions when that reduces interaction burden;
- preserve all previously supplied findings;
- withhold the final holistic classification and treatment synthesis until the omissions are supplied.

It must not:

- convert an omitted finding into a negative finding;
- fill gaps with a statistically likely answer;
- issue a reassuring final classification from partial evidence;
- present a partial set of classifications as if it were the completed encounter result.

### Urgent findings

Known urgent findings must not be hidden merely because the holistic assessment is incomplete. The interface should surface an already-established urgent action immediately while clearly distinguishing it from the withheld final holistic synthesis.

This exception does not authorize the system to invent the remaining classifications or imply that the encounter is complete. The precise relationship between immediate urgent-action warnings, continued assessment, stabilization, and referral must follow the authoritative IMCI protocol and deployment policy.

---

## Reframing retrieval and conversational depth

The earlier design question was framed as a choice among:

1. progressive conversational acquisition;
2. a context-specific decision or assessment card;
3. assessment bundles.

That framing assumed EdgeIMCI would normally lead the worker through information acquisition. The updated domain understanding changes the default: IMCI is holistic, and the worker is expected to complete the major assessment checklist before classification and treatment.

The primary question is no longer:

> What should the chatbot ask next?

It is:

> **Has the worker supplied the findings required for a complete holistic decision, and if so, what is the correct integrated classification and management synthesis?**

The earlier interaction modes still have value as fallback, support, training, accessibility, and reference features.

### Secondary mode A — Missing-elements request

This is the closest fallback to an assessment bundle. After an incomplete free-form submission, EdgeIMCI returns a compact, self-contained group of omitted assessment elements so the worker can assess or report them together.

The request should expose the actual checks when the category label alone would require guideline recall.

Bad:

> Complete the danger-sign assessment.

Better:

> Provide the remaining general danger-sign findings: ability to drink or breastfeed, vomiting everything, convulsions during this illness, lethargy or unconsciousness, and whether the child is convulsing now.

This mode supports recovery from omission; it is not the normal acquisition loop.

### Secondary mode B — Guided assessment

A step-by-step mode may help in onboarding, unusual cases, low-confidence situations, or settings where the complete assessment cannot be entered at once. It can use the information policy to ask for decision-relevant unknowns progressively.

This mode should be deliberately selected or triggered by a defined policy. It should not become the default merely because the system has a chat interface.

### Secondary mode C — Assessment bundle

The system may present several related checks together when guided support is useful. Bundling reduces repeated assess–type–wait cycles and is usually preferable to one observation per turn when the observations can be collected safely together.

### Secondary mode D — Context-specific assessment or decision card

EdgeIMCI may retrieve a compact, self-contained procedural fragment as a reference aid. A useful card includes the observations or rules the worker needs; it does not merely name an IMCI category and assume the worker remembers its contents.

Cards are supportive procedural memory, not a substitute for returning the completed encounter findings when EdgeIMCI is expected to classify and synthesize treatment.

### Retained UX principle

The useful principle from the earlier design remains:

> **Minimize what the PHC worker must retrieve from memory while also minimizing unnecessary interaction with the system.**

Under the updated default, the most important application of this principle is concise completeness feedback and clear synthesis—not continuous conversational control of the assessment.

---

## Two architectures for two purposes

The hackathon model and a practical deployed product should be distinguished explicitly. They share the same clinical task and data substrate, but they place authority in different runtime components.

### Hackathon architecture: evaluate the model itself

```text
completed free-form IMCI assessment
                ↓
fine-tuned edge-capable instruct model
                ↓
integrated classifications + treatment synthesis
```

For incomplete inputs:

```text
incomplete free-form assessment
                ↓
fine-tuned edge-capable instruct model
                ↓
missing required elements + final synthesis withheld
```

The hackathon evaluates model inference. A hidden deterministic engine should not rescue the model at evaluation time if the research claim is that post-training has taught the model to perform the bounded EdgeIMCI task.

The model must therefore learn to:

- interpret realistic free-form PHC documentation;
- distinguish unknown from known-absent findings;
- recognize whether the whole supported assessment is complete;
- withhold the final answer for incomplete cases;
- produce the correct simultaneous classifications;
- synthesize the combined treatment and management plan;
- apply urgency, precedence, and interaction logic faithfully.

### Production architecture: natural interface, deterministic clinical core

```text
PHC worker completes IMCI assessment
                ↓
free-form findings (or another supported input channel)
                ↓
parser / LLM extracts canonical structured findings
                ↓
schema, terminology, and completeness validation
                ↓
validated deterministic IMCI rule engine
                ↓
integrated classifications and actions
                ↓
natural-language rendering and explanation
```

In a practical deployment, the user experience can remain free-form while the clinical decision core is deterministic and auditable.

The parsing layer may normalize language into structured observations, but it must preserve uncertainty, negation, temporality, subject, and provenance. Low-confidence or ambiguous extraction must be surfaced rather than silently resolved.

The deterministic layer should:

- validate completeness against the applicable encounter scope;
- apply the authoritative IMCI logic;
- compute classifications and integrated actions;
- enforce precedence, contraindication, referral, and interaction rules represented in the system;
- produce traceable decision evidence.

The rendering layer should explain and present the validated result without changing it or adding unsupported clinical content.

This division can be summarized as:

> **Let language-capable components understand and communicate; let validated rules determine the production clinical result.**

That is a likely production architecture, not a claim that every implementation detail has already been decided or validated.

---

## Shared canonical data factory

The two architectures should not require two unrelated data programmes. Both can be built from the same canonical clinical data factory:

```text
complete or deliberately incomplete encounter state
                    ↓
canonical structured representation
                    ↓
deterministic completeness and clinical oracle
                    ↓
expected classifications, actions, and decision trace
                    ↓
realistic free-form PHC input + natural-language target
```

A canonical example should be able to contain:

- encounter scope and patient context;
- structured observation truth;
- explicit `KNOWN_PRESENT`, `KNOWN_ABSENT`, `UNKNOWN`, and, where needed, `NOT_APPLICABLE` states;
- provenance and confidence metadata for extracted findings;
- completeness requirements and missing-element labels;
- expected classifications;
- expected integrated treatment and management actions;
- precedence and interaction outcomes;
- a decision trace or oracle evidence;
- one or more realistic free-form input renderings;
- one or more faithful natural-language output renderings.

### Hackathon use

For supervised fine-tuning and direct model evaluation:

```text
free-form assessment
        →
natural-language integrated answer
```

Incomplete examples instead map to a missing-elements response with final synthesis withheld.

### Production use

The structured representation, completeness specification, and deterministic oracle become operational components or validation assets. The free-form variants support parser development, extraction evaluation, and rendering tests.

### Strategic benefit

The hackathon tests whether a small model can internalize the bounded task. The production system can later use the structured middle layer for safety and auditability. Improvements to canonical clinical coverage strengthen both tracks.

---

## Dataset implications

The primary corpus should move from isolated conditions and next-question trajectories toward complete, whole-encounter examples across the supported major IMCI assessment.

### Required example families

The dataset should include:

- complete encounters with a single classification;
- complete encounters with simultaneous classifications;
- cases with interacting actions or treatment blocks;
- cases in which urgent referral or another priority rule changes routine management;
- borderline threshold cases;
- realistic paraphrases, shorthand, varied ordering, and documentation styles;
- explicit negative findings;
- deliberately incomplete encounters with one or many omissions;
- ambiguous or contradictory inputs that require clarification rather than guessing;
- out-of-scope cases and inputs that should not receive an unsupported IMCI synthesis.

### Omission training

Omission cases must be first-class training and evaluation data, not incidental malformed examples.

The desired behavior is:

```text
complete encounter
        → integrated classification + treatment synthesis

incomplete encounter
        → missing required findings + final synthesis withheld
```

Useful omission variants include:

- one missing finding;
- a missing major assessment area;
- several omissions across areas;
- omissions phrased so that a model may be tempted to infer normality;
- clinically plausible partial notes;
- explicit negatives mixed with unmentioned findings;
- follow-up turns that supply all omissions together;
- follow-up turns that remain incomplete.

### Evaluation targets

Evaluation should separately measure:

- complete-versus-incomplete detection;
- rate of converting omissions into false negatives;
- accuracy of missing-element identification;
- correct withholding of final synthesis;
- extraction accuracy for present, absent, unknown, and ambiguous findings;
- classification accuracy at the encounter level;
- correctness and completeness of the integrated action plan;
- precedence, interaction, urgency, and referral-rule accuracy;
- faithfulness of the natural-language output to the canonical result;
- robustness across realistic PHC language and ordering;
- performance on out-of-scope and contradictory cases.

Exact-match scoring on isolated labels is insufficient. The unit of success is the whole supported encounter.

### Existing data assets

Earlier isolated-condition examples, next-question trajectories, acquisition bundles, and rendering work remain useful for component tests, fallback modes, and language variation. They should not define the primary product objective or dominate the new corpus.

---

## Key design guarantees

EdgeIMCI should be designed and evaluated against the following guarantees:

1. **Holistic before final synthesis.** The system does not present a final encounter-level classification and treatment plan until the supported assessment is complete, including required reassessment stages and resolution of clinically significant contradictions or ambiguities.
2. **Unknown is not negative.** Omitted findings remain unknown and are never silently converted into normal or absent findings.
3. **No invented clinical evidence.** The system does not manufacture observations to complete a pathway.
4. **Explicit completeness feedback.** Incomplete submissions receive a concise account of what is missing.
5. **Integrated result.** Complete encounters produce a coordinated set of classifications and actions, not an unexamined concatenation of condition-specific outputs.
6. **Urgency is visible.** Already-established urgent actions are surfaced promptly and clearly even when final holistic synthesis is withheld.
7. **Traceability.** Production classifications and actions can be traced to structured findings and authoritative rules.
8. **Faithful rendering.** Natural-language presentation does not alter or embellish the validated clinical result.
9. **Low interaction burden.** The default is one complete submission and one answer; omissions are requested in useful groups where safe.
10. **Offline viability.** The supported workflow, clinical logic, and essential explanation remain usable within the intended edge and connectivity constraints.

These are design goals that require clinical validation, implementation tests, and field evaluation before they can be treated as demonstrated guarantees.

---

## Updated component architecture

The earlier information-policy work remains useful, but its role changes.

```text
authoritative IMCI sources
            ↓
canonical clinical representation
            ↓
validated deterministic oracle / rules
            ↓
┌──────────────────────────────────────────────┐
│ shared data factory                          │
│ structured cases, omissions, traces, text    │
└──────────────────────────────────────────────┘
            ↓                         ↓
hackathon model training       production runtime assets
            ↓                         ↓
free-form → model result       free-form → extraction
                                      ↓
                               completeness validation
                                      ↓
                               deterministic decision
                                      ↓
                               faithful explanation
```

Within either track, an information policy can compute:

```text
known findings
        ↓
required but unknown findings
        ↓
whether final synthesis is permitted
        ↓
missing-elements request or completed result
```

For secondary guided modes, the same state can also render as:

```text
semantic state
 ├── grouped missing-elements request
 ├── progressive question
 ├── assessment bundle
 └── compact decision / assessment card
```

Thus, earlier work on unknown evidence, valid completions, decision-directed acquisition, and rendering contracts is preserved. It no longer defines the core UX; it supports completeness enforcement and fallback interaction.

---

## Open decisions

### 1. Supported encounter scope

Which age bands, major assessment areas, country adaptations, and protocol version are in scope for the hackathon and for the first practical pilot?

Completeness can only be judged relative to an explicit scope and applicable pathway.

### 2. Minimum complete assessment schema

What findings are always required, what findings are conditionally required, and what can legitimately be marked not applicable? This must be specified by the authoritative protocol rather than inferred from training examples.

### 3. Free-form input contract

How much structure should be encouraged inside free-form entry? Options include unrestricted notes, a lightweight section template, voice-to-text, or hybrid text with optional prompts. The choice should be tested with PHC workers for speed, omission rates, and usability.

### 4. Handling ambiguity and contradiction

When should the system ask for clarification, reject the entry, display competing interpretations, or allow a worker to confirm the extracted structure? Production policy should define confidence thresholds and correction workflows.

### 5. Visibility of parsed findings

Should a production user confirm the structured findings before the deterministic engine runs, or only when extraction is ambiguous or high-risk? This trades interaction burden against error detection.

### 6. Urgent action during incompleteness

Which urgent actions may or must be surfaced before holistic completeness, and how should they be worded without implying a final result? This requires protocol-specific clinical review.

### 7. Authority and versioning

Which IMCI source and local adaptation are authoritative? How will rule versions, model versions, provenance, and updates be managed and audited offline?

### 8. Hackathon evaluation boundary

Which preprocessing, prompt scaffolding, decoding constraints, and post-processing are permitted while still honestly evaluating the model itself? The evaluation harness should make this boundary explicit.

### 9. Model-output contract

Should the hackathon model emit only natural language, a structured result plus natural rendering, or a constrained intermediate representation? The format must match the evaluation objective without disguising a rule engine as model performance.

### 10. Role of secondary modes

When should guided questions, bundles, and cards be available or recommended? Candidate triggers include onboarding, explicit user choice, detected omission, low extraction confidence, and unusual pathway complexity.

### 11. Human factors and field workflow

The default hypothesis must be tested with actual PHC workers: whether whole-assessment free-form entry is faster, clearer, and less error-prone than structured or guided alternatives, especially on low-cost devices and under offline conditions.

### 12. Safety and regulatory validation

What clinical validation, human oversight, audit, privacy, security, post-deployment monitoring, and local regulatory requirements must be satisfied before practical use?

---

## Near-term product and research priorities

1. Define the supported holistic encounter scope and versioned authoritative source.
2. Build the canonical structured schema for complete encounters, explicit negatives, unknowns, applicability, classifications, and integrated actions.
3. Implement or validate a deterministic oracle for data generation and evaluation.
4. Expand the corpus from isolated cases to whole encounters, especially simultaneous classifications and interacting actions.
5. Generate systematic omission cases and measure whether the model mistakes missing information for negative findings.
6. Train and evaluate the hackathon model on free-form whole-assessment input to integrated output, without a runtime rule engine masking model errors.
7. Prototype the production extraction–validation–rules–rendering pipeline using the same canonical cases.
8. Test the default workflow and fallback modes with PHC workers before fixing the final interface.

---

## Current working hypothesis

The default EdgeIMCI experience should be:

> **Complete the holistic IMCI assessment, enter the findings naturally, and receive an integrated classification and treatment synthesis. If the supported assessment is incomplete, EdgeIMCI identifies the missing or unresolved elements and withholds the final holistic synthesis until completion.**

For the hackathon, the fine-tuned instruct model performs this transformation directly because the model itself is under evaluation.

For practical deployment, the same free-form experience can sit on top of structured extraction, deterministic completeness checking and IMCI logic, and faithful natural-language explanation.

Both tracks should be generated, tested, and compared against the same canonical structured data factory.

---

## Design principles to retain

> **Missing is unknown, not negative.**

> **Incomplete assessment means no final holistic classification or treatment synthesis.**

> **The default unit of work is the whole supported IMCI encounter, not the next chatbot question.**

> **Minimize memorization and interaction burden without weakening completeness or clinical traceability.**

> **Use the model directly where model capability is the research object; use validated deterministic clinical logic where practical deployment safety is the objective.**
