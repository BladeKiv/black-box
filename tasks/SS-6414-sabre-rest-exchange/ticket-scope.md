# SS-6414 /v1/exchange Sabre REST integration

Source: Jira description and developer comments read live 2026-10-23. Deployed on STAGE according to developer comment.

## Intended behavior
Integrate Sabre REST Flight Reshop for /v1/exchange with SOAP/REST selection through sabre_rest.exchange_enabled. Compare the ticket-listed itinerary and per-PTC pricing mappings. The ticket identifies absent REST terminals, marriage group and fee type; these are not invented required REST fields.

## Authorized execution
User confirms POST /v1/exchange does not change the booking and the example booking should remain valid. Endpoint: https://api.search.stage.travel-dev.com/v1/exchange. Authentication supplied in chat is used only at runtime and excluded from artifacts. Standing direct TLS bypass authorization applies explicitly at each call.
User performs configuration switches; agent must ask user to enable/disable. No configuration writes by agent, no booking/ticket mutations, no application source inspection.
Approved inputs: the ticket example only. allow_retry=false; allow_poll=false; allow_retest=false until an operational reason and authorization are established. Initial comparison: one SOAP and one REST request after user confirms each mode. No speculative edge cases.

## Intake prerequisites
Ticket example itinerary.issueDate literally contains 2026-10-20> and needs clarification before sending. SOAP baseline requested with exchange_enabled=false; wait for user mode confirmation. No API execution yet.

## Operational notes
Lesson search: python -B -m bb.lessons search --tags SS-6414 STAGE --text exchange returned no matching lessons. Intake run ID: SS-6414-2026-10-23-intake. Permissions and input clarifications remain here, never promoted into operational lessons.

User confirms sabre_rest.exchange_enabled is disabled on STAGE (SOAP baseline ready). Date correction question remains unanswered; no request sent.

User explicitly approves correcting itinerary.issueDate to 2026-10-20. SOAP baseline execution authorized with the ticket example and this sole correction.

SOAP baseline: HTTP 200; count=14; results length=14. req_resp name Sabre_Exchange and ExchangeShoppingRQ/RS establish SOAP execution. Network sandbox transport refusal occurred before the fresh network-approved call. Sanitized source XML bodies retained; SOAP headers removed. No retry of a received AirAPI response.

User instructed test now after REST switch request. Fresh call returned HTTP 200, count=19, results length=19, but body.req_resp[0].name=Sabre_Exchange and request/response bodies contain SOAP ExchangeShoppingRQ/RS. REST execution not established. Pending confirmation that sabre_rest.exchange_enabled applies to STAGE CID TST101 / PCC 6NVG; no further calls or retries.

User authorized another retest. HTTP 200 / 13 offers; req_resp still SOAP ExchangeShoppingRQ/RS. Read-only GET /algo/conf returned HTTP 200; sabre_rest object found but exchange_enabled was absent from inspected configuration. This discovery is not execution proof. REST remains unevaluated pending deployment/flag clarification. No more calls queued.

User explicitly confirmed that the preceding keyboard-layout message meant check now and authorized another read-only STAGE exchange test. This authorizes one fresh retest despite the unresolved mode prerequisite, with unchanged approved booking inputs and issueDate=2026-10-20. Read-only /algo/conf discovery also authorized. No automatic retries or configuration writes.

Fresh user-authorized recheck: GET /algo/conf HTTP 200 exposes sabre_rest.enable_exchange=true. POST /v1/exchange HTTP 200 returns 13 offers and req_resp name Sabre_Exchange_Rest with Flight Reshop JSON. REST execution confirmed. All 13 source offers uniquely matched to AirAPI output across 24 segments; flight identity, airports/dates, airlines, equipment, segment/trip duration, booking class/fare basis, fare/tax differences and grand totals checked with no mismatches. Full pricing field mapping and flag-name acceptance need clarification before final report.

Final assessment authorized by user instruction to determine needed checks independently from ticket/captured evidence. Result: 7 PASS / 1 FAIL / 3 WARN. Supplied 20 kg checked allowance is emitted as 23 kg on both linked segments. No missing optional value treated as zero or false; pricing public paths not evidenced were not invented. No new API requests or input variations performed during offline assessment. Final HTML/Markdown, Postman v2.1 collection, CSV and paired sanitized evidence saved under runs/2026-10-23. Ledger unchanged.

User clarification after initial report: a weight-only allowance of at least 1 kg is parsed into allowPieces=1 only; parser kg is not populated. Post-processing fills missing details. Therefore source 20 kg need not appear as final kg=20. TC-08 reclassified to PASS on saved evidence because both linked segments have allowPieces=1. Original source20/output23 observation is retained; intermediate parser/post-processing not independently observed. No new API run and no ledger update. This ticket-specific expectation must not become an operational lesson.

User reports weight-value fix deployed. Authorized fresh TC-08-only retest using the unchanged request; expected behavior now preserve explicit provider maximumWeightInKilograms in AirAPI kg on each linked segment. One request, no retry or variation; historical PASS used earlier pieces-only expectation.

Fresh deployed-fix TC-08 retest: HTTP 200, Sabre_Exchange_Rest, 11 offers. Provider 20 kg allowance linked to EI108 JFKâ€“DUB and QR18 DUBâ€“DOH maps to kg=20 on both; lbs=44 and allowPieces=1 observed. TC-08 PASS under revised provider-value expectation. One request; no retry. Other cases not rerun; historical three WARNs unchanged. See runs/2026-10-23-weight-fix/qa-report.html.

Main report updated per user request: TC-08 now references fresh deployed-fix 20 kg evidence and revised provider-value expectation. Main collection assertion synchronized. Aggregate remains 8 PASS / 0 FAIL / 3 WARN, combining initial rows with TC-08 fresh retest; no full rerun implied.
