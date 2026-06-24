# Reusable Packaging Checklist

Before publishing or sharing an automated-research workflow template:

- Replace real ChatGPT conversation ids with placeholders.
- Replace account names, repository names, branch names, local paths, remote
  hosts, private IPs, dataset names, and commit hashes with placeholders unless
  they are intentionally public examples.
- Remove Web payload JSON, raw transcript text, connector metadata, endpoint
  URLs, tunnel URLs, tokens, and secrets.
- Keep policy defaults disabled or read-only.
- Include tests for model policy, commit equality, goal hash, stale commit,
  substituted goal, and privacy scanning.
- Run `python3 scripts/autoscience_cli.py privacy-scan --strict .`.
- Run `python3 -m unittest discover -s tests`.

