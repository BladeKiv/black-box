SS-6436 Sabre NDC - Sabre OAuth token is never renewed after a 401 (dead retry branch, cached token never invalidated)

**WARN — 0 PASS / 0 FAIL / 4 WARN**

2026-11-02 | STAGE | Search → Result regression | SFO–FRA, LAX–LHR, LAX–MAD | V/8Ki0 | cid=tst101

Four V/8Ki0 Searches returned HTTP 200 with results: [], including a fresh LAX-LHR request with explicit fare=PUB. No offer key was available for Result.

Intended behavior: User-approved regression scope: Search returns usable Sabre NDC offers for gds=V, pcc=8Ki0, cid=tst101; Result resolves a returned opaque key unchanged into itinerary and price data.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | SFO–FRA 2026-11-20; 1 ADT; Y; V/8Ki0; cid=tst101; fare=PUB | Usable V/8Ki0 offers and opaque key for Result | HTTP 200; results: []; no Result key (NO_DATA) | WARN |
| TC-02 | LAX-LHR-2027-01-15; 1 ADT; Y; V/8Ki0; cid=tst101; fare=PUB | Usable V/8Ki0 offers and opaque key for Result | HTTP 200; results: []; no Result key (NO_DATA) | WARN |
| TC-03 | LAX-MAD-2027-02-15; 1 ADT; Y; V/8Ki0; cid=tst101; fare=PUB | Usable V/8Ki0 offers and opaque key for Result | HTTP 200; results: []; no Result key (NO_DATA) | WARN |
| TC-04 | Fresh LAX-LHR 2027-01-15; V/8Ki0; cid=tst101; fare=PUB; Y; 1 ADT | Usable V/8Ki0 offers and key for Result | HTTP 200; results: []; NO_DATA | WARN |

Supporting evidence and rerun artifacts

Four V/8Ki0 Search steps total, including one user-requested repeated-input retest; zero Result calls. fare=PUB was present in all four requests. Project max_steps=4 reached. Earlier S/8D55 evidence archived separately. Regression only; no fault injection, booking, ticketing or configuration changes. No lessons applied; ledger unchanged.

Collection: SS-6436.postman_collection.json; CSV: expected-outcomes.csv.
### TC-01

Request:
```json
{
  "method": "GET",
  "url": "https://api.search.stage.travel-dev.com/v1/search?cid=tst101&gds=V&pcc=8Ki0&fare=PUB&adt=1&cabin=Y&fl.0.o=SFO&fl.0.d=FRA&fl.0.dt=2026-11-20"
}
```

Response:
```json
{
  "http_status": 200,
  "body": {
    "results": [],
    "starUTCTime": "2026-11-02 14:45:37.408",
    "endUTCTime": "2026-11-02 14:45:37.437",
    "excutionTime": "28.577456ms",
    "ngsMap": {},
    "messages": [
      {
        "type": "TRACEID",
        "value": "3ea0222b-1e29-45a4-9ba0-7c0f7eeee07d"
      }
    ]
  },
  "transport_error": null,
  "reason_code": "NO_DATA",
  "status": "WARN",
  "retryable": false
}
```
### TC-02

Request:
```json
{
  "method": "GET",
  "url": "https://api.search.stage.travel-dev.com/v1/search?cid=tst101&gds=V&pcc=8Ki0&fare=PUB&adt=1&cabin=Y&fl.0.o=LAX&fl.0.d=LHR&fl.0.dt=2027-01-15"
}
```

Response:
```json
{
  "http_status": 200,
  "body": {
    "results": [],
    "starUTCTime": "2026-11-02 14:52:36.087",
    "endUTCTime": "2026-11-02 14:52:36.116",
    "excutionTime": "28.550694ms",
    "ngsMap": {},
    "messages": [
      {
        "type": "TRACEID",
        "value": "bda05637-7a2e-4ba1-94f4-61e4d64972bd"
      }
    ]
  },
  "transport_error": null,
  "reason_code": "NO_DATA",
  "status": "WARN",
  "retryable": false
}
```
### TC-03

Request:
```json
{
  "method": "GET",
  "url": "https://api.search.stage.travel-dev.com/v1/search?cid=tst101&gds=V&pcc=8Ki0&fare=PUB&adt=1&cabin=Y&fl.0.o=LAX&fl.0.d=MAD&fl.0.dt=2027-02-15"
}
```

Response:
```json
{
  "http_status": 200,
  "body": {
    "results": [],
    "starUTCTime": "2026-11-02 14:52:36.723",
    "endUTCTime": "2026-11-02 14:52:36.726",
    "excutionTime": "2.878343ms",
    "ngsMap": {},
    "messages": [
      {
        "type": "TRACEID",
        "value": "991a2268-1ad6-43cc-95fe-2dfbaac863c9"
      }
    ]
  },
  "transport_error": null,
  "reason_code": "NO_DATA",
  "status": "WARN",
  "retryable": false
}
```
### TC-04

Request:
```json
{
  "method": "GET",
  "url": "https://api.search.stage.travel-dev.com/v1/search?cid=tst101&gds=V&pcc=8Ki0&fare=PUB&adt=1&cabin=Y&fl.0.o=LAX&fl.0.d=LHR&fl.0.dt=2027-01-15"
}
```

Response:
```json
{
  "http_status": 200,
  "body": {
    "results": [],
    "starUTCTime": "2026-11-02 14:57:23.816",
    "endUTCTime": "2026-11-02 14:57:23.819",
    "excutionTime": "3.297191ms",
    "ngsMap": {},
    "messages": [
      {
        "type": "TRACEID",
        "value": "83c26de7-53cc-41cc-9f47-4d0c6b89d06c"
      }
    ]
  },
  "transport_error": null,
  "reason_code": "NO_DATA",
  "status": "WARN",
  "retryable": false
}
```
