# Automated Research Control-Plane Workflow

This template separates instruction handoff from scientific authorization.

## Roles

- Master Controller: coordinates one bounded work unit, commits evidence, and
  reports the decision in plain language.
- Workflow Guardian: verifies Codex, GitHub, fixed Web review, MCP policy,
  prompt delivery, model policy, commit equality, and controlled inbox safety.
- Research Engineer: verifies scientific stage state, dataset readiness, label
  provenance, split hygiene, baseline retention, and whether training is
  authorized.
- Fixed Web Review: independently reviews the exact pushed GitHub commit.
- MCP: provides optional read-only context only.
- Controlled Inbox: stores a verified review decision and next `/goal`; it is
  not an executor.

## One Unit

1. Read the current goal and current state.
2. Do one bounded work unit.
3. Write only lightweight evidence.
4. Run local safety checks.
5. Commit and push to GitHub.
6. Submit a fixed Web review request for the exact pushed commit.
7. Require model, GitHub, Codex-conclusion, required-file, gate, Markdown, and
   next-goal blocks.
8. Promote only if branch head and reviewed commit match the pushed commit.
9. Queue the next goal in the controlled inbox.
10. Codex validates the inbox item before executing anything.

## Required Stop

If a unit only proves control-plane readiness, stop there. Do not convert
control-plane readiness into training, data access, or stage acceptance.

