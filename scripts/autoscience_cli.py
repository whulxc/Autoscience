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
    validate_inbox_record,
    validate_policy,
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
