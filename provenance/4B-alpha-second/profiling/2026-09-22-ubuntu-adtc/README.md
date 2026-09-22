# Ubuntu ADTC Participant Profile

**Status: full accuracy-enabled participant run completed; all 17 original evidence files imported byte-for-byte and verified.** All measurements below came from the Ubuntu PC. No Mac accuracy result is combined with them. This is retained participant evidence, not an organizer audit.

## Evidence Source

The original report is [`raw/submission.json`](raw/submission.json), accompanied by the unchanged [supporting files](raw/). All 17 files were imported from `/Users/niniola/Downloads/profile-alpha-second-adtc-g1G6ns`. Their byte counts and SHA-256 hashes are recorded in [`import-verification.json`](import-verification.json). The source directory on Ubuntu was:

```text
/media/ubuntu/eagleNo/profile-alpha-second-adtc-g1G6ns/submission.json
```

Import validation independently checked the complete report against schema 1.3.0 from the recorded official profiler commit. The report and log match the operator's post-run checksums; pre/post model-verification records and submission commits match, and both worktree-status files are empty. The archived metadata is byte-identical to `metadata.json` at the measured submission commit, and its public fields match the report's submission block. Both profiler and GNU time exit statuses are zero.

The earlier [`report-excerpt.console.json`](report-excerpt.console.json) remains as a transcript of the first supplied summary. Its five sections were compared against the original report and match exactly; it is not a substitute report. The original report SHA-256 is `20244dcb046ef3c68c0d0aa10e2784bb4928d1c1876dbd52adf1d2d7b44b2a48`.

## Identity and Configuration

| Field | Recorded evidence |
|---|---|
| Model | `EdgeIMCI-4B-alpha-second-Q4_K_M.gguf` |
| Pre/post-run verified file size | 2,497,280,288 bytes |
| Pre/post-run verified SHA-256 | `a4a8c5bb2d9f3401defa1cb8ea007812d5916c0242d8306a1c7ed6322d550919` |
| Submission checkout | `0017d85836d7a0cf7c03f12315ae68502138b8a4` |
| Reported submission commit | `0017d85836d7`, matching the checkout prefix |
| Profiler installation pin | `7f117dde3d8f2a0b3d3f05948a7bfd4bf693e909` |
| Installed Python / accuracy dependencies | Python 3.11.16; `llama-cpp-python` 0.3.34; `lm-eval` 0.4.12 |
| Machine/session | Intel Core i5-4210U, Ubuntu 22.04.5 LTS, kernel 6.8.0-40-generic; report `ram_gb: 11.6`, preflight `free -h` 11 GiB and no swap |
| Throughput backend | CPU `llama-bench`, recorded commit `aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3`; CMake cache confirms Release, native build, CUDA and BLAS disabled |
| Benchmark executable SHA-256 | `3f09294f2cab744b1b9b021404226e64a03fb9762d7026b9705ca7ff48e3f5de` |
| Throughput configuration | 512 prompt tokens, 128 generation tokens, 2 threads, zero GPU layers; repetitions left at the pinned benchmark's default (5) |
| Accuracy backend | Separate Linux x86-64 CPU wheel for `llama-cpp-python`; official accuracy function, default context 2048 and default backend thread policy |
| Accuracy task | ARC-Easy, limit 50, seed 42, no `--skip-accuracy` |
| Offline settings | `HF_HUB_OFFLINE=1`, `HF_DATASETS_OFFLINE=1`; console confirmed cached dataset use |
| Docker image digest | `unknown`; this was a native participant run, not a Docker audit |

Both artifact-verifier records match [`artifact.json`](../../artifact.json). The GGUF remained on the exFAT model USB and was referenced by an ignored symbolic link from the ext4 submission checkout. The Python environment and dataset cache were under `/mnt/adtc-storage/edgeimci-full-vEUb6D`, not the RAM-backed live root. The accuracy wheel URL is retained in `accuracy-backend-source.json`; its `archive_info` is empty, so that receipt does not independently record a wheel checksum. The GGUF itself is not duplicated in this evidence directory.

ARC-Easy (`allenai/ai2_arc`, configuration `ARC-Easy`) was prepared online before profiling: 2,251 train, 2,376 test and 570 validation rows. The official task evaluates 50 test questions; downloading all splits is not training. The console identified the cached dataset builder directory ending in `210d026faf9955653af8916fad021475a3f00453`; do not confuse that cache identifier with a dataset repository revision.

The supplied invocation was:

```bash
adtc-profiler run \
  --submission "$SUBMISSION" \
  --mode participant \
  --accuracy-task arc_easy \
  --accuracy-limit 50 \
  --seed 42 \
  --output "$RUN_DIR/submission.json"
```

`SUBMISSION` was `/mnt/adtc-storage/edgeimci-full-vEUb6D/repos/submission-ckzgp5`, confirmed by the original GNU time command record. `RUN_DIR` was the Ubuntu source directory above. GNU time wrapped the invocation, and stdout/stderr were captured with `tee`. The environment preflight is timestamped `2026-09-22 18:56:37 UTC`; this is not an exact benchmark-start timestamp.

## Results

| Measurement | Reported value |
|---|---:|
| ARC-Easy `acc_norm` | **0.78**, 50 samples |
| Generation throughput | **5.03 tokens/s** |
| `first_token_latency_ms` | 46,052.31 ms; derived prompt-processing estimate, not directly measured streaming TTFT |
| Peak RSS | **4,288.94 MiB (4.188 GiB)** |
| Steady-state RSS | 4,147.98 MiB |
| Peak VMS | 4,779.79 MiB |
| CPU utilization p99 | 61.7% |
| Reported peak core temperature | **80.0 C** |
| Profiler `throttled` flag | `false` |
| Random seed | 42 |

The separate [GNU time record](raw/time-and-memory.txt) covers the full command, including accuracy:

| Whole-command measurement | Value |
|---|---:|
| Elapsed time | **18:29.24 (1,109.24 seconds)** |
| Maximum process RSS | **4,805,892 KiB (4.583 GiB)** |
| User / system CPU time | 3,220.29 / 28.86 seconds |
| Aggregate CPU percentage | 292% |
| Swaps / exit status | 0 / 0 |

The profiler names memory fields `*_mb` but computes them using bytes divided by `1024**2`, hence MiB above. Its memory sampler sums the profiler process and recursive children during throughput. Memory and thermal sampling stop before the accuracy stage. GNU time supplies a separate full-command maximum process RSS, not a simultaneous sum of the whole process tree or an isolated accuracy-stage peak. Its 292% CPU value aggregates CPU time across cores and is not the profiler's sampled CPU p99 percentage.

At this source pin, `first_token_latency_ms` is computed as prompt tokens divided by prompt-processing rate, multiplied by 1000. The `throttled` flag uses a temperature-threshold heuristic, not direct kernel throttle-event detection. `false` therefore does not prove absence of all throttling or sustained thermal stability. The 50-question score is a small general-science benchmark result, not the full ARC-Easy test set or the organizer's hidden accuracy/quality score. The 11 GiB participant machine does not demonstrate an official 8 GB hardware pass.

## Git Warning

The terminal printed `fatal: not a git repository` after evaluation. In `lm-eval` 0.4.12, `lm_eval.loggers.utils.get_git_commit_hash()` invokes `git describe --always` in the current directory and catches failure; the shell was in `/home/ubuntu`, outside the clone. ADTC separately captures the submission commit using `cwd=submission`, and the resulting `0017d85836d7` matches the verified checkout. This warning alone does not invalidate the reported run. No Git hash was manually substituted in the report.

## Retention and Scope

The complete transferred directory is retained under `raw/`, including the full report, console log, GNU time record, environment/build/dependency records, original metadata, pre/post model checks, pre/post submission commits, empty pre/post worktree-status files and the original report/log checksum file. Original absolute Ubuntu paths, console control characters and file contents are preserved, not rewritten for the Mac. The portable import inventory maps each raw basename to its byte count and hash; the original checksum file still references Ubuntu paths.

This profile belongs to submission commit `0017d85836d7a0cf7c03f12315ae68502138b8a4`; later repository commits must not be substituted into it. The root submission's public prompt pair has since changed, while this report intentionally retains the old metadata snapshot. ARC-Easy did not evaluate either public prompt pair. A report synchronized to a later submission snapshot must come from a new profiler run, not editing these archived bytes.

Raw-file retention and local report validation are complete; organizer auditing remains separate. The [earlier pp128/tg32 microbenchmark](../2026-09-22-cpu/README.md) remains a separate console-derived run whose originals have not been imported. The attempted Mac accuracy setup produced no accuracy result and is not used as evidence here.
