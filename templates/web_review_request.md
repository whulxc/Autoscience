[MODEL_CHECK_BEGIN]
Please self-report the current model first.
If the model is not an allowed Pro or thinking model, stop and return MODEL_POLICY_BLOCKED.
[MODEL_CHECK_END]

Review only the exact current pushed Git commit.

Repository: <OWNER>/<REPO>
Branch: <BRANCH>
Expected BRANCH_HEAD_SEEN: <40_HEX_COMMIT>
Expected COMMIT_REVIEWED: <40_HEX_COMMIT>

[CODEX_EXECUTION_CONCLUSION_BEGIN]
Plain-language conclusion:
<EXECUTION_CONCLUSION>

Required boundaries:
- GitHub exact pushed HEAD remains the formal evidence source.
- The fixed ChatGPT Web review session remains the formal review entry.
- MCP is read-only auxiliary context only.
- The controlled inbox may contain only a verified review decision and next `/goal`.
- Codex or the local executor remains the only executor.
- No write, bash, raw data, checkpoint, remote GPU, training, inference, evaluation, parser, target, split, or view authority is granted.
[CODEX_EXECUTION_CONCLUSION_END]

Required files to read through GitHub:

- <REQUIRED_FILE_1>
- <REQUIRED_FILE_2>

Return exactly these blocks:

[MODEL_CHECK_BEGIN]
MODEL_SELF_REPORT=
MODEL_ALLOWED=
MODEL_POLICY=allowed_only_if_model_self_report_contains_allowed_pro_or_thinking_model
[MODEL_CHECK_END]

[CODEX_CONCLUSION_REVIEW_BEGIN]
CODEX_CONCLUSION_READ=
CODEX_CONCLUSION_ACCEPTED_BY_REVIEW=
CONTROL_PLANE_BOUNDARIES_ACCEPTED=
FIXED_WEB_GITHUB_REVIEW_AUTHORITY_PRESERVED=
GENERIC_WRITE_OR_BASH_AUTHORIZED=False
TRAINING_OR_SCIENTIFIC_STAGE_AUTHORIZED=False
CODEX_CONCLUSION_REVIEW_NOTES=
[CODEX_CONCLUSION_REVIEW_END]

[GITHUB_EVIDENCE_BEGIN]
GITHUB_READ_VERIFIED=
GITHUB_READ_NOT_VERIFIED=
BRANCH_HEAD_SEEN=
COMMIT_REVIEWED=
FILES_READ=
GATE_DECISION=READY|BLOCKED
BLOCKER_SUMMARY=
[GITHUB_EVIDENCE_END]

[MARKDOWN_BEGIN]
Explain the decision in plain language.
[MARKDOWN_END]

[GOAL_BEGIN]
/goal Create and read docs/goals/<NEXT_GOAL_FILE>.md ...
[GOAL_END]

