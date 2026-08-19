#!/usr/bin/env python3
"""Index separate benchmark run artifacts without merging their scores."""

from __future__ import annotations

import argparse

from edge_imci.evaluation.reporting import write_results_index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", required=True, help="Path to run.json or strict_run.json; repeatable")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    index = write_results_index(args.run, args.output)
    print(f"indexed {sum(len(items) for items in index['sections'].values())} runs in {len(index['sections'])} separate sections")


if __name__ == "__main__":
    main()
