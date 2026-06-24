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
- request hash matches the rendered Web review request;
- source Web review artifact path and SHA-256 are recorded;
- review payload path and SHA-256 are recorded;
- fixed review session binding is recorded and is not merely the user's active
  tab;
- the item is not already consumed.

When `run-unit` is used with the default `require_review_provenance=true` and
`verify_review_provenance_files=true`, the runner also checks that the recorded
review artifact and payload files exist under safe relative paths and that their
SHA-256 hashes match the inbox record. This protects the Codex/Web loop from
stale output, local goal substitution, and fabricated inbox fields.
Reusable examples may use `examples/`; real project adapters typically use an
ignored `runtime/` artifact directory or a committed `research_context/web_reviews/`
record, depending on whether the artifact is only transport evidence or a
formal review record.

## Local Command Output

When the reusable runner executes a project-private `local_command` adapter, it
captures stdout/stderr as bytes and decodes them with UTF-8/UTF-8-SIG/GB18030
fallback before writing runtime log tails. This is intentional: browser/CDP
helpers often run across WSL, Windows Python, PowerShell, or other shells, and
their diagnostic output may not be valid UTF-8. A log-decoding mismatch must be
treated as a local transport compatibility issue, not as a Web, GitHub, model,
or prompt-delivery failure.

Project adapters should still keep stdout/stderr lightweight and free of
secrets. Runtime log tails are for local debugging and should remain under
ignored runtime artifact directories.

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

In a live project, the private adapter should still use the same JSON contract:
it submits the rendered request, monitors prompt delivery and generation,
captures the promoted Web review plus payload, writes `handoff_record.json` and
`inbox_record.json`, and lets the reusable runner validate them. The public
runner should not contain project conversation ids, browser profile details,
connector settings, endpoints, tokens, local paths, or remote host names.

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
  --required-file <PATH_FROM_REQUEST> \
  --require-provenance
```

The full deterministic path is:

```bash
python3 scripts/autoscience_cli.py run-unit <project-config.json>
```

The runner, not the adapter, decides whether a returned result is usable.
