from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autoscience.control_plane import (  # noqa: E402
    goal_command_is_valid,
    privacy_scan_text,
    sha256_text,
    validate_inbox_record,
    validate_policy,
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


class ControlPlaneTest(unittest.TestCase):
    def test_valid_inbox_record(self) -> None:
        result = validate_inbox_record(valid_record())
        self.assertTrue(result.ok, result.to_dict())

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


if __name__ == "__main__":
    raise SystemExit(unittest.main())
