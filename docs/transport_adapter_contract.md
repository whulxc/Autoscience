# Transport Adapter Contract

This contract defines what a project-private adapter may do for the reusable
Autoscience runner.

## Plain-Language Split

- GitHub stores the formal review materials.
- ChatGPT Web reviews the exact pushed GitHub commit.
- The transport adapter carries the Codex conclusion to Web, monitors whether
  Web actually reviewed the current request, and returns Web's structured
  decision to a controlled inbox.
- Codex or the local executor validates the inbox before executing anything.

The adapter is useful because it reduces manual copy/paste, detects prompt
delivery failures, detects stale Web output, and stages the next goal in a
machine-checkable form. It is not useful as a replacement for GitHub evidence.
If ChatGPT Web forces a choice between GitHub and a project MCP app, use GitHub
for formal review.

## Required Inputs

A project adapter should consume only the lightweight request artifacts rendered
by `run-unit`:

- `AUTOSCIENCE_REVIEW_REQUEST`: Markdown prompt sent to Web.
- `AUTOSCIENCE_REVIEW_PAYLOAD`: JSON payload containing expected commit,
  required files, request hash, repository, and branch.
- `AUTOSCIENCE_EXPECTED_COMMIT`: full 40-hex commit.
- `AUTOSCIENCE_ARTIFACT_DIR`: directory where the adapter writes JSON results.

Adapters must not require raw datasets, checkpoints, run directories, secrets,
browser credentials, private keys, or remote compute credentials.

## Required Outputs

The adapter must write these files into `AUTOSCIENCE_ARTIFACT_DIR`:

- `handoff_record.json`: lifecycle proof for the current request.
- `inbox_record.json`: the returned review decision and next `/goal`.

Optional project-specific files are allowed, such as a boundary audit or a
human-readable summary, as long as they are lightweight and contain no secrets.

`handoff_record.json` must prove:

- bridge role is `codex_web_handoff_trigger_monitor_return`;
- formal material source is `github_exact_pushed_head`;
- formal review authority is fixed ChatGPT Web plus GitHub exact pushed HEAD;
- MCP is not selected as the formal review connector;
- expected commit and required files match the request payload;
- prompt delivery is verified for the latest user turn;
- composer state is safe after submission;
- Web response is after the latest current request;
- structured review blocks are present;
- stale or prior-commit output was not promoted;
- the embedded inbox record validates.

`inbox_record.json` must prove:

- expected commit is a 40-hex SHA;
- branch head equals expected commit;
- reviewed commit equals expected commit;
- Web model is allowed;
- GitHub read is verified;
- all required files were read;
- gate decision is valid;
- next goal starts with `/goal` and references `docs/goals/`;
- goal text hash matches;
- the item is not already consumed.

## Adapter Modes

Recommended modes:

- `dry-run`: produce synthetic records only for shape and policy validation.
  This proves the project can speak the Autoscience schema; it is not a Web
  review gate.
- `from-review`: parse already promoted Web review artifacts and payloads into
  handoff/inbox records.
- `live`: call a project-owned browser/CDP/MCP transport after a separate
  project-specific current-HEAD review authorizes that exact operation.

Reusable public templates should implement `dry-run` or static examples only.
Live transport belongs in the private project repository.

## Forbidden Capabilities

Adapters must not expose or perform:

- generic write, edit, apply-patch, bash, shell, or terminal tools;
- raw dataset reads;
- checkpoint load/write;
- run-directory reads/writes;
- secret or browser-profile reads;
- remote GPU or remote training jobs;
- training, inference, or evaluation;
- parser, target, split, or view construction;
- long-lived public endpoints, tunnels, tokens, or connector URLs.

If a project later needs any of these capabilities, it must add a separate
project-specific reviewed goal and a narrower policy. Control-plane readiness
never grants scientific authorization.

## Validation Sequence

Run the reusable validator after the adapter writes its outputs:

```bash
python3 scripts/autoscience_cli.py workflow-health \
  --policy configs/control_plane_policy.example.json \
  --scientific-policy configs/scientific_policy.example.json \
  --handoff <artifact_dir>/handoff_record.json \
  --inbox <artifact_dir>/inbox_record.json \
  --expected-commit <40_HEX_COMMIT> \
  --request-sha256 <REQUEST_SHA256> \
  --required-file <PATH_FROM_REQUEST>
```

The full deterministic path is:

```bash
python3 scripts/autoscience_cli.py run-unit <project-config.json>
```

The runner, not the adapter, decides whether a returned result is usable.
