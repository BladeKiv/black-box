# Security and Git preparation — 2026-10-21

Historical blocked audit, superseded by the user-authorized cleanup described
in [security-cleanup-report.md](security-cleanup-report.md). Counts below refer
to the original working tree and old Git history.

**BLOCKED BEFORE PHASE 3: token-bearing historical versions require review/cleanup.**

Branch: `master`. Remote: none. Index: empty. No branch, staging, commits or push performed.

Size snapshot: 3,586,619,749 bytes total (3.59 GB), comprising 3,563,324,777 working-tree bytes and 23,294,972 Git bytes. 347 files exceed 5 MiB. Files were retained locally.

Full working-tree scan plus final-rule supplemental scans: 290 finding locations. Reachable branch/tag/reflog history: 55 finding locations. These are pattern matches, including source expressions and test fixtures; they are not counts of confirmed active credentials.

| Finding type | Working tree | History |
|---|---:|---:|
| auth_value | 26 | 17 |
| credential | 145 | 7 |
| embedded_credential | 1 | 1 |
| local_path | 82 | 30 |
| passenger_data | 24 | 0 |
| postman_value | 12 | 0 |

Complete file/line/type inventories: [security-audit.json](security-audit.json) and [security-history.json](security-history.json). The audit JSON also lists every file over 5 MiB. These local inventories are ignored and contain no matched values.

Historical literal-token review locations:

| File | Line | Type |
|---|---:|---|
| `tasks/ss-6341/successful-booking-payloads.json` | 14 | credential/token pattern |
| `tasks/ss-6341/successful-booking-payloads.json` | 226 | credential/token pattern |
| `tasks/ss-6344/payload-evidence.json` | 147 | credential/token pattern |
| `tasks/ss-6344/payload-evidence.json` | 30364 | credential/token pattern |
| `tasks/ss-6344/qa.cjs` | 6 | credential/token pattern |
| `tasks/ss-6344/recovery.postman_collection.json` | 97 | credential/token pattern |
| `tasks/ss-6344/recovery.postman_collection.json` | 108 | credential/token pattern |

Files that must be reviewed/cleaned before first push: the historical token-bearing payloads, source and collection above; raw token-bearing Search/Result/booking captures under tasks/ss-6340, tasks/ss-6341 and tasks/ss-6344; passenger-name request captures under tasks/SS-6415-voluntary-change/runs/; and files containing personal absolute paths listed in the JSON inventory. Some tokens are deliberately invalid test fixtures: preserve approved test intent while removing genuine secrets. Token validity was not checked.

History rewrite: the repository is not cleared for push. Treat genuine secret-bearing historical versions as requiring a reviewed rewrite before publication, even after working files are cleaned. First distinguish fixtures and documentation from genuine secrets. No history was rewritten and no credential rotation was attempted.

Ignore rules now cover raw runs/evidence, request/response and paired payload captures, flow/latest markers, local env/Postman environment files and local environment references, secrets, caches, dependencies, private audit JSON, and 347 explicit existing large-file paths. Source scripts, scopes, sanitized reports/collections, knowledge, bb, templates and tests remain eligible for selective review. Ignore rules do not remove history or already tracked content.

`tasks/SS-6390-atlas-baggage/with-prior-auth.cjs:3` reads an old Codex session log to recover runtime credentials. It is flagged and unchanged. The README proposes validating BOOKING_USERNAME and BOOKING_PASSWORD environment variables and invoking the existing flow without session-log parsing. Running that historical flow still requires current endpoint authorization.

The installed local hook is `.githooks/pre-commit`, configured through repository-local core.hooksPath. It scans staged bytes and current lesson JSONL files, rejects findings and fails closed on scan errors. Verified with `git hook run pre-commit`; no files were staged for that check.

Checks passed: offline learning/transport assertions, scanner index/history regression checks, source parsing, reviewed new-file secret scan and whitespace validation. Pattern scanning does not prove arbitrary prose, encoded attachments or personal data without recognized fields are safe. The history scan covers reachable refs and reflogs, not unreferenced garbage objects.

Manual next actions: review the listed locations, rotate any genuine exposed credentials, approve a separate history-cleanup plan, rerun the audit, then resume the gated commit phase. No push commands are proposed while the history gate remains blocked.
