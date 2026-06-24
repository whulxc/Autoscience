# Security Model

Autoscientce is designed to fail closed.

## Safe-by-Default Rules

- Default bridge state is disabled until a project-specific review authorizes a
  narrower mode.
- Do not expose generic write, edit, apply-patch, bash, shell, or terminal
  tools.
- Do not expose raw data, checkpoints, run directories, secrets, remote GPUs,
  training, inference, evaluation, parser construction, target construction,
  split construction, or view construction.
- Do not commit long-lived endpoints, connector URLs, tunnel URLs, tokens,
  secrets, credentials, private hostnames, or private IP addresses.
- Treat MCP as read-only auxiliary context; GitHub exact pushed HEAD remains
  the formal evidence source.
- Treat the fixed Web review as the review entry; Codex or the local executor
  remains the only executor.

## Main Risks

- Permission drift: a future policy may enable write, bash, training, raw data,
  checkpoint, or remote GPU access.
- Endpoint exposure: a public MCP endpoint or tunnel may become a remote
  attack surface.
- Goal injection: a malicious or stale goal could be queued if provenance
  checks are weakened.
- Context leakage: review transcripts and request files can contain private
  project state even when they are not raw datasets.
- Stale review promotion: an older READY block can be mistaken for the current
  commit if polling is not bound to the latest user turn.

## Required Mitigations

- Enforce allowlisted read-only MCP tools.
- Bind inbox entries to exact commit, fixed Web payload metadata, review
  artifact, required-file list, gate decision, goal text, and goal hash.
- Reject stale commits, missing required files, disallowed models, unverified
  GitHub reads, and substituted goals.
- Run strict privacy scans before publishing reusable templates.
- Store real project identifiers only in private instance configuration.

