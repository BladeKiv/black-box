Release signal: PASS
Scope/run: 2026-10-01 | DEV | RT AMS–LHR | 1 ADT | Result and book/create | token / optionKeys+outboundKey+inboundKey

Intended behavior: Malformed token or offer IDs trigger service-owned Search and Match recovery. Retain airports, flight dates, airlines and flight numbers; timing changes on the same flights are accepted by the user. Match fare.checkedBaggage and exchange/refund permissions with applicability before. Booking may accept a price update from a 422 Price change response and retry once. No expired-token timing, missing-match cases or vendor payload mapping tested.

4 PASS / 0 FAIL / 0 WARN. Endpoint responses establish observable recovery and match retention; internal Search execution is not directly visible.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| result-token | RT AMS–LHR, 1 ADT; malformed token | Automatic recovery; same segments, checkedBaggage and before exchange/refund penalties | Result HTTP 200; same airports, flight dates, airlines and flight numbers; baggage flag and before penalties retained | PASS |
| result-offers | RT AMS–LHR, 1 ADT; malformed offers | Automatic recovery; same segments, checkedBaggage and before exchange/refund penalties | Result HTTP 200; same airports, flight dates, airlines and flight numbers; baggage flag and before penalties retained | PASS |
| booking-token | RT AMS–LHR, 1 ADT; malformed token | Automatic recovery; same segments, checkedBaggage and before exchange/refund penalties | Booking HTTP 200; HN8Y66 / IBE15530652; same flights, baggage flag and before penalties retained; 5-minute schedule changes accepted by user | PASS |
| booking-offers | RT AMS–LHR, 1 ADT; malformed offers | Automatic recovery; same segments, checkedBaggage and before exchange/refund penalties | Booking HTTP 200; HN8Y6C / IBE15530653; same flights, baggage flag and before penalties retained; 5-minute schedule changes accepted by user | PASS |

Evidence: .\tasks\ss-6344\runs\2026-10-01T11-51-03-476Z; payload-evidence.json contains request/response pairs with tokens redacted. Rerun via recovery.postman_collection.json and expected-outcomes.csv, with local booking_username/booking_password environment variables.

