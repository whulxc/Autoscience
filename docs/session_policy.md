# ChatGPT Web Session Policy

Use separate Web conversations for different responsibilities.

## Recommended Sessions

- Control-plane session: used for bridge, MCP, GitHub handoff, and workflow
  health reviews.
- Research-review session: used for scientific decisions after bootstrapping
  context from GitHub.

Do not assume a new Web chat remembers old context. Bootstrap it from GitHub
files and a concise current-state packet.

## Bootstrap Packet

A fresh research-review session should receive:

- project context brief;
- progress summary;
- stage protocol;
- current state registry;
- latest accepted control-plane review;
- current branch and exact commit;
- required files;
- model policy;
- GitHub exact-HEAD review contract;
- forbidden actions.

## Isolation Rules

- Do not follow the user's active ChatGPT tab.
- Do not create routine review chats when a fixed review session exists.
- For formal reviews, keep the ChatGPT Web connector choice on GitHub when the
  UI makes GitHub and MCP mutually exclusive.
- Use MCP/bridge automation outside the formal Web evidence path to submit the
  request, monitor delivery/generation, capture the latest current response,
  and stage a controlled inbox record.
- If a long control-plane session may bias scientific review, create a fresh
  research-review session and bootstrap it from GitHub evidence.
- If a chat reaches length limit, replace it only after a bootstrap packet.
- If login, passkey, two-factor, payment, admin, or security confirmation is
  visible, stop as manual-required.

## New Research Session

When a project moves from bridge/debug work back to scientific decisions, start
a fresh research-review conversation when practical. The first prompt must say:

- do not rely on previous chat memory;
- use GitHub files and the current Codex conclusion as the evidence source;
- self-report the model before review;
- block if the model is not an allowed Pro/thinking model;
- verify branch head and reviewed commit equal the expected current commit;
- remember that control-plane readiness is not scientific readiness.
