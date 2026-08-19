#!/usr/bin/env python3
"""Fetch and verify a pinned Lundin external benchmark into a local cache."""

from __future__ import annotations

import argparse

from edge_imci.evaluation.external import DEFAULT_EXTERNAL_CACHE, fetch_external_benchmark, load_external_specs


def main() -> None:
    specs = load_external_specs()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark_id", choices=sorted(specs))
    parser.add_argument("--cache-dir", default=DEFAULT_EXTERNAL_CACHE)
    args = parser.parse_args()
    spec, questions, destination = fetch_external_benchmark(args.benchmark_id, args.cache_dir)
    print(f"verified {len(questions)} questions at {spec.revision}; cache: {destination}")


if __name__ == "__main__":
    main()
