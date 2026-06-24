#!/usr/bin/env python3
"""Example private-transport adapter for Autoscience.

This adapter does not contact ChatGPT Web. It copies static example handoff and
inbox records into the runtime artifact directory so the reusable runner can be
tested end to end. Real projects replace this script with a private CDP,
browser, or MCP adapter that writes the same two JSON files.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def main() -> int:
    artifact_dir = Path(os.environ["AUTOSCIENCE_ARTIFACT_DIR"])
    root = Path.cwd()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / "examples/valid_handoff_record.json", artifact_dir / "handoff_record.json")
    shutil.copyfile(root / "examples/valid_inbox_record.json", artifact_dir / "inbox_record.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
