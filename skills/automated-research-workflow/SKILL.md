---
name: automated-research-workflow
description: Use for reusable automated research control-plane work: Codex or executor units, GitHub exact-HEAD handoff, fixed ChatGPT Web review, safe MCP read-only context, controlled inbox goal validation, workflow health, and separating control-plane readiness from scientific training authorization.
---

# Automated Research Workflow

Use this skill when coordinating automated research work that must be reviewed
through a fixed Web model and GitHub exact pushed commits.

## Core Loop

1. Execute one bounded unit.
2. Commit and push lightweight evidence.
3. Ask the fixed Web review session to self-report its model.
4. Require GitHub verification of the exact pushed commit.
5. Promote only a review with matching branch head, matching reviewed commit,
   full required-file coverage, accepted Codex conclusion, valid gate, Markdown
   explanation, and next `/goal`.
6. Queue the next goal in a controlled inbox.
7. Validate inbox provenance before execution.

## Required Roles

- Workflow Guardian: control-plane safety, GitHub, Web, MCP, prompt delivery,
  commit equality, model policy, inbox provenance.
- Research Engineer: scientific stage logic, data readiness, labels, splits,
  baselines, training authorization, result validity.
- Master Controller: commit/push, Web packet, inbox validation, summary, and
  final decision.

Keep these states separate:

- control-plane readiness;
- scientific route readiness;
- training authorization;
- model or stage acceptance.

## MCP Policy

MCP is read-only auxiliary context only. Never expose generic write, edit,
apply-patch, bash, shell, terminal, raw data, checkpoint, remote GPU, training,
inference, evaluation, parser, target, split, or view capabilities through MCP.

Do not start long-running servers, public tunnels, connector registration, or
persisted endpoint/token material unless a project-specific current-HEAD Web
review explicitly authorizes that exact proof.

## Controlled Inbox Policy

The controlled inbox is not a general write bridge. It may contain only a
verified review decision and next `/goal`.

Codex must verify:

- expected commit format;
- branch head equals expected commit;
- reviewed commit equals expected commit;
- allowed model;
- GitHub read verified;
- required files present;
- valid gate;
- `/goal` references `docs/goals/`;
- goal text hash matches;
- review artifact and payload metadata are bound to the fixed session;
- item is not stale, substituted, duplicated, or already consumed.

## Web Session Policy

Use a fixed Web review session for a workflow track. For formal scientific
review after long bridge/debug work, prefer a fresh research-review session
bootstrapped from GitHub evidence. The old control-plane session remains
historical evidence; the new research session must not rely on remembered
context.

## Stop Conditions

Stop when:

- model is not allowed;
- GitHub cannot verify the exact commit and files;
- prompt delivery is unproven;
- output is stale or for another commit;
- required files are missing;
- connector recovery needs login, passkey, two-factor, payment, admin, or
  security confirmation;
- a goal would grant write, bash, data, checkpoint, remote GPU, training, or
  scientific-stage authority without a separate explicit review.

