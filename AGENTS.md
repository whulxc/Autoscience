# Autoscientce Agent Instructions

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
- Treat the controlled inbox as a narrow review-decision and next-goal queue,
  not as an executor.

## Checks

Run before committing:

```bash
python3 -m unittest discover -s tests
python3 scripts/autoscience_cli.py validate-policy configs/control_plane_policy.example.json
python3 scripts/autoscience_cli.py validate-inbox examples/valid_inbox_record.json
python3 scripts/autoscience_cli.py privacy-scan --strict .
git diff --check
```

