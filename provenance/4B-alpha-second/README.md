# 4B-alpha-second Evidence

This packet belongs only to the selected enriched 2,258-row fine-tune, run
`multitask2258-20260922-v1--qwen4-e2-lr3-s20260824`, exported at epoch 2.

Original training configuration and loss logs are retained byte-for-byte.
The original LoRA adapter is published separately from the GGUF on Hugging Face;
its immutable reference and checksums are recorded in `artifact.json`. Anonymous
hosting metadata matches the expected weight hashes and sizes. Large weights are
not stored in ordinary Git blobs. Run `python3 provenance/4B-alpha-second/download_adapter.py`
from the repository root to retrieve and verify both original adapter files into
the ignored `adapter/` subdirectory. Confirm organizer acceptance of this hosted
adapter arrangement before calling the Gate 2 packet complete.

See [adapter delivery status](adapter_delivery.md) for the public-fork LFS
restriction and the current public hosting arrangement. No large-weight Git
workaround has been committed.

The dataset source-release hashes are recorded in `dataset_info.md`. Its public
JSONL/Parquet publication is pinned at immutable Hugging Face revision
`da8daa8efbd583d92000920366085f6dd00c3fb2`; consolidated dataset/source-license
review remains pending.

The [source and rights disclosure](../dataset/source_rights.md) identifies the
WHO reference, AI-assisted construction roles, applicable-terms questions, and
the owner's confirmation that no separate permissions have been obtained.
It is not a new license or a claim of legal clearance.

The source training authorization was research-only. The owner subsequently
selected this candidate for quantization, public hosting, and submission profiling;
that does not authorize clinical use or establish that clinical review is complete.

## Preliminary Laptop Profiling

The [2026-09-22 Ubuntu CPU microbenchmark](profiling/2026-09-22-cpu/README.md)
records the operator's successful one-repetition pp128/tg32 run and GNU time
memory result for the selected Q4_K_M GGUF. Console transcriptions are retained
separately from the unchanged training/conversion evidence. Original flash-drive
files have not yet been imported; the complete official ADTC profile, accuracy,
sustained thermals and 8 GB qualification remain pending.
