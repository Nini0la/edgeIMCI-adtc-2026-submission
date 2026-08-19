#!/usr/bin/env python3
"""Synchronize the human-readable YAML rules from the canonical JSON artifact."""

from __future__ import annotations

import argparse

from edge_imci.rules.loader import DEFAULT_RULE_PATH
from edge_imci.rules.yaml_sync import DEFAULT_YAML_RULE_PATH, sync_rule_yaml


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=str(DEFAULT_RULE_PATH), help="canonical JSON rule path")
    parser.add_argument("--yaml", default=str(DEFAULT_YAML_RULE_PATH), help="generated YAML rule path")
    args = parser.parse_args()

    output_path = sync_rule_yaml(args.json, args.yaml)
    print(f"synchronized YAML rules to {output_path}")


if __name__ == "__main__":
    main()
