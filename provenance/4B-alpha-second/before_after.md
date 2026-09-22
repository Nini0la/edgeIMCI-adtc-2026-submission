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

## Measured Evidence and Gap

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

**Gate 2 before/after evidence is incomplete.** Complete it by evaluating the
pinned untouched base and the fine-tuned checkpoint on the same authorized
held-out development/validation inputs with identical prompts, chat-template
policy, decoding settings, and scoring, preserving raw outputs and identities.
Evaluate free-form behavior separately under its authorized protocol. Do not
access the sealed TEST set or claim an improvement from training-loss reduction.
