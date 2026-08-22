"""Command-line utilities for EdgeIMCI experiment infrastructure."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from edge_imci.experiments.accounting import derive_cost, load_rate_card
from edge_imci.experiments.profiling import (
    create_profile_summary,
    validate_official_adtc_report,
)
from edge_imci.experiments.provenance import atomic_write_json
from edge_imci.experiments.registry import (
    DEFAULT_BRANCH_PATH,
    DEFAULT_MATRIX_PATH,
    DEFAULT_MATRIX_YAML_PATH,
    DEFAULT_RUN_INDEX_PATH,
    REPO_ROOT,
    ExperimentRegistry,
    load_json_object,
    sync_matrix_yaml,
)
from edge_imci.experiments.tracking import build_run_index, validate_run_sidecar


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate-registry", help="validate matrix, campaign branches, and references"
    )
    validate.add_argument("--matrix", default=str(DEFAULT_MATRIX_PATH))
    validate.add_argument("--branches", default=str(DEFAULT_BRANCH_PATH))
    validate.add_argument("--repo-root", default=str(REPO_ROOT))

    sync = subparsers.add_parser(
        "sync-yaml", help="regenerate YAML from canonical experiment JSON"
    )
    sync.add_argument("--matrix", default=str(DEFAULT_MATRIX_PATH))
    sync.add_argument("--output", default=str(DEFAULT_MATRIX_YAML_PATH))

    run = subparsers.add_parser("validate-run", help="validate one common run sidecar")
    run.add_argument("sidecar")

    index = subparsers.add_parser(
        "build-index", help="build a deterministic index from common sidecars"
    )
    index.add_argument(
        "roots", nargs="+", help="directories containing edgeimci_run.json files"
    )
    index.add_argument("--repo-root", default=str(REPO_ROOT))
    index.add_argument("--output", default=str(DEFAULT_RUN_INDEX_PATH))

    cost = subparsers.add_parser(
        "derive-cost", help="derive cost from raw metrics and a named rate card"
    )
    cost.add_argument("usage", help="JSON object containing raw metrics")
    cost.add_argument("rate_card")
    cost.add_argument("--calculation-id", required=True)
    cost.add_argument("--output", required=True)
    cost.add_argument("--attempt-count", type=int)
    cost.add_argument("--accepted-count", type=int)
    cost.add_argument("--example-count", type=int)

    official = subparsers.add_parser(
        "validate-adtc",
        help="validate an untouched official report against a pinned schema",
    )
    official.add_argument("report")
    official.add_argument("schema")

    profile = subparsers.add_parser(
        "summarize-profiles", help="summarize explicit comparable profile sidecars"
    )
    profile.add_argument("sidecars", nargs="+")
    profile.add_argument(
        "--schema", required=True, help="pinned official ADTC JSON Schema"
    )
    profile.add_argument("--summary-id", required=True)
    profile.add_argument("--generated-at", default=None)
    profile.add_argument("--repo-root", default=str(REPO_ROOT))
    profile.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate-registry":
        registry = ExperimentRegistry(
            args.matrix, args.branches, repo_root=args.repo_root
        )
        registry.validate()
        print(
            f"validated {len(registry.matrix['experiments'])} experiments and {len(registry.branches['branches'])} branches"
        )
    elif args.command == "sync-yaml":
        print(sync_matrix_yaml(args.matrix, args.output))
    elif args.command == "validate-run":
        record = validate_run_sidecar(args.sidecar)
        print(f"validated {record['run_id']} ({record['status']})")
    elif args.command == "build-index":
        index = build_run_index(
            args.roots, output_path=args.output, repo_root=args.repo_root
        )
        print(f"indexed {len(index['runs'])} runs in {args.output}")
    elif args.command == "derive-cost":
        metrics = load_json_object(args.usage)
        calculation = derive_cost(
            metrics,
            load_rate_card(args.rate_card),
            calculation_id=args.calculation_id,
            attempt_count=args.attempt_count,
            accepted_count=args.accepted_count,
            example_count=args.example_count,
        )
        atomic_write_json(args.output, calculation)
        print(args.output)
    elif args.command == "validate-adtc":
        validate_official_adtc_report(args.report, args.schema)
        print(f"validated {args.report} without modifying it")
    elif args.command == "summarize-profiles":
        create_profile_summary(
            args.sidecars,
            profile_summary_id=args.summary_id,
            generated_at=args.generated_at or _now(),
            official_schema_path=args.schema,
            repo_root=args.repo_root,
            output_path=args.output,
        )
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
