# SS-6443 — TravelFusion Search and Result regression

2026-11-02. User narrowed scope to a small normal-path regression on STAGE; PROD login-expiry defect is not reproducible here. No claim about the four defect fixes.

Intended behavior: Search with gds=F, cid=TST101 returns usable offers; Result resolves an unchanged opaque Search key into a usable itinerary. PCC is unrestricted and omitted from requests.

Environment: https://api.search.stage.travel-dev.com; secure reference: <local Downloads>/AirAPI Stage.postman_environment.json. Host verified; enabled search_authorization variable absent. No credential fallback from other environments.

Five prepared examples: search-examples.json. Execute the first example only, then one Result for a returned key. Small-regression execution limit: one Search plus one Result; other examples are preparation only. allow_retry=false; allow_poll=false; allow_retest=false. Approved inputs: gds=F, cid=TST101; agent-selected LHR-DUB 2026-11-20, Y, 1 ADT. No live requests yet.

Flow: GET /v1/search -> results[].key -> GET /v1/result/ANY/{key}?cid=TST101. Preserve key verbatim. Inspect observed Result shape before choosing data assertions. No booking, ticketing, configuration mutations or fault injection.

Lessons searched: SS-6443/STAGE TravelFusion login expired stale session. Returned lessons d772e78246dd4f3685f2d6c5a181e71c and b230dfee9dcf41d6a474238b2bcfcce7 do not match this scope; neither applied. Prior defect-fixture question superseded by user narrowing; no defect fixtures required.

User correction: Search authentication is universal across environments. Resolved securely from existing DEV environment search_authorization while retaining STAGE host; no values persisted. This permission belongs in scope and personal memory, never operational lessons. Initial sandbox connection was refused before application access; network-enabled request returned HTTP 200, results=[]. No Result executed. Asked live before route variation.

User approved one STN-DUB input variation. Fresh Search returned HTTP 200 results=[]. Two live Search calls total, no repeats/polling/Result. Final regression WARN/NO_DATA; successful transport does not certify usable offers or Result. No further calls.

User approved SFO-FRA input variation, same 2026-11-20, Y, 1 ADT, gds=F, cid=TST101. One Search followed by one Result if a key is returned; no retry or polling.

SFO-FRA fresh result: HTTP 200, results=[]. No Result key; no Result call executed. Cumulative 3 Search requests, all empty; 0 PASS / 0 FAIL / 3 WARN.

User approved SFO-FRA retest with exact pcc=def and fare=pub, preserving date 2026-11-20, Y, 1 ADT, gds=F, cid=TST101. One Search then one read-only Result if a key is available. No retries/polling.

Exact lowercase def/pub Search returned HTTP 200, 57 offers. Selected first offer was E/2HE4; Result HTTP 200 preserved its key and prices and returned one trip. This is not TravelFusion verification. Remaining offers were not retained or evaluated for F; no conclusion on all returned providers. Requested live clarification before uppercase DEF/PUB rerun.

User approved uppercase DEF/PUB rerun with gds=F, SFO-FRA, same date/passengers/cabin; select only returned gds F for Result. One Search and one Result, no retries/polling.

Final uppercase run: 57 Search offers, 37 F and 20 E. Selected F/DEF offer; Result HTTP 200, same opaque key and F/DEF, populated trip segments and numeric totalPrice. 2 PASS / 0 FAIL / 0 WARN for this scoped pair. Mixed-provider Search output is an observation, not an exclusivity assertion. Earlier runs archived separately. No verification of PROD defect fixes.
