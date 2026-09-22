# Public Submission Prompts

`public_prompts.json` mirrors the two exact inputs in `metadata.json`. The owner
selected this pair on 2026-09-22 and reported having verified it:

| ID | Intended mode | Input |
|---|---|---|
| `edgeimci_public_001` | Free-form natural language | The 18-month-old child who cannot drink/breastfeed and vomits everything, with an incomplete assessment |
| `edgeimci_public_002` | Extraction-v2 JSON | The convulsing-now findings enclosed in the exact extraction-v2 wrapper |

Send these inputs as written. Do not add an extraction wrapper to the first or
double-wrap the second. Metadata intentionally contains only prompt IDs and
inputs, not reference answers, system instructions, or extra mode fields.

No new model inference was run as part of this prompt-selection change. The
owner's verification is not represented here as a retained automated test receipt.

## Historical Evidence

`historical_extraction_prompts.json` preserves the old fixture file unchanged:
unwrapped convulsing-now findings and a complete diarrhoea assessment, with their
expected encounter targets and states. The legacy 0.6B verifier and reproducible
4B before/after runner use that historical file, not the current submission pair.

The retained F16/Q4 2/2 smoke and before/after evidence concern those historical
fixtures under their recorded extraction wrappers/system instructions. They do
not establish results for the current mixed-mode pair. Original IDs are retained
inside the historical receipts; match evidence by fixture content and protocol,
not by prompt ID alone. No historical receipt or raw output was relabelled.
