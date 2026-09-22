# Original LoRA Adapter Delivery

## Available Evidence

The original epoch-2 adapter for `4B-alpha-second` is publicly available, without
credentials, in the model repository at immutable revision
`1aeace1a2eb6e46e5e93d6536cbd1c19db982e53`:

- [adapter_model.safetensors](https://huggingface.co/Nini0la/edgeimci-4b-alpha-second-gguf/resolve/1aeace1a2eb6e46e5e93d6536cbd1c19db982e53/adapter/adapter_model.safetensors): 132,187,888 bytes.
- [adapter_config.json](https://huggingface.co/Nini0la/edgeimci-4b-alpha-second-gguf/resolve/1aeace1a2eb6e46e5e93d6536cbd1c19db982e53/adapter/adapter_config.json): 896 bytes.

[`artifact.json`](artifact.json) records both files' original identities. The
retained configuration, training/loss logs, and source receipt accompany them in
this provenance packet. Retrieve the two files into this packet's ignored
`adapter/` directory with:

```bash
python3 provenance/4B-alpha-second/download_adapter.py
```

The helper verifies both original files before installing them. It is a retrieval
helper, **not an original training script**. The before/after runner is also not a
training script. The final GGUF download remains independent of adapter retrieval.

## Repository Constraint

The adapter is larger than GitHub's 100 MiB ordinary-file limit. An attempt to
upload it through Git LFS on 2026-09-22 was rejected by GitHub because this
submission repository is a public fork. No LFS pointer or adapter binary was
committed, and the repository's fork relationship was not changed.

The official template asks for adapter weights or training scripts in
`provenance/`, while its general rules say not to put model weights in Git.
It does not expressly address this combination of a large LoRA adapter and
public-fork LFS restrictions.

The project owner approved an offline split bundle **only if competition rules
permit it**. No such permission has been established, so no split or compressed
weight archive has been committed as a workaround.

## Acceptance Status

**Original adapter availability: complete. Competition acceptance of this
hosted delivery arrangement: unconfirmed.** A precise clarification request is
prepared in [`ORGANIZER_ADAPTER_QUESTION.md`](../../docs/ORGANIZER_ADAPTER_QUESTION.md).
No organizer reply has been received or represented as approval.

This is a packaging question, not a missing-weight or model-identity problem,
and it does not prevent standalone GGUF profiling. The next action is to use the
delivery method the organizers confirm, without changing the existing GGUF or
the organizer's two-placeholder downloader.
