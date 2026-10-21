# AirAPI QA report — SS-6296 CMS dump PCC validation

> **Release signal:** `PASS`
> **Run:** 2026-09-02 · **Scope:** commission dump validation, PCC `W2GM`, `6NVG`, and `8C4T`

## What we observed

SS-6296 requires no commission when PCC `W2GM` has no matching rule for the
requested project. That scenario returned `200 OK`, retained `pcc: "W2GM"`,
and reported `prices.comm: 0`.

The requested PCC boundary checks produced two distinct outcomes. `6NVG` / GDS
`S` returned a valid original itinerary but no applied commission. `8C4T` /
GDS `E` did apply a non-deductable segment fee: `amount: 10` and
`deduct: false`. Its aggregate `prices.comm: 0` is correct for that fee type.

## Executed tests

| ID | Test case | Test data | Expected result | Actual result | Status |
| --- | --- | --- | --- | --- | --- |
| TC-01 | Commission validation access | Supplied dump payload and PCC `W2GM` | `200 OK` JSON response | `200 OK` | PASS |
| TC-02 | PCC context | Query PCC `W2GM` | Response retains requested PCC | `pcc: "W2GM"` | PASS |
| TC-03 | Commission outcome | Validation result | No commission | `prices.comm: 0`; `passengers.ADT.comm: 0` | PASS |
| TC-04 | Consolidator boundary: 6NVG / S | Supplied LH dump, PCC `6NVG` | GDS `S`; no commission when no PCC rule is configured | `originalItinerary.gds: "S"`; `prices.comm: 0`; no `commBreakdown` | PASS |
| TC-05 | Consolidator boundary: 8C4T / E | Supplied LH dump, PCC `8C4T` | GDS `E`; an applied commission entry | `prices.commBreakdown.segmentFees[0]`: `amount: 10`, `deduct: false`; aggregate `comm: 0` | PASS |

## Evidence and rerun

- TC-04 passes: `6NVG` / `S` has no configured commission rule, so no
  commission entry is expected.
- TC-05 passes: commission is present as a non-deductable segment fee, so the
  aggregate commission remains zero.
- [Postman collection](/./tasks/SS-6296-cms-dump-validation-pcc/airapi-ss-6296-live.postman_collection.json)
- [Expected-outcome CSV](/./tasks/SS-6296-cms-dump-validation-pcc/airapi-ss-6296-live-scenarios.csv)

## Manual-review handoff

Review the collection and CSV, set authorized credentials, then run it in
Postman Runner. No QA-evidence ledger entry has been proposed or written.
