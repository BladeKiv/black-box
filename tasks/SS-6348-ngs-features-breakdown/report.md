# SS-6348 — ngsFeatures incorrect breakdown

Release signal: **PASS**

Run: 2026-09-22T12:13:17.6474026Z | http://airapi51.kivops.info | Search only | S/8KI0 | SFO–DVO 2026-10-23 / DVO–SFO 2026-11-24 | HTTP 200 | 3.82s

Retest on airapi51: PASS. The ticket itinerary contains 7 affected features; exact expected breakdown ["1:2","2:1"] check: PASS. Across 40 results and 560 references, 0 references are invalid in 0 results. Added 5 Searches without val_cr: 546 results, 7514 references, 0 invalid. The original retest is retained from 2026-09-22T12:13:17.6474026Z; additional run times are recorded below. Missing optional features are not counted as validated references.

Intended behavior: breakdown references identify existing trips and segments using confirmed one-based numbering. The ticket fixture expects `["1:2","2:1"]`.

| ID | Test data | Expected | Actual | Status |
|---|---|---|---|---|
| TC-01 | Ticket itinerary: PR105 / PR2813; PR2818 / PR104. S/8KI0, GTT102, 1 ADT, cabin Y, fare SR. | Affected COMFORT CLASS feature breakdowns equal ["1:2","2:1"]. | 1 matching itinerary; 7 features. Breakdown values: [["1:2", "2:1"], ["1:2", "2:1"], ["1:2", "2:1"], ["1:2", "2:1"], ["1:2", "2:1"], ["1:2", "2:1"], ["1:2", "2:1"]]. Trip IDs: [1,2]. | PASS |
| TC-02 | All 40 results from the same ticket Search; 280 features, 560 breakdown references. | Every returned breakdown reference resolves to an existing trip and segment using confirmed one-based numbering. | 0 invalid references across 0/40 results. | PASS |
| TC-03 | SFO–DVO return; 2026-10-30 / 2026-12-01. S/8KI0, GTT102, 1 ADT, Y, SR; no val_cr. | Every returned breakdown reference resolves to an existing trip and segment using one-based numbering; at least one reference is required for a conclusive check. | 60 results; 49 with breakdown references; 616 references; 0 invalid. Validating carriers: BR, PR. | PASS |
| TC-04 | LAX–DVO return; 2026-10-23 / 2026-11-24. S/8KI0, GTT102, 1 ADT, Y, SR; no val_cr. | Every returned breakdown reference resolves to an existing trip and segment using one-based numbering; at least one reference is required for a conclusive check. | 84 results; 47 with breakdown references; 691 references; 0 invalid. Validating carriers: BR, CI, CX, PR, SQ. | PASS |
| TC-05 | JFK–DVO return; 2026-10-23 / 2026-11-24. S/8KI0, GTT102, 1 ADT, Y, SR; no val_cr. | Every returned breakdown reference resolves to an existing trip and segment using one-based numbering; at least one reference is required for a conclusive check. | 54 results; 52 with breakdown references; 1355 references; 0 invalid. Validating carriers: BR, CI, CX, EY, JL, PR, QR. | PASS |
| TC-06 | SFO–MNL return; 2026-10-23 / 2026-11-24. S/8KI0, GTT102, 1 ADT, Y, SR; no val_cr. | Every returned breakdown reference resolves to an existing trip and segment using one-based numbering; at least one reference is required for a conclusive check. | 149 results; 57 with breakdown references; 1706 references; 0 invalid. Validating carriers: AA, BR, CI, CX, JL, JX, KE, NH, OZ, PR, SQ, UA. | PASS |
| TC-07 | LAX–MNL return; 2026-10-23 / 2026-11-24. S/8KI0, GTT102, 1 ADT, Y, SR; no val_cr. | Every returned breakdown reference resolves to an existing trip and segment using one-based numbering; at least one reference is required for a conclusive check. | 199 results; 125 with breakdown references; 3146 references; 0 invalid. Validating carriers: AA, BR, CA, CI, CX, DL, JL, JX, KE, MU, NH, OZ, PR, SQ, UA. | PASS |

## TC-01 and TC-02 paired request/response evidence

The following reduced response supports the current results; unrelated fields and authorization are omitted. Earlier run artifacts are preserved under runs/.

```json
{
  "request": {
    "method": "GET",
    "url": "http://airapi51.kivops.info/v1/search?fl[1][d]=SFO&adt=1&cabin=Y&fl[0][o]=SFO&fl[0][d]=DVO&fl[0][dt]=2026-10-23&fl[1][o]=DVO&fl[1][dt]=2026-11-24&cid=GTT102&gds=S&pcc=8KI0&fare=SR&debug=1&files=1&val_cr=PR&extra=false"
  },
  "response": {
    "http_status": 200,
    "body_excerpt": {
      "count": 40,
      "results": [
        {
          "key": "51_R1RUMTAyKlkxMDAwL1NGT0RWTzIwMjYtMTAtMjNfMDAwOC9EVk9TRk8yMDI2LTExLTI0XzE3MjMqUFJ+I1BSMTA1I1BSMjgxMyNQUjI4MTgjUFIxMDR+bGM6ZW5fdXM=",
          "gds": "S",
          "pcc": "8KI0",
          "cons": "GTT",
          "validatingCarrier": "PR",
          "fareType": "COMM",
          "trips": [
            {
              "tripId": 1,
              "segments": [
                {
                  "segmentId": 1,
                  "departureTime": "2026-10-23 00:30",
                  "arrivalTime": "2026-10-24 05:30",
                  "flightNumber": "105",
                  "marketingAirline": "PR",
                  "departureAirportCode": "SFO",
                  "arrivalAirportCode": "MNL"
                },
                {
                  "segmentId": 2,
                  "departureTime": "2026-10-24 08:20",
                  "arrivalTime": "2026-10-24 10:10",
                  "flightNumber": "2813",
                  "marketingAirline": "PR",
                  "departureAirportCode": "MNL",
                  "arrivalAirportCode": "DVO",
                  "brandId": "COMFCLS",
                  "brandName": "COMFORT CLASS"
                }
              ]
            },
            {
              "tripId": 2,
              "segments": [
                {
                  "segmentId": 1,
                  "departureTime": "2026-11-24 17:55",
                  "arrivalTime": "2026-11-24 19:45",
                  "flightNumber": "2818",
                  "marketingAirline": "PR",
                  "departureAirportCode": "DVO",
                  "arrivalAirportCode": "MNL",
                  "brandId": "COMFCLS",
                  "brandName": "COMFORT CLASS"
                },
                {
                  "segmentId": 2,
                  "departureTime": "2026-11-24 23:15",
                  "arrivalTime": "2026-11-24 19:45",
                  "flightNumber": "104",
                  "marketingAirline": "PR",
                  "departureAirportCode": "MNL",
                  "arrivalAirportCode": "SFO"
                }
              ]
            }
          ],
          "ngsFeatures": {
            "stars": 3,
            "name": "COMFORT CLASS",
            "list": [
              {
                "id": "11",
                "application": "F",
                "serviceType": "T",
                "tag": "CHANGE",
                "commercialName": "CHANGE FEE",
                "atpco": "055",
                "breakdown": [
                  "1:2",
                  "2:1"
                ]
              },
              {
                "id": "5",
                "application": "F",
                "serviceType": "Z",
                "tag": "MILES",
                "commercialName": "115 PERCENT MILES EARNED",
                "atpco": "06E",
                "breakdown": [
                  "1:2",
                  "2:1"
                ]
              },
              {
                "id": "27",
                "application": "C",
                "serviceType": "T",
                "tag": "REFUND",
                "commercialName": "REFUND BEFORE DEPARTURE",
                "atpco": "06K",
                "breakdown": [
                  "1:2",
                  "2:1"
                ]
              },
              {
                "id": "13",
                "application": "C",
                "serviceType": "T",
                "tag": "REFUND",
                "commercialName": "REFUND AFTER DEPARTURE",
                "atpco": "06L",
                "breakdown": [
                  "1:2",
                  "2:1"
                ]
              },
              {
                "id": "8",
                "application": "F",
                "serviceType": "M",
                "tag": "MEAL",
                "commercialName": "SNACK",
                "atpco": "0AT",
                "breakdown": [
                  "1:2",
                  "2:1"
                ]
              },
              {
                "id": "4",
                "application": "F",
                "serviceType": "Z",
                "tag": "PRIORITY",
                "commercialName": "SEAT RESERVATION",
                "atpco": "0B5",
                "breakdown": [
                  "1:2",
                  "2:1"
                ]
              },
              {
                "id": "18",
                "application": "F",
                "serviceType": "C",
                "tag": "CABIN",
                "commercialName": "CARRY7KG 15LB UPTO45LI 115LCM",
                "atpco": "0M3",
                "breakdown": [
                  "1:2",
                  "2:1"
                ]
              }
            ]
          }
        }
      ]
    }
  },
  "note": "Response excerpt; unrelated fields omitted. Key preserved exactly as returned."
}
```

Full reduced response: `search-evidence.json`. Complete invalid-reference list: `invalid-references.json`.
Rerun: `SS-6348.postman_collection.json` with `SS-6348.expected-outcomes.csv` and a locally supplied authorization variable.
Proposed fix and verification: `implementation-plan.md`.
Source: https://traveldev.atlassian.net/browse/SS-6348. The Jira attachment is historical context, not fresh execution evidence.

### TC-03 regression evidence

```json
{
  "id": "TC-03",
  "run_utc": "2026-09-22T12:18:23.8322198Z",
  "elapsed_seconds": 5.0844092,
  "request": {
    "method": "GET",
    "url": "http://airapi51.kivops.info/v1/search?fl[1][d]=SFO&adt=1&cabin=Y&fl[0][o]=SFO&fl[0][d]=DVO&fl[0][dt]=2026-10-30&fl[1][o]=DVO&fl[1][dt]=2026-12-01&cid=GTT102&gds=S&pcc=8KI0&fare=SR&debug=1&files=1&extra=false"
  },
  "response": {
    "http_status": 200,
    "by_carrier": {
      "BR": {
        "results": 21,
        "features": 70,
        "references": 70
      },
      "PR": {
        "results": 39,
        "features": 294,
        "references": 546
      }
    },
    "feature_list_states": {
      "list null": 11,
      "list populated": 49
    }
  }
}
```

### TC-04 regression evidence

```json
{
  "id": "TC-04",
  "run_utc": "2026-09-22T12:18:29.4245854Z",
  "elapsed_seconds": 5.829838,
  "request": {
    "method": "GET",
    "url": "http://airapi51.kivops.info/v1/search?fl[1][d]=LAX&adt=1&cabin=Y&fl[0][o]=LAX&fl[0][d]=DVO&fl[0][dt]=2026-10-23&fl[1][o]=DVO&fl[1][dt]=2026-11-24&cid=GTT102&gds=S&pcc=8KI0&fare=SR&debug=1&files=1&extra=false"
  },
  "response": {
    "http_status": 200,
    "by_carrier": {
      "BR": {
        "results": 39,
        "features": 35,
        "references": 35
      },
      "PR": {
        "results": 40,
        "features": 280,
        "references": 560
      },
      "CI": {
        "results": 2,
        "features": 0,
        "references": 0
      },
      "CX": {
        "results": 2,
        "features": 16,
        "references": 96
      },
      "SQ": {
        "results": 1,
        "features": 0,
        "references": 0
      }
    },
    "feature_list_states": {
      "list null": 37,
      "list populated": 47
    }
  }
}
```

### TC-05 regression evidence

```json
{
  "id": "TC-05",
  "run_utc": "2026-09-22T12:18:35.7604099Z",
  "elapsed_seconds": 6.8183644,
  "request": {
    "method": "GET",
    "url": "http://airapi51.kivops.info/v1/search?fl[1][d]=JFK&adt=1&cabin=Y&fl[0][o]=JFK&fl[0][d]=DVO&fl[0][dt]=2026-10-23&fl[1][o]=DVO&fl[1][dt]=2026-11-24&cid=GTT102&gds=S&pcc=8KI0&fare=SR&debug=1&files=1&extra=false"
  },
  "response": {
    "http_status": 200,
    "by_carrier": {
      "PR": {
        "results": 40,
        "features": 208,
        "references": 862
      },
      "EY": {
        "results": 7,
        "features": 56,
        "references": 336
      },
      "BR": {
        "results": 2,
        "features": 7,
        "references": 7
      },
      "JL": {
        "results": 1,
        "features": 2,
        "references": 12
      },
      "QR": {
        "results": 1,
        "features": 7,
        "references": 42
      },
      "CX": {
        "results": 2,
        "features": 16,
        "references": 96
      },
      "CI": {
        "results": 1,
        "features": 0,
        "references": 0
      }
    },
    "feature_list_states": {
      "list populated": 52,
      "list null": 2
    }
  }
}
```

### TC-06 regression evidence

```json
{
  "id": "TC-06",
  "run_utc": "2026-09-22T12:18:42.8173737Z",
  "elapsed_seconds": 5.2987799,
  "request": {
    "method": "GET",
    "url": "http://airapi51.kivops.info/v1/search?fl[1][d]=SFO&adt=1&cabin=Y&fl[0][o]=SFO&fl[0][d]=MNL&fl[0][dt]=2026-10-23&fl[1][o]=MNL&fl[1][dt]=2026-11-24&cid=GTT102&gds=S&pcc=8KI0&fare=SR&debug=1&files=1&extra=false"
  },
  "response": {
    "http_status": 200,
    "by_carrier": {
      "PR": {
        "results": 40,
        "features": 13,
        "references": 18
      },
      "CI": {
        "results": 7,
        "features": 0,
        "references": 0
      },
      "CX": {
        "results": 40,
        "features": 320,
        "references": 1280
      },
      "UA": {
        "results": 24,
        "features": 96,
        "references": 288
      },
      "OZ": {
        "results": 3,
        "features": 0,
        "references": 0
      },
      "BR": {
        "results": 27,
        "features": 0,
        "references": 0
      },
      "JX": {
        "results": 2,
        "features": 0,
        "references": 0
      },
      "KE": {
        "results": 2,
        "features": 10,
        "references": 40
      },
      "NH": {
        "results": 1,
        "features": 0,
        "references": 0
      },
      "SQ": {
        "results": 1,
        "features": 0,
        "references": 0
      },
      "JL": {
        "results": 1,
        "features": 2,
        "references": 8
      },
      "AA": {
        "results": 1,
        "features": 18,
        "references": 72
      }
    },
    "feature_list_states": {
      "list null": 92,
      "list populated": 57
    }
  }
}
```

### TC-07 regression evidence

```json
{
  "id": "TC-07",
  "run_utc": "2026-09-22T12:18:48.4951168Z",
  "elapsed_seconds": 8.0852887,
  "request": {
    "method": "GET",
    "url": "http://airapi51.kivops.info/v1/search?fl[1][d]=LAX&adt=1&cabin=Y&fl[0][o]=LAX&fl[0][d]=MNL&fl[0][dt]=2026-10-23&fl[1][o]=MNL&fl[1][dt]=2026-11-24&cid=GTT102&gds=S&pcc=8KI0&fare=SR&debug=1&files=1&extra=false"
  },
  "response": {
    "http_status": 200,
    "by_carrier": {
      "PR": {
        "results": 40,
        "features": 0,
        "references": 0
      },
      "CA": {
        "results": 2,
        "features": 4,
        "references": 16
      },
      "NH": {
        "results": 15,
        "features": 30,
        "references": 120
      },
      "KE": {
        "results": 33,
        "features": 225,
        "references": 720
      },
      "CI": {
        "results": 4,
        "features": 0,
        "references": 0
      },
      "OZ": {
        "results": 9,
        "features": 0,
        "references": 0
      },
      "CX": {
        "results": 22,
        "features": 176,
        "references": 704
      },
      "BR": {
        "results": 17,
        "features": 0,
        "references": 0
      },
      "DL": {
        "results": 14,
        "features": 185,
        "references": 470
      },
      "JX": {
        "results": 2,
        "features": 0,
        "references": 0
      },
      "UA": {
        "results": 35,
        "features": 210,
        "references": 948
      },
      "MU": {
        "results": 1,
        "features": 0,
        "references": 0
      },
      "AA": {
        "results": 2,
        "features": 36,
        "references": 144
      },
      "JL": {
        "results": 2,
        "features": 6,
        "references": 24
      },
      "SQ": {
        "results": 1,
        "features": 0,
        "references": 0
      }
    },
    "feature_list_states": {
      "list null": 74,
      "list populated": 125
    }
  }
}
```
