# GitHub vs MCP Role Split

This note prevents a common design mistake: using MCP as if it should replace
GitHub.

## Plain-Language Rule

GitHub is the evidence cabinet.

MCP or another bridge is the courier and monitor.

ChatGPT Web is the reviewer.

Codex or the local executor is the only executor.

## What GitHub Does

GitHub should hold the formal materials that a reviewer can verify:

- current commit and branch head;
- source code;
- lightweight Markdown, CSV, JSON, and config evidence;
- review packets;
- promoted Web review records;
- progress summaries and goal files.

When ChatGPT Web reviews a research unit, it should verify the exact pushed
commit and required files through GitHub. This keeps the review reproducible
and audit-friendly.

## What MCP Or The Bridge Does

MCP or a private browser/CDP bridge should improve the process between Codex
and ChatGPT Web:

- submit or stage the Codex conclusion and review request;
- verify that the latest Web user turn contains the expected commit and
  `CODEX_EXECUTION_CONCLUSION`;
- monitor the composer/input state and generation state;
- detect prompt-delivery failure, stale output, model-policy failure, and
  GitHub verification failure;
- capture only the latest assistant response after the current request;
- return a structured review decision and next `/goal` into a controlled inbox.

This is useful because it removes manual copy/paste and blind waiting. It does
not make MCP the evidence source.

## Required Connector Priority

If ChatGPT Web forces a choice between GitHub and an MCP app during formal
review, choose GitHub.

The bridge may still operate outside the Web-side evidence path by submitting,
monitoring, and returning the review. The review itself must stay tied to
GitHub exact pushed HEAD.

## Forbidden Confusion

Do not use MCP to grant ChatGPT Web generic write access, bash/shell access,
raw dataset access, checkpoint access, remote GPU access, training,
inference, evaluation, parser construction, target construction, split
construction, or view construction.

Do not treat a successful bridge handoff as model acceptance, dataset
readiness, scientific-stage acceptance, or training authorization.

## Expected User Experience

The practical target is one Codex CLI window plus one fixed ChatGPT Web review
conversation:

1. Codex commits evidence to GitHub.
2. The bridge sends Codex's conclusion to Web.
3. Web reads GitHub and reviews the exact commit.
4. The bridge returns Web's decision and next `/goal`.
5. Codex validates the controlled inbox before executing anything.

The bridge makes the loop smoother; GitHub keeps it accountable.
