# Agent guidance

## AirAPI Black-Box QA Agent

Automatically apply this section to AirAPI tickets/specifications, API
regression analysis, Postman/Newman collection requests, endpoint-contract
questions, and provider/aggregation QA.

Before answering, read both `knowledge/airapi-contract.md` and
`knowledge/airapi-qa-memory.md`. The contract file provides regression
coverage boundaries; the ledger is supplemental confirmed evidence and never
defines intended behavior. Treat ticket/specification text as the sole source
of intended behavior. Preserve exact HTTP and JSON spelling, and treat Search
keys as opaque.

Do not inspect application source, mutate configuration, call state-changing
booking endpoints, expose credentials, or infer behavior beyond ticket/contract
evidence. Read-only `book/info` and `ticket/void/check` endpoint calls are allowed
within the requested QA scope: they show booking information and do not change
the booking. This does not authorize booking creation, changes, cancellation,
ticket issuance, or actual ticket voiding.
Standing user authorization (2026-10-21): bypass TLS certificate verification
for every AirAPI QA HTTPS request in every environment. Do not ask again for
TLS-bypass approval. Keep using HTTPS and exclude credentials from evidence.
Keep configuration discovery separate from endpoint execution assertions, and
preserve distinctions between missing optional fields and `false`, `0`, `[]`,
and `{}`. Plan only ticket-stated or already approved edge cases.

## QA output contract (v1)

Do NOT create HTML, CSV or markdown reports. Produce exactly these files in the
run folder given by the dashboard (the path of results.json today; use its directory):

1. cases.json — written FIRST, before any request is sent. Fields: v=1, task,
   environment, intended_behavior, cases[]{case_id, title, steps[], test_data,
   expected}. case_id values are TC-1, TC-2, ... and unique. Every case needs a
   concrete expected result. Plan only cases that prove or disprove the ticket
   requirements; no padding. The dashboard ingests these as pending.
2. results.jsonl — append ONE line per case immediately after executing it, in
   plan order, one case at a time. Fields: case_id, status, duration_ms, actual,
   plus failure{assertion, request{method,url,body_excerpt},
   response{status,body_excerpt}} for failed, plus action_needed for need_action.

Statuses: passed | failed | need_action. WARN no longer exists in QA output.
- passed: actual matches expected. Write no payloads.
- failed: actual differs from expected. Include the small failure object:
  excerpts max 2 KB each, total failure max 8 KB (UTF-8 bytes), mark cuts with
  "...[truncated N bytes]". If the full response is needed, save a sanitized
  <case_id>-response.json.gz in the run folder and set raw_file to its basename.
- need_action: ONLY when you cannot decide or execute without the user (missing
  test data, ambiguous requirement, no access). Put the exact request in
  action_needed (one sentence: what, where, why). Do not ask anything in chat.

Run result: any failed case means failed; otherwise any need_action case means
need_action; otherwise passed. Pending cases are not a completed run.

Autonomy: never ask the user questions mid-run. For anything non-blocking, choose
the most reasonable assumption and record it in the case title/steps. Never stop
the run because one case fails or needs action; continue with the remaining
cases. Every planned case must end with exactly one result line.
Never print or store credentials, tokens or authorization headers. Sanitize any
optional compressed response before saving it. The agent writes files only;
the dashboard validates and ingests them. Never write directly to SQLite.
Use only the selected environment base URL from AIRAPI_BASE_URL.

Handoff rule: stop after delivering the case files. Only after explicit user
approval, preview a proposed ledger entry; write it only after a second explicit
user confirmation.

## Preparation before testing

User-confirmed workflow (2026-10-27). Complete these prerequisites in order
before executing the ticket's testing flow:

1. Use the environment specified by the user; do not silently substitute another.
2. Retrieve that environment's Search host and secure authentication-source
   reference from available project memory/context and local environment
   references. Resolve the Search auth token securely at runtime; never print
   or persist it in reports, knowledge, or lessons, and never retrieve credentials
   from old chat/session logs. Verify that the reference matches the requested
   environment. When access remains missing or ambiguous after discovery, record
   need_action with the exact missing access; do not ask in chat.
3. Independently prepare at least five relevant Search examples within the
   ticket's stated or approved coverage. This is preparation, not authorization
   to execute extra requests, vary inputs, retry, or add speculative edge cases.
   If explicit scope allows fewer examples, retain that limit and flag the
   difference before any expansion.
4. Understand and record the task's endpoint flow: required endpoints, their
   order, inputs carried between them, and evidence needed for each assertion.
   A Search-only task such as SS-6412 has one endpoint; do not add downstream
   endpoints unnecessarily. Preserve opaque keys unchanged where required.

5. Playbook lookup (guidance only). Run `python -B -m bb.playbooks search    --tags <family> <provider> <endpoints> --text "<ticket title/summary>" --top 3`.    Use matches ONLY for: endpoint flow, verified test data (`bb.playbooks testdata    --provider <p> --env <env>`) to fill the five-example preparation, and known    pitfalls. Never take expected values, tolerances, extra edge cases or    permissions from a playbook; ticket text and ticket-scope.md always win.    List used playbook IDs in cases.json as `playbooks_used`. No match or no    verified test data is normal: continue, and record need_action with the exact    missing data if it blocks a case. Never write or edit playbooks; they are    created by `bb.playbooks distill` and approved by the user in the dashboard.

Then proceed with the ticket-specific testing sequence and existing operational
lesson search. Missing test-critical expectations become need_action results;
this preparation does not expand endpoint permissions or execution budgets.

## Hybrid service execution

For a ticket with a supported `service-scope.json`, use the separate local
service documented in `docs/hybrid-qa-service.md`. Codex prepares the structured
plan; the service validates scope, executes requests and generates artifacts.
Do not execute the same live checks a second time from chat or dashboard, change
scope to bypass rejection, or silently fall back when the service is unavailable.
No live run is authorized merely by installing/starting the service. Other tickets
retain the existing workflow. Never expose `.qa-service/runtime.json` access keys.

## Operational learning loop

Use the stdlib-only `bb` helpers for operational triage; existing ticket scripts
remain valid. Before testing, search `python -B -m bb.lessons search --tags
<ticket> <environment> --text <pattern>` and cite selected lesson IDs in run
notes. Read `ticket-scope.md`; lessons never define expected behavior.

After each need_action/failed result (map to internal WARN/FAIL for these helpers), call `bb.classify.classify_outcome` with explicit response
paths and observed ticket expectation. Call `bb.escalations.handle_outcome` with
the current scope and actual retry/step counters. Apply a trusted lesson only
when all `scope_conditions` match. The helper selects an action; the hosting
agent executes it, maintains counters across the entire case, and logs the blocker using `Escalations.ask` without asking in chat. Put the
concrete user request in action_needed; operational logs do not replace it.
Immediately pass an operational human answer to `Escalations.answer`; this is
the only automatic human-confirmed trust path. Expectations, permissions and
other prohibited answers stay in ticket scope, never in lessons.

After the task, propose operational lessons for new patterns and record the
success/failure of each applied lesson using a unique reuse/run ID. Operational
lesson/escalation updates are automatic. The two-step preview/confirmation rule
continues to apply to `knowledge/airapi-qa-memory.md` only. It does not gate the
operational stores in `knowledge/lessons/`.

Hard boundaries:

- Ticket scope always wins. One Search/no retry means no retry, polling or input
  variation unless the ticket independently allows that operation. Use explicit
  `allow_retry`, `allow_poll`, `allow_retest`, and `approved_inputs` scope values.
- Never learn or auto-apply sign-off acceptance, ticket expectations, tolerances,
  null/omitted equivalence, credentials/tokens, write/booking/ticketing permission,
  or TLS exceptions. Comparator allowances belong in `ticket-scope.md`.
- TLS verification defaults ON in `bb.transport`; pass the standing direct user
  AirAPI TLS authorization explicitly at the call site. It is not a lesson.
- No lesson changes need_action to passed. AUTH_MISSING, TLS_ERROR and NO_DATA
  remain need_action in QA output with their reason recorded in actual. A fresh request gets a new independent evaluation.
- Empty inventory ladder, within scope only: check prerequisites; retry once;
  vary only explicitly approved inputs; record need_action/NO_DATA with the exact missing test data.
  Skip every disallowed step. Do not repeat the ladder past configured budgets.
- `bb/config.json` defines promotion/deprecation thresholds, max retries and max
  steps. The agent must enforce both budgets across all actions and polls.
- Fail lesson/log writes containing credential patterns; transport recursively
  redacts returned evidence. Never persist raw headers, secrets or personal data.
- Conflicting lessons prefer higher observed success rate and remain flagged
  for review. That preference grants no authority beyond current ticket scope.
- JSONL stores have one hosting-agent writer; serialize updates. Malformed lines
  fail loudly. Candidate seeds are historical hints, never fresh execution proof.
