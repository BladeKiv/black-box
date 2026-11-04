SS-6436 Sabre NDC - Sabre OAuth token is never renewed after a 401 (dead retry branch, cached token never invalidated)

**WARN — 0 PASS / 0 FAIL / 1 WARN**

2026-11-02 | STAGE | Search → Result regression | SFO–FRA 2026-11-20 | S/8D55 | cid=tst101

Search returned HTTP 200 with results: []. No offer key was available, so Result was not executed. The Search-to-Result regression remains inconclusive.

Intended behavior: User-approved regression scope: Search returns usable Sabre REST offers for gds=S, pcc=8D55, cid=tst101; Result resolves a returned opaque key unchanged into itinerary and price data.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | SFO–FRA 2026-11-20; 1 ADT; Y; S/8D55; cid=tst101; fare=PUB | Usable S/8D55 offers and opaque key for Result | HTTP 200; results: []; no Result key (NO_DATA) | WARN |

Supporting evidence and rerun artifacts

Regression only. One live Search; zero Result calls, retries or input variations. No authentication fault injection or OAuth-recovery assertions are part of this verdict. User states missing provider credentials are validated; this run did not establish provider credential configuration. No booking, ticketing or configuration changes. Sandbox refusal retained separately. No lessons applied; ledger unchanged.

Collection: SS-6436.postman_collection.json; CSV: expected-outcomes.csv.
### TC-01

Request:
```json
{
  "method": "GET",
  "url": "https://api.search.stage.travel-dev.com/v1/search?cid=tst101&gds=S&pcc=8D55&fare=PUB&adt=1&cabin=Y&fl.0.o=SFO&fl.0.d=FRA&fl.0.dt=2026-11-20"
}
```

Response:
```json
{
  "http_status": 200,
  "body": {
    "results": [],
    "starUTCTime": "2026-11-02 14:38:14.604",
    "endUTCTime": "2026-11-02 14:38:14.680",
    "excutionTime": "75.851759ms",
    "ngsMap": {},
    "messages": [
      {
        "type": "TRACEID",
        "value": "80982fb1-3461-41a5-a322-9e5995384c8d"
      }
    ]
  },
  "transport_error": null,
  "reason_code": "NO_DATA",
  "status": "WARN",
  "retryable": false
}
```
