#!/usr/bin/env python3
"""Regenerate information-policy YAML review mirrors from canonical JSON."""

from edge_imci.information_policy.artifacts import sync_information_policy_yaml


if __name__ == "__main__":
    for output_path in sync_information_policy_yaml():
        print(output_path)
