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
- If a long control-plane session may bias scientific review, create a fresh
  research-review session and bootstrap it from GitHub evidence.
- If a chat reaches length limit, replace it only after a bootstrap packet.
- If login, passkey, two-factor, payment, admin, or security confirmation is
  visible, stop as manual-required.

