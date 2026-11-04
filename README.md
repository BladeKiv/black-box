# AirAPI Black-Box QA

Read `AGENTS.md`, `knowledge/airapi-contract.md`, and the evidence ledger before
ticket work. Existing ticket scripts and dispatch rendering are unchanged.

## Hybrid QA service

The separate local execution service starts with `python -B -m bb.service`.
Codex chat and QA Control can prepare supported plans; the service enforces
ticket-local scope and executes deterministic checks. Initially only SS-6412's
Search currency `points_diff` flow is supported. See
[launch, integration and limits](docs/hybrid-qa-service.md).

## Operational lessons

Preparation playbooks and verified relative-date inputs are documented in
[Playbooks](docs/playbooks.md). Start with `python -B -m bb.playbooks search
--tags <family> <provider> <endpoint> --text "<ticket summary>" --top 3`.
Playbooks provide guidance only; the operational lessons layer remains separate.

Python 3, standard library only. Run from the repo root:

```powershell
python -m bb.selftest
python -B -m tests.test_learning
python -B -m bb.lessons search --tags SS-6425 retest --text "human reported fix"
python -B -m bb.lessons list
python -B -m bb.lessons propose --file lesson.json
python -B -m bb.lessons record-use --id <lesson-id> --run <unique-reuse-id> --success
python -B -m bb.lessons deprecate --id <lesson-id>
python -B -m bb.report
```

`bb.selftest` runs every `tests/test_*.py` module and the five ticket-local
offline checks, using Python 3 and Node.js. It prints a PASS/SKIP/FAIL table
and exits non-zero on failure. It copies tracked working files into a temporary
directory, so report generators cannot modify the checkout and ignored evidence
is never loaded. The two checks requiring ignored captures report
`SKIP: evidence not in repo` (exit 77). Missing runtimes and malformed evidence
are failures. Stage new test files before running so they enter this snapshot.

`lesson.json` fields: tags (list), trigger_pattern, situation, action, outcome,
created_run, scope_conditions (object). Source defaults to agent. Actions are
check_prerequisites, retry, vary_inputs, poll, report_warn and fresh_retest.
Candidates become trusted after configured successful reuses; repeated failures
deprecate them. Human operational answers are immediately saved by
`Escalations.answer`. These stores are append-only snapshots with one writer.
Do not edit older lines. `list` returns latest snapshots. Search flags conflicts
and orders by observed success rate then keyword/tag score. Tags are case-sensitive.
Seeds remain candidate because historical mentions do not establish reusable
human authorization. The SS-6388 tid hint applies only to its scoped API; it
does not replace the contract's separate async API shape.

Reports show UTC ISO-week escalation rate (distinct escalated runs / recorded
runs), reason-code occurrences, uses/promotions/deprecations and tasks by worst
recorded status. An empty report means no hosting-agent run records, not zero
production escalations. The end-to-end test uses temporary stores to demonstrate
a 100% to 0% per-run drop; it does not claim live QA improvement.

## Wiring a ticket script: SS-6425 worked example

This is an opt-in example, not a migration or an executable booking flow.
Keep SS-6425's existing Book/Info request bytes and ticket-scoped evaluation.
Read credentials from runtime environment variables. Never retrieve old session
logs. Supply the already-authorized endpoint and TLS policy explicitly:

```python
import os
from pathlib import Path
from bb.transport import request

# Existing authorized SS-6425 Book/Info request; never put it in lessons.
payload = Path('tasks/SS-6425-baggage-description/book-info-request.json').read_bytes()
result = request(
    os.environ['AIRAPI_BOOK_INFO_URL'], method='POST', data=payload,
    headers={'Authorization': os.environ['AIRAPI_AUTHORIZATION'],
             'Content-Type': 'application/json'},
    allowed_endpoint=('POST', '/ndc/v1/book/info'),
    credentials_required=True, timeout=60,
    verify_tls=False, tls_bypass_authorized=True,  # direct standing user authority
)
# result contains sanitized body, HTTP status, operational reason and WARN until
# the hosting runner evaluates the ticket expectation. It does not certify PASS.
# Feed fresh trace-correlated source evidence into the ticket evaluator, then
# pass its boolean outcome as classify_outcome's expectation_observed context.
```

The existing dispatch renderer still renders ticket report-data.json using the
shared HTML template and embedded collection/CSV Blob downloads. `bb.report`
is an operational aggregate, not a replacement ticket dispatch sheet.

Scope selection: pass current ticket/environment/route and explicit action
permissions to `handle_outcome`; it returns a lesson/action or escalation ID,
never executes a retry. Maintain counters across the case, preserve WARN and
paired evidence, ask the returned question live, then save only operational
answers. Tolerances/equivalences, intended behavior and authorization remain
in ticket scope. Record a reuse only after its outcome is actually observed.

## Security and what is not committed

Run `python -B scripts/check_secrets.py --audit --output docs/security-audit.json`
for the full working tree (including ignored files) and reachable/reflog git
objects. The JSON contains file, line and finding type, never matched values.
It also inventories files over 5 MiB and reports working-tree and Git sizes.
Matches require review: source literals and placeholders may be false positives.
The scanner is pattern based; it cannot prove arbitrary personal text is safe.

The local hook uses `.githooks/pre-commit` to inspect the index and the lesson
JSONL working copies. It fails closed on scan errors or findings. On a fresh
clone enable it with `git config --local core.hooksPath .githooks`. It is a local
guard; server-side enforcement is outside this change.

Ignored: raw run directories and request/response captures, evidence directories,
flow state/latest markers, environments/secrets, local environment references,
caches/dependencies, private security inventories, and the explicitly listed
existing files over 5 MiB. Ignore rules do not untrack or erase old Git objects.
Source scripts, scopes, sanitized reports/collections, knowledge, bb, templates
and tests remain eligible for review. Never use `git add .` for this repository.
Some historical reports embed payloads; review them before committing too.

The former `tasks/SS-6390-atlas-baggage/with-prior-auth.cjs` read credentials
from an old Codex session log. Its current implementation validates runtime
environment variables before invoking the existing flow:

```javascript
const assert = require('node:assert/strict');
for (const name of ['BOOKING_USERNAME', 'BOOKING_PASSWORD']) {
  assert(process.env[name], 'Required runtime credential missing');
}
require('./run-flow.cjs');
```

The current wrapper implements this environment-only behavior. Atlas loaders
also require `AIRAPI_POSTMAN_COLLECTION`, the path to the caller's local
Postman collection. Collection credential values are not used as a fallback.

SS-6401 runners read `AIRAPI_SEARCH_TOKEN` (the credential component expected
by their existing authorization-header construction). SS-6426 reads the base
Search URL from `AIRAPI_<ENV>_SEARCH_URL` and the complete header value from
`AIRAPI_<ENV>_AUTHORIZATION`, using uppercase environment names. SS-6416 reads
`BOOKING_USERNAME` and `BOOKING_PASSWORD` directly. Postman collections use
runtime variables; deliberately corrupt token cases use `INVALID_TEST_TOKEN`.

The cleanup replaces session-log parsing while retaining the existing flow caller.
Do not run the flow without current ticket endpoint authorization. If a history
finding contains credentials, rotate affected credentials and agree on a cleanup
plan before any push. History rewriting is a separate destructive operation;
the earlier blocked phase did not rewrite history or push.

The user subsequently authorized a fresh local Git history after a verified
external `.git` backup. See `docs/security-cleanup-report.md` for this cleanup;
the earlier blocked Phase 2 report is historical. No push is performed by the agent.
