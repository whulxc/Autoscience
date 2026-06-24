# Autoscientce

Reusable control-plane template for automated research workflows.

The project standardizes a safe handoff loop:

1. Codex or another executor performs one bounded work unit.
2. The executor commits lightweight evidence to GitHub.
3. A fixed ChatGPT Web review session reviews the exact pushed commit through GitHub.
4. The Web review returns a structured decision and next `/goal`.
5. A controlled local inbox validates that decision before any executor continues.

Autoscientce is intentionally conservative. It does not grant ChatGPT Web or MCP
generic repository write access, shell access, training access, dataset access,
checkpoint access, or remote compute access. MCP is treated as an auxiliary
read-only context channel unless a project creates and reviews a narrower policy.

## What This Template Includes

- `autoscience/control_plane.py`: dependency-free validation helpers.
- `scripts/autoscience_cli.py`: local status, inbox validation, and privacy scan.
- `configs/control_plane_policy.example.json`: fail-closed policy template.
- `skills/automated-research-workflow/SKILL.md`: reusable Codex skill.
- `docs/`: control-plane workflow, security model, and session policy.
- `templates/web_review_request.md`: sanitized fixed-Web review request template.
- `tests/`: unit tests for the validator and privacy scanner.

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
python3 scripts/autoscience_cli.py validate-inbox examples/valid_inbox_record.json
python3 -m unittest discover -s tests
```

## Project-Specific Setup

Copy this template into a real research repository and replace the placeholders
in `configs/control_plane_policy.example.json` and
`templates/web_review_request.md`.

Do not commit actual ChatGPT conversation ids, connector tokens, tunnel URLs,
raw datasets, checkpoints, run outputs, private hostnames, private IP
addresses, or account-specific paths to a reusable public template.

