# SS-6332 — QA dispatch

Release signal: IN PROGRESS — 12 PASS, 0 FAIL, 0 WARN across executed checks.

DEV | GET /v1/search | TST101 | LHR–LAS 2026-10-14 | Y / 1 ADT / PUB

Intended behavior: eligible UA options map to G / DEF / GTT. Mapping requires enabled=true and CID OR project eligibility; operating carrier differences do not block it. Ineligible options continue through existing mapping rules.

12 PASS, 0 FAIL, 0 WARN across 11 Search calls. All 200 UA itineraries matched uniquely between the enabled and disabled runs; 14 WS itineraries kept the same final triple.  Testing remains in progress; remaining configuration rounds and exact pricing calculations are not certified.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| A01 | UA; TST101; LHR–LAS 2026-10-14; Y; 1 ADT; PUB; S/6NVG | Returned all-UA marketed options map to G / DEF / GTT | 200/200 UA options match the target triple; all have ndcMapped=true | PASS |
| A02 | Same request with val_cr=WS; only UA configured | WS does not receive the UA NDC target triple | 14/14 WS options return E / 8C4T / VZU; ndcMapped is absent | PASS |
| A03 | UA response subset with a non-UA operating carrier | Non-UA operating carrier does not block the UA target triple | 56/56 codeshare options retain G / DEF / GTT with all-UA marketing | PASS |
| B01 | UA; same Search; ndc_mapping.enabled=false | No NDC target mapping; NDC marker/asset absent; compare matching itineraries | 200/200 uniquely matched UA itineraries changed from G / DEF / GTT to E / 8C4T / VZU; NDC marker/asset absent | PASS |
| B02 | WS; same Search; ndc_mapping.enabled=false | WS mapping remains unchanged across enabled/disabled rounds | 14/14 uniquely matched WS itineraries stayed E / 8C4T / VZU; NDC marker/asset absent | PASS |
| C01 | Request cid=TST101; enabled=true; configured cid=[TST102]; projects=[] | CID rejection prevents UA NDC mapping | 200/200 UA options retain E / 8C4T / VZU and match the disabled baseline; NDC marker/asset absent | PASS |
| D01 | Request TST101; configured cid=[TST102]; projects=[*]; enabled=true | Project wildcard admits mapping despite CID mismatch (OR) | 200/200 UA options map to G / DEF / GTT with ndcMapped=true | PASS |
| F01 | Exact-CID positive control; cid=[TST101]; projects=[]; enabled=true | Matching CID admits eligible UA content: G / DEF / GTT | 200/200 UA options map with ndcMapped=true | PASS |
| G01 | Source GTT; configured source_cons=VZU; exact TST101 CID eligible | Source consolidator mismatch skips NDC mapping using pre-mapping values | 200/200 retain E / 8C4T / VZU; original_info.cons=GTT; NDC marker/asset absent; all match disabled baseline | PASS |
| I01 | Search S/6NVG; configured source pairs S/8C4T and E/6NVG; source_cons=GTT | PCC listed under another GDS does not qualify; skip NDC mapping | 200/200 return E / 8C4T / VZU; original_info confirms S / 6NVG / GTT; NDC marker/asset absent. 183 match earlier baseline itineraries; 17 differ in itinerary/fare attributes | PASS |
| J01 | Search S/6NVG; configured S/6NVG and E/6NVG | Matching the PCC within the correct GDS restores G / DEF / GTT | 200/200 UA options map to G / DEF / GTT with ndcMapped=true | PASS |
| K01 | UA; Search fare=PUB; configured source_fare=[SR]; source S/6NVG eligible | Source fare-type mismatch skips NDC mapping | 200/200 UA options have fareType=PUB and return E / 8C4T / VZU; NDC marker/asset absent | PASS |

Fields: results[].gds, pcc, cons, validatingCarrier and trips[].segments[].marketingAirline / operatingAirline. NDC markers/assets provide supporting evidence. Baselines match explicit itinerary, fare and passenger attributes; Search keys remain opaque. Configuration snapshots are user-confirmed. Use each CSV only with its corresponding configuration; set authorization locally in Postman. A03 reuses the A01 response.

Evidence files: evidence-round-A-UA.json, evidence-round-A-WS.json, evidence-round-B-UA.json, evidence-round-B-WS.json, evidence-round-C-UA.json, evidence-round-D-UA.json, evidence-round-F-UA.json, evidence-round-G-UA.json, evidence-round-I-UA.json, evidence-round-J-UA.json, evidence-round-K-UA.json.
