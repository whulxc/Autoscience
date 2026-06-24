"""Reusable workflow helpers for automated research handoff loops."""

from __future__ import annotations

import json
import os
import subprocess
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


@dataclass
class AutomationUnitPaths:
    request_path: Path
    payload_path: Path
    report_path: Path


@dataclass
class AutomationUnitResult:
    validation: ValidationResult
    paths: AutomationUnitPaths

    def to_dict(self) -> dict[str, Any]:
        payload = self.validation.to_dict()
        payload["paths"] = {
            "request": str(self.paths.request_path),
            "payload": str(self.paths.payload_path),
            "report": str(self.paths.report_path),
        }
        return payload


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def decode_subprocess_output(data: bytes | str | None) -> str:
    """Decode adapter output without letting platform encoding break a unit."""

    if data is None:
        return ""
    if isinstance(data, str):
        return data
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


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


def summarize_inbox_queue(
    queue_dir: Path,
    *,
    expected_commit: str | None = None,
    required_files: list[str] | None = None,
) -> ValidationResult:
    issues: list[str] = []
    warnings: list[str] = []
    records: list[dict[str, Any]] = []
    for path in sorted(queue_dir.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            issues.append(f"inbox_record_json_invalid:{path}")
            continue
        result = validate_inbox_record(record, expected_commit=expected_commit, required_files=required_files)
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


def consume_inbox_record(
    record_path: Path,
    *,
    expected_commit: str | None = None,
    required_files: list[str] | None = None,
) -> ValidationResult:
    record = json.loads(record_path.read_text(encoding="utf-8"))
    result = validate_inbox_record(record, expected_commit=expected_commit, required_files=required_files)
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
    required_files: list[str] | None = None,
    request_sha256: str | None = None,
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
        result = validate_handoff_record(
            handoff_record,
            expected_commit=expected_commit,
            required_files=required_files,
            request_sha256=request_sha256,
        )
        issues.extend(f"handoff:{item}" for item in result.issues)
        warnings.extend(f"handoff:{item}" for item in result.warnings)
        details["handoff_ok"] = result.ok
    if inbox_record is not None:
        result = validate_inbox_record(inbox_record, expected_commit=expected_commit, required_files=required_files)
        issues.extend(f"inbox:{item}" for item in result.issues)
        warnings.extend(f"inbox:{item}" for item in result.warnings)
        details["inbox_ok"] = result.ok

    return ValidationResult(ok=not issues, issues=issues, warnings=warnings, details=details)


def run_automation_unit(config: dict[str, Any], *, base_dir: Path | None = None) -> AutomationUnitResult:
    """Run one reusable automated-research control-plane unit.

    This runner deliberately does not contain a real ChatGPT/CDP/MCP connector.
    A project-specific private adapter is responsible for transporting the
    generated review request to Web and writing validated handoff/inbox JSON.
    The reusable runner owns the deterministic parts: request rendering,
    policy/scientific-policy checks, handoff validation, inbox enqueue/status,
    optional consume, and workflow-health reporting.
    """

    root = base_dir or Path.cwd()
    artifact_dir = root / str(config.get("artifact_dir") or "runtime/autoscience_unit")
    queue_dir = root / str(config.get("queue_dir") or "runtime/autoscience_goal_inbox")
    artifact_dir.mkdir(parents=True, exist_ok=True)

    request_path = artifact_dir / "web_review_request.md"
    payload_path = artifact_dir / "web_review_payload.json"
    report_path = artifact_dir / "unit_report.json"

    required_keys = ["repository", "branch", "expected_commit", "conclusion_file", "required_files"]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        result = ValidationResult(ok=False, issues=[f"config_required_key_missing:{key}" for key in missing_keys])
        report_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return AutomationUnitResult(result, AutomationUnitPaths(request_path, payload_path, report_path))

    expected_commit = str(config["expected_commit"])

    try:
        template_text = (root / str(config.get("template_path") or "templates/web_review_request.md")).read_text(encoding="utf-8")
        conclusion_text = (root / str(config["conclusion_file"])).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        result = ValidationResult(ok=False, issues=[f"config_input_file_missing:{exc.filename}"])
        report_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return AutomationUnitResult(result, AutomationUnitPaths(request_path, payload_path, report_path))
    request = render_web_review_request(
        template_text,
        repository=str(config["repository"]),
        branch=str(config["branch"]),
        expected_commit=expected_commit,
        codex_execution_conclusion=conclusion_text,
        required_files=[str(item) for item in config["required_files"]],
    )
    write_review_request(request, request_path, payload_path)

    transport = config.get("transport") or {}
    mode = transport.get("mode")
    transport_details: dict[str, Any] = {"mode": str(mode or "")}
    if mode == "local_command":
        if bool(config.get("allow_local_transport_command")) is not True:
            result = ValidationResult(
                ok=False,
                issues=["local_transport_command_requires_explicit_allow_flag"],
                details={"flag": "allow_local_transport_command"},
            )
            report_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return AutomationUnitResult(result, AutomationUnitPaths(request_path, payload_path, report_path))
        command = transport.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
            result = ValidationResult(ok=False, issues=["local_transport_command_must_be_nonempty_string_list"])
            report_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return AutomationUnitResult(result, AutomationUnitPaths(request_path, payload_path, report_path))
        env = dict(os.environ)
        env.update(
            {
                "AUTOSCIENCE_REVIEW_REQUEST": str(request_path),
                "AUTOSCIENCE_REVIEW_PAYLOAD": str(payload_path),
                "AUTOSCIENCE_EXPECTED_COMMIT": expected_commit,
                "AUTOSCIENCE_ARTIFACT_DIR": str(artifact_dir),
            }
        )
        completed = subprocess.run(
            command,
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        stdout_text = decode_subprocess_output(completed.stdout)
        stderr_text = decode_subprocess_output(completed.stderr)
        stdout_log = artifact_dir / "local_transport_stdout.txt"
        stderr_log = artifact_dir / "local_transport_stderr.txt"
        stdout_log.write_text(stdout_text[-12000:], encoding="utf-8")
        stderr_log.write_text(stderr_text[-12000:], encoding="utf-8")
        transport_details.update(
            {
                "returncode": completed.returncode,
                "stdout_tail_path": str(stdout_log),
                "stderr_tail_path": str(stderr_log),
                "stdout_tail": stdout_text[-2000:],
                "stderr_tail": stderr_text[-2000:],
            }
        )
        if completed.returncode != 0:
            result = ValidationResult(
                ok=False,
                issues=["local_transport_command_failed"],
                details={"transport": transport_details},
            )
            report_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return AutomationUnitResult(result, AutomationUnitPaths(request_path, payload_path, report_path))
    elif mode != "static_files":
        result = ValidationResult(
            ok=False,
            issues=["transport_mode_not_supported_or_not_configured"],
            details={"supported_modes": ["static_files", "local_command"]},
        )
        report_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return AutomationUnitResult(result, AutomationUnitPaths(request_path, payload_path, report_path))

    def read_json_file(config_path: str, issue_prefix: str) -> tuple[dict[str, Any] | None, list[str]]:
        if not config_path:
            return None, [f"{issue_prefix}_path_missing"]
        path = root / str(config_path)
        try:
            return json.loads(path.read_text(encoding="utf-8")), []
        except FileNotFoundError:
            return None, [f"{issue_prefix}_missing:{path}"]
        except IsADirectoryError:
            return None, [f"{issue_prefix}_is_directory:{path}"]
        except json.JSONDecodeError:
            return None, [f"{issue_prefix}_json_invalid:{path}"]

    handoff_record, handoff_errors = read_json_file(str(transport.get("handoff_record") or ""), "transport_handoff")
    inbox_record, inbox_errors = read_json_file(str(transport.get("inbox_record") or ""), "transport_inbox")
    policy, policy_errors = read_json_file(str(config.get("policy_path") or "configs/control_plane_policy.example.json"), "policy")
    scientific_policy, scientific_policy_errors = read_json_file(
        str(config.get("scientific_policy_path") or "configs/scientific_policy.example.json"),
        "scientific_policy",
    )
    json_errors = handoff_errors + inbox_errors + policy_errors + scientific_policy_errors
    if json_errors:
        result = ValidationResult(ok=False, issues=json_errors, details={"request": request.payload})
        report_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return AutomationUnitResult(result, AutomationUnitPaths(request_path, payload_path, report_path))

    issues: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"request": request.payload, "transport": transport_details}

    health = summarize_workflow_health(
        policy=policy,
        scientific_policy=scientific_policy,
        handoff_record=handoff_record,
        inbox_record=inbox_record,
        expected_commit=expected_commit,
        required_files=request.payload["required_files"],
        request_sha256=request.payload["request_sha256"],
    )
    issues.extend(health.issues)
    warnings.extend(health.warnings)
    details["health"] = health.details

    if not issues:
        enqueue_result = enqueue_inbox_record(inbox_record, queue_dir, expected_commit=expected_commit)
        issues.extend(f"enqueue:{item}" for item in enqueue_result.issues)
        warnings.extend(f"enqueue:{item}" for item in enqueue_result.warnings)
        details["enqueue"] = enqueue_result.details

        queue_result = summarize_inbox_queue(queue_dir, expected_commit=expected_commit, required_files=request.payload["required_files"])
        issues.extend(f"queue:{item}" for item in queue_result.issues)
        warnings.extend(f"queue:{item}" for item in queue_result.warnings)
        details["queue"] = queue_result.details

        if not issues and bool(config.get("consume_after_enqueue")):
            target = enqueue_result.details.get("target")
            if target:
                consume_result = consume_inbox_record(Path(target), expected_commit=expected_commit, required_files=request.payload["required_files"])
                issues.extend(f"consume:{item}" for item in consume_result.issues)
                warnings.extend(f"consume:{item}" for item in consume_result.warnings)
                details["consume"] = consume_result.details

    result = ValidationResult(ok=not issues, issues=issues, warnings=warnings, details=details)
    report_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return AutomationUnitResult(result, AutomationUnitPaths(request_path, payload_path, report_path))
