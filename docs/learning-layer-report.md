# Learning layer delivery — 2026-10-21

Historical Phase 1/2 handoff. The subsequent user-authorized repository cleanup
is documented in [security-cleanup-report.md](security-cleanup-report.md).

**STOP BEFORE PHASE 3 — historical token values require cleanup/review.**

Scope: additive stdlib Python helpers and Git security preparation; no live API
requests, ticket migrations, historical evidence changes or QA-ledger updates.

Intended behavior: the hosting agent reuses scoped operational lessons without
learning expectations, comparator allowances, credentials or authorization.
Unknown access/inventory/transport outcomes remain WARN. No lesson upgrades a
WARN to PASS. Current ticket scope and budgets remain authoritative.

| Check / test data | Expected | Actual | Status |
|---|---|---|---|
| Seeded 422 Price change, 408 Retry, 401, TLS, missing auth, empty inventory, missing comparisons, async, invalid JSON and unexpected message | Operational reason; WARN for inconclusive outcomes; PASS only for supplied observed expectation | Plain-assert classification checks pass; JSON null stays distinct from invalid JSON | PASS |
| Mocked HTTPS, 422 and 302; nested secrets, short authorization token, Postman variable | TLS on by default; explicit bypass authority; no redirect/retry; redaction and blocked secret writes | Transport/security checks pass; no live requests | PASS |
| Temporary lesson stores, scoped retry prohibition, budgets, successes/failures and conflicting actions | Append-only lifecycle; trusted-only selection within scope; conflicts flagged; forbidden lessons rejected | Lesson checks pass; six production seeds remain candidate | PASS |
| Two mocked empty-inventory runs with an operational human answer | One question in first run, zero in second, both WARN | Observed; aggregate escalation rate 50%, per-run escalation drops 100% to 0% | PASS |
| Temporary Git repo: secret in index then clean working copy; secret in old commit then clean tip | Both indexed and historical value detected | Scanner assertions pass; dummy repository removed | PASS |
| Installed local pre-commit hook | Runs scanner against index and lesson working copies | `git hook run pre-commit` exits 0; current index is empty | PASS |

Verification: `python -B -m tests.test_learning`, `python -B -m tests.test_secrets`,
Python AST parsing, reviewed-file secret scan and `git diff --check`.

Changes: `bb/` classification, transport, security, append-only lessons/escalations,
weekly operational report and config; six candidate seeds; AGENTS learning-loop
append; README usage and SS-6425 transport example; tests; `.gitignore`;
`scripts/check_secrets.py`; local `.githooks/pre-commit`.

The hosting agent must call the helpers and maintain case-wide counters. Existing
ticket runners are not automatically instrumented. Operational improvement is
demonstrated only with mocks; live escalation reduction has not been measured.

Security findings and size inventory are in [the Phase 2 report](security-report.md).
The private JSON inventories list every finding as file, line, type and, for Git
history, object ID. They do not include matched values.

Phase 3 was not entered: no feature branch, staging, commits or push. Current
branch remains `master`; no remote is configured. Existing unrelated changes
remain present. History cleanup requires a separate reviewed action.
