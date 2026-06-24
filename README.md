# Autoscience

Reusable control-plane template for automated research workflows.

The project standardizes a safe handoff loop. In plain language:

- GitHub is the formal evidence cabinet.
- ChatGPT Web is the independent reviewer.
- The bridge/MCP layer is the courier and monitor between Codex and Web.
- Codex, or another local executor, is the only component that executes the
  next command after validating the returned review.

## Core Loop

1. Codex or another executor performs one bounded work unit.
2. The executor commits lightweight evidence to GitHub.
3. The bridge submits the Codex conclusion, exact commit, and review request to
   the fixed ChatGPT Web session.
4. ChatGPT Web reviews the exact pushed commit through GitHub.
5. The bridge monitors prompt delivery, generation state, and the latest Web
   answer after the current request.
6. The bridge stages Web's structured decision and next `/goal` in a controlled
   local inbox.
7. Codex validates that inbox entry before doing anything else.

Autoscience is intentionally conservative. It does not grant ChatGPT Web or MCP
generic repository write access, shell access, training access, dataset access,
checkpoint access, or remote compute access. If ChatGPT Web offers GitHub and an
MCP app as mutually exclusive choices during formal review, choose GitHub.
MCP/bridge automation remains useful as the submit-monitor-return layer; it is
not the formal evidence source.

## What This Template Includes

- `autoscience/control_plane.py`: dependency-free validation helpers.
- `scripts/autoscience_cli.py`: policy, handoff, inbox, and privacy validation.
- `configs/control_plane_policy.example.json`: fail-closed policy template.
- `configs/scientific_policy.example.json`: fail-closed scientific authorization
  template.
- `skills/automated-research-workflow/SKILL.md`: reusable Codex skill.
- `docs/`: control-plane workflow, security model, and session policy.
- `docs/transport_adapter_contract.md`: contract for project-private transport
  adapters.
- `templates/web_review_request.md`: sanitized fixed-Web review request template.
- `examples/`: handoff, inbox, review-provenance, stage, dataset, label, and
  authorization records.
- `tests/`: unit tests for validators and privacy scanner.

## Safety Defaults

- No long-lived public endpoint, tunnel, URL, token, or secret.
- No generic write/edit/apply-patch/bash/shell/terminal tool exposure.
- No raw data, checkpoint, run directory, secret, remote GPU, training,
  inference, evaluation, parser, target, split, or view authority.
- GitHub exact pushed HEAD remains the formal review source.
- Codex or the local executor remains the only executor.
- The controlled inbox is not trusted unless review artifact, payload metadata,
  commit, model, GitHub evidence, files read, goal text, goal hash, and replay
  checks all pass.

## Quick Check

```bash
python3 scripts/autoscience_cli.py privacy-scan .
python3 scripts/autoscience_cli.py validate-policy configs/control_plane_policy.example.json
python3 scripts/autoscience_cli.py validate-scientific-policy configs/scientific_policy.example.json
python3 scripts/autoscience_cli.py validate-handoff examples/valid_handoff_record.json --expected-commit 0123456789abcdef0123456789abcdef01234567 --request-sha256 c0da5a2c41a965771b951fe4e4e4a505825cf1efb8d1afb3e93e6e70afe1d6b0 --require-provenance
python3 scripts/autoscience_cli.py validate-inbox examples/valid_inbox_record.json --expected-commit 0123456789abcdef0123456789abcdef01234567 --request-sha256 c0da5a2c41a965771b951fe4e4e4a505825cf1efb8d1afb3e93e6e70afe1d6b0 --require-provenance
python3 scripts/autoscience_cli.py validate-csv-schema stage-state examples/stage_state_registry.example.csv
python3 scripts/autoscience_cli.py validate-csv-schema dataset-role examples/dataset_role_matrix.example.csv
python3 scripts/autoscience_cli.py validate-csv-schema label-authorization examples/label_authorization_matrix.example.csv
python3 scripts/autoscience_cli.py validate-csv-schema execution-authorization examples/execution_authorization_registry.example.csv
python3 scripts/autoscience_cli.py workflow-health --policy configs/control_plane_policy.example.json --scientific-policy configs/scientific_policy.example.json --handoff examples/valid_handoff_record.json --inbox examples/valid_inbox_record.json --expected-commit 0123456789abcdef0123456789abcdef01234567 --request-sha256 c0da5a2c41a965771b951fe4e4e4a505825cf1efb8d1afb3e93e6e70afe1d6b0 --require-provenance
python3 scripts/autoscience_cli.py run-unit configs/automation_unit.example.json
python3 scripts/autoscience_cli.py run-unit configs/automation_unit.local_command.example.json
python3 -m unittest discover -s tests
```

`run-unit` is the reusable automation unit runner. It renders the Web review
request, validates fail-closed control/scientific policy, reads the transport
handoff and inbox records, validates required-file coverage, request binding,
review artifact provenance, payload provenance, fixed-session binding, goal
hashing, enqueues the next goal, and writes a unit report under `runtime/`.
By default `require_review_provenance=true` and
`verify_review_provenance_files=true`, so an inbox record without the Web review
artifact hash and payload hash is rejected.
For `local_command` transports, the runner captures adapter stdout/stderr as
bytes, decodes them with UTF-8/UTF-8-SIG/GB18030 fallback, and stores log tails
under the runtime artifact directory. A project adapter's platform-specific
output encoding must not break an otherwise valid Web review handoff.

The public template supports:

- `static_files`: read prewritten handoff/inbox JSON records.
- `local_command`: run a local private adapter without shell expansion only
  when `allow_local_transport_command=true`.

A real project can add a private CDP, browser, or MCP adapter that writes the
same handoff and inbox JSON files. The adapter transports messages; the runner
decides whether the result is usable. Do not commit real session ids, endpoints,
tokens, transcripts, or private host details to this template.

See `docs/transport_adapter_contract.md` before writing a project adapter. In
short: GitHub remains the formal evidence source; the adapter only submits,
monitors, and returns the Web review decision.
For a plain-language split between GitHub and MCP/bridge responsibilities, read
`docs/github_mcp_role_split.md`.

In practical use, the user can keep watching one Codex CLI window and one fixed
ChatGPT Web review conversation. Codex still commits evidence to GitHub; the
private adapter only reduces manual copy/paste and blind waiting by moving the
Codex conclusion to Web and bringing the verified review result back to Codex.

Before any workflow declares a goal complete, perform a requirement-by-
requirement completion audit against current evidence. A green control-plane
unit proves instruction handoff; it does not prove training authorization,
model acceptance, dataset readiness, or scientific stage acceptance.

## Project-Specific Setup

Copy this template into a real research repository and replace the placeholders
in `configs/control_plane_policy.example.json` and
`templates/web_review_request.md`.

Do not commit actual ChatGPT conversation ids, connector tokens, tunnel URLs,
raw datasets, checkpoints, run outputs, private hostnames, private IP
addresses, or account-specific paths to a reusable public template.
