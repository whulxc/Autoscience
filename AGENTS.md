# Autoscience Agent Instructions

This repository is a reusable automated-research control-plane template.

## Boundaries

- Do not add real ChatGPT conversation ids, connector ids, endpoint URLs,
  tunnel URLs, tokens, private hostnames, private IP addresses, raw datasets,
  checkpoints, run directories, or private research transcripts.
- Keep example configuration placeholder-only.
- Keep MCP read-only by default.
- Do not add generic write, edit, apply-patch, bash, shell, terminal, raw data,
  checkpoint, remote GPU, training, inference, or evaluation tools.
- Treat GitHub exact pushed HEAD plus fixed Web review as the formal gate.
- Treat MCP/bridge automation as the Codex-Web courier: submit the review
  request, monitor delivery/generation, and return a structured result. It must
  not replace GitHub as the formal evidence source.
- If ChatGPT Web cannot use GitHub and MCP simultaneously, use GitHub for the
  formal review and keep MCP out of the Web-side evidence path.
- Treat the controlled inbox as a narrow review-decision and next-goal queue,
  not as an executor.

## Checks

Run before committing:

```bash
python3 -m unittest discover -s tests
python3 scripts/autoscience_cli.py validate-policy configs/control_plane_policy.example.json
python3 scripts/autoscience_cli.py validate-scientific-policy configs/scientific_policy.example.json
python3 scripts/autoscience_cli.py validate-handoff examples/valid_handoff_record.json
python3 scripts/autoscience_cli.py validate-inbox examples/valid_inbox_record.json
python3 scripts/autoscience_cli.py validate-csv-schema stage-state examples/stage_state_registry.example.csv
python3 scripts/autoscience_cli.py validate-csv-schema dataset-role examples/dataset_role_matrix.example.csv
python3 scripts/autoscience_cli.py validate-csv-schema label-authorization examples/label_authorization_matrix.example.csv
python3 scripts/autoscience_cli.py validate-csv-schema execution-authorization examples/execution_authorization_registry.example.csv
python3 scripts/autoscience_cli.py workflow-health --policy configs/control_plane_policy.example.json --scientific-policy configs/scientific_policy.example.json --handoff examples/valid_handoff_record.json --inbox examples/valid_inbox_record.json --expected-commit 0123456789abcdef0123456789abcdef01234567
python3 scripts/autoscience_cli.py privacy-scan --strict .
git diff --check
```
