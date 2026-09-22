# Preliminary Ubuntu CPU Microbenchmark

**Status: successful user-reported direct benchmark; original evidence files not yet imported.** This is a measurement of **4B-alpha-second**, not alpha-first or the historical 0.6B model. It is not an official ADTC participant report, accuracy evaluation, or clinical qualification.

## Evidence Source

The operator pasted the completed Ubuntu terminal output into the repository-maintenance conversation. The two benchmark rows are transcribed in [`benchmark.console.json`](benchmark.console.json); GNU time output is transcribed in [`time.console.txt`](time.console.txt), with indentation normalized. These files preserve the supplied values, but are **not byte-for-byte imports** of the files on the Ubuntu machine. No benchmark was rerun on the repository-maintenance laptop.

The operator's reported source directory is:

```text
/media/ubuntu/eagleNo/profile-alpha-second-Qv7vzX
```

The console reported benchmark exit status `0`, completed model hashing, and printed the final results-directory message after `sync`. The supplied command saved `benchmark.json`, `benchmark.log`, `time-and-memory.txt`, `status.txt`, `model.sha256`, `environment.txt`, and `CMakeCache.txt` there. The original directory and these files have not been independently inspected or imported here.

## Artifact Identity

| Field | Evidence |
|---|---|
| Model | `EdgeIMCI-4B-alpha-second-Q4_K_M.gguf` |
| Reported model type | `qwen3 4B Q4_K - Medium` |
| Reported parameters | 4,022,468,096 |
| Reported SHA-256 | `a4a8c5bb2d9f3401defa1cb8ea007812d5916c0242d8306a1c7ed6322d550919` |
| Hash comparison | Matches the selected GGUF in [`artifact.json`](../../artifact.json) |
| Expected GGUF file size from artifact manifest | 2,497,280,288 bytes; the laptop's `stat` output was saved separately and not pasted |
| Benchmark `model_size` field | 2,491,323,904 bytes; do not substitute this runtime-reported value for GGUF file size |

The checksum comparison uses the operator's pasted `sha256sum` output; it is not an independent rehash of the flash-drive file. The reported model path was:

```text
/media/ubuntu/eagleNo/EdgeIMCI-4B-alpha-second-Q4_K_M-20260922/EdgeIMCI-4B-alpha-second-Q4_K_M.gguf
```

## Environment and Configuration

| Field | Evidence |
|---|---|
| CPU | Intel Core i5-4210U CPU @ 1.70GHz, reported by benchmark |
| OS/session | Ubuntu live USB session, reported by operator; boot media labeled Ubuntu 22.04.5 LTS amd64 |
| Earlier session memory preflight | 11 GiB total, 9.1 GiB available, no configured swap; not a simultaneous benchmark measurement |
| Model storage | exFAT flash drive mounted at `/media/ubuntu/eagleNo` |
| Live storage | Writable overlay `/cow`; `/tmp` on tmpfs; source/build used disposable `/home/ubuntu/edgeimci-quick-profile/llama.cpp` |
| Backend / offload | CPU, zero GPU layers |
| Threads / repetitions | 2 threads, 1 repetition per test |
| Batch / microbatch | 2048 / 512 |
| KV cache / mmap | F16 K and V; mmap enabled |
| Requested source pin | `aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3` |
| Observed build identity | `build_commit: aedb2a5`, `build_number: 1`; full checkout SHA and binary hash await original `environment.txt` |
| Requested build settings | Release; `GGML_NATIVE=ON`, `GGML_CUDA=OFF`, `GGML_BLAS=OFF`, `LLAMA_CURL=OFF`, tests/server disabled; build parallelism 2 |

Build settings are from the supplied build command, not an inspected CMake cache. This differs from the full runbook's OpenBLAS-enabled build. The pasted build log reached `Built target llama-bench`; a subsequent unsupported `--version` option failed without invalidating the build. The benchmark then ran successfully without that option. The OpenSSL/HTTPS warning did not prevent local-file benchmarking.

The timed invocation, rendered with shell quoting from GNU time's command record, was:

```bash
/usr/bin/time -v -o "$RUN_DIR/time-and-memory.txt" \
  timeout 240 /home/ubuntu/edgeimci-quick-profile/llama.cpp/build/bin/llama-bench \
    -m /media/ubuntu/eagleNo/EdgeIMCI-4B-alpha-second-Q4_K_M-20260922/EdgeIMCI-4B-alpha-second-Q4_K_M.gguf \
    -p 128 -n 32 -t 2 -ngl 0 -r 1 --progress --output json
```

This excerpt identifies the workload, not the complete evidence-capture wrapper. Default warmup was not disabled. AC-power state, background load, CPU governor and temperatures were not supplied.

## Results

| Test | Reported UTC row timestamp | Tokens | Duration (ns) | Throughput (tokens/s) |
|---|---|---:|---:|---:|
| Prompt processing | `2026-09-22T16:53:46Z` | 128 | 10,534,903,420 | 12.150088 |
| Generation | `2026-09-22T16:54:07Z` | 32 | 5,905,677,684 | 5.418514 |

| GNU time measurement | Value |
|---|---:|
| Elapsed wall time | 148.10 seconds (2:28.10) |
| User / system CPU time | 57.01 / 5.33 seconds |
| Aggregate CPU percentage | 42% |
| Maximum resident set size | 4,259,852 KiB (4,160.012 MiB; 4.062511 GiB) |
| Swaps reported | 0 |
| Exit status | 0 |

GNU time covers the timed command, including loading, warmup and both tests; it does not give per-test peak memory. Full wall time is not generation latency or time to first token. Storage/loading overhead was not measured separately, so the gap between test timings and full elapsed time cannot be assigned entirely to USB I/O. The aggregate CPU percentage is not ADTC's sampled CPU p99 metric.

## Interpretation and Remaining Work

- This is a short CPU feasibility measurement with one repetition per workload. The two rows are separate synthetic prompt-processing and generation tests, not two repetitions or one clinical interaction.
- Zero standard deviation is a consequence of one sample, not evidence of stable performance. The 32-token generation test starts at depth zero; it does not establish long-context throughput.
- Peak RSS is process memory, not total machine consumption, steady-state memory, or a demonstrated pass on the official 8 GB laptop profile. Zero reported swaps alone would not establish that swap was disabled; the earlier session preflight separately reported no swap.
- Accuracy, clinical extraction behavior, time to first token, sustained thermal behavior, throttling and an ADTC score were not measured in this microbenchmark. No `submission.json` is fabricated from this output. A [subsequent accuracy-enabled Ubuntu participant run](../2026-09-22-ubuntu-adtc/README.md) is recorded separately with its complete original report and logs retained and verified.
- Historical 0.6B measurements use a different model and workloads; this run is not a controlled speed or memory comparison against them.
- Import the entire original flash-drive evidence directory, preserve its bytes, and compare its JSON, time output and checksum with these transcriptions. Inspect the saved environment and build cache before upgrading provenance claims.
- The subsequent ADTC run does not change this microbenchmark's scope. Independent repeatability measurements and clinical/source-governance review remain separate work. See the [profiling runbook](../../../../docs/PROFILING_RUNBOOK.md).
