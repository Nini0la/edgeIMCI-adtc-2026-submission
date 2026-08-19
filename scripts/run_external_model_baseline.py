#!/usr/bin/env python3
"""Run one pinned untuned local model on one pinned external Lundin benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from edge_imci.evaluation.external import (
    DEFAULT_EXTERNAL_CACHE,
    fetch_external_benchmark,
    load_external_specs,
    run_external_benchmark,
)
from edge_imci.inference.mlx_adapter import adapter_from_config, load_model_matrix


def main() -> None:
    model_names = [item["name"] for item in load_model_matrix()["models"]]
    benchmark_ids = sorted(load_external_specs())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=model_names)
    parser.add_argument("benchmark_id", choices=benchmark_ids)
    parser.add_argument("--cache-dir", default=DEFAULT_EXTERNAL_CACHE)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--policy",
        choices=("edge_imci_strict_external_eval", "lundin_upstream_compat_eval"),
        default="edge_imci_strict_external_eval",
    )
    args = parser.parse_args()
    spec, questions, _ = fetch_external_benchmark(args.benchmark_id, args.cache_dir)
    adapter = adapter_from_config(args.model, external=True)
    artifact = run_external_benchmark(questions, spec, adapter, Path(args.output), policy=args.policy)
    print(
        f"model={adapter.model_id} benchmark={spec.benchmark_id} policy={args.policy} "
        f"accuracy={artifact['accuracy']} invalid={artifact['invalid_count']} denominator={artifact['denominator']}"
    )


if __name__ == "__main__":
    main()
