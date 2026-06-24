from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autoscience.control_plane import (  # noqa: E402
    goal_command_is_valid,
    privacy_scan_text,
    sha256_text,
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
    consume_inbox_record,
    render_web_review_request,
    summarize_inbox_queue,
    summarize_workflow_health,
)


GOOD_COMMIT = "0123456789abcdef0123456789abcdef01234567"


def valid_record() -> dict:
    goal = "/goal Create and read docs/goals/example_next_goal.md after first running git fetch origin main."
    return {
        "expected_commit": GOOD_COMMIT,
        "branch_head_seen": GOOD_COMMIT,
        "commit_reviewed": GOOD_COMMIT,
        "model_self_report": "GPT-5.5 Thinking",
        "model_allowed": True,
        "github_read_verified": True,
        "github_read_not_verified": False,
        "gate_decision": "READY",
        "files_read": ["docs/control_plane_workflow.md"],
        "goal_command": goal,
        "goal_command_sha256": sha256_text(goal),
        "consumed": False,
    }


def valid_handoff() -> dict:
    return json.loads((ROOT / "examples/valid_handoff_record.json").read_text(encoding="utf-8"))


class ControlPlaneTest(unittest.TestCase):
    def test_valid_inbox_record(self) -> None:
        result = validate_inbox_record(valid_record())
        self.assertTrue(result.ok, result.to_dict())

    def test_valid_handoff_record(self) -> None:
        result = validate_handoff_record(valid_handoff())
        self.assertTrue(result.ok, result.to_dict())

    def test_rejects_mcp_as_formal_review_connector(self) -> None:
        record = valid_handoff()
        record["mcp_selected_as_formal_review_connector"] = True
        result = validate_handoff_record(record)
        self.assertFalse(result.ok)
        self.assertIn("mcp_selected_as_formal_review_connector", result.issues)

    def test_rejects_unsubmitted_web_prompt(self) -> None:
        record = valid_handoff()
        record["codex_to_web"]["prompt_delivery_verified"] = False
        record["codex_to_web"]["composer_state"] = "draft_contains_current_request_not_sent"
        result = validate_handoff_record(record)
        self.assertFalse(result.ok)
        self.assertIn("prompt_delivery_not_verified", result.issues)
        self.assertIn("composer_state_not_safe_after_submit:draft_contains_current_request_not_sent", result.issues)

    def test_rejects_stale_web_response(self) -> None:
        record = valid_handoff()
        record["web_to_codex"]["response_after_latest_request"] = False
        record["web_to_codex"]["stale_or_prior_commit_output"] = True
        result = validate_handoff_record(record)
        self.assertFalse(result.ok)
        self.assertIn("web_response_not_bound_to_latest_request", result.issues)
        self.assertIn("stale_or_prior_commit_output", result.issues)

    def test_rejects_commit_mismatch(self) -> None:
        record = valid_record()
        record["commit_reviewed"] = "f" * 40
        result = validate_inbox_record(record)
        self.assertFalse(result.ok)
        self.assertIn("commit_reviewed_mismatch", result.issues)

    def test_rejects_goal_substitution_hash(self) -> None:
        record = valid_record()
        record["goal_command"] = "/goal Create and read docs/goals/evil.md after first running git fetch origin main."
        result = validate_inbox_record(record)
        self.assertFalse(result.ok)
        self.assertIn("goal_command_hash_mismatch", result.issues)

    def test_policy_forbidden_authority(self) -> None:
        policy = json.loads((ROOT / "configs/control_plane_policy.example.json").read_text(encoding="utf-8"))
        self.assertTrue(validate_policy(policy).ok)
        policy["forbidden_authorities"]["allow_bash"] = True
        result = validate_policy(policy)
        self.assertFalse(result.ok)
        self.assertIn("forbidden_authority_enabled:allow_bash", result.issues)

    def test_scientific_policy_is_fail_closed(self) -> None:
        policy = json.loads((ROOT / "configs/scientific_policy.example.json").read_text(encoding="utf-8"))
        self.assertTrue(validate_scientific_policy(policy).ok)
        policy["authorization_flags"]["training_authorized"] = True
        result = validate_scientific_policy(policy)
        self.assertFalse(result.ok)
        self.assertIn("scientific_authorization_enabled_by_default:training_authorized", result.issues)

    def test_example_scientific_csv_schemas(self) -> None:
        self.assertTrue(validate_csv_headers(ROOT / "examples/stage_state_registry.example.csv", STAGE_REGISTRY_HEADERS).ok)
        self.assertTrue(validate_csv_headers(ROOT / "examples/dataset_role_matrix.example.csv", DATASET_ROLE_HEADERS).ok)
        self.assertTrue(validate_csv_headers(ROOT / "examples/label_authorization_matrix.example.csv", LABEL_AUTHORIZATION_HEADERS).ok)
        self.assertTrue(
            validate_csv_headers(
                ROOT / "examples/execution_authorization_registry.example.csv",
                EXECUTION_AUTHORIZATION_HEADERS,
            ).ok
        )

    def test_goal_command_shape(self) -> None:
        self.assertTrue(goal_command_is_valid("/goal Create and read docs/goals/x.md"))
        self.assertFalse(goal_command_is_valid("continue with next step"))

    def test_privacy_scan_blocks_secret_like_text(self) -> None:
        result = privacy_scan_text("api" + "_key=abc123")
        self.assertFalse(result.ok)
        self.assertTrue(result.issues)

    def test_cli_privacy_scan_strict(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/autoscience_cli.py", "privacy-scan", "--strict", "."],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_validate_handoff(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/autoscience_cli.py", "validate-handoff", "examples/valid_handoff_record.json"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_validate_scientific_policy(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/autoscience_cli.py", "validate-scientific-policy", "configs/scientific_policy.example.json"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_render_web_review_request(self) -> None:
        template = (ROOT / "templates/web_review_request.md").read_text(encoding="utf-8")
        request = render_web_review_request(
            template,
            repository="OWNER/REPO",
            branch="main",
            expected_commit=GOOD_COMMIT,
            codex_execution_conclusion="CODEX_EXECUTION_CONCLUSION: example",
            required_files=["docs/control_plane_workflow.md", "docs/security_model.md"],
        )
        self.assertIn(GOOD_COMMIT, request.text)
        self.assertIn("- docs/control_plane_workflow.md", request.text)
        self.assertIn("github_exact_pushed_head", request.payload["formal_material_source"])

    def test_workflow_health_summary(self) -> None:
        result = summarize_workflow_health(
            policy=json.loads((ROOT / "configs/control_plane_policy.example.json").read_text(encoding="utf-8")),
            scientific_policy=json.loads((ROOT / "configs/scientific_policy.example.json").read_text(encoding="utf-8")),
            handoff_record=valid_handoff(),
            inbox_record=valid_record(),
            expected_commit=GOOD_COMMIT,
        )
        self.assertTrue(result.ok, result.to_dict())

    def test_cli_make_review_request_and_enqueue_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request_path = Path(tmp) / "request.md"
            payload_path = Path(tmp) / "payload.json"
            queue_dir = Path(tmp) / "queue"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/autoscience_cli.py",
                    "make-review-request",
                    "--repository",
                    "OWNER/REPO",
                    "--branch",
                    "main",
                    "--expected-commit",
                    GOOD_COMMIT,
                    "--conclusion-file",
                    "examples/codex_execution_conclusion.example.md",
                    "--required-file",
                    "docs/control_plane_workflow.md",
                    "--required-file",
                    "docs/security_model.md",
                    "--output",
                    str(request_path),
                    "--payload-output",
                    str(payload_path),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(GOOD_COMMIT, request_path.read_text(encoding="utf-8"))
            self.assertTrue(payload_path.exists())

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/autoscience_cli.py",
                    "enqueue-inbox",
                    "examples/valid_inbox_record.json",
                    "--queue-dir",
                    str(queue_dir),
                    "--expected-commit",
                    GOOD_COMMIT,
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(len(list(queue_dir.glob("*.json"))), 1)

    def test_inbox_status_and_consume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue_dir = Path(tmp) / "queue"
            queue_dir.mkdir()
            record_path = queue_dir / "record.json"
            record_path.write_text(json.dumps(valid_record(), indent=2), encoding="utf-8")

            status = summarize_inbox_queue(queue_dir, expected_commit=GOOD_COMMIT)
            self.assertTrue(status.ok, status.to_dict())
            self.assertEqual(status.details["record_count"], 1)

            consumed = consume_inbox_record(record_path, expected_commit=GOOD_COMMIT)
            self.assertTrue(consumed.ok, consumed.to_dict())

            duplicate = consume_inbox_record(record_path, expected_commit=GOOD_COMMIT)
            self.assertFalse(duplicate.ok)
            self.assertIn("inbox_record_already_consumed", duplicate.issues)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
