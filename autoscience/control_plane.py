"""Dependency-free validators for automated research control planes."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ALLOWED_MODEL_MARKERS = ("gpt 5.5 pro", "thinking")
VALID_GATES = {"READY", "BLOCKED", "R2_IMPLEMENTED_STOP"}
FORBIDDEN_TRUE_FLAGS = {
    "allow_generic_write",
    "allow_edit",
    "allow_apply_patch",
    "allow_bash",
    "allow_shell",
    "allow_terminal",
    "allow_raw_dataset_reads",
    "allow_secret_reads",
    "allow_checkpoint_io",
    "allow_run_directory_io",
    "allow_remote_gpu",
    "allow_training",
    "allow_inference",
    "allow_evaluation",
    "allow_parser_construction",
    "allow_target_construction",
    "allow_split_or_view_construction",
    "allow_long_lived_server",
    "allow_public_tunnel",
    "allow_persisted_endpoint_or_token",
}

SECRET_PATTERNS = {
    "api_key_like": re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|secret|password|private[_-]?key)\b\s*[:=]"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "private_key_block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "chatgpt_conversation_id": re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),
    "private_ipv4": re.compile(r"\b(?:10|127|192\.168|172\.(?:1[6-9]|2[0-9]|3[0-1]))\.[0-9]{1,3}\.[0-9]{1,3}(?:\.[0-9]{1,3})?\b"),
    "endpoint_url": re.compile(r"https?://[^\s)>\"]+"),
}


@dataclass
class ValidationResult:
    ok: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "issues": self.issues,
            "warnings": self.warnings,
            "details": self.details,
        }


def normalize_model_text(value: str) -> str:
    return re.sub(r"[^a-z0-9.]+", " ", (value or "").lower()).strip()


def model_is_allowed(model_self_report: str, allowed_models: tuple[str, ...] = ALLOWED_MODEL_MARKERS) -> bool:
    normalized = normalize_model_text(model_self_report)
    return bool(normalized) and any(normalize_model_text(item) in normalized for item in allowed_models)


def goal_command_is_valid(goal_command: str) -> bool:
    text = goal_command or ""
    return bool(re.search(r"(?m)^\s*/goal\b", text)) and "docs/goals/" in text


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_policy(policy: dict[str, Any]) -> ValidationResult:
    issues: list[str] = []
    warnings: list[str] = []
    forbidden = policy.get("forbidden_authorities") or {}
    for name in sorted(FORBIDDEN_TRUE_FLAGS):
        if bool(forbidden.get(name)):
            issues.append(f"forbidden_authority_enabled:{name}")

    if policy.get("formal_review_authority") != "fixed_chatgpt_web_github_exact_pushed_head":
        issues.append("formal_review_authority_must_remain_github_exact_head")
    if policy.get("mcp_role") != "read_only_auxiliary_context_only":
        issues.append("mcp_role_must_be_read_only_auxiliary")
    if policy.get("codex_role") != "sole_executor_after_validating_inbox":
        issues.append("codex_role_must_remain_sole_executor")

    conversation_id = str(policy.get("fixed_chatgpt_conversation_id") or "")
    if not conversation_id or conversation_id.startswith("<"):
        warnings.append("fixed_chatgpt_conversation_id_is_placeholder")
    if not policy.get("github_repository") or str(policy.get("github_repository")).startswith("<"):
        warnings.append("github_repository_is_placeholder")

    return ValidationResult(ok=not issues, issues=issues, warnings=warnings)


def validate_inbox_record(record: dict[str, Any], *, expected_commit: str | None = None) -> ValidationResult:
    issues: list[str] = []
    warnings: list[str] = []
    commit = expected_commit or str(record.get("expected_commit") or "")
    branch_head_seen = str(record.get("branch_head_seen") or "")
    commit_reviewed = str(record.get("commit_reviewed") or "")
    gate = str(record.get("gate_decision") or "").upper()
    files_read = record.get("files_read") or []
    goal = str(record.get("goal_command") or "")

    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        issues.append("expected_commit_invalid")
    if commit and branch_head_seen.lower() != commit.lower():
        issues.append("branch_head_seen_mismatch")
    if commit and commit_reviewed.lower() != commit.lower():
        issues.append("commit_reviewed_mismatch")
    if bool(record.get("model_allowed")) is not True:
        issues.append("model_allowed_not_true")
    if not model_is_allowed(str(record.get("model_self_report") or "")):
        issues.append("model_self_report_not_allowed")
    if bool(record.get("github_read_verified")) is not True:
        issues.append("github_read_verified_not_true")
    if bool(record.get("github_read_not_verified")) is True:
        issues.append("github_read_not_verified_true")
    if gate not in VALID_GATES:
        issues.append("gate_decision_invalid")
    if not isinstance(files_read, list) or not files_read:
        issues.append("files_read_missing")
    if not goal_command_is_valid(goal):
        issues.append("goal_command_invalid")

    recorded_goal_hash = str(record.get("goal_command_sha256") or "")
    if recorded_goal_hash and recorded_goal_hash != sha256_text(goal):
        issues.append("goal_command_hash_mismatch")
    if bool(record.get("consumed")):
        warnings.append("record_already_consumed")

    return ValidationResult(
        ok=not issues,
        issues=issues,
        warnings=warnings,
        details={
            "expected_commit": commit,
            "gate_decision": gate,
            "goal_command_sha256": sha256_text(goal) if goal else "",
        },
    )


def privacy_scan_text(text: str, *, allow_placeholder_urls: bool = True) -> ValidationResult:
    issues: list[str] = []
    warnings: list[str] = []
    for name, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(text):
            value = match.group(0)
            if name == "endpoint_url" and allow_placeholder_urls and (
                "example.com" in value or "<" in value or "github.com/<OWNER>/<REPO>" in value
            ):
                continue
            if name in {"endpoint_url", "chatgpt_conversation_id", "private_ipv4"}:
                warnings.append(f"{name}:{value[:80]}")
            else:
                issues.append(f"{name}:{value[:80]}")
    return ValidationResult(ok=not issues, issues=issues, warnings=warnings)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

