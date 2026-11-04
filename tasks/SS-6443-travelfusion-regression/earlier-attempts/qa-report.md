# SS-6443 — TravelFusion regression

WARN — 0 PASS / 0 FAIL / 3 WARN

STAGE | 2026-11-02 | gds=F | cid=TST101 | PCC omitted | 3 Search, 0 Result

All three STAGE Search requests returned HTTP 200 with results: []. No usable offers were available; Result was not executed. This does not verify the PROD login-defect fixes.

Intended behavior: Search supplies usable offers; Result resolves an unchanged Search key into itinerary data.

| ID | Test data | Expected | Actual | Status |
|---|---|---|---|---|
| TC-01 | LHR-DUB, 2026-11-20, 1 ADT, Y; gds=F; cid=TST101 | Usable Search offers with an opaque key | HTTP 200; results=[]; no key for Result | WARN |
| TC-02 | STN-DUB, 2026-11-20, 1 ADT, Y; gds=F; cid=TST101 | Usable Search offers with an opaque key | HTTP 200; results=[]; no key for Result | WARN |
| TC-03 | SFO-FRA, 2026-11-20, 1 ADT, Y; gds=F; cid=TST101 | Usable Search offers with an opaque key | HTTP 200; results=[]; no key for Result | WARN |

Result coverage: not executed because all three searches had no key.

### TC-01 paired evidence

```json
{
  "request": {
    "method": "GET",
    "url": "https://api.search.stage.travel-dev.com/v1/search?cid=TST101&gds=F&adt=1&cabin=Y&fl.0.o=LHR&fl.0.d=DUB&fl.0.dt=2026-11-20"
  },
  "http_status": 200,
  "transport_error": null,
  "root_fields": [
    "results",
    "starUTCTime",
    "endUTCTime",
    "excutionTime",
    "ngsMap",
    "messages"
  ],
  "results_count": 0,
  "body": {
    "results": [],
    "starUTCTime": "2026-11-02 12:33:51.506",
    "endUTCTime": "2026-11-02 12:33:51.507",
    "excutionTime": "1.154014ms",
    "ngsMap": {},
    "messages": [
      {
        "type": "TRACEID",
        "value": "62941899-d3a5-4db4-9831-6e361b0c33ec"
      }
    ]
  }
}
```

### TC-02 paired evidence

```json
{
  "request": {
    "method": "GET",
    "url": "https://api.search.stage.travel-dev.com/v1/search?cid=TST101&gds=F&adt=1&cabin=Y&fl.0.o=STN&fl.0.d=DUB&fl.0.dt=2026-11-20"
  },
  "http_status": 200,
  "transport_error": null,
  "results_count": 0,
  "body": {
    "results": [],
    "starUTCTime": "2026-11-02 12:34:27.738",
    "endUTCTime": "2026-11-02 12:34:27.738",
    "excutionTime": "271.331\u00b5s",
    "ngsMap": {},
    "messages": [
      {
        "type": "TRACEID",
        "value": "f73ec211-7a9a-441c-a5ab-cc460632f9f6"
      }
    ]
  }
}
```

No retries, polling, configuration changes, booking or ticketing. Authentication resolved at runtime using user-confirmed shared Search auth. No applicable operational lessons; no ledger changes.

### TC-03 paired evidence

```json
{
  "request": {
    "method": "GET",
    "url": "https://api.search.stage.travel-dev.com/v1/search?cid=TST101&gds=F&adt=1&cabin=Y&fl.0.o=SFO&fl.0.d=FRA&fl.0.dt=2026-11-20"
  },
  "http_status": 200,
  "transport_error": null,
  "results_count": 0,
  "body": {
    "results": [],
    "starUTCTime": "2026-11-02 12:35:58.885",
    "endUTCTime": "2026-11-02 12:35:58.885",
    "excutionTime": "301.197\u00b5s",
    "ngsMap": {},
    "messages": [
      {
        "type": "TRACEID",
        "value": "181ed6f6-7746-4b7b-90de-507fe2f344d0"
      }
    ]
  }
}
```

## Latest lowercase def/pub run — TravelFusion not verified

| ID | Test data | Expected | Actual | Status |
|---|---|---|---|---|
| TC-04 | SFO-FRA; gds=F; pcc=def; fare=pub | TravelFusion Search offer | HTTP 200; 57 offers; selected offer gds=E, pcc=2HE4 | FAIL |
| TC-05 | Selected E/2HE4 Search key | TravelFusion Result | HTTP 200; same key and prices, one trip; selected provider is E, not F | WARN |

Other offers were not evaluated for gds F. This pair cannot certify TravelFusion.

### TC-04 paired evidence

```json
{
  "request": {
    "method": "GET",
    "url": "https://api.search.stage.travel-dev.com/v1/search?cid=TST101&gds=F&pcc=def&fare=pub&adt=1&cabin=Y&fl.0.o=SFO&fl.0.d=FRA&fl.0.dt=2026-11-20"
  },
  "http_status": 200,
  "transport_error": null,
  "results_count": 57,
  "body": {
    "results": [
      {
        "key": "0_VFNUMTAxKlkxMDAwL09BS0ZSQTIwMjYtMTEtMjBfMTAxNTA3KkZJfiNXTjIzMDMjRkk2NzAjRkk1MjB+bGM6ZW5fdXN+Y3VyOlVTRDpOR1MjMQ==",
        "gds": "E",
        "pcc": "2HE4",
        "trips": [
          {
            "tripId": 1,
            "segments": [
              {
                "segmentId": 1,
                "departureTime": "2026-11-20 10:20",
                "arrivalTime": "2026-11-20 13:45",
                "stop": 0,
                "stops": null,
                "flightNumber": "2303",
                "operatingFlightNumber": "2303",
                "bookingClass": "C",
                "duration": 145,
                "departureAirportCode": "OAK",
                "departureAirportTerminal": "2",
                "arrivalAirportCode": "DEN",
                "arrivalAirportTerminal": "",
                "operatingAirline": "WN",
                "airEquipType": "7M8",
                "aircraft": "Boeing 737 MAX 8",
                "marketingAirline": "WN",
                "marriageGroup": "I",
                "mileage": 943,
                "cabin": "Y",
                "brandId": "2219422",
                "brandName": "ECONOMY STANDARD",
                "meal": "",
                "fareCode": "VO1QOOEC",
                "baggage": {
                  "ADT": {
                    "carryOn": true,
                    "carryOnSet": true,
                    "carryOnSource": "provider",
                    "airlineCode": "FI",
                    "allowPieces": 1,
                    "allowMaxWeight": "UP TO 50 POUNDS/23 KILOGRAMS",
                    "allowMaxSize": "UP TO 62 LINEAR INCHES/158 LINEAR CENTIMETERS",
                    "charge": [
                      {
                        "firstPiece": 1,
                        "lastPiece": 1,
                        "price": 130,
                        "currency": "USD"
                      }
                    ],
                    "kg": 23,
                    "lbs": 50,
                    "cm": 158,
                    "inch": 62
                  }
                },
                "recheckBaggage": false
              },
              {
                "segmentId": 2,
                "departureTime": "2026-11-20 15:40",
                "arrivalTime": "2026-11-21 06:05",
                "stop": 0,
                "stops": null,
                "flightNumber": "670",
                "operatingFlightNumber": "670",
                "bookingClass": "V",
                "duration": 445,
                "departureAirportCode": "DEN",
                "departureAirportTerminal": "",
                "arrivalAirportCode": "KEF",
                "arrivalAirportTerminal": "",
                "operatingAirline": "FI",
                "airEquipType": "7M8",
                "aircraft": "Boeing 737 MAX 8",
                "marketingAirline": "FI",
                "marriageGroup": "I",
                "mileage": 3579,
                "cabin": "Y",
                "brandId": "2219422",
                "brandName": "ECONOMY STANDARD",
                "meal": "",
                "fareCode": "VO1QOOEC",
                "baggage": {
                  "ADT": {
                    "carryOn": true,
                    "carryOnSet": true,
                    "carryOnSource": "provider",
                    "airlineCode": "FI",
                    "allowPieces": 1,
                    "allowMaxWeight": "UP TO 50 POUNDS/23 KILOGRAMS",
                    "allowMaxSize": "UP TO 62 LINEAR INCHES/158 LINEAR CENTIMETERS",
                    "charge": [
                      {
                        "firstPiece": 1,
                        "lastPiece": 1,
                        "price": 130,
                        "currency": "USD"
                      }
                    ],
                    "kg": 23,
                    "lbs": 50,
                    "cm": 158,
                    "inch": 62
                  }
                },
                "recheckBaggage": false,
                "overnightFlight": true
              },
              {
                "segmentId": 3,
                "departureTime": "2026-11-21 07:25",
                "arrivalTime": "2026-11-21 12:10",
                "stop": 0,
                "stops": null,
                "flightNumber": "520",
                "operatingFlightNumber": "520",
                "bookingClass": "V",
                "duration": 225,
                "departureAirportCode": "KEF",
                "departureAirportTerminal": "",
                "arrivalAirportCode": "FRA",
                "arrivalAirportTerminal": "3",
                "operatingAirline": "FI",
                "airEquipType": "7M9",
                "aircraft": "Boeing 737 MAX 9",
                "marketingAirline": "FI",
                "marriageGroup": "O",
                "mileage": 1486,
                "cabin": "Y",
                "brandId": "2219422",
                "brandName": "ECONOMY STANDARD",
                "meal": "",
                "fareCode": "VO1QOOEC",
                "baggage": {
                  "ADT": {
                    "carryOn": true,
                    "carryOnSet": true,
                    "carryOnSource": "provider",
                    "airlineCode": "FI",
                    "allowPieces": 1,
                    "allowMaxWeight": "UP TO 50 POUNDS/23 KILOGRAMS",
                    "allowMaxSize": "UP TO 62 LINEAR INCHES/158 LINEAR CENTIMETERS",
                    "charge": [
                      {
                        "firstPiece": 1,
                        "lastPiece": 1,
                        "price": 130,
                        "currency": "USD"
                      }
                    ],
                    "kg": 23,
                    "lbs": 50,
                    "cm": 158,
                    "inch": 62
                  }
                },
                "recheckBaggage": false
              }
            ],
            "duration": 1010,
            "airlineRating": "3",
            "baggage": {
              "carryOn": true,
              "carryOnSource": "provider",
              "allowPieces": 1,
              "allowMaxWeight": "UP TO 50 POUNDS/23 KILOGRAMS",
              "allowMaxSize": "UP TO 62 LINEAR INCHES/158 LINEAR CENTIMETERS",
              "charge": [
                {
                  "firstPiece": 1,
                  "lastPiece": 1,
                  "price": 130,
                  "currency": "USD"
                }
              ],
              "kg": 23,
              "lbs": 50,
              "cm": 158,
              "inch": 62
            }
          }
        ],
        "prices": {
          "lastTicketDate": "2026-11-05",
          "totalPrice": 981.3,
          "totalTax": 186.3,
          "comm": 0,
          "isCk": false,
          "markupId": 142309,
          "markupUid": "0eedfe8d-b4e4-4d85-a44f-0c85b13e9e51",
          "markup": 1,
          "oMarkup": {
            "amount": 1,
            "currency": "USD"
          }
        }
      }
    ]
  }
}
```

### TC-05 paired evidence

```json
{
  "request": {
    "method": "GET",
    "url": "https://api.search.stage.travel-dev.com/v1/result/ANY/0_VFNUMTAxKlkxMDAwL09BS0ZSQTIwMjYtMTEtMjBfMTAxNTA3KkZJfiNXTjIzMDMjRkk2NzAjRkk1MjB%2BbGM6ZW5fdXN%2BY3VyOlVTRDpOR1MjMQ%3D%3D?cid=TST101&gds=F&pcc=def&fare=pub"
  },
  "http_status": 200,
  "transport_error": null,
  "root_fields": [
    "key",
    "url",
    "routingId",
    "gdsOfferId",
    "priceElement",
    "prices",
    "passengers",
    "penalties",
    "trips",
    "maxSeats",
    "paxCnt",
    "validatingCarrier",
    "gds",
    "pcc",
    "cons",
    "fareType",
    "tripType",
    "cabin",
    "currency",
    "currencySymbol",
    "currencies",
    "currencyRates",
    "founded_dt",
    "keys",
    "ngsItineraries",
    "ngsFeatures",
    "meta",
    "products"
  ],
  "body": {
    "key": "0_VFNUMTAxKlkxMDAwL09BS0ZSQTIwMjYtMTEtMjBfMTAxNTA3KkZJfiNXTjIzMDMjRkk2NzAjRkk1MjB+bGM6ZW5fdXN+Y3VyOlVTRDpOR1MjMQ==",
    "gds": "E",
    "pcc": "2HE4",
    "trips": [
      {
        "tripId": 1,
        "segments": [
          {
            "segmentId": 1,
            "departureTime": "2026-11-20 10:20",
            "arrivalTime": "2026-11-20 13:45",
            "stop": 0,
            "stops": null,
            "flightNumber": "2303",
            "operatingFlightNumber": "2303",
            "bookingClass": "C",
            "duration": 145,
            "departureAirportCode": "OAK",
            "departureAirportTerminal": "2",
            "arrivalAirportCode": "DEN",
            "arrivalAirportTerminal": "",
            "operatingAirline": "WN",
            "airEquipType": "7M8",
            "aircraft": "Boeing 737 MAX 8",
            "marketingAirline": "WN",
            "marriageGroup": "I",
            "mileage": 943,
            "cabin": "Y",
            "brandId": "2219422",
            "brandName": "ECONOMY STANDARD",
            "meal": "",
            "fareCode": "VO1QOOEC",
            "baggage": {
              "ADT": {
                "carryOn": true,
                "carryOnSet": true,
                "carryOnSource": "provider",
                "airlineCode": "FI",
                "allowPieces": 1,
                "allowMaxWeight": "UP TO 50 POUNDS/23 KILOGRAMS",
                "allowMaxSize": "UP TO 62 LINEAR INCHES/158 LINEAR CENTIMETERS",
                "charge": [
                  {
                    "firstPiece": 1,
                    "lastPiece": 1,
                    "price": 130,
                    "currency": "USD"
                  }
                ],
                "kg": 23,
                "lbs": 50,
                "cm": 158,
                "inch": 62
              }
            },
            "recheckBaggage": false
          },
          {
            "segmentId": 2,
            "departureTime": "2026-11-20 15:40",
            "arrivalTime": "2026-11-21 06:05",
            "stop": 0,
            "stops": null,
            "flightNumber": "670",
            "operatingFlightNumber": "670",
            "bookingClass": "V",
            "duration": 445,
            "departureAirportCode": "DEN",
            "departureAirportTerminal": "",
            "arrivalAirportCode": "KEF",
            "arrivalAirportTerminal": "",
            "operatingAirline": "FI",
            "airEquipType": "7M8",
            "aircraft": "Boeing 737 MAX 8",
            "marketingAirline": "FI",
            "marriageGroup": "I",
            "mileage": 3579,
            "cabin": "Y",
            "brandId": "2219422",
            "brandName": "ECONOMY STANDARD",
            "meal": "",
            "fareCode": "VO1QOOEC",
            "baggage": {
              "ADT": {
                "carryOn": true,
                "carryOnSet": true,
                "carryOnSource": "provider",
                "airlineCode": "FI",
                "allowPieces": 1,
                "allowMaxWeight": "UP TO 50 POUNDS/23 KILOGRAMS",
                "allowMaxSize": "UP TO 62 LINEAR INCHES/158 LINEAR CENTIMETERS",
                "charge": [
                  {
                    "firstPiece": 1,
                    "lastPiece": 1,
                    "price": 130,
                    "currency": "USD"
                  }
                ],
                "kg": 23,
                "lbs": 50,
                "cm": 158,
                "inch": 62
              }
            },
            "recheckBaggage": false,
            "overnightFlight": true
          },
          {
            "segmentId": 3,
            "departureTime": "2026-11-21 07:25",
            "arrivalTime": "2026-11-21 12:10",
            "stop": 0,
            "stops": null,
            "flightNumber": "520",
            "operatingFlightNumber": "520",
            "bookingClass": "V",
            "duration": 225,
            "departureAirportCode": "KEF",
            "departureAirportTerminal": "",
            "arrivalAirportCode": "FRA",
            "arrivalAirportTerminal": "3",
            "operatingAirline": "FI",
            "airEquipType": "7M9",
            "aircraft": "Boeing 737 MAX 9",
            "marketingAirline": "FI",
            "marriageGroup": "O",
            "mileage": 1486,
            "cabin": "Y",
            "brandId": "2219422",
            "brandName": "ECONOMY STANDARD",
            "meal": "",
            "fareCode": "VO1QOOEC",
            "baggage": {
              "ADT": {
                "carryOn": true,
                "carryOnSet": true,
                "carryOnSource": "provider",
                "airlineCode": "FI",
                "allowPieces": 1,
                "allowMaxWeight": "UP TO 50 POUNDS/23 KILOGRAMS",
                "allowMaxSize": "UP TO 62 LINEAR INCHES/158 LINEAR CENTIMETERS",
                "charge": [
                  {
                    "firstPiece": 1,
                    "lastPiece": 1,
                    "price": 130,
                    "currency": "USD"
                  }
                ],
                "kg": 23,
                "lbs": 50,
                "cm": 158,
                "inch": 62
              }
            },
            "recheckBaggage": false
          }
        ],
        "duration": 1010,
        "airlineRating": "3",
        "baggage": {
          "carryOn": true,
          "carryOnSource": "provider",
          "allowPieces": 1,
          "charge": [
            {
              "firstPiece": 1,
              "lastPiece": 1,
              "price": 130,
              "currency": "USD"
            }
          ],
          "kg": 23,
          "lbs": 50,
          "cm": 158,
          "inch": 62
        }
      }
    ],
    "prices": {
      "lastTicketDate": "2026-11-05",
      "totalPrice": 981.3,
      "totalTax": 186.3,
      "comm": 0,
      "isCk": false,
      "markupId": 142309,
      "markupUid": "0eedfe8d-b4e4-4d85-a44f-0c85b13e9e51",
      "markup": 1,
      "oMarkup": {
        "amount": 1,
        "currency": "USD"
      }
    }
  }
}
```
