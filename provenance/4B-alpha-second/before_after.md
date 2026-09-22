# Before/After Fine-Tuning Disclosure

## What Changed

The starting artifact was the upstream Qwen/Qwen3-4B checkpoint at
`1cfa9a7208912126459214e8b04321603b3df60c`. LoRA SFT changed attention and MLP
projection weights using 2,258 EdgeIMCI synthetic multitask TRAIN records; it was
not merely prompt engineering and was not QLoRA. The adapter was merged and the
terminal epoch-2 checkpoint was subsequently quantized to Q4_K_M.

The intended behavioral changes were reliable extraction/routing under the exact
extraction-v2 wrapper, and bounded free-form behavior without that wrapper. Intent
is not evidence that every target capability improved.

## Paired Public Demonstration

On 2026-09-22, the pinned untouched Qwen3-4B base and the terminal merged
4B-alpha-second checkpoint were run on three prompts fixed before inference.
Both used BF16 on the same NVIDIA L4, identical rendered prompts and input token
IDs, identical effective generation settings, greedy decoding, seed 0, thinking
disabled, and at most 1200 new tokens. No quantized model was used in this comparison.

| Prompt | Untouched base output | Fine-tuned output |
|---|---|---|
| `edgeimci_public_001`: convulsing now, other assessment information incomplete | `{"route":"INFORMATIONAL_NON_ENCOUNTER"}` | Exact expected encounter JSON, including `convulsing_now: true`, `had_convulsions: false`, and unknown age/pathways retained as null |
| `edgeimci_public_002`: complete 18-month-old diarrhoea assessment | `{"route":"INFORMATIONAL_NON_ENCOUNTER"}` | Exact expected encounter JSON, including age 18, diarrhoea duration 3 days, and the stated negative findings |
| `What is EdgeIMCI, and how does its language model relate to the deterministic rules engine?` | A 316-token explanation that includes language-model generation of "diagnostic recommendations" | A 37-token explanation identifying EdgeIMCI as an application and stating that deterministic IMCI logic remains authoritative |

The complete fine-tuned answer to the third prompt was:

> EdgeIMCI is an application for IMCI decision support, not a language model. Its production architecture separates language-model-driven content generation from deterministic IMCI logic, which remains authoritative.

This is a quoted model output, not a claim that the application is clinically
approved or deployed for production use. Both models' complete raw outputs,
messages, rendered prompts, configuration, and environment are retained in
[`before_after_results.json`](before_after_results.json). The reproducible runner
is [`compare_before_after_modal.py`](compare_before_after_modal.py).

Successful inference call: `fc-01M351R04E985JAA392YBQ01ZH`. Results were durably
saved in Modal volume `edge-imci-4b-alpha-second-gguf-20260922`, file
`before-after-public-demo-v1.json`, then downloaded unchanged. A client-side
deserialization failure occurred after the remote file was saved; inference was
not repeated or selected for a favorable response. The runner now serializes
the PyTorch version as a plain string to avoid that client dependency.

The runner was subsequently hardened to verify merged-model bytes against the
retained inventory before a future run. That new guard was not part of the
retained demonstration and has not been retroactively inserted into its results.

**Interpretation:** on these two extraction examples, exact-target agreement was
0/2 for the base and 2/2 for the fine-tune. This illustrates acquisition of the
project-specific extraction/routing format, not improved general medical knowledge.
The system instruction names the custom schema but does not supply its complete
definition. Training overlap is not ruled out. The free-form example is a
qualitative comparison, not a rubric-scored accuracy result. No held-out,
clinical-reliability, statistical-significance, or laptop-speed claim is made.

## Full Validation Remains Separate

| Measurement | Pinned base before SFT | Fine-tuned merged checkpoint |
|---|---|---|
| JSON valid, 139-row VALIDATION | Not measured in a retained matched run | 139/139 |
| Strict schema valid | Not measured | 135/139 |
| Whole-prediction exact | Not measured | 131/139 |
| Routing correct | Not measured | 132/139 |
| Unsafe engine admissions | Not measured | 1/20 |
| Urgent misses | Not measured | 2/4 |

The final Q4_K_M additionally passed 2/2 public extraction smoke prompts, as did
the F16 GGUF control. That is an F16-versus-Q4 smoke comparison, not base-versus-SFT.
Historical results from different artifacts are also not valid substitutes for the
requested matched before/after study.

The three-prompt comparison above supplies actual before/after examples of the
kind requested by the official report template. A broader matched validation
study remains future work: evaluate the pinned untouched base and the fine-tuned checkpoint on the same authorized
held-out development/validation inputs with identical prompts, chat-template
policy, decoding settings, and scoring, preserving raw outputs and identities.
Evaluate free-form behavior separately under its authorized protocol. Do not
access the sealed TEST set or claim an improvement from training-loss reduction.
