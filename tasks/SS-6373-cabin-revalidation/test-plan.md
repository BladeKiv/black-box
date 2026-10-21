# SS-6373 — Cabin revalidation

PREPROD: http://airapi51.kivops.info. Scope: AirAPI Result revalidation only.

## Intended behavior

When booking classes remain the same, preserve the original cabin if it has a value. When the original cabin is empty or null, select the cabin declared by revalidation. Source: https://traveldev.atlassian.net/browse/SS-6373.

## Test plan

| ID | Test data | Expected result |
|---|---|---|
| TC-01 | Exact ticket Result request; CPH–IST–ORD–DEN, 2027-06-30, classes Z/Z/Z; historical empty cabins and L05L C/C/C | Result cabins C/C/C; distinguish current output verification from fresh original-input verification |
| TC-02 | Fresh Search with empty segment cabins; revalidation declares values; same classes | Use declared cabins on matching segments |
| TC-03 | Fresh Search with explicit null segment cabins; revalidation declares values; same classes | Use declared cabins on matching segments |
| TC-04 | Fresh Search with populated segment cabins; same classes | Preserve original segment cabins |

For TC-02–04 retain Search and Result request/response pairs, match trips and segments by identifiers and flight details, and verify booking classes before evaluating cabin behavior. Missing qualifying inventory is WARN. Missing cabin properties are not null test data. Do not call provider or booking endpoints. Provider logs serve only as supplemental evidence.

## Historical evidence

The ticket's ELKM link uses the production index and September 29, 2026 timestamps. The original itinerary has empty cabins on all three segments and bookingClass Z. L05L LowestFarePrice logs declare cabin C for all three matching segments. Final AirAPI Result retained empty cabins. This is historical defect evidence, not a fresh PREPROD test.

## Fresh exact-request observation

The exact opaque ticket key was sent unchanged to PREPROD GET /v1/result/SALKIV/{key}. The response was HTTP 200 and returned C/C/C with Z/Z/Z. PREPROD returned a different opaque key; it has been retained exactly in exact-response.json. No key rewriting was performed by the test.

The response alone does not establish the original cabin state used by PREPROD or identify L05L as its selected routing. Fresh Search data is required for the remaining assertions.

## User scope clarification — 2026-09-30
Revalidation is identified by a change from the original GDS. TC-04b has G → G and remains WARN because it does not exercise revalidation. Null means empty for this task; TC-03 is merged into TC-02 coverage and is no longer a separate required test. The earlier separate-null plan is superseded. No additional endpoint runs were performed for this report update.

## TC-04b replacement — 2026-09-30
Three alternative mixed-cabin keys were tried. The first two remained G → G. The third changed G → S and retained C/C/F with R/R/R. This replacement supersedes the earlier TC-04b WARN; the earlier captures are retained as TC-04b-superseded-*.json. The final active matrix has four PASS cases; TC-03 stays merged into empty-cabin coverage.
