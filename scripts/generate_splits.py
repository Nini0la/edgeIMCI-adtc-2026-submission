#!/usr/bin/env python3
"""Generate demonstration split cases and their deterministic manifest."""

from __future__ import annotations

import argparse

from edge_imci.generation.splits import DEFAULT_CASES_PATH, DEFAULT_MANIFEST_PATH, write_split_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases-output", default=DEFAULT_CASES_PATH)
    parser.add_argument("--manifest-output", default=DEFAULT_MANIFEST_PATH)
    args = parser.parse_args()
    cases, manifest = write_split_artifacts(args.cases_output, args.manifest_output)
    counts = {name: regime["counts"] for name, regime in manifest["regimes"].items()}
    print(f"wrote {len(cases)} demonstration cases; split counts: {counts}")


if __name__ == "__main__":
    main()
