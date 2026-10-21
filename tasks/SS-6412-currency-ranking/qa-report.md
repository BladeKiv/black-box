# SS-6412 - Currency ranking

**Release signal: WARN | 0 PASS / 0 FAIL / 3 WARN**

2026-10-21 | STAGE1 | GET /v1/search | Ticket route and USD/GBP/INR | TLS verification disabled by standing authorization.

All three authenticated STAGE1 searches returned HTTP 200 with results: []. No matching itineraries were available to evaluate currency ranking. The ticket fix remains unverified.

**Intended behavior:** Keep the itinerary-quality price anchor in USD while applying currencyRates and the requested currency. Compare the same search in USD, GBP and INR; review observed rank differences with the user allowing ties.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | USD; OVA101; EWR-LGW; 2026-12-14; 1 ADT; Y; limit=50 | Comparable itineraries for currency-ranking observation | HTTP 200; results: []; no ranking comparison possible | WARN |
| TC-02 | GBP; OVA101; EWR-LGW; 2026-12-14; 1 ADT; Y; limit=50 | Comparable itineraries for currency-ranking observation | HTTP 200; results: []; no ranking comparison possible | WARN |
| TC-03 | INR; OVA101; EWR-LGW; 2026-12-14; 1 ADT; Y; limit=50 | Comparable itineraries for currency-ranking observation | HTTP 200; results: []; no ranking comparison possible | WARN |

## Supporting evidence

### TC-01

Request
```json
{
  "method": "GET",
  "url": "https://api.search.stage1.travel-dev.com/v1/search?cid=OVA101&original_cid=1&adt=1&debug=true&cabin=Y&fl%5B0%5D%5Bo%5D=EWR&fl%5B0%5D%5Bd%5D=LGW&fl%5B0%5D%5Bdt%5D=2026-12-14&currency=USD&limit=50",
  "headers": {
    "Authorization": "[REDACTED]",
    "Accept": "application/json"
  }
}
```

Response
```json
{
  "results": [],
  "starUTCTime": "2026-10-21 09:37:24.138",
  "endUTCTime": "2026-10-21 09:37:24.156",
  "excutionTime": "17.889849ms",
  "timing": [
    {
      "process": "Full process",
      "starUTCTime": "2026-10-21 09:37:24.138",
      "endUTCTime": "2026-10-21 09:37:24.156",
      "executionTime": "17.892919ms"
    }
  ],
  "ngsMap": {},
  "messages": [
    {
      "type": "TRACEID",
      "value": "bdeb8818-956f-47c2-b653-5409d82113d4"
    }
  ]
}
```

### TC-02

Request
```json
{
  "method": "GET",
  "url": "https://api.search.stage1.travel-dev.com/v1/search?cid=OVA101&original_cid=1&adt=1&debug=true&cabin=Y&fl%5B0%5D%5Bo%5D=EWR&fl%5B0%5D%5Bd%5D=LGW&fl%5B0%5D%5Bdt%5D=2026-12-14&currency=GBP&limit=50",
  "headers": {
    "Authorization": "[REDACTED]",
    "Accept": "application/json"
  }
}
```

Response
```json
{
  "results": [],
  "starUTCTime": "2026-10-21 09:37:24.705",
  "endUTCTime": "2026-10-21 09:37:24.706",
  "excutionTime": "444.802\u00c2\u00b5s",
  "timing": [
    {
      "process": "Full process",
      "starUTCTime": "2026-10-21 09:37:24.705",
      "endUTCTime": "2026-10-21 09:37:24.706",
      "executionTime": "446.765\u00c2\u00b5s"
    }
  ],
  "ngsMap": {},
  "messages": [
    {
      "type": "TRACEID",
      "value": "9f5e362a-078e-4ca3-96df-c76f417a5940"
    }
  ]
}
```

### TC-03

Request
```json
{
  "method": "GET",
  "url": "https://api.search.stage1.travel-dev.com/v1/search?cid=OVA101&original_cid=1&adt=1&debug=true&cabin=Y&fl%5B0%5D%5Bo%5D=EWR&fl%5B0%5D%5Bd%5D=LGW&fl%5B0%5D%5Bdt%5D=2026-12-14&currency=INR&limit=50",
  "headers": {
    "Authorization": "[REDACTED]",
    "Accept": "application/json"
  }
}
```

Response
```json
{
  "results": [],
  "starUTCTime": "2026-10-21 09:37:25.236",
  "endUTCTime": "2026-10-21 09:37:25.237",
  "excutionTime": "462.789\u00c2\u00b5s",
  "timing": [
    {
      "process": "Full process",
      "starUTCTime": "2026-10-21 09:37:25.236",
      "endUTCTime": "2026-10-21 09:37:25.237",
      "executionTime": "464.897\u00c2\u00b5s"
    }
  ],
  "ngsMap": {},
  "messages": [
    {
      "type": "TRACEID",
      "value": "9001b3b7-430d-4f69-a43d-6203026293cc"
    }
  ]
}
```

Historical Jira attachments confirm the original example ranks 5/1/26 and 1/5/8 across USD/GBP/INR. This is historical evidence, not a fresh fix verdict. See evidence/historical-attachment-ranks.json.

Rerun: import SS-6412.postman_collection.json and expected-outcomes.csv; populate search_authorization locally; disable TLS verification. Run CSV order USD, GBP, INR. The collection records exact-key rank differences for tie review, and skips the ranking verdict when inventory is empty. Assertion results for response structure are not a functional ranking PASS. No application source, configuration or bookings changed; ledger unchanged.
