# AirAPI QA report — SS-6258 routing classification

> **Release signal:** `PASS`
> **Run:** 2026-09-02 · **Scope:** Search fare-level `routingInversion`

## What we observed

The supplied international returning Search, `YYC → SIN // SIN → YYC`, returned
345 options. Across 453 observed fare records under
`keys.commission_info.fareCalculation`, every `routingInversion` value was a
boolean: 301 `false` and 152 `true`. The passenger-visible fare route remains
in natural physical segment order; inversion is represented only by the flag.

## Executed tests

| ID | Test case | Test data | Expected result | Actual result | Status |
| --- | --- | --- | --- | --- | --- |
| TC-01 | Search availability | Supplied stage return Search | `200 OK` with `results[]` | `200 OK`; 345 results | PASS |
| TC-02 | Flag location and type | All observed fare records in `keys.commission_info.fareCalculation` | `routingInversion` is a boolean | 453 flags, all boolean | PASS |
| TC-03 | Inverted fare representation | First returned option | Inverted fare uses `routingInversion: true`; displayed route stays physical | One `true`; both fare routes remain physical | PASS |
| TC-04 | Default non-inverted representation | First returned option | Non-inverted fare uses `routingInversion: false`; displayed route stays physical | One `false`; both fare routes remain physical | PASS |

## Evidence and rerun

- The run verifies the agreed boolean contract, not the ticket's superseded
  numeric `routing` logging proposal.
- [Postman collection](/./tasks/SS-6258-routing-classification/airapi-ss-6258-routing-classification.postman_collection.json)
- [Expected-outcome CSV](/./tasks/SS-6258-routing-classification/airapi-ss-6258-routing-classification-scenarios.csv)

## Manual-review handoff

No QA-evidence ledger entry has been proposed or written.
