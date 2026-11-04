# SS-6409 scope intake - 2026-10-22

Source: Jira SS-6409 description and three developer comments read live.

Intended behavior: Support /offers/shop, /offers/flightShop and /offers/flightShopLite with consistent AirAPI output; route by sabre_rest project/cid lists, default to shop when unlisted; config-only switching; no fallback on error; revalidation/checkout support for all three. New blocks do not support pcc. Overlap follows the first list per ticket; exact interpretation requires clarification before testing overlap.

Developer comments: DEV; example flight_shop.cid=[TST101], flight_shop_lite.cid=[TST102]; meta.sabreRest removed, keys.sabre.endpoint added. Examples identify flightShop, flightShopLite and bargainFinderMax. No exact shop marker supplied.

Fresh configuration discovery: DEV GET /algo/conf returned HTTP 200; sabre_rest.enable=true and enable_revalidate=true; both flight_shop and flight_shop_lite have cid=null and projects=null. Null is preserved and is not assumed equivalent to empty lists. This is configuration discovery only, not routing execution evidence. Credentials excluded. Initial sandbox transport failed; network-enabled discovery succeeded.

Execution scope: no Search, Result, revalidation or checkout requests executed. No configuration changes or booking/ticket writes authorized. allow_retry=false; allow_poll=false; allow_retest=false; approved_inputs=[] pending live scope inputs. No matching SS-6409 DEV sabre operational lesson found.

Pending: target environment and configured project/CID/Search fixtures for each route. Related SS-6330 parity research must be read before defining output parity checks. Checkout execution remains outside authorized state-changing scope.

## Configuration update verified live

DEV confirmed by user. Fresh GET /algo/conf: HTTP 200; enable=true; enable_revalidate=true; flight_shop.cid=[TST101]; flight_shop_lite.cid=[TST102]; projects=null in both blocks. Paired sanitized evidence: config-discovery.json. User configured CID routing as requested; project routing remains outside this round. Search URL and a valid unlisted default-route CID remain pending. No Search execution yet.

## Approved execution round

User approved DEV; gds=S, pcc=6NVG, default cid=TST104; fare clarified to PUB only. Routed CIDs TST101 and TST102 are configured by user. Agent selected LHR-JFK 2026-11-20, Y, 1 ADT as a common live-inventory fixture. Three synchronous Search requests, one per CID; no retry, polling or input variations. Read-only Result may consume each returned key without alteration; no state-changing checkout. SS-6330 read live: documented gaps include mileage, meal, seatsavailable/maxSeats default 9 and fareCalculation surcharges. These historical research observations do not waive SS-6409 acceptance criteria. No matching operational lessons.

## User clarification and executed outcome

User clarified fare=PUB only and confirmed bargainFinderMax plus RestBargainFinderMaxRQ is the intended default route. These are ticket-scope expectations and are not operational lessons. Search: TST101 50/50 flightShop; TST102 95/95 flightShopLite; TST104 195/195 bargainFinderMax. Three read-only Result GETs returned HTTP 200, retained selected keys/markers and exposed itinerary/prices directly at the response root. This observed Result shape is recorded without changing the global contract. Eight scoped checks PASS; no full ticket closure claim. Revalidation/checkout and project/config-transition coverage remain unexecuted exclusions. No retries, polling, writes, applied lessons or ledger update. Each case used two endpoint steps, within configured max_steps=4.

## Remaining coverage extension

User requested remaining ticket points. See remaining-coverage.md for staged configuration rounds and precise execution budgets. Round 2 awaits user confirmation of explicitly empty lists. Additional saved-response analysis is stored separately in saved-field-gap-analysis.json; it is not fresh execution or acceptance of missing fields.

## Remaining coverage clarification

User confirmed flight_shop wins when CID/project matches both blocks. This defines the overlap expected result for subsequent execution and is not an operational lesson. User stated Sabre errors cannot be reproduced and requested accepting the no-fallback point as passed. Record this separately as user acceptance of unexecuted error coverage; it is not an executed PASS or proof that fallback does not occur. No error injection or speculative error cases will be attempted. Project identification and read-only revalidation/checkout request details remain unanswered. Empty-list round still awaits user configuration readiness.

## Empty-list round authorized and clarified

User confirmed readiness and explicitly approved treating null CID/project lists as empty for this test. This comparator allowance applies only to SS-6409 this round and is not an operational lesson. Config discovery returned HTTP 200 with all four lists null and both enable flags true. Three fresh Search requests authorized, one per previously approved CID with unchanged itinerary/filters; no retry or polling.

Empty-list round result: 3/3 fresh Search checks PASS; HTTP 200 and 197/197 bargainFinderMax options per CID. Request objects identical to preserved first-round Search requests. All six routing lists observations retain actual null/array values; null-as-empty is this round user clarification only. Cumulative 11 PASS across 6 Search and 3 Result requests; no retries. No-fallback remains separately user-accepted and unexecuted. No operational lessons applied; no new operational pattern requiring a lesson.

## CID overlap round

User confirmed configured readiness. Verified TST101 in both flight_shop.cid and flight_shop_lite.cid. Expected flightShop wins, per explicit user clarification. One fresh Search using identical original TST101 request; allow_retry=false, allow_poll=false, allow_retest=true for this configuration only; approved inputs unchanged. Max four steps; no writes.

Overlap result: HTTP 200, 50/50 options flightShop with TST101 present in both CID blocks. TC-12 PASS; cumulative 12 PASS / 0 FAIL / 0 WARN. Original Search request unchanged; one Search, no retries. Root CSV now targets overlap configuration; original and empty-list phase CSVs are preserved in their respective run directories. No lessons applied or new operational patterns; ledger unchanged.

User clarified the revalidation test operation: take any Search key and call v1/result. Executed one fresh GET /v1/result/ANY/{key}?cid=TST101&debug=true using the first latest overlap Search key unchanged. This is user-defined Result coverage; provider-internal execution is not separately inferred. No retries or state-changing calls. Paired evidence: runs/2026-10-22-overlap/TST101-result.json.

## Final handoff

User stated testing is enough and requested final report. Final artifacts contain 13 executed PASS, no executed FAIL/WARN; unexecuted scope and separate no-fallback user acceptance retained. No fresh API calls during final rendering. Ledger unchanged.
