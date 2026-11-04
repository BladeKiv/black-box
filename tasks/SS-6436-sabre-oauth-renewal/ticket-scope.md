# SS-6436 Sabre NDC - Sabre OAuth token is never renewed after a 401 (dead retry branch, cached token never invalidated)

Source: https://traveldev.atlassian.net/browse/SS-6436 read live 2026-11-02. Developer comment confirms STAGE deployment.

## Intended behavior
When Sabre answers 401 Unauthorized, fetch a new token bypassing the cache, overwrite the cached token and retry the original request once. If the retry still fails, return the error with no further retries.

## Environment and access discovery
Requested environment: STAGE. HTTPS Search host: https://api.search.stage.travel-dev.com. Local source: <local Downloads>/AirAPI Stage.postman_environment.json (name AirAPI Stage). That file has no populated search_authorization or X-Yuni-Auth; no matching AirAPI runtime environment variable was available. No credentials retrieved from session history.

## Endpoint flow and evidence prerequisites
Prepare Search to obtain a Sabre REST offer, then carry its opaque key unchanged to Result for read-only pricing coverage, subject to confirmation of the target PCC/CID and controlled 401 mechanism. Correlated provider trace evidence must establish initial 401, fresh-token acquisition/cache replacement, exactly one retry, and terminal handling of a repeated failure. AirAPI success alone cannot prove these internal effects. No provider endpoints, configuration/cache mutations, credential rotation, booking or ticketing operations authorized.

## Preparation candidates (not executed or approved fixtures)
Five candidate Y / 1 ADT Search inputs: LHR-JFK 2026-12-02; JFK-LHR 2026-12-03; FRA-JFK 2026-12-04; JFK-FRA 2026-12-05; CDG-JFK 2026-12-06. Candidate routes remain preparation only; Sabre REST PCC/CID and the controlled test setup are unresolved.

## Execution boundaries
No live AirAPI requests executed. No test verdict assigned. No retries, polls or retests authorized by this intake. The single provider retry required by the ticket is distinct from agent retries.

## Operational lessons
Search SS-6436 STAGE / Sabre OAuth 401 token renewal returned only unrelated candidate lessons d772e78246dd4f3685f2d6c5a181e71c and ead3ef65cee1407ba01a9dc22fed71ad. Neither matches this scope; neither applied.

## User-approved regression scope, 2026-11-02
Search authentication is shared across all environments; resolve search_authorization from the existing DEV Postman environment at runtime while retaining the STAGE host. Previous target-file-only access restriction is superseded. User cannot supply controlled 401 fixtures and approves normal-path regression as in SS-6443, with PCC 8D55 and exact CID tst101. Execute one Search (gds=S, fare=PUB, 1 ADT, Y, SFO-FRA 2026-11-20) and one Result using a matching S/8D55 key unchanged. No automatic retries/polls/input variation; no mutation. If no 401 occurs, report regression only, not OAuth recovery verification.

Run: one live Search returned HTTP 200 results=[]. No Result call. WARN/NO_DATA. No retry/input variation. Sandbox refusal retained separately. Universal Search-auth correction saved to personal memory without secrets.

## Final scope clarification
User requests regression only because validation exists when provider credentials are not configured. OAuth fault injection/recovery is excluded from acceptance scope. This user statement does not establish that 8D55 has configured credentials or explain the empty Search response. Report intended behavior and verdict now cover only normal Search-to-Result regression. No additional live requests authorized or executed by this documentation update.

User authorizes fresh regression with exact pcc=8Ki0 and gds=V, retaining cid=tst101, SFO-FRA 2026-11-20, PUB, 1 ADT, Y. One Search then one Result on matching V/8Ki0 key unchanged; no retries or polling. Previous S/8D55 attempt archived separately. Lesson search returned no applicable scope-matching lesson; none applied.

V/8Ki0 run: HTTP 200 results=[]. No matching key, no Result call. Latest regression verdict WARN/NO_DATA; previous run remains separate. No additional request/input variation.

User approves later-date route variations LAX-LHR and LAX-MAD until inventory is found. Preserve exact V/8Ki0 and cid=tst101, PUB, 1 ADT, Y. Prepare LAX-LHR 2027-01-15, LAX-MAD 2027-02-15, LAX-LHR 2027-03-15, LAX-MAD 2027-04-15, LAX-LHR 2027-05-15. Execute sequentially, stop at first matching key. Enforce max_steps=4 across case; prior V Search used one step. Reserve one step for Result, so at most two new Searches in this case. No repeated-input retry or polling.

Later-date execution: LAX-LHR 2027-01-15 and LAX-MAD 2027-02-15 both HTTP 200 results=[]. Cumulative V case 3 Search steps, 0 Result, 0 retries. One step remains under max_steps=4, reserved for Result; continuing discovery plus Result requires explicit increased budget. Latest report: 0 PASS / 0 FAIL / 3 WARN.

User requests fare=PUB explicitly. Earlier requests already contained fare=PUB. Authorizes one fresh LAX-LHR 2027-01-15 Search with unchanged V/8Ki0, cid=tst101, PUB, Y, 1 ADT. This consumes fourth cumulative V Search step; no automatic repetition.

Explicit PUB fresh retest: HTTP 200 results=[]. Four cumulative V Search steps, one repeated-input retest, zero Result calls. Budget exhausted. Report updated 0 PASS / 0 FAIL / 4 WARN.

User supplies exact working Search and authorizes fresh execution beyond earlier exhausted discovery budget: extra=false, cabin=T, adt=1, debug=true, fare=PUB, cid=TST101, gds=V, pcc=8KI0, LAX-MAD 2026-11-14. Preserve casing exactly. One exact Search then one read-only Result if a matching key is available; no retries. Shared Search auth resolved securely from existing local source; pasted credential is not copied to artifacts. This is a new explicit two-request execution scope. Earlier lowercase requests remain independent evidence and cannot diagnose provider availability.

Exact user fixture: Search HTTP 200, 37 V/8KI0 offers. Result HTTP 200; same opaque key and V/8KI0, populated trip segments, numeric totalPrice=595. 2 PASS / 0 FAIL / 0 WARN for exact regression pair only. No retry. Earlier differing-input attempts archived. Changed casing/cabin/date/route/options together; no isolated root-cause claim.
