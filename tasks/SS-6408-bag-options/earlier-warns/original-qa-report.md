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

Working fixture / current feature signal: PASS for observed dual-option path only.

Intended behavior: when both options can be created, 1-piece main and 2-piece ngsItineraries child with unique keys and corresponding prices.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-05 | Exact user curl; TST101; S/6NVG/SR; C; LH; FRA-CDG Nov 20; CDG-MUC Nov 30 | 1-piece main and 2-piece child | 24/24 pairs contain both; first USD 666.40 and 876.40 | PASS |
| TC-06 | Same response, 24 pairs | Distinct keys, no duplicated pair option | 48 distinct nonempty parent/child keys | PASS |
| TC-07 | Same response, paired itinerary fields | Same flights, dates, airports, cabin and fare details | Checked fields match in all 24 pairs | PASS |

Request: GET https://api.search.stage.travel-dev.com/v1/search?adt=1&debug=true&cid=TST101&fl.0.dt=2026-11-20&fl.1.dt=2026-11-30&val_cr=LH&gds=S&pcc=6NVG&fare=SR&cabin=C&fl.0.o=FRA&fl.0.d=CDG&fl.1.o=CDG&fl.1.d=MUC
Authorization omitted; body none.
Full response: search-working-response.json. Exact opaque keys and pair prices: working-pairs.json. TRACEID 126565a7-5cc5-4cb1-ae0b-f6775990aa00.

Earlier UPG checks used cons=UPG, which is not a reliable upgrade identifier in this response: upgrade entries retain cons=GTT and expose keys.upgrade_info and meta.prod_types. Earlier counts did not establish absence of upgrades from every possible field. Their no-ngsItineraries observation remains valid. Documentation and other flag combinations were not executed in this run.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-08 | Working Search; user confirmed secondBag=true, keepBothBagOptions=false | Only 2-piece upgrade options; no retained 1-piece upgrade variant | HTTP 200; 60 main results; 15 upgrade parents identified via keys.upgrade_info; all allowPieces=2; no upgrade children | PASS |

Request: GET https://api.search.stage.travel-dev.com/v1/search?adt=1&debug=true&cid=TST101&fl.0.dt=2026-11-20&fl.1.dt=2026-11-30&val_cr=LH&gds=S&pcc=6NVG&fare=SR&cabin=C&fl.0.o=FRA&fl.0.d=CDG&fl.1.o=CDG&fl.1.d=MUC
Authorization omitted; body none. Response: search-secondBag-true-keepBoth-false-response.json. Exact keys and prices: secondBag-true-keepBoth-false-summary.json. TRACEID b9e9f1e9-f78a-4cc5-9b92-8ca9a2f8ed56. Config state supplied by user; not independently fetched. Counts differ from prior live inventory and are not asserted invariant.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-09 | Exact working Search; secondBag=true; keepBothBagOptions omitted (user confirmed) | Default false: only 2-piece upgrades | HTTP 200; 60 main results; 12 upgrade parents, all keys.baggage.allowPieces=2; no upgrade children | PASS |

Request: GET as retained in search-working-url.txt; Authorization omitted; body none. Paired full response: search-secondBag-true-keepBoth-omitted-response.json. Exact keys/prices: secondBag-true-keepBoth-omitted-summary.json. TRACEID c89ad2fd-9381-4826-a67c-9ad614676140. Config state user-confirmed; not independently fetched. Inventory counts are not expected to remain constant.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-10 | Exact working Search; secondBag=false; keepBothBagOptions=true (user confirmed) | Flag ignored: only 1-piece upgrades | HTTP 200; 60 main results; 12 upgrade parents, all keys.baggage.allowPieces=1; no upgrade children | PASS |

Request: exact GET in search-working-url.txt; authorization omitted; body none. Full response: search-secondBag-false-keepBoth-true-response.json. Exact keys/prices: secondBag-false-keepBoth-true-summary.json. TRACEID 8b071bd8-3dff-4e51-81c3-cf08a5b0a72a. Configuration user-confirmed; not independently fetched.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-11 | Exact working Search; secondBag=false; keepBothBagOptions=false (user confirmed) | Only 1-piece upgrades | HTTP 200; 60 main results; 38 upgrade parents, all keys.baggage.allowPieces=1; no upgrade children | PASS |

Request: exact GET in search-working-url.txt; authorization omitted; body none. Response: search-secondBag-false-keepBoth-false-response.json. Exact keys/prices: secondBag-false-keepBoth-false-summary.json. TRACEID f08f6f08-81e5-4d3f-9629-f940110de6b1. Configuration user-confirmed; not independently fetched. All five agreed flag scenarios have passed on available upgrade inventory. Documentation acceptance remains outside this live Search matrix; previously reported missing by user.
