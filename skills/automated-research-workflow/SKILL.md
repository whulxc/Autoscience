---
name: automated-research-workflow
description: Use for reusable automated research control-plane work: Codex or executor units, GitHub exact-HEAD evidence, fixed ChatGPT Web review, MCP/bridge submit-monitor-return handoff, controlled inbox goal validation, workflow health, and separating control-plane readiness from scientific training authorization.
---

# Automated Research Workflow

Use this skill when coordinating automated research work that must be reviewed
through a fixed Web model and GitHub exact pushed commits.

Human-readable role split:

- GitHub is the formal evidence source.
- ChatGPT Web is the reviewer.
- MCP/bridge automation submits the Codex conclusion to Web, monitors Web
  delivery/generation, and returns Web's structured result.
- Codex is the only executor after validating the returned inbox record.

## Core Loop

1. Execute one bounded unit.
2. Commit and push lightweight evidence.
3. Use the bridge to submit the Codex conclusion, expected commit, required
   files, and gate question to the fixed Web review session.
4. Ask the fixed Web review session to self-report its model.
5. Require GitHub verification of the exact pushed commit.
6. Poll for prompt delivery, composer state, generation state, and the latest
   assistant response after the current request.
7. Promote only a review with matching branch head, matching reviewed commit,
   full required-file coverage, accepted Codex conclusion, valid gate, Markdown
   explanation, and next `/goal`.
8. Queue the next goal in a controlled inbox.
9. Validate inbox provenance before execution.

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

Before claiming training, model acceptance, stage acceptance, data readiness, or
evaluation authority, require project-specific registries:

- stage state registry;
- dataset role matrix;
- label authorization matrix;
- execution authorization registry.

Run `validate-scientific-policy` and the relevant `validate-csv-schema` checks.
Reusable templates must keep all scientific authorization flags false by
default. A Web/MCP/control-plane `READY` does not grant training, remote jobs,
parser/target/view/split construction, checkpoint I/O, final-test reopening, or
evaluation-only label use for model selection.

## MCP/Bridge Policy

MCP/bridge automation is the submit-monitor-return layer between Codex and
ChatGPT Web. It is not the formal evidence source and not an executor.

For formal review, GitHub exact pushed HEAD remains authoritative. If ChatGPT
Web forces a choice between GitHub and an MCP app, choose GitHub for formal
review. Use MCP/bridge automation outside that Web-side evidence path to:

- stage or submit the review prompt;
- verify the latest user turn contains the expected commit and Codex conclusion;
- monitor composer/input state and generation state;
- capture the latest assistant response after the current request;
- stage a controlled inbox entry containing only the review decision and next
  `/goal`.

Never expose generic write, edit, apply-patch, bash, shell, terminal, raw data,
checkpoint, remote GPU, training, inference, evaluation, parser, target, split,
or view capabilities through MCP.

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

Run `python3 scripts/autoscience_cli.py validate-handoff <record.json>` before
trusting a bridge return. This check is separate from
`validate-inbox`: handoff validation proves that the prompt was delivered and
the Web answer belongs to the latest request; inbox validation proves the
returned goal is safe to execute.

Use the reusable CLI sequence:

```bash
python3 scripts/autoscience_cli.py run-unit configs/automation_unit.example.json
```

Use `run-unit` for the full deterministic unit when a project has already
produced transport handoff/inbox JSON, or when a private local adapter is
allowed to produce those records. It renders the review request, validates
policies, validates request hash, required-file coverage, handoff/inbox,
enqueues the next goal, and writes a unit report. Public templates should use
`static_files`; project-private adapters may use `local_command` with no shell
expansion and explicit `allow_local_transport_command=true`. For lower-level
debugging, run the component commands:

```bash
python3 scripts/autoscience_cli.py make-review-request ...
python3 scripts/autoscience_cli.py validate-handoff <handoff.json>
python3 scripts/autoscience_cli.py validate-inbox <inbox.json>
python3 scripts/autoscience_cli.py enqueue-inbox <inbox.json> --queue-dir <queue>
python3 scripts/autoscience_cli.py inbox-status --queue-dir <queue>
python3 scripts/autoscience_cli.py consume-inbox <queued-record.json>
python3 scripts/autoscience_cli.py workflow-health ...
```

Project-specific CDP, browser, or MCP adapters should call into this sequence
instead of bypassing it. The adapter may transport the prompt and capture the
response; the validator decides whether the returned result is usable.

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
