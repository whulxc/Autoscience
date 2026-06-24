# Automated Research Control-Plane Workflow

This template separates instruction handoff from scientific authorization.

## Plain-Language Contract

- GitHub stores the formal evidence.
- ChatGPT Web reviews the exact pushed GitHub commit.
- The bridge/MCP layer carries messages, watches Web state, and brings the
  structured answer back.
- Codex validates the returned answer before executing the next `/goal`.

Do not use MCP as a second evidence source when GitHub already contains the
review materials. MCP is valuable because it removes manual copy/paste,
prevents blind waiting, detects Web delivery failures, and returns a structured
result to Codex.

## Roles

- Master Controller: coordinates one bounded work unit, commits evidence, and
  reports the decision in plain language.
- Workflow Guardian: verifies Codex, GitHub, fixed Web review, MCP policy,
  prompt delivery, model policy, commit equality, and controlled inbox safety.
- Research Engineer: verifies scientific stage state, dataset readiness, label
  provenance, split hygiene, baseline retention, and whether training is
  authorized.
- Fixed Web Review: independently reviews the exact pushed GitHub commit.
- Bridge/MCP: submits the review request to Web, monitors prompt delivery and
  generation state, captures the latest response after the current request, and
  stages only a verified review decision plus next `/goal`.
- Controlled Inbox: stores a verified review decision and next `/goal`; it is
  not an executor.

## One Unit

1. Read the current goal and current state.
2. Do one bounded work unit.
3. Write only lightweight evidence.
4. Run local safety checks.
5. Commit and push to GitHub.
6. Use the bridge to submit a fixed Web review request for the exact pushed
   commit.
7. On every poll, verify prompt delivery, composer state, generation state, and
   that the answer being read is after the latest current request.
8. Require model, GitHub, Codex-conclusion, required-file, gate, Markdown, and
   next-goal blocks.
9. Promote only if branch head and reviewed commit match the pushed commit.
10. Queue the next goal in the controlled inbox.
11. Codex validates the inbox item before executing anything.

## Handoff Validation

Run:

```bash
python3 scripts/autoscience_cli.py make-review-request \
  --repository <OWNER>/<REPO> \
  --branch <BRANCH> \
  --expected-commit <40_HEX_COMMIT> \
  --conclusion-file examples/codex_execution_conclusion.example.md \
  --required-file docs/control_plane_workflow.md \
  --required-file docs/security_model.md \
  --output /tmp/autoscience_review_request.md \
  --payload-output /tmp/autoscience_review_payload.json

python3 scripts/autoscience_cli.py validate-handoff examples/valid_handoff_record.json
python3 scripts/autoscience_cli.py enqueue-inbox examples/valid_inbox_record.json \
  --queue-dir /tmp/autoscience_goal_inbox \
  --expected-commit 0123456789abcdef0123456789abcdef01234567
python3 scripts/autoscience_cli.py inbox-status \
  --queue-dir /tmp/autoscience_goal_inbox \
  --expected-commit 0123456789abcdef0123456789abcdef01234567
python3 scripts/autoscience_cli.py workflow-health \
  --policy configs/control_plane_policy.example.json \
  --scientific-policy configs/scientific_policy.example.json \
  --handoff examples/valid_handoff_record.json \
  --inbox examples/valid_inbox_record.json \
  --expected-commit 0123456789abcdef0123456789abcdef01234567
```

A handoff is valid only when:

- bridge role is `codex_web_handoff_trigger_monitor_return`;
- formal material source is `github_exact_pushed_head`;
- Web-side formal review did not select MCP instead of GitHub;
- latest user turn contains the expected commit and `CODEX_EXECUTION_CONCLUSION`;
- composer state proves the prompt was sent, not left as a draft;
- Web response is after the latest request and not stale output;
- structured review blocks are present;
- the embedded inbox record passes exact commit, model, GitHub, gate, required
  files, goal shape, and goal-hash checks.

## Required Stop

If a unit only proves control-plane readiness, stop there. Do not convert
control-plane readiness into training, data access, or stage acceptance.

## Scientific Authorization Layer

Every project must provide project-specific scientific registries before any
automation loop can claim training, model acceptance, stage acceptance, or data
readiness:

- stage state registry;
- dataset role matrix;
- label authorization matrix;
- execution authorization registry.

Run:

```bash
python3 scripts/autoscience_cli.py validate-scientific-policy configs/scientific_policy.example.json
python3 scripts/autoscience_cli.py validate-csv-schema stage-state examples/stage_state_registry.example.csv
python3 scripts/autoscience_cli.py validate-csv-schema dataset-role examples/dataset_role_matrix.example.csv
python3 scripts/autoscience_cli.py validate-csv-schema label-authorization examples/label_authorization_matrix.example.csv
python3 scripts/autoscience_cli.py validate-csv-schema execution-authorization examples/execution_authorization_registry.example.csv
```

The default template is fail-closed:

- control-plane READY does not grant scientific authorization;
- training, remote jobs, parser/target/view/split construction, checkpoint I/O,
  and final-test reopening are false by default;
- evaluation-only labels cannot be used for training, threshold learning, model
  selection, or split design unless a later project-specific reviewed goal
  explicitly changes the policy.
