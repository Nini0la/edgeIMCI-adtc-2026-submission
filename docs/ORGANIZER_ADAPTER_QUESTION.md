# Gate 2 Adapter Delivery Question

Status: draft for replying to the organizer's template-update email. Not sent;
no answer or approval is assumed.

## Email Draft

Subject: EdgeIMCI Gate 2: delivery of original LoRA adapter

Hello ADTC team,

We have updated our public submission repository for Gate 2:
https://github.com/Nini0la/edgeIMCI-adtc-2026-submission

The selected model is a LoRA-fine-tuned Qwen3-4B, and `provenance/` contains its
configuration, training/loss logs, dataset information, conversion records, and
before/after examples. The final GGUF is publicly hosted and the unchanged
template downloader pins its exact revision.

Our original LoRA adapter is 132,187,888 bytes, above GitHub's ordinary-file limit.
GitHub also rejected its Git LFS upload because our submission is a public fork
of your template.

Is it acceptable to provide the original adapter and adapter configuration at
this public immutable URL, with their identities and a verified retrieval helper
inside `provenance/`?

https://huggingface.co/Nini0la/edgeimci-4b-alpha-second-gguf/tree/1aeace1a2eb6e46e5e93d6536cbd1c19db982e53/adapter

If that arrangement is not accepted, which delivery method do you require for a
LoRA adapter of this size? We have not committed split weight files or changed
the fork relationship because we do not want to bypass your large-file rules.

Thank you,
Team EdgeIMCI

## Scope of the Answer

This question concerns competition packaging only. An organizer's acceptance
would not itself clear third-party source rights or provider-contract questions
documented in [`source_rights.md`](../provenance/dataset/source_rights.md).
