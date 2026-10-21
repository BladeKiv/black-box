# AirAPI Black-Box QA Agent Design

## Purpose

Create a project-local, automatically applied QA agent for AirAPI tickets and specifications. It must derive testable behavior only from ticket text, public HTTP/JSON contracts, and confirmed project knowledge. It must never inspect or infer from application source code.

## Scope and boundaries

- Covers Search, asynchronous Search, Result, NGS Air Pricing, AllFares, and read-only `algo.conf` discovery.
- Covers provider/aggregator regression analysis and Postman/Newman artifacts.
- Excludes booking and configuration mutation.
- Treats Search itinerary keys as opaque values: preserve and reuse them unchanged.
- Labels every behavior not supported by the ticket or contract as `[assumption]`; explicit contract gaps remain gaps rather than invented assertions.

## Components

### `AGENTS.md`

Repository-level activation rules recognize AirAPI QA, test plans, regression reports, Postman/Newman collections, endpoint-contract questions, and ticket reviews. The rules direct the agent to load the knowledge reference before answering and to use the durable ledger only as confirmed supplemental evidence.

### `knowledge/airapi-contract.md`

A concise contract reference distilled from `airapi-technical-reference.pdf`. It records evidence labels, endpoint dependencies, request and response invariants, documented status boundaries, and schema facts relevant to black-box assertions. It retains ambiguity instead of filling it with guesses.

### `knowledge/airapi-qa-memory.md`

A versioned evidence ledger. Each entry records date, source, scope, confirmed observation, and regression consequence. The agent may propose additions after completing a ticket, but writes only when the user explicitly approves the exact addition. Assumptions and open questions cannot be entered as confirmed memory.

### `templates/`

Reusable report and Postman/Newman guidance. The agent uses Track A for provider-level evidence only when a provider contract endpoint/payload is supplied, and Track B for AirAPI aggregation. Where inventory is variable, it uses expected-outcome CSV data and does not assert a particular offer exists.

## Behavior flow

1. Classify the input as ticket/spec, API observation, or follow-up.
2. Load the contract reference and relevant confirmed ledger entries.
3. Extract explicit requirements and separately list assumptions, unknowns, and evidence gaps.
4. Design happy-path, negative, edge, provider-specific, async/downstream, and airport-fallback regression tests where applicable.
5. Deliver a markdown QA report plus an importable Postman collection. Do not access application source code.
6. Stop for manual review. Only after explicit approval, preview a proposed ledger change; write it only after a second explicit approval.

## Key contract safeguards

- A completed Search without an offer is `200` with `results: []`; it is not a functional failure.
- Async initiation may be `200` or `202`; poll until `completed: true`; final retrieval must use the Search results shape.
- Result, NGS Air Pricing, and AllFares are sibling consumers of a Search key. One is never made a prerequisite for another.
- Do not generalize status/error bodies where the reference marks them unspecified.
- `GET /algo/conf` is read-only discovery. Its response cannot prove a module ran for a request.

## Verification

- Confirm `AGENTS.md` points to existing knowledge and template files.
- Confirm the contract reference preserves endpoint names and explicit uncertainty boundaries from the PDF.
- Confirm the durable ledger accepts only the approved entry format and includes no unconfirmed behavior.
- Perform a dry-run prompt check: an AirAPI ticket produces a black-box QA report/collection plan and refuses source-code inspection or unapproved memory writes.
