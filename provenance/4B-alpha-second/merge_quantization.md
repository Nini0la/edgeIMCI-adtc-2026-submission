# Merge and Quantization

## Training and Merge

The original `training_config.json` records LoRA on the pinned Qwen/Qwen3-4B base:
rank 16, alpha 32, dropout 0.05, no bias, targeting `q_proj`, `k_proj`, `v_proj`,
`o_proj`, `gate_proj`, `up_proj`, and `down_proj`. Training used BF16, not QLoRA:
2 epochs, LR 0.0003, seed 20260824, effective batch size 16, cosine schedule,
warmup ratio 0.05, weight decay 0.01, and assistant-only loss. Thinking was disabled,
maximum sequence length was 3072, and truncation was forbidden.

`merge_adapter_after_training=true` is recorded in the original recipe. The
terminal epoch-2 merged checkpoint was exported alongside the LoRA adapter.
The historical merge implementation is not recovered here; do not treat an
invented command as its execution log. The original merged files and adapter
are bound to `artifact_hashes.json`, SHA-256
`7f53d7a0eac4938194fdbc977f64bd0b17bbb8fc6131f3573fcc790edfbca1a0`.

## GGUF Conversion

The conversion worker verified all 14 merged-model files against that original
inventory, then ran the commands in `conversion_manifest.json` on Modal CPU
(16 cores, 32 GiB requested RAM). No original training artifacts were modified.

Tool source: `https://github.com/ggml-org/llama.cpp`, commit
`aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3`.

Equivalent commands, with `MERGED`, `F16`, and `Q4` set to the recorded paths:

```bash
python /opt/llama.cpp/convert_hf_to_gguf.py "$MERGED" --outfile "$F16" --outtype f16
/opt/llama.cpp/build/bin/llama-quantize "$F16" "$Q4" Q4_K_M 16
```

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| F16 control | 8,051,284,768 | `2ffd882dc415f8c1356b2cde1b010a2218a52dfdc1b6ae8b026f23fbc9f74f0e` |
| Q4_K_M | 2,497,280,288 | `a4a8c5bb2d9f3401defa1cb8ea007812d5916c0242d8306a1c7ed6322d550919` |

Q4_K_M is mixed-precision 4-bit quantization. The F16 intermediate was not
downloaded locally. Both representations passed the two public extraction prompts
with exact JSON targets and matching deterministic states (`URGENT_INCOMPLETE`,
`COMPLETE`). Raw outputs and parsed results are in `smoke_results.json`.

The smoke used the extraction-v2 system instruction, exact wrapper, tokenizer
chat template with `enable_thinking=False`, temperature 0, seed 0, context 3072,
and at most 1200 generated tokens. These are not raw unwrapped free-form results.
No full quantization-drift, matched-base comparison, or laptop performance claim
is established by these two prompts.
