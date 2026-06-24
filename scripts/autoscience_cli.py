#!/usr/bin/env python3
"""CLI for Autoscientce control-plane validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from autoscience.control_plane import (  # noqa: E402
    load_json,
    privacy_scan_text,
    DATASET_ROLE_HEADERS,
    EXECUTION_AUTHORIZATION_HEADERS,
    LABEL_AUTHORIZATION_HEADERS,
    STAGE_REGISTRY_HEADERS,
    validate_csv_headers,
    validate_handoff_record,
    validate_inbox_record,
    validate_policy,
    validate_scientific_policy,
)
from autoscience.workflow import (  # noqa: E402
    enqueue_inbox_record,
    render_web_review_request,
    summarize_workflow_health,
    write_review_request,
)


SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "dist", "build"}
TEXT_SUFFIXES = {".md", ".py", ".json", ".txt", ".yaml", ".yml", ".toml", ".cfg", ".ini"}


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def command_validate_policy(args: argparse.Namespace) -> int:
    result = validate_policy(load_json(Path(args.policy)))
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 2


def command_validate_inbox(args: argparse.Namespace) -> int:
    result = validate_inbox_record(load_json(Path(args.record)), expected_commit=args.expected_commit or None)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 2


def command_validate_handoff(args: argparse.Namespace) -> int:
    result = validate_handoff_record(load_json(Path(args.record)), expected_commit=args.expected_commit or None)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 2


CSV_SCHEMAS = {
    "stage-state": STAGE_REGISTRY_HEADERS,
    "dataset-role": DATASET_ROLE_HEADERS,
    "label-authorization": LABEL_AUTHORIZATION_HEADERS,
    "execution-authorization": EXECUTION_AUTHORIZATION_HEADERS,
}


def command_validate_scientific_policy(args: argparse.Namespace) -> int:
    result = validate_scientific_policy(load_json(Path(args.policy)))
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 2


def command_validate_csv_schema(args: argparse.Namespace) -> int:
    result = validate_csv_headers(Path(args.csv), CSV_SCHEMAS[args.schema])
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 2


def command_make_review_request(args: argparse.Namespace) -> int:
    conclusion = Path(args.conclusion_file).read_text(encoding="utf-8")
    template = Path(args.template).read_text(encoding="utf-8")
    request = render_web_review_request(
        template,
        repository=args.repository,
        branch=args.branch,
        expected_commit=args.expected_commit,
        codex_execution_conclusion=conclusion,
        required_files=args.required_file,
    )
    write_review_request(request, Path(args.output), Path(args.payload_output) if args.payload_output else None)
    print(json.dumps({"ok": True, "payload": request.payload}, indent=2, sort_keys=True))
    return 0


def command_enqueue_inbox(args: argparse.Namespace) -> int:
    result = enqueue_inbox_record(
        load_json(Path(args.record)),
        Path(args.queue_dir),
        expected_commit=args.expected_commit or None,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 2


def command_workflow_health(args: argparse.Namespace) -> int:
    result = summarize_workflow_health(
        policy=load_json(Path(args.policy)) if args.policy else None,
        scientific_policy=load_json(Path(args.scientific_policy)) if args.scientific_policy else None,
        handoff_record=load_json(Path(args.handoff)) if args.handoff else None,
        inbox_record=load_json(Path(args.inbox)) if args.inbox else None,
        expected_commit=args.expected_commit or None,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 2


def command_privacy_scan(args: argparse.Namespace) -> int:
    root = Path(args.path)
    issues = []
    warnings = []
    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        result = privacy_scan_text(text)
        issues.extend(f"{path}:{item}" for item in result.issues)
        warnings.extend(f"{path}:{item}" for item in result.warnings)
    if args.strict:
        issues.extend(f"strict_warning:{item}" for item in warnings)
    payload = {"ok": not issues, "issues": issues, "warnings": warnings, "files_scanned": len(list(iter_text_files(root)))}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not issues else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    policy = sub.add_parser("validate-policy")
    policy.add_argument("policy")
    policy.set_defaults(func=command_validate_policy)

    inbox = sub.add_parser("validate-inbox")
    inbox.add_argument("record")
    inbox.add_argument("--expected-commit", default="")
    inbox.set_defaults(func=command_validate_inbox)

    handoff = sub.add_parser("validate-handoff")
    handoff.add_argument("record")
    handoff.add_argument("--expected-commit", default="")
    handoff.set_defaults(func=command_validate_handoff)

    scientific = sub.add_parser("validate-scientific-policy")
    scientific.add_argument("policy")
    scientific.set_defaults(func=command_validate_scientific_policy)

    csv_schema = sub.add_parser("validate-csv-schema")
    csv_schema.add_argument("schema", choices=sorted(CSV_SCHEMAS))
    csv_schema.add_argument("csv")
    csv_schema.set_defaults(func=command_validate_csv_schema)

    make_request = sub.add_parser("make-review-request")
    make_request.add_argument("--template", default="templates/web_review_request.md")
    make_request.add_argument("--repository", required=True)
    make_request.add_argument("--branch", required=True)
    make_request.add_argument("--expected-commit", required=True)
    make_request.add_argument("--conclusion-file", required=True)
    make_request.add_argument("--required-file", action="append", required=True)
    make_request.add_argument("--output", required=True)
    make_request.add_argument("--payload-output", default="")
    make_request.set_defaults(func=command_make_review_request)

    enqueue = sub.add_parser("enqueue-inbox")
    enqueue.add_argument("record")
    enqueue.add_argument("--queue-dir", required=True)
    enqueue.add_argument("--expected-commit", default="")
    enqueue.set_defaults(func=command_enqueue_inbox)

    health = sub.add_parser("workflow-health")
    health.add_argument("--policy", default="")
    health.add_argument("--scientific-policy", default="")
    health.add_argument("--handoff", default="")
    health.add_argument("--inbox", default="")
    health.add_argument("--expected-commit", default="")
    health.set_defaults(func=command_workflow_health)

    privacy = sub.add_parser("privacy-scan")
    privacy.add_argument("path")
    privacy.add_argument("--strict", action="store_true", help="fail on endpoint, UUID, and private-IP warnings")
    privacy.set_defaults(func=command_privacy_scan)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
