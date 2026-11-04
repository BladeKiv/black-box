SS-6436 Sabre NDC - Sabre OAuth token is never renewed after a 401 (dead retry branch, cached token never invalidated)

**PASS — 2 PASS / 0 FAIL / 0 WARN**

2026-11-02 | STAGE | Search → Result | LAX–MAD 2026-11-14 | V/8KI0 | cid=TST101 | cabin=T

Exact user-supplied Search returned HTTP 200 with 37 matching V/8KI0 offers. Result returned HTTP 200, preserving the selected opaque key and V/8KI0 identifiers, with populated itinerary segments and totalPrice=595.

Intended behavior: User-approved regression: Search returns usable V/8KI0 offers; Result resolves an unchanged matching Search key into itinerary and price data.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | LAX–MAD 2026-11-14; 1 ADT; T; V/8KI0; TST101; PUB; extra=false; debug=true | Usable V/8KI0 offers and opaque key for Result | HTTP 200; 37 offers, all V/8KI0 | PASS |
| TC-02 | Selected V/8KI0 Search key unchanged; cid=TST101 | Matching key/provider identifiers; populated itinerary and numeric price | HTTP 200; same key; V/8KI0; 1 trip with segments; totalPrice=595 | PASS |

Supporting evidence and rerun artifacts

Latest exact-input regression: one Search and one Result; no retries. extra=false, cabin=T, adt=1, debug=true, fare=PUB, cid=TST101, gds=V, pcc=8KI0. Earlier different-input attempts are retained separately and excluded from this verdict. Several inputs changed together, so the cause of earlier empty responses is not isolated. OAuth recovery is outside regression scope. No booking, ticketing or configuration changes. No lessons applied; ledger unchanged.

Collection: SS-6436.postman_collection.json; CSV: expected-outcomes.csv.
### TC-01

Request:
```json
{
  "method": "GET",
  "url": "https://api.search.stage.travel-dev.com/v1/search?extra=false&cabin=T&adt=1&debug=true&fare=PUB&cid=TST101&gds=V&pcc=8KI0&fl.0.o=LAX&fl.0.d=MAD&fl.0.dt=2026-11-14"
}
```

Response:
```json
{
  "http_status": 200,
  "results_count": 37,
  "matching_count": 37
}
```
### TC-02

Request:
```json
{
  "method": "GET",
  "url": "https://api.search.stage.travel-dev.com/v1/result/ANY/0_VFNUMTAxKlkxMDAwL0xBWE1BRDIwMjYtMTEtMTRfMTAxNypBQX4jQkE0NzkyI0JBNDI3Mn5sYzplbl91c35jdXI6VVNE?cid=TST101&gds=V&pcc=8KI0&fare=PUB&debug=true"
}
```

Response:
```json
{
  "http_status": 200,
  "same_key": true,
  "gds": "V",
  "pcc": "8KI0",
  "trips": 1,
  "totalPrice": 595
}
```
