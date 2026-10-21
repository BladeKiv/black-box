# AirAPI QA — <ticket title>

> **Release signal:** `PASS / FAIL / WARN`
> **Run:** <date> · **Scope:** <route, endpoint, or provider>

## What we observed

<!-- Summarize only confirmed ticket/specification and live API behavior.
Preserve exact HTTP and JSON spelling. Keep this to 2-4 short sentences. -->

## Executed tests

| ID | Test case | Test data | Expected result | Actual result | Status |
| --- | --- | --- | --- | --- | --- |
| TC-01 |  |  |  |  | PASS / FAIL / WARN |

<!-- PASS: expected result observed. FAIL: observed result contradicts it.
WARN: the test cannot be conclusively evaluated because access, test data, or
stable inventory is unavailable. Ask the user live about test-critical
ambiguities and confirm any non-ticket edge cases before including them. Do
not include assumptions or unresolved questions in the report. -->

## Evidence and rerun

- Task directory: `tasks/<task-slug>/`
- Live evidence: <response count, field paths, or relevant API facts>
- Postman collection: <path>
- Expected-outcome CSV: <path>

For every `WARN` or `FAIL` test, include paired request and response payload
evidence in the report. Exclude credentials and unrelated response fields.

### Postman collection design

- AirAPI behavior only; do not include provider-level tracks.

The importable collection must be Postman Collection v2.1 and include:

- `pm.test` assertions limited to ticket/contract evidence;
- pre-request setup;
- scenario variables;
- expected-outcome CSV variables for non-deterministic inventory; and
- CSV rows with `scenario_id`, `expected_result`, `provider_filter`,
  `search_url`, and ticket-specific inputs.

Unknown response paths must be parameterized, never guessed. Ask the user live
when their meaning is required to evaluate a test. Keep Search keys opaque and
carry them forward unchanged.

## Manual-review handoff

Stop after delivering this report and the collection. Only after explicit user
approval, preview a proposed ledger entry; write it only after a second
explicit user confirmation.
