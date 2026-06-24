"""Dependency-free validators for automated research control planes."""

from __future__ import annotations

import hashlib
import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ALLOWED_MODEL_MARKERS = ("gpt 5.5 pro", "thinking")
VALID_GATES = {"READY", "BLOCKED", "R2_IMPLEMENTED_STOP"}
FORMAL_REVIEW_AUTHORITY = "fixed_chatgpt_web_github_exact_pushed_head"
BRIDGE_ROLE = "codex_web_handoff_trigger_monitor_return"
FORMAL_MATERIAL_SOURCE = "github_exact_pushed_head"
CODEX_ROLE = "sole_executor_after_validating_inbox"
MCP_ROLE = "handoff_monitor_return_only_not_formal_evidence"
ALLOWED_COMPOSER_STATES = {
    "empty_after_submit_or_idle",
    "submitted_and_cleared",
    "not_applicable_verified_transcript",
}
ALLOWED_GENERATION_STATES = {"complete", "stopped", "ready_for_review_capture"}
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
SCIENTIFIC_AUTHORIZATION_FLAGS = {
    "control_plane_ready_grants_scientific_authorization",
    "training_authorized",
    "remote_job_allowed",
    "parser_converter_authorized",
    "target_construction_authorized",
    "timestamp_join_authorized",
    "view_or_split_construction_authorized",
    "training_config_authorized",
    "inference_or_evaluation_authorized",
    "checkpoint_io_authorized",
    "final_once_reopening_authorized",
    "new_trained_model_acceptance_authorized",
    "stage_reactivation_authorized",
    "next_stage_start_authorized",
    "eval_only_label_selection_use_authorized",
}
REQUIRED_SCIENTIFIC_REGISTRIES = {
    "stage_state_registry",
    "dataset_role_matrix",
    "label_authorization_matrix",
    "execution_authorization_registry",
}
STAGE_REGISTRY_HEADERS = {
    "stage",
    "trained_model_accepted",
    "stage_outcome_accepted",
    "blocked_or_manual_required",
    "training_authorized",
    "next_action",
}
DATASET_ROLE_HEADERS = {
    "dataset",
    "raw_present",
    "parser_covered",
    "view_or_unified_ready",
    "split_ready",
    "train_allowed",
    "eval_only",
    "manual_required",
    "parser_status",
}
LABEL_AUTHORIZATION_HEADERS = {
    "label_source",
    "timestamp_basis",
    "coordinate_frame",
    "train_allowed",
    "eval_only",
    "forbidden_use_now",
    "provenance_status",
}
EXECUTION_AUTHORIZATION_HEADERS = {
    "authorization",
    "allowed",
    "scope",
    "evidence",
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

    if policy.get("formal_review_authority") != FORMAL_REVIEW_AUTHORITY:
        issues.append("formal_review_authority_must_remain_github_exact_head")
    if policy.get("mcp_role") not in {MCP_ROLE, "read_only_auxiliary_context_only"}:
        issues.append("mcp_role_must_be_handoff_monitor_return_or_read_only_auxiliary")
    if policy.get("codex_role") != CODEX_ROLE:
        issues.append("codex_role_must_remain_sole_executor")
    if policy.get("bridge_role") != BRIDGE_ROLE:
        issues.append("bridge_role_must_be_handoff_trigger_monitor_return")
    if policy.get("formal_material_source") != FORMAL_MATERIAL_SOURCE:
        issues.append("formal_material_source_must_be_github_exact_head")
    if bool(policy.get("mcp_can_replace_github_review")):
        issues.append("mcp_must_not_replace_github_review")

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


def validate_handoff_record(record: dict[str, Any], *, expected_commit: str | None = None) -> ValidationResult:
    """Validate one Codex -> Web -> Codex handoff lifecycle.

    The handoff bridge is allowed to trigger a fixed Web review, monitor Web
    delivery/generation state, and bring back a structured result. It is not the
    formal material source. GitHub exact pushed HEAD remains the evidence source,
    and Codex remains the only executor after validating the inbox item.
    """

    issues: list[str] = []
    warnings: list[str] = []
    commit = expected_commit or str(record.get("expected_commit") or "")
    bridge_role = str(record.get("bridge_role") or "")
    material_source = str(record.get("formal_material_source") or "")
    review_authority = str(record.get("formal_review_authority") or "")
    mcp_role = str(record.get("mcp_role") or "")
    codex_role = str(record.get("codex_role") or "")

    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        issues.append("expected_commit_invalid")
    if bridge_role != BRIDGE_ROLE:
        issues.append("bridge_role_invalid")
    if material_source != FORMAL_MATERIAL_SOURCE:
        issues.append("formal_material_source_invalid")
    if review_authority != FORMAL_REVIEW_AUTHORITY:
        issues.append("formal_review_authority_invalid")
    if mcp_role != MCP_ROLE:
        issues.append("mcp_role_invalid")
    if codex_role != CODEX_ROLE:
        issues.append("codex_role_invalid")
    if bool(record.get("mcp_selected_as_formal_review_connector")):
        issues.append("mcp_selected_as_formal_review_connector")

    codex_to_web = record.get("codex_to_web") or {}
    if bool(codex_to_web.get("submission_requested")) is not True:
        issues.append("codex_to_web_submission_not_requested")
    if bool(codex_to_web.get("prompt_delivery_verified")) is not True:
        issues.append("prompt_delivery_not_verified")
    if bool(codex_to_web.get("latest_user_turn_contains_commit")) is not True:
        issues.append("latest_user_turn_missing_commit")
    if bool(codex_to_web.get("latest_user_turn_contains_codex_conclusion")) is not True:
        issues.append("latest_user_turn_missing_codex_conclusion")
    composer_state = str(codex_to_web.get("composer_state") or "")
    if composer_state not in ALLOWED_COMPOSER_STATES:
        issues.append(f"composer_state_not_safe_after_submit:{composer_state or 'missing'}")

    web_to_codex = record.get("web_to_codex") or {}
    if bool(web_to_codex.get("response_after_latest_request")) is not True:
        issues.append("web_response_not_bound_to_latest_request")
    generation_state = str(web_to_codex.get("generation_state") or "")
    if generation_state not in ALLOWED_GENERATION_STATES:
        issues.append(f"generation_state_not_complete:{generation_state or 'missing'}")
    if bool(web_to_codex.get("structured_review_blocks_present")) is not True:
        issues.append("structured_review_blocks_missing")
    if bool(web_to_codex.get("stale_or_prior_commit_output")):
        issues.append("stale_or_prior_commit_output")
    review_artifact_path = str(web_to_codex.get("review_artifact_path") or "")
    if review_artifact_path and not review_artifact_path.startswith("research_context/web_reviews/"):
        warnings.append("review_artifact_path_is_not_standard_web_reviews_path")

    inbox_record = record.get("inbox_record")
    if not isinstance(inbox_record, dict):
        issues.append("inbox_record_missing")
    else:
        inbox_result = validate_inbox_record(inbox_record, expected_commit=commit)
        issues.extend(f"inbox:{item}" for item in inbox_result.issues)
        warnings.extend(f"inbox:{item}" for item in inbox_result.warnings)

    return ValidationResult(
        ok=not issues,
        issues=issues,
        warnings=warnings,
        details={
            "expected_commit": commit,
            "bridge_role": bridge_role,
            "formal_material_source": material_source,
        },
    )


def validate_scientific_policy(policy: dict[str, Any]) -> ValidationResult:
    """Validate fail-closed scientific authorization defaults.

    This does not decide whether a real project may train. It proves the
    reusable template keeps control-plane readiness separate from scientific
    readiness unless a project-specific reviewed policy explicitly changes it.
    """

    issues: list[str] = []
    warnings: list[str] = []
    flags = policy.get("authorization_flags") or {}
    for name in sorted(SCIENTIFIC_AUTHORIZATION_FLAGS):
        if bool(flags.get(name)):
            issues.append(f"scientific_authorization_enabled_by_default:{name}")

    registries = set(policy.get("required_registries") or [])
    missing = sorted(REQUIRED_SCIENTIFIC_REGISTRIES - registries)
    if missing:
        issues.append("missing_required_scientific_registries:" + ",".join(missing))

    if bool(policy.get("gate_scope_required")) is not True:
        issues.append("gate_scope_required_must_be_true")
    if bool(policy.get("plain_language_status_required")) is not True:
        issues.append("plain_language_status_required_must_be_true")

    return ValidationResult(ok=not issues, issues=issues, warnings=warnings)


def validate_csv_headers(path: Path, required_headers: set[str]) -> ValidationResult:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            headers = next(reader, [])
    except FileNotFoundError:
        return ValidationResult(ok=False, issues=[f"csv_missing:{path}"])

    present = {item.strip() for item in headers}
    missing = sorted(required_headers - present)
    return ValidationResult(
        ok=not missing,
        issues=[f"csv_missing_headers:{','.join(missing)}"] if missing else [],
        details={"headers": headers},
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
