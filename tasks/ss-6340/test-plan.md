# SS-6340 — Brightsun Search → Result test plan

Release signal: Fresh Search → Result workflow not yet executed.
Scope/run: DEV | https://api.search.dev.travel-dev.com | GET /brightsun/v1/search → POST /brightsun/v1/result | plan created 2026-09-30.

Intended behavior: Result reprices the selected solution and returns updated/real-time fares before booking. keys.brightsun is additional info: retain the Result Key and any refreshed token for booking rather than reusing Search additional info. Codes 113 (price not available) and 112 (fare not available) are terminal for that selected solution.

## Run sequence

1. Run the collection's existing Search request:
   https://api.search.dev.travel-dev.com/brightsun/v1/search?tripType=RT&fl[0][o]=AMS&fl[0][d]=LHR&fl[0][dt]=2026-11-11&cabin=Y&adt=1&fl[1][o]=LHR&fl[1][d]=AMS&fl[1][dt]=2026-11-18&limit=100
2. Inspect the actual Search response and select any complete returned solution (use the first available solution for reproducibility). Save its index/location, complete JSON, prices, currency, and keys.brightsun. Preserve opaque key/token values exactly. Do not reuse the pasted static solution for this workflow.
3. POST that complete, unchanged solution object as raw JSON to https://api.search.dev.travel-dev.com/brightsun/v1/result with Content-Type: application/json. Save the exact request and response, HTTP status, and timestamp.
4. Evaluate the Result checks below. Record Search and Result prices side by side. A price change is permitted; an unchanged price is also permitted. A changed Key/token is not required by the ticket: the returned values must be used regardless of equality with Search values.
5. On success, save the complete returned keys.brightsun as brightsun_result_additional_info. Confirm the saved object exactly matches the Result object, including any refreshed token and other returned additional info. Do not merge stale Search values over the Result object.
6. If the response contains terminal code 113 or 112, clear reusable Result additional info and stop processing that selected solution. Do not retry it or proceed to booking. Save paired request/response evidence. Use known reproducing test data for the two terminal scenarios; do not manufacture invalid keys or unrelated edge cases.

## Planned test-case results

WARN below means not yet evaluated in this planned workflow; it is not an executed result. Assign PASS/FAIL/WARN from actual evidence when running.

| Test | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 Fresh selected-solution handoff | Existing AMS–LHR RT Search; 1 ADT; first complete returned solution | Result POST body exactly equals selected Search object, preserving opaque additional info | Not executed with a fresh Search | WARN |
| TC-02 Reprice selected solution | TC-01 POST body | Success response returns the selected itinerary with current fare data; capture prices.totalPrice, prices.totalTax, and currency and compare with Search without requiring a price change | Not executed with a fresh Search | WARN |
| TC-03 Result additional info | Successful TC-02 response | keys.brightsun contains a nonempty Key; use the returned object for subsequent booking preparation, preserving any returned token; stored brightsun_result_additional_info equals it exactly | Not executed with a fresh Search | WARN |
| TC-04 Price unavailable | Selected solution with reproducible code 113 | Recognize 113 as terminal; stop that solution and clear reusable Result additional info | Reproducing inventory unavailable; not executed | WARN |
| TC-05 Fare unavailable | Selected solution with reproducible code 112 | Recognize 112 as terminal; stop that solution and clear reusable Result additional info | Reproducing inventory unavailable; not executed | WARN |

Search is setup for the Result tests. If Search produces no selectable solution, mark the dependent success checks WARN and preserve its request/response evidence. For unavailable error-scenario inventory, mark those cases WARN rather than claiming coverage. Confirm error response locations from actual evidence before adding automated code-path assertions; no error path or error HTTP status is specified here.

## Existing evidence, separate from the planned workflow

A prior POST using the user-supplied static solution returned HTTP 200, GBP 187.75 total / GBP 124.75 tax, a new keys.brightsun.key, and an unchanged token. That supports this single captured Result response, not a fresh Search → Result run or error coverage.

| Test | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| Prior Result smoke request | User-supplied static AMS–LHR RT solution | Repriced solution with Result additional info | HTTP 200; fare values returned; nonempty Key/token | PASS |

Evidence: result-request.json, result-response.json, result-response-meta.json. Keep fresh Search request/response, selected solution, Result request/response, comparison values, and each FAIL/WARN request/response pair in this ticket directory. Exclude credentials and unrelated fields from reports.

No booking call is part of this plan. This validates additional info preparation only. Generate the matching HTML dispatch sheet from templates/airapi-qa-dispatch-template.html when the workflow is executed, with actual case results and embedded collection/CSV Blob downloads where downloads are offered.
