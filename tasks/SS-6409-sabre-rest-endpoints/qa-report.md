SS-6409 — Sabre REST – add /offers/flightShop and /offers/flightShopLite as config-switchable alternatives to /offers/shop

**PASS — 13 PASS / 0 FAIL / 0 WARN**

2026-10-22 | DEV | PUB; S/6NVG | TST101/TST102/TST104 | LHR-JFK 2026-11-20; Y; 1 ADT

Completed user-approved DEV scope: 13 PASS / 0 FAIL / 0 WARN. Configured CID routes, empty/unlisted routing, config-only switching, CID overlap priority, endpoint markers, matching top-level option fields and read-only Result retrieval passed. User ended testing at this coverage. No-fallback-on-error was separately user accepted without execution; this adds no executed PASS.

Intended behavior: Route listed project/CID entries through their configured Sabre REST endpoint; unlisted traffic uses the default route. All three produce AirAPI output and support revalidation/checkout. User confirmed bargainFinderMax with RestBargainFinderMaxRQ is the intended default route for this test.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | TST101; PUB; S/6NVG; LHR-JFK 2026-11-20; Y/1 ADT | Nonempty results; all keys.sabre.endpoint=flightShop | HTTP 200; 50/50 options match | PASS |
| TC-02 | TST102; PUB; S/6NVG; LHR-JFK 2026-11-20; Y/1 ADT | Nonempty results; all keys.sabre.endpoint=flightShopLite | HTTP 200; 95/95 options match | PASS |
| TC-03 | TST104; PUB; S/6NVG; LHR-JFK 2026-11-20; Y/1 ADT | Nonempty results; all keys.sabre.endpoint=bargainFinderMax | HTTP 200; 195/195 options match | PASS |
| TC-04 | All 340 returned Search options across three CIDs | Same top-level AirAPI option field set across all three routes | 340 options; 25 top-level fields each; identical field sets=True | PASS |
| TC-05 | All returned Search options; meta.sabreRest and keys.sabre.endpoint | Legacy meta.sabreRest absent; endpoint marker present | 340/340 legacy flags absent; all route markers populated | PASS |
| TC-06 | TST101; first fresh Search key carried unchanged into GET Result | Readable itinerary/prices; selected key and endpoint marker retained | HTTP 200; key retained=True; endpoint=flightShop | PASS |
| TC-07 | TST102; first fresh Search key carried unchanged into GET Result | Readable itinerary/prices; selected key and endpoint marker retained | HTTP 200; key retained=True; endpoint=flightShopLite | PASS |
| TC-08 | TST104; first fresh Search key carried unchanged into GET Result | Readable itinerary/prices; selected key and endpoint marker retained | HTTP 200; key retained=True; endpoint=bargainFinderMax | PASS |
| TC-09 | TST101; all lists null (user-approved empty); unchanged Search inputs | All options use default bargainFinderMax after config-only update | HTTP 200; 197/197 default options; previous marker=flightShop | PASS |
| TC-10 | TST102; all lists null (user-approved empty); unchanged Search inputs | All options use default bargainFinderMax after config-only update | HTTP 200; 197/197 default options; previous marker=flightShopLite | PASS |
| TC-11 | TST104; all lists null (user-approved empty); unchanged Search inputs | All options use default bargainFinderMax after config-only update | HTTP 200; 197/197 default options; previous marker=bargainFinderMax | PASS |
| TC-12 | TST101 listed in both CID blocks; PUB/S/6NVG; unchanged itinerary | flightShop wins over flightShopLite | HTTP 200; 50/50 flightShop options | PASS |
| TC-13 | Latest overlap Search key; GET /v1/result/ANY/{key}; TST101 | Result succeeds with selected key, itinerary/prices and flightShop marker retained | HTTP 200; selected key retained=True; flightShop marker retained | PASS |

Supporting evidence and rerun artifacts

13 executed checks across 7 Search and 4 Result requests, without retries. Configuration discovery is separate evidence in config-discovery.json. Source pairs: runs/2026-10-22/TST101.json, TST102.json, TST104.json and corresponding -result.json files. Same top-level field set does not certify nested field/value parity. Search requests used S/6NVG; returned gds/pcc included E/8C4T for 48/50 TST101 and 183/195 TST104 options; TST102 returned S/6NVG throughout. No assertion of returned GDS/PCC equality was made. Result GET does not establish provider revalidation. Excluded: checkout, booking/ticket writes, revalidation execution, project routing, forced provider errors/no-fallback, SR, and debug=false. SS-6330 research lists mileage/meal/seat/surcharge gaps; no waiver or full nested parity assertion. No operational lessons applied or new reusable operational patterns observed. No ledger update. Empty-list phase evidence: runs/2026-10-22-empty-lists/. Actual list values were null; user explicitly approved this as empty for this test only. Root CSV is for the current CID-overlap phase; original CSV is retained under runs/2026-10-22/. No-fallback-on-error is user accepted but NOT EXECUTED and adds no executed PASS. See acceptance-notes.md. Overlap winner is confirmed as flight_shop; project routing and revalidation/checkout execution remain pending. Overlap evidence: runs/2026-10-22-overlap/; both CID lists contained TST101, both project lists were null. Earlier eight-check and empty-list results retain their original evidence and configuration contexts. User clarified v1/result as the revalidation test operation. TC-13 covers that requested operation for flightShop; TC-06/07/08 previously cover Result for all three routes. No separate provider-internal execution proof or booking checkout is claimed. FINAL HANDOFF: user explicitly ended testing and requested the final report. Project routing, separate booking checkout and full nested field/value parity remain unexecuted. The 13 PASS result certifies only the cases in this table, not every acceptance criterion. Data-gap analysis is in saved-field-gap-analysis.json; no waiver of those differences is inferred. Current rerun CSV requires TST101 in both CID lists. No additional endpoint execution was performed to generate this final report.

Collection: SS-6409.postman_collection.json; CSV: expected-outcomes.csv.
