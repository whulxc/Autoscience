"""Reusable workflow helpers for automated research handoff loops."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .control_plane import (
    ValidationResult,
    sha256_text,
    validate_handoff_record,
    validate_inbox_record,
    validate_policy,
    validate_scientific_policy,
)


@dataclass
class ReviewRequest:
    text: str
    payload: dict[str, Any] = field(default_factory=dict)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def render_web_review_request(
    template_text: str,
    *,
    repository: str,
    branch: str,
    expected_commit: str,
    codex_execution_conclusion: str,
    required_files: list[str],
) -> ReviewRequest:
    required_files_list = "\n".join(f"- {item}" for item in required_files)
    replacements = {
        "<OWNER>/<REPO>": repository,
        "<BRANCH>": branch,
        "<40_HEX_COMMIT>": expected_commit,
        "<EXECUTION_CONCLUSION>": codex_execution_conclusion.strip(),
        "<REQUIRED_FILES_LIST>": required_files_list,
        "<NEXT_GOAL_FILE>": "<NEXT_GOAL_FILE>",
    }
    text = template_text
    for key, value in replacements.items():
        text = text.replace(key, value)

    payload = {
        "created_at_utc": utc_now_iso(),
        "repository": repository,
        "branch": branch,
        "expected_commit": expected_commit,
        "required_files": required_files,
        "codex_execution_conclusion_sha256": sha256_text(codex_execution_conclusion.strip()),
        "request_sha256": sha256_text(text),
        "formal_material_source": "github_exact_pushed_head",
        "bridge_role": "codex_web_handoff_trigger_monitor_return",
    }
    return ReviewRequest(text=text, payload=payload)


def write_review_request(request: ReviewRequest, output: Path, payload_output: Path | None = None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(request.text, encoding="utf-8")
    if payload_output is not None:
        payload_output.parent.mkdir(parents=True, exist_ok=True)
        payload_output.write_text(json.dumps(request.payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def enqueue_inbox_record(record: dict[str, Any], queue_dir: Path, *, expected_commit: str | None = None) -> ValidationResult:
    result = validate_inbox_record(record, expected_commit=expected_commit)
    if not result.ok:
        return result

    commit = result.details["expected_commit"]
    goal_hash = result.details["goal_command_sha256"][:16]
    target = queue_dir / f"{commit}_{goal_hash}.json"
    if target.exists():
        return ValidationResult(
            ok=False,
            issues=["inbox_duplicate_record"],
            details={"target": str(target)},
        )

    queue_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ValidationResult(ok=True, details={"target": str(target)})


def summarize_inbox_queue(queue_dir: Path, *, expected_commit: str | None = None) -> ValidationResult:
    issues: list[str] = []
    warnings: list[str] = []
    records: list[dict[str, Any]] = []
    for path in sorted(queue_dir.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            issues.append(f"inbox_record_json_invalid:{path}")
            continue
        result = validate_inbox_record(record, expected_commit=expected_commit)
        if result.issues:
            issues.extend(f"{path}:{item}" for item in result.issues)
        if result.warnings:
            warnings.extend(f"{path}:{item}" for item in result.warnings)
        records.append(
            {
                "path": str(path),
                "ok": result.ok,
                "expected_commit": result.details.get("expected_commit", ""),
                "gate_decision": result.details.get("gate_decision", ""),
                "consumed": bool(record.get("consumed")),
            }
        )
    return ValidationResult(
        ok=not issues,
        issues=issues,
        warnings=warnings,
        details={"queue_dir": str(queue_dir), "record_count": len(records), "records": records},
    )


def consume_inbox_record(record_path: Path, *, expected_commit: str | None = None) -> ValidationResult:
    record = json.loads(record_path.read_text(encoding="utf-8"))
    result = validate_inbox_record(record, expected_commit=expected_commit)
    if not result.ok:
        return result
    if bool(record.get("consumed")):
        return ValidationResult(ok=False, issues=["inbox_record_already_consumed"])
    record["consumed"] = True
    record["consumed_at_utc"] = utc_now_iso()
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ValidationResult(ok=True, details={"record": str(record_path)})


def summarize_workflow_health(
    *,
    policy: dict[str, Any] | None = None,
    scientific_policy: dict[str, Any] | None = None,
    handoff_record: dict[str, Any] | None = None,
    inbox_record: dict[str, Any] | None = None,
    expected_commit: str | None = None,
) -> ValidationResult:
    issues: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}

    if policy is not None:
        result = validate_policy(policy)
        issues.extend(f"policy:{item}" for item in result.issues)
        warnings.extend(f"policy:{item}" for item in result.warnings)
        details["policy_ok"] = result.ok
    if scientific_policy is not None:
        result = validate_scientific_policy(scientific_policy)
        issues.extend(f"scientific_policy:{item}" for item in result.issues)
        warnings.extend(f"scientific_policy:{item}" for item in result.warnings)
        details["scientific_policy_ok"] = result.ok
    if handoff_record is not None:
        result = validate_handoff_record(handoff_record, expected_commit=expected_commit)
        issues.extend(f"handoff:{item}" for item in result.issues)
        warnings.extend(f"handoff:{item}" for item in result.warnings)
        details["handoff_ok"] = result.ok
    if inbox_record is not None:
        result = validate_inbox_record(inbox_record, expected_commit=expected_commit)
        issues.extend(f"inbox:{item}" for item in result.issues)
        warnings.extend(f"inbox:{item}" for item in result.warnings)
        details["inbox_ok"] = result.ok

    return ValidationResult(ok=not issues, issues=issues, warnings=warnings, details=details)
