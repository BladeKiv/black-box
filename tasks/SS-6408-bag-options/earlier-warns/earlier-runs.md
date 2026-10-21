WARN — SS-6408 upgrade behavior inconclusive
STAGE | 2026-10-19 | Search | TST103 | FRA-AMS | 2026-11-20 | OW | 1 ADT | cabin Y

Intended behavior: When both upgrades can be created, return the 1-piece main itinerary and a uniquely keyed 2-piece ngsItineraries child; baggage allowance and price differ.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | TST103; FRA-AMS; 2026-11-20; secondBag=true and keepBothBagOptions=true supplied by user | When both upgrades can be created, return the 1-piece main itinerary and a uniquely keyed 2-piece ngsItineraries child; baggage allowance and price differ. | HTTP 200; results: []; ngsMap: {}. No eligible itinerary available to evaluate upgrades. Timing lists S/G9MJ/PUB and K/DEF/PUB, not the supplied upgrade-config jobs. | WARN |

Request: GET https://api.search.stage.travel-dev.com/v1/search?extra=false&adt=1&debug=true&cid=TST103&fl.0.dt=2026-11-20&cabin=Y&fl.0.o=FRA&fl.0.d=AMS
Authorization omitted. No request body.

Response (relevant): HTTP 200; {"results":[],"ngsMap":{},"messages":[{"type":"TRACEID","value":"9f81b750-cfba-4860-9e0a-fce391a9c269"}]}

Supporting evidence: search-response.json contains the complete response. Configuration was not changed; supplied configuration is not proof of per-request execution. This run does not validate rule 141067 execution or baggage upgrades.

Corrected run (user-specified job and cabin):

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-02 | TST103; FRA-AMS; 2026-11-20; cabin=C; gds=S; pcc=6NVG; fare=PUB | Business upgrade options: 1-piece main and 2-piece ngsItineraries child when both can be created | HTTP 200; results: []; no supplier-search job listed in timing; upgrade behavior inconclusive | WARN |

Request: GET https://api.search.stage.travel-dev.com/v1/search?extra=false&adt=1&debug=true&cid=TST103&fl.0.dt=2026-11-20&cabin=C&fl.0.o=FRA&fl.0.d=AMS&gds=S&pcc=6NVG&fare=PUB
Authorization omitted; no body.
Response: HTTP 200; results: []; ngsMap: {}. Complete paired evidence: search-business-url.txt and search-business-response.json.
The earlier cabin=Y run does not represent the intended business-upgrade retrieval.

TST101 inventory discovery (does not validate upgrade behavior):

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-03 | TST101; FRA-AMS; 2026-11-20; cabin=C; S/6NVG/PUB | Determine whether Search returns inventory | HTTP 200; 198 results; timing confirms RestBargainFinderMaxRQ S_6NVG_PUB_2026-11-20_0 | PASS |

GET https://api.search.stage.travel-dev.com/v1/search?extra=false&adt=1&debug=true&cid=TST101&fl.0.dt=2026-11-20&cabin=C&fl.0.o=FRA&fl.0.d=AMS&gds=S&pcc=6NVG&fare=PUB
Evidence: search-TST101-response.json. TRACEID db02a383-50d1-4174-a0c0-59603b70e935. Inventory PASS only; rule 141067 and dual-bag upgrades remain unverified.

Post-change rerun:

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-04 | TST101; FRA-AMS; 2026-11-20; C; S/6NVG/PUB; user updated rule/config | When both upgrades can be created, 1-piece main and uniquely keyed 2-piece child | HTTP 200; 199 results; 27 validatingCarrier=LH; cons counts GTT=2 and VZU=197; no cons=UPG and no results[].ngsItineraries. Requested S/6NVG/PUB is present in timing. Upgrade rule execution remains unverified. | WARN |

Request: GET https://api.search.stage.travel-dev.com/v1/search?extra=false&adt=1&debug=true&cid=TST101&fl.0.dt=2026-11-20&cabin=C&fl.0.o=FRA&fl.0.d=AMS&gds=S&pcc=6NVG&fare=PUB
Authorization omitted; body none.
Response evidence: search-TST101-updated-response.json (full response). TRACEID 9dda6847-d59c-4d09-a93e-5c6aec3490b0. No qualifying upgraded itinerary identified; feature cannot be conclusively evaluated.


Correction: cons=UPG alone is not a reliable upgrade identifier. Earlier runs had no ngsItineraries; they did not validate the feature. TC-03 is inventory discovery only.
