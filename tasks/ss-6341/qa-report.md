Release signal: PASS
Scope/run: 2026-10-01 | DEV | booking only | 5 new scenarios + 1 earlier captured booking | OW / RT / MC | economy

Intended behavior: POST /brightsun/v1/book/create returns HTTP 200 and booking references data.additionalInfo.recLoc and brightsunReference. On HTTP 422 Price change, update only trip.total_price from data.response.total_price and resubmit once. Search and Result supply fresh booking data only. TC-07 vendor mapping is excluded pending user clarification.

6 PASS / 0 FAIL / 0 WARN. One row retains earlier executed booking evidence; five rows are additional live scenarios. Each row represents a booking scenario, including any price retry.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| rt-adt-chd-inf | RT; ADT 1 / CHD 1 / INF 1 | Booking HTTP 200; PNR and Brightsun reference returned; on 422 Price change update price and resend once | HTTP 422 → 200; HN8X2F; IBE15530644; 569.55 GBP | PASS |
| ow-1adt | OW; ADT 1 / CHD 0 / INF 0 | Booking HTTP 200; PNR and Brightsun reference returned; on 422 Price change update price and resend once | HTTP 200; HN8X4W; IBE15530645; 118.5 GBP | PASS |
| rt-2adt | RT; ADT 2 / CHD 0 / INF 0 | Booking HTTP 200; PNR and Brightsun reference returned; on 422 Price change update price and resend once | HTTP 200; HN8X52; IBE15530646; 385.5 GBP | PASS |
| ow-adt-chd | OW; ADT 1 / CHD 1 / INF 0 | Booking HTTP 200; PNR and Brightsun reference returned; on 422 Price change update price and resend once | HTTP 200; HN8X57; IBE15530647; 237 GBP | PASS |
| rt-adt-inf | RT; ADT 1 / CHD 0 / INF 1 | Booking HTTP 200; PNR and Brightsun reference returned; on 422 Price change update price and resend once | HTTP 422 → 200; HN8X59; IBE15530648; 379.7 GBP | PASS |
| mc-2adt | MC; ADT 2 / CHD 0 / INF 0 | Booking HTTP 200; PNR and Brightsun reference returned; on 422 Price change update price and resend once | HTTP 200; HN8X5G; IBE15530649; 1356.6 GBP | PASS |

Evidence and rerun: booking-scenarios.json records evidence paths and provenance; booking-payloads.json contains full request/response pairs with session tokens redacted. Set local Postman Basic Auth environment variables booking_username and booking_password; run with expected-outcomes.csv. No Search/Result assertions; TC-07 excluded.

All booking scenarios conclusively evaluated.
