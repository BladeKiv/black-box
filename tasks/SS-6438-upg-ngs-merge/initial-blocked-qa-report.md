SS-6438 — Build UPG itineraries as main itineraries with NGS children (regular + upgrade options)

WARN — BLOCKED | 0 PASS / 0 FAIL / 3 WARN
PREPROD | 2026-11-02 | http://airapi51.kivops.info | Search-only ticket; configuration prerequisites separate

Intended behavior: For an itinerary with UPG options, the cheapest eligible regular or UPG option becomes main NGS#1. Regular children require ngs_jobs; other UPG children also require keepBothBagOptions=true. Subsequent retained options must be equal or better on all bags/exchange/refund features and strictly better on at least one. Equal-feature higher-price and feature-losing options are dropped.

Merge testing is blocked: PREPROD reports upgrade_config.enable_merge=false. Direct HTTP Search works, but the TST101 reconnaissance returned only regular PUB fares and cannot evaluate the merge. Five configuration-relevant BCKDCR/AKKDCR examples are prepared and unexecuted.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | PREPROD GET /algo/conf | Ticket prerequisite: upgrade_config.enable_merge=true; ngs_jobs enabled for eligible CID/OD. | HTTP 200; upgrade_config.enable_merge=false; upgrade_config.enable=true; ngs_jobs.enable=true. Merge matrix blocked. | WARN |
| TC-02 | S02: TST101; C; LH/S/6NVG/SR; FRA-CDG 2026-11-20, CDG-MUC 2026-11-30 | A qualifying group with UPG options is required to evaluate cheapest-main and progressive feature filtering. | HTTP 200; 40 PUB results; 0 UPG results; no ngsItineraries fields. TST101 is absent from the returned UPG/ngs CID lists. | WARN |
| TC-03 | S01: initial HTTP Search through inherited localhost proxy | Reach Search and obtain evaluable response data. | No HTTP response; WinError 10061 from inherited proxy route. Direct HTTP access later succeeded independently in S02. | WARN |

Supporting evidence: configuration-http-direct.json, S02.json, S01.json. Request/response excerpts are embedded in the matching HTML dispatch.

Configuration eligibility: BCKDCR keepBothBagOptions=false; AKKDCR keepBothBagOptions=true; ngs_jobs includes US-Europe routes. Configuration discovery does not prove per-request merge execution. No merge checks, downstream requests, configuration changes, or Jira writes were performed. Search keys were not decoded or rewritten.

Current HTTP Search and authenticated HTTP configuration access were explicitly authorized by the user. Earlier transport errors came through an unavailable localhost proxy. The initial query flag parameters are not evidence of effective configuration.

Operational lesson search returned no matching ticket/endpoint conditions; no lesson applied. The access decision remains in ticket scope, never learned.
