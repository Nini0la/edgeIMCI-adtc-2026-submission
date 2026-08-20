#!/usr/bin/env python3
"""Regenerate the tiny golden JSONL/YAML conversion slice and review file."""

from edge_imci.generation.golden import (
    DEFAULT_GOLDEN_PATH,
    DEFAULT_GOLDEN_YAML_PATH,
    DEFAULT_REVIEW_PATH,
    write_golden_slice,
)


if __name__ == "__main__":
    records = write_golden_slice()
    print(f"wrote {len(records)} golden records to {DEFAULT_GOLDEN_PATH}")
    print(f"wrote golden YAML mirror to {DEFAULT_GOLDEN_YAML_PATH}")
    print(f"wrote human review package to {DEFAULT_REVIEW_PATH}")
