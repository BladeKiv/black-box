# Reusing AirAPI QA evidence

Updated 2026-10-19 under explicit user knowledge/memory consolidation authorization.

## Start here

Read AGENTS.md, [contract](airapi-contract.md), and [ledger](airapi-qa-memory.md).
Find the named report and request/response evidence before reusing an assertion.
Ticket/spec text defines intended behavior; historical observations do not create
new contract requirements. Old dates, routes, hosts, rules, CIDs, PCCs and inventory
are historical fixtures. Verify current prerequisites without changing configuration.
Reuse assertions and artifact structure, not old credentials, tokens or Search keys.
Booking permission and TLS exceptions from old tasks never authorize a new run.

## Preparation workflow

Follow [AGENTS.md preparation before testing](../AGENTS.md#preparation-before-testing)
in order: user-selected environment; discover its Search host and secure runtime
authentication source from existing context; prepare at least five in-scope
Search examples; understand the endpoint flow; then execute the ticket's testing
sequence. The preparation workflow was confirmed by the user on 2026-10-27.
Explicit ticket limits and existing permission boundaries continue to apply.

## Reusable assertion lessons

- Baggage: correlate fresh source evidence by retrieval traceID and associated
  segment/passenger type. Check every supplied quantity, weight, dimension and
  text field. Structure/prefix checks alone do not prove numeric parity. Source
  absence equivalence requires ticket approval; supplied-but-unmapped fields
  remain defects. SS-6394 pound recalculation and QF restrictive 105 cm choice
  are scoped approvals, not universal conversions.
- Cabin: establish the required GDS transition before evaluating revalidation.
  Refresh original Search snapshots and opaque keys together.
- Commission: inspect every exposed passenger/consolidator and fare component.
  Missing commissions is not explicit zero; aggregate zero may coexist with a
  non-deductable fee. Compare matched exposed inputs and state unmatched inventory.
  Use SS-6401 ticket-scope.md for exact tolerances, duplicate handling and rule
  equivalences; never generalize them to another ticket, OD or currency.
- Features: resolve every populated one-based trip:segment reference against the
  actual response. Missing/null/empty feature data does not establish coverage.
- Schedules: lower scores precede time tie-breaks. Keep synthetic fixture results,
  live schedule checks, configuration observations and user sign-offs distinct.
- Upgrade baggage: SS-6408 identifies parents through keys.upgrade_info and pieces
  through keys.baggage.allowPieces. Both-flags behavior requires paired variants,
  distinct keys and retained flight/fare fields. Confirm targeted rule prerequisites
  and usable inventory before evaluating endpoint behavior.
- Brightsun: preserve selected Search objects and complete returned additional
  info. Price-change retry and recovery matching approvals are ticket-scoped.
  Endpoint success does not independently prove internal Search execution.

## Execution and reporting

Execute ticket-stated or user-approved cases only. Configuration and inventory
discovery are setup evidence, not functional PASS. PASS means expectation observed,
FAIL means contradiction, WARN means required access/data/inventory unavailable.
Keep executed PASS distinct from explicit user-sign-off PASS. A TLS failure before
an application response is inconclusive; old TLS exceptions are not standing policy.

Store report, Postman collection, expected-outcome CSV and sanitized evidence in
 tasks/<task-slug>/, with subsequent runs in separate dated directories. Use
 templates/airapi-qa-dispatch-template.html for HTML; embed actual collection/CSV
bytes for Blob downloads. Reports need intended behavior and test data, expected,
actual and status columns; FAIL/WARN need paired request/response evidence.
Keep public reports concise and supporting evidence complete. Preserve exact HTTP
and JSON spelling, opaque Search keys, and missing/null/false/0/[]/{} distinctions
unless a ticket explicitly approves a narrow equivalence. Unknown paths require
live clarification, never guessed assertions.

Release folders hold confirmed report copies; release sign-off does not erase
older task failures. Wall-clock timings cannot establish CPU/allocation savings.
