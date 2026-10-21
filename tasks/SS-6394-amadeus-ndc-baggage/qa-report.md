Release signal: WARN
Scope/run: PREPROD | 2026-10-16 | Book/Info only | 3 existing bookings | TLS verification disabled by explicit user authorization

4 PASS / 0 FAIL / 1 WARN. All three PREPROD Book/Info calls returned HTTP 200 and JSON status 200. Explicit breakdown checks passed; numeric source parity remains inconclusive. Earlier TLS failures were superseded by this user-authorized run with certificate verification disabled.

Intended behavior: Add baggage/carryOn breakdown when available, with weights, dimensions, piece counts, and FBA/FBD/COA/COD full-text prefixes. User accepts populated source values and missing/null/empty differences from illustrative examples. PriceClass fallback and personal-item exclusion are excluded.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | AA / JCB / BFJ7RS / 2 segments | Breakdown present; checked 0P/00P; carry-on 1P; FBA/FBD/COA/COD prefixes. | Both segments expose 0P/00P, 1P, checked 50 lb/23 kg and 62 in/158 cm; carry-on 45 in/115 cm. Prefixes observed. | PASS |
| TC-02 | QR / ADT / CXTS37 / 4 segments | Checked 2P/02P breakdown and FBA/FBD prefixes; unavailable carry-on may be null. | All four segments: 2P/02P, 70 lb/32 kg, FBA/FBD text; carryOnAllowance and carryOn are null, accepted by clarification. | PASS |
| TC-03 | LX / ADT / 2L2FGK / checked baggage | Ticket checked-bag example: 1P/01P, 70 lb/32 kg, 62 in/158 cm and exact full-text values. | All checked-bag fields and both full-text values exactly match the ticket LX example. | PASS |
| TC-04 | LX / ADT / 2L2FGK / carry-on structure | Carry-on breakdown with COA/COD prefixes and piece formatting; personal-item exclusion is outside scope. | 3P, 8 kg, 46 in/118 cm, COA/COD text present. No assertion on excluding the personal item. | PASS |
| TC-05 | AA / QR / LX / numeric source mapping | Returned numeric values match corresponding provider baggage values for the live retrieval. | Fresh matching provider responses were not captured. Historical LX source text contains 18LB; live output gives weightLb=17 and COD UPTO17LB. Full numeric source parity is inconclusive. | WARN |

## Paired evidence

```json
{
  "request": {
    "method": "POST",
    "url": "https://airapi51.kivops.info:8089/ndc/v1/book/info",
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "gds": {
        "gds_id": 2,
        "gds_pcc": "SFOG3210A"
      },
      "additionalInfo": {
        "isNDC": true
      },
      "data": {
        "historical": 0,
        "pnr": "BFJ7RS",
        "rebook": 0,
        "provider_locator_code": "BFJ7RS"
      },
      "sender": {
        "action": "checkExchangeDiscrepancies",
        "component": "ExchangeSaleService",
        "app": "backoffice.backend",
        "module": "app-backend"
      }
    }
  },
  "response": {
    "httpStatus": 200,
    "status": 200,
    "name": "Success",
    "code": 0,
    "attempt_utc": "2026-10-16T12:51:44.540928+00:00",
    "tls_verification": false,
    "authorization": "[REDACTED] authorized for this PREPROD host and Book/Info tests only",
    "segments": [
      {
        "tripId": 1,
        "segmentNumber": 1,
        "baggageAllowance": "0P",
        "baggage": {
          "JCB": {
            "weightLb": 50,
            "weightKg": 23,
            "lengthInch": 62,
            "lengthCm": 158,
            "numberOfPcs": "00P",
            "baggageFullTextA": "FBA  FREE BAGGAGE ALLOWANCE 0PC",
            "baggageFullTextD": "FBD UPTO50LB 23KG AND62LI 158LCM"
          }
        },
        "carryOnAllowance": "1P",
        "carryOn": {
          "JCB": {
            "lengthInch": 45,
            "lengthCm": 115,
            "numberOfPcs": "1P",
            "baggageFullTextA": "COA  CARRYON HAND BAGGAGE ALLOWANCE1PC",
            "baggageFullTextD": "COD UP TO 1  UPTO45LI 115LCM"
          }
        }
      },
      {
        "tripId": 2,
        "segmentNumber": 1,
        "baggageAllowance": "0P",
        "baggage": {
          "JCB": {
            "weightLb": 50,
            "weightKg": 23,
            "lengthInch": 62,
            "lengthCm": 158,
            "numberOfPcs": "00P",
            "baggageFullTextA": "FBA  FREE BAGGAGE ALLOWANCE 0PC",
            "baggageFullTextD": "FBD UPTO50LB 23KG AND62LI 158LCM"
          }
        },
        "carryOnAllowance": "1P",
        "carryOn": {
          "JCB": {
            "lengthInch": 45,
            "lengthCm": 115,
            "numberOfPcs": "1P",
            "baggageFullTextA": "COA  CARRYON HAND BAGGAGE ALLOWANCE1PC",
            "baggageFullTextD": "COD UP TO 1  UPTO45LI 115LCM"
          }
        }
      }
    ]
  },
  "source_traceID": "bd61604d-c90d-11f1-aed3-960002c1e0df"
}
```

```json
{
  "request": {
    "method": "POST",
    "url": "https://airapi51.kivops.info:8089/ndc/v1/book/info",
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "gds": {
        "gds_id": 2,
        "gds_pcc": "SFOG3210A"
      },
      "additionalInfo": {
        "isNDC": true
      },
      "data": {
        "historical": 0,
        "pnr": "CXTS37",
        "rebook": 0,
        "provider_locator_code": "CXTS37"
      },
      "sender": {
        "action": "checkExchangeDiscrepancies",
        "component": "ExchangeSaleService",
        "app": "backoffice.backend",
        "module": "app-backend"
      }
    }
  },
  "response": {
    "httpStatus": 200,
    "status": 200,
    "name": "Success",
    "code": 0,
    "attempt_utc": "2026-10-16T12:51:49.053296+00:00",
    "tls_verification": false,
    "authorization": "[REDACTED] authorized for this PREPROD host and Book/Info tests only",
    "segments": [
      {
        "tripId": 1,
        "segmentNumber": 1,
        "baggageAllowance": "2P",
        "baggage": {
          "ADT": {
            "weightLb": 70,
            "weightKg": 32,
            "numberOfPcs": "02P",
            "baggageFullTextA": "FBA  FREE BAGGAGE ALLOWANCE 2PC",
            "baggageFullTextD": "FBD UP TO 2  UPTO70LB 32KG"
          }
        },
        "carryOnAllowance": null,
        "carryOn": null
      },
      {
        "tripId": 1,
        "segmentNumber": 2,
        "baggageAllowance": "2P",
        "baggage": {
          "ADT": {
            "weightLb": 70,
            "weightKg": 32,
            "numberOfPcs": "02P",
            "baggageFullTextA": "FBA  FREE BAGGAGE ALLOWANCE 2PC",
            "baggageFullTextD": "FBD UP TO 2  UPTO70LB 32KG"
          }
        },
        "carryOnAllowance": null,
        "carryOn": null
      },
      {
        "tripId": 2,
        "segmentNumber": 1,
        "baggageAllowance": "2P",
        "baggage": {
          "ADT": {
            "weightLb": 70,
            "weightKg": 32,
            "numberOfPcs": "02P",
            "baggageFullTextA": "FBA  FREE BAGGAGE ALLOWANCE 2PC",
            "baggageFullTextD": "FBD UP TO 2  UPTO70LB 32KG"
          }
        },
        "carryOnAllowance": null,
        "carryOn": null
      },
      {
        "tripId": 2,
        "segmentNumber": 2,
        "baggageAllowance": "2P",
        "baggage": {
          "ADT": {
            "weightLb": 70,
            "weightKg": 32,
            "numberOfPcs": "02P",
            "baggageFullTextA": "FBA  FREE BAGGAGE ALLOWANCE 2PC",
            "baggageFullTextD": "FBD UP TO 2  UPTO70LB 32KG"
          }
        },
        "carryOnAllowance": null,
        "carryOn": null
      }
    ]
  },
  "source_traceID": "8f7de3bb-c900-11f1-90e7-9600023dbd52"
}
```

```json
{
  "request": {
    "method": "POST",
    "url": "https://airapi51.kivops.info:8089/ndc/v1/book/info",
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "additionalInfo": {
        "isNDC": true,
        "ngs": false,
        "order_id": "LX724S9XOP5A2",
        "order_items": [
          {
            "orderItemID": "PFC6EFA5C-8A9F-4DB6-B78Akqt745cor6xi7-1-1_1APAX_T1",
            "paxRefIds": "1"
          },
          {
            "orderItemID": "PFC6EFA5C-8A9F-4DB6-B78Akqt745cor6xi7-1-1_1APAX_T2",
            "paxRefIds": "2"
          }
        ],
        "ownerCode": "LX",
        "passengers": [
          {
            "id": "1",
            "ptc": "ADT"
          },
          {
            "id": "2",
            "ptc": "ADT"
          }
        ],
        "pcc": "SFOG3210A",
        "updated_schedule": true
      },
      "data": {
        "historical": 0,
        "pnr": "2L2FGK",
        "provider_locator_code": "2L2FGK",
        "rebook": 0
      },
      "gds": {
        "backoffice_id": 3569020,
        "gds_id": 2,
        "gds_offer_id": "143_VVdLTVVTKkMyMDAwL0xBWEFUSDIwMjYtMTEtMDRfMTcxNi9WQ0VaUkgyMDI2LTExLTE1XzA5L1pSSExBWDIwMjYtMTEtMTdfMTAxNSpMSH4jTEg0NTMjTEgxNzU0I0xYMTY2MSNMWDMxOCNMWDMwNTZ+bGM6ZW5fdXM=",
        "gds_pcc": "SFOG3210A",
        "hybrid_id": "UNDE1B0A5D"
      },
      "sender": {
        "action": "RetrieveTicketCommand",
        "app": "backoffice.console",
        "component": "auto-ticketing",
        "module": "app-console"
      }
    }
  },
  "response": {
    "httpStatus": 200,
    "status": 200,
    "name": "Success",
    "code": 0,
    "attempt_utc": "2026-10-16T12:52:47.884926+00:00",
    "tls_verification": false,
    "segments": [
      {
        "tripId": 1,
        "segmentNumber": 1,
        "baggageAllowance": "1P",
        "baggage": {
          "ADT": {
            "weightLb": 70,
            "weightKg": 32,
            "lengthInch": 62,
            "lengthCm": 158,
            "numberOfPcs": "01P",
            "baggageFullTextA": "FBA  FREE BAGGAGE ALLOWANCE 1PC",
            "baggageFullTextD": "FBD UP TO 1  UPTO70LB 32KG AND62LI 158LCM"
          }
        },
        "carryOnAllowance": "3P",
        "carryOn": {
          "ADT": {
            "weightLb": 17,
            "weightKg": 8,
            "lengthInch": 46,
            "lengthCm": 118,
            "numberOfPcs": "3P",
            "baggageFullTextA": "COA  CARRYON HAND BAGGAGE ALLOWANCE3PC",
            "baggageFullTextD": "COD UP TO 3  UPTO17LB 8KG AND46LI 118LCM"
          }
        }
      }
    ]
  },
  "source_traceID": "60aed8d9-c391-11f1-9596-9600023dc4ba"
}
```

Historical source evidence is distinct from fresh PREPROD endpoint results. No Book/Create, Ticket/Create, cancellation or configuration-change endpoint was called. The earlier TLS attempts remain preserved separately. No numeric mapping PASS is inferred for AA/QR from the output itself.
