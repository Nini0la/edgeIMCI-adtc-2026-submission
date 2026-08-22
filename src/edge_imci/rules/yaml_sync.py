"""Generate the review-oriented YAML mirror from the canonical JSON rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from edge_imci.rules.loader import DEFAULT_RULE_PATH

DEFAULT_YAML_RULE_PATH = DEFAULT_RULE_PATH.with_suffix(".yaml")
class _IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        return super().increase_indent(flow, indentless=False)


def load_canonical_rule_data(path: str | Path = DEFAULT_RULE_PATH) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("canonical rule artifact must contain a JSON object")
    return data


def render_rule_yaml(
    data: dict[str, Any],
    source_path: str | Path = DEFAULT_RULE_PATH,
    sync_script: str = "scripts/sync_rule_yaml.py",
) -> str:
    source = Path(source_path)
    try:
        display_path = source.resolve().relative_to(DEFAULT_RULE_PATH.parents[2].resolve())
    except ValueError:
        display_path = source
    header = (
        f"# Generated from {display_path}.\n"
        f"# Review this file freely, but edit the canonical JSON and rerun {sync_script}.\n"
    )
    body = yaml.dump(
        data,
        Dumper=_IndentedSafeDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=100,
    )
    return header + body


def sync_rule_yaml(
    json_path: str | Path = DEFAULT_RULE_PATH,
    yaml_path: str | Path = DEFAULT_YAML_RULE_PATH,
) -> Path:
    output_path = Path(yaml_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_rule_yaml(load_canonical_rule_data(json_path), json_path),
        encoding="utf-8",
    )
    return output_path
