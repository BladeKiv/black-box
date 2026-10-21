# SS-6401 Search comparison plan

Source: user-supplied SS-6401 description, 2026-10-13.

Intended behavior: reduce commission CPU and allocations without changing which rules match or commissions applied. PROD is the user-approved correctness baseline.

Confirmed scope: GET /v1/search, cid=TSTCOM (user-corrected active CID); omit gds, pcc, fare and validating-carrier filters. Initial SAL103 calls remain separate preliminary evidence; those responses omitted commission_info. Both active environments expose it for TSTCOM. The user confirmed the environments use the same rule source. Check commission rule selection and applied commission output across returned consolidators and fare components. Preserve missing/null/false/zero/empty distinctions and opaque Search keys.

Proposed starting volume: 30 paired Search scenarios, three repetitions per environment (180 requests). Alternate PROD/PREPROD order between repetitions. Use matched request parameters and record timestamps. This is regression sampling, not a concurrent load test.

Comparison: match itineraries, flight dates/times, passenger mix, fare owner, booking class, cabin, fare basis, currency and fare amounts before comparing selected rules/sub-rules, contracts, commission rates/amounts, ticket-code effects and observable resulting prices. Compare every returned consolidator where corresponding fare data exists. Keep inventory-only differences separate from commission regressions; unmatched results cannot establish commission parity.

Timing: measure end-to-end response duration for every request. Inspect response fields/headers for an explicitly defined commission-processing duration. Do not label total Search time as commission time or infer CPU/allocation savings from endpoint latency. Graph paired durations and median/p95 by environment; identify errors and unequal inventory workloads separately.

Execution setup: PROD https://airsearch.api.travelinsides.com; PREPROD http://airapi51.kivops.info. User supplied authentication is passed to the runner through stdin and is not saved in artifacts. Route/passenger scenarios use normal inventory to exercise ticket-listed filters; no speculative edge cases. Ten route pairs use 2026-11-20/2026-11-30, with Y/ADT, C/ADT, and Y/ADT+CHD+INF variants. No date-boundary or unusual booking-class fixtures are claimed.

Deliverables after execution: standard AirAPI HTML/Markdown dispatch sheets with test data, expected/actual and one PASS/FAIL/WARN per executed case; importable Postman v2.1 collection; expected-outcome CSV; sanitized paired request/response evidence; timing data and graphs. Embed collection/CSV downloads in HTML using Blob downloads. Use templates/airapi-qa-dispatch-template.html. Do not update the QA ledger.

Execution status: complete; see runs/TSTCOM/ for final evidence and report. 180 planned attempts plus eight retry attempts yielded 184 HTTP 200 responses and four retained transport failures. After the user-confirmed duplicate-rule exemption for 6189/6082, ninety-four paired comparisons produce 145 PASS, 35 FAIL and eight WARN checks (two checks per pair); 90 successful pairs supply summary timing statistics. 189 commission/financial mismatches remain. USD backend/upfront passenger breakdown entries allow $3 tolerance. The user-confirmed PROD oComm bug is excluded. All Lowest sub-rule choices are accepted when other commission fields match. Equivalent duplicate rule/sub-rule choices are ignored while monetary values and other selections remain checked. Commission-service duration is observed in timing[].executionTime where process starts with 'Commission service processed '. Explicit duration units are parsed; multiple entries are summed. This is elapsed service time, not CPU.
