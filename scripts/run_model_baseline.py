#!/usr/bin/env python3
"""Run one pinned untuned local model on the EdgeIMCI development benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from edge_imci.evaluation.baseline import run_baseline
from edge_imci.generation.cases import DEFAULT_BENCHMARK_PATH, load_benchmark
from edge_imci.inference.mlx_adapter import adapter_from_config, load_model_matrix


def main() -> None:
    names = [item["name"] for item in load_model_matrix()["models"]]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=names)
    parser.add_argument("--benchmark", default=DEFAULT_BENCHMARK_PATH)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    adapter = adapter_from_config(args.model)
    artifact = run_baseline(load_benchmark(args.benchmark), adapter, Path(args.output))
    print(
        f"model={adapter.model_id} cases={artifact['case_count']} "
        f"passed={artifact['aggregate_scores']['passed_cases']} "
        f"parse_failures={artifact['parse_failure_count']} output={Path(args.output) / 'run.json'}"
    )


if __name__ == "__main__":
    main()
