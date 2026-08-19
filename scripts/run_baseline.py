#!/usr/bin/env python3
"""Run the local mock adapter against an EdgeIMCI benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from edge_imci.evaluation.baseline import run_baseline
from edge_imci.generation.cases import DEFAULT_BENCHMARK_PATH, load_benchmark
from edge_imci.inference.adapters import MockOracleAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", default=str(DEFAULT_BENCHMARK_PATH), help="benchmark JSONL path")
    parser.add_argument("--output", required=True, help="directory for run.json")
    parser.add_argument("--adapter", choices=("mock",), default="mock", help="inference adapter")
    args = parser.parse_args()

    cases = load_benchmark(args.benchmark)
    expected = {case.case_id: case.expected_result for case in cases if case.expected_result is not None}
    adapter = MockOracleAdapter(expected)
    artifact = run_baseline(cases, adapter, args.output, benchmark_version=Path(args.benchmark).stem)
    aggregate = artifact["aggregate_scores"]
    print(f"evaluated {artifact['case_count']} cases; passed {aggregate['passed_cases']}; artifact: {Path(args.output) / 'run.json'}")


if __name__ == "__main__":
    main()
