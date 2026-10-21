# AirAPI black-box contract reference

## Use and evidence

This is a public-contract reference for black-box QA. Ticket/spec text is the
sole intended behavior source. Contract knowledge is used only to design
regression coverage and to record explicit evidence boundaries. Preserve exact
HTTP and JSON spelling; Search keys are opaque values.

Missing optional fields differ from `false`, `0`, an empty array, and an empty
object. Unspecified nested shapes and transport statuses remain unspecified.
Any behavior not stated by the ticket/spec is an `[assumption]`, not an
assertion.

## Endpoint map

```text
GET /v1/search -> results[].key
GET /v1/search?async=true -> searchId, status, completed, progress
GET /v1/async/poll?searchId=... -> completed, progress
GET /v1/async/get?searchId=... -> Search-compatible results[]
GET /v1/result/ANY/{key} -> result
GET /v1/ngs-air-pricing/{product_type}/{key} -> shelves
GET /v1/air-pricing/allfares/{product_type}/{key} -> fares
GET /algo/conf -> JSON object root
```

## Search

`GET /v1/search` exposes result entries through `results[].key`. The key is an
opaque value and must be carried forward without normalization or spelling
changes. A completed synchronous Search with no matching itinerary is `200 OK`
with `results: []`. The contract does not specify the remaining nested result
shape or other transport statuses.

## Asynchronous Search

`GET /v1/search?async=true` exposes `searchId`, `status`, `completed`, and
`progress`; async initiation permits `200 OK` or `202 Accepted`, with no
canonical initiation code. Polling uses `GET /v1/async/poll?searchId=...` and
exposes `completed` and `progress`; poll until `completed` is `true` before
final retrieval. Retrieval uses `GET /v1/async/get?searchId=...` and is
Search-compatible, returning `results[]`. Optional-field distinctions and
unspecified nested shapes remain as described in Use and evidence.

## Selected-itinerary endpoints

Result, NGS Air Pricing, and AllFares independently consume a Search key:

```text
GET /v1/result/ANY/{key} -> result
GET /v1/ngs-air-pricing/{product_type}/{key} -> shelves
GET /v1/air-pricing/allfares/{product_type}/{key} -> fares
```

Each endpoint is a separate regression target. A Search key is opaque, and the
contract does not define the unspecified nested response shapes.

## Read-only configuration discovery

`GET /algo/conf` returns a JSON object root and is read-only configuration
discovery. It cannot demonstrate execution of a module for an individual
request. Configuration discovery must therefore remain separate from endpoint
execution assertions.

## Response-schema guardrails

- Match exact HTTP and JSON names, including casing and punctuation.
- Treat Search keys as opaque; do not parse, synthesize, or rewrite them.
- Distinguish a missing optional field from `false`, `0`, `[]`, and `{}`.
- Assert only documented top-level fields and explicitly evidenced values.
- Leave unspecified nested shapes unspecified.

## Status guardrails

The documented status safeguards are narrow: a completed synchronous Search
with no matching itinerary is `200 OK` with `results: []`, and async initiation
permits `200 OK` or `202 Accepted` without a canonical code. Poll until
`completed` is `true` before final async retrieval. Unknown, expired, or
incomplete async IDs remain unspecified, as do all other unlisted transport
statuses and error-body shapes. Do not invent status or error assertions. The
asynchronous status value and completion fields are contract data, but their
unlisted value vocabulary remains unspecified.

## Regression design

Build regression coverage around the documented observable boundaries:

- synchronous Search exposes `results[].key`; a completed no-match response is
  `200 OK` with `results: []`;
- asynchronous Search exposes its identifiers/progress fields and permits
  `200 OK` or `202 Accepted` at initiation, poll exposes completion/progress
  until `completed` is `true`, and get exposes Search-compatible results;
- each selected-itinerary endpoint independently consumes a Search key and
  exposes its documented top-level output;
- configuration discovery returns a JSON object root and is not treated as
  proof of per-request module execution.

Assertions must preserve optional-field distinctions, exact names, opaque keys,
and the unspecified-shape/status boundaries. Unknown, expired, or incomplete
async IDs, all other unlisted transport statuses, and error-body shapes remain
unspecified. Non-ticket behavior remains an `[assumption]` until an observable
ticket/spec/API observation is approved.

## Historical evidence and reuse

For ticket-scoped observations and exclusions, consult
[the evidence ledger](airapi-qa-memory.md) and [reuse guide](airapi-qa-reuse.md).
Their historical results do not expand this public contract or replace current
ticket/specification text. Consolidated 2026-10-19; no endpoint rerun implied.
