# SS-6445 /v1/commission/rules - possibility to request specific rules

Release signal: WARN — 5 PASS / 0 FAIL / 1 WARN

2026-11-03 · DEV · 1 successful baseline GET + 6 POST lookups · no application retries

All five available-ID lookups returned exactly the requested rules and matching content under the user-approved airline-code comparator. The documented sample IDs are unavailable on DEV.

Intended behavior: POST /v1/commission/rules/search retrieves specified top-level commission rule Id values supplied in the JSON ids array.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | [8378] | Exactly requested IDs; matching rule content, comparing Marketing/Operating code membership and counts. | HTTP 200; returned [8378]; content matches. | PASS |
| TC-02 | [7839] | Exactly requested IDs; matching rule content, comparing Marketing/Operating code membership and counts. | HTTP 200; returned [7839]; content matches. | PASS |
| TC-03 | [8378, 8379] | Exactly requested IDs; matching rule content, comparing Marketing/Operating code membership and counts. | HTTP 200; returned [8378, 8379]; content matches. | PASS |
| TC-04 | [7839, 7840] | Exactly requested IDs; matching rule content, comparing Marketing/Operating code membership and counts. | HTTP 200; returned [7839, 7840]; content matches. | PASS |
| TC-05 | [8378, 7839] | Exactly requested IDs; matching rule content, comparing Marketing/Operating code membership and counts. | HTTP 200; returned [8378, 7839]; content matches. | PASS |
| TC-06 | [563, 1900] (ticket sample) | Retrieve documented sample rules when available. | HTTP 200; rules={}; neither ID is present in DEV baseline (NO_DATA). | WARN |

TC-06 paired evidence

Request:
```json
{
  "method": "POST",
  "url": "https://api.search.dev.travel-dev.com/v1/commission/rules/search",
  "body": {
    "ids": [
      563,
      1900
    ]
  }
}
```
Response:
```json
{
  "http_status": 200,
  "body": {
    "rules": {},
    "distributions": {},
    "distributionJobs": {},
    "distributionSources": {},
    "enabledGds": {},
    "repoLastUpdate": "2026-11-02 20:14"
  }
}
```

Evidence: TC-01.json through TC-05.json, ticket-example.json, baseline-network-check.json. Original strict comparisons were re-evaluated from saved responses after user approved unordered Marketing/Operating arrays; no fresh requests. All other arrays, missing fields and value types remain exact. Initial sandbox refusal is retained in baseline.json as an operational incident, superseded by the successful network-access baseline. Lessons search found none; none applied.

Excluded: malformed/empty/duplicate/unknown-ID behavior, ordering requirements, performance, other environments, flight Search and booking. No ledger update. Postman baseline is a dated snapshot.
