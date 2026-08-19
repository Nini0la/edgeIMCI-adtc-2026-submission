#!/usr/bin/env python3
"""Generate the deterministic EdgeIMCI development benchmark."""

from __future__ import annotations

import argparse

from edge_imci.generation.cases import DEFAULT_BENCHMARK_PATH, DEFAULT_SEED, write_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_BENCHMARK_PATH), help="output JSONL path")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="fixed generation seed")
    args = parser.parse_args()
    cases = write_benchmark(args.output, args.seed)
    print(f"wrote {len(cases)} cases to {args.output}")


if __name__ == "__main__":
    main()
