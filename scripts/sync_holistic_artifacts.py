#!/usr/bin/env python3
"""Regenerate expanded major sick-child YAML mirrors from canonical JSON."""

import json

from edge_imci.information_policy.artifacts import render_generated_yaml
from edge_imci.information_policy.holistic_artifacts import (
    HOLISTIC_DECISIONS_PATH,
    HOLISTIC_DECISIONS_YAML_PATH,
    HOLISTIC_POLICY_PATH,
    HOLISTIC_POLICY_YAML_PATH,
    HOLISTIC_OXYGEN_REFERRAL_DISPOSITION_PATH,
    HOLISTIC_OXYGEN_REFERRAL_DISPOSITION_YAML_PATH,
    HOLISTIC_RULE_PATH,
    HOLISTIC_RULE_YAML_PATH,
)
from edge_imci.rules.yaml_sync import render_rule_yaml


def _load(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == "__main__":
    HOLISTIC_RULE_YAML_PATH.write_text(
        render_rule_yaml(
            _load(HOLISTIC_RULE_PATH),
            HOLISTIC_RULE_PATH,
            "scripts/sync_holistic_artifacts.py",
        ),
        encoding="utf-8",
    )
    HOLISTIC_POLICY_YAML_PATH.write_text(
        render_generated_yaml(
            _load(HOLISTIC_POLICY_PATH),
            HOLISTIC_POLICY_PATH.name,
            "scripts/sync_holistic_artifacts.py",
        ),
        encoding="utf-8",
    )
    HOLISTIC_DECISIONS_YAML_PATH.write_text(
        render_generated_yaml(
            _load(HOLISTIC_DECISIONS_PATH),
            HOLISTIC_DECISIONS_PATH.name,
            "scripts/sync_holistic_artifacts.py",
        ),
        encoding="utf-8",
    )
    HOLISTIC_OXYGEN_REFERRAL_DISPOSITION_YAML_PATH.write_text(
        render_generated_yaml(
            _load(HOLISTIC_OXYGEN_REFERRAL_DISPOSITION_PATH),
            HOLISTIC_OXYGEN_REFERRAL_DISPOSITION_PATH.name,
            "scripts/sync_holistic_artifacts.py",
        ),
        encoding="utf-8",
    )
    print(HOLISTIC_RULE_YAML_PATH)
    print(HOLISTIC_POLICY_YAML_PATH)
    print(HOLISTIC_DECISIONS_YAML_PATH)
    print(HOLISTIC_OXYGEN_REFERRAL_DISPOSITION_YAML_PATH)
