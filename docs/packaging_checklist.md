# Reusable Packaging Checklist

Before publishing or sharing an automated-research workflow template:

- Replace real ChatGPT conversation ids with placeholders.
- Replace account names, repository names, branch names, local paths, remote
  hosts, private IPs, dataset names, and commit hashes with placeholders unless
  they are intentionally public examples.
- Remove Web payload JSON, raw transcript text, connector metadata, endpoint
  URLs, tunnel URLs, tokens, and secrets.
- Keep policy defaults disabled or read-only.
- Keep scientific authorization defaults false; include placeholder stage,
  dataset, label, and execution authorization registries.
- Include tests for model policy, commit equality, goal hash, stale commit,
  substituted goal, handoff delivery, stale Web output, MCP-as-formal-source
  rejection, and privacy scanning.
- Run `python3 scripts/autoscience_cli.py validate-policy configs/control_plane_policy.example.json`.
- Run `python3 scripts/autoscience_cli.py validate-scientific-policy configs/scientific_policy.example.json`.
- Run `python3 scripts/autoscience_cli.py validate-handoff examples/valid_handoff_record.json`.
- Run `python3 scripts/autoscience_cli.py validate-inbox examples/valid_inbox_record.json`.
- Run all `validate-csv-schema` checks for example registries.
- Run `python3 scripts/autoscience_cli.py workflow-health ...` with the
  template policy, scientific policy, handoff, inbox, and expected commit.
- Run `python3 scripts/autoscience_cli.py run-unit configs/automation_unit.example.json`.
- If a project adds a `local_command` transport adapter, keep it private unless
  it contains no real session ids, endpoints, tokens, private paths, or raw
  transcript material.
- Run `python3 scripts/autoscience_cli.py privacy-scan --strict .`.
- Run `python3 -m unittest discover -s tests`.
