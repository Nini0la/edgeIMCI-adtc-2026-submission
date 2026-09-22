# Shortlisted Candidate Training Recipe

**Historical 1,831-row candidate recipe, not the selected 2,258-row
4B-alpha-second run.** See the [selected artifact packet](4B-alpha-second/README.md)
for the selected run's configuration and evidence.

## Shared Recipe

Both candidates were initialized fresh from their pinned Qwen base revisions and trained with the same implementation and dataset.

| Setting | Value |
|---|---|
| Method | LoRA causal-language-model SFT, adapter merged after training |
| LoRA rank / alpha / dropout | 16 / 32 / 0.05 |
| LoRA bias | `none` |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| TRAIN / VALIDATION | 1,831 / 139 records |
| Per-device train / eval batch | 1 / 1 |
| Gradient accumulation | 16 |
| Effective train batch | 16 |
| Optimizer | `adamw_torch_fused` |
| Scheduler | Cosine |
| Warmup ratio / weight decay | 0.05 / 0.01 |
| Maximum gradient norm | 1.0 |
| Precision | BF16 with TF32 enabled |
| Gradient checkpointing | Enabled, non-reentrant |
| Loss | Assistant-only |
| Thinking | Disabled |
| Maximum sequence length | 3,072 |
| Truncation | Prohibited; observed truncated rows: 0 |
| Validation generation | Deterministic, no sampling, maximum 1,200 new tokens |
| Checkpointing | Every epoch plus recovery checkpoints every 50 steps |
| Early stopping / automatic retry | Disabled / disabled |
| Export policy | Terminal epoch, not lowest-loss checkpoint |

Software pins were Python 3.11, Transformers 4.57.1, PyTorch 2.7.1, PEFT 0.16.0, Datasets 3.6.0, Accelerate 1.9.0, and huggingface_hub 0.34.2.

## Candidate-Specific Settings

| Setting | `qwen17-e3-lr1-s3407` | `qwen4-e2-lr3-s20260824` |
|---|---|---|
| Base model | `Qwen/Qwen3-1.7B` | `Qwen/Qwen3-4B` |
| Base/tokenizer revision | `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` | `1cfa9a7208912126459214e8b04321603b3df60c` |
| Epochs | 3 | 2 |
| Learning rate | 0.0001 | 0.0003 |
| Seed | 3407 | 20260824 |
| Global steps | 345 | 230 |
| Total parameters | 1,738,007,552 | 4,055,498,240 |
| Trainable parameters | 17,432,576 | 33,030,144 |
| Epoch checkpoints | 115, 230, 345 | 115, 230 |
| Terminal export | Checkpoint 345 | Checkpoint 230 |
| Lowest-loss checkpoint | 230, epoch 2 | 230, epoch 2 |
| Config SHA-256 | `61c7aa3899529ecff93e520fa47518f143e917b3362b100b22abca30b187463f` | `69407c7734a08ff83b9bde8e188f81338492dcb1d89205f808cc44871bd3a754` |

The data and recipe structure are the same; the model family and the four experiment axes shown above are not. Reproducing either candidate requires its own base revision, epochs, learning rate, seed, and config hash.
