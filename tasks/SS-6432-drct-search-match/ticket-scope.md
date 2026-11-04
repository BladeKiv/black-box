# SS-6432 DRCT S&M

Source: https://traveldev.atlassian.net/browse/SS-6432, read live 2026-10-26.
Ticket description: Add S&M logic for DRCT and allow to result non-DRCT itineraries.

User-requested DEV flows:
1. Search with gds other than D; carry a returned opaque key unchanged to Result; observe gds becomes D through Search and Match recovery.
2. Search with gds=D; Result; book/create with malformed offer-tracking additional info.

Direct user request authorizes the named DEV book/create test. No issuance, cancellation or configuration changes are authorized.
Standing direct user instruction authorizes HTTPS TLS verification bypass.

Execution bounds: allow_retry=false; allow_poll=false; allow_retest=false; approved_inputs=[] pending current DEV fixture.
Do not infer malformed field names or a booking outcome before inspecting the current API fixture and resolving test-critical unknowns.

Prerequisites pending: current DEV Search URL/CID and route/date fixture; runtime credential source; synthetic booking fixture.
No API request executed. No test result asserted.
Lessons search: SS-6432 DEV / Dida returned no matches; no lesson applied.

User clarification: gds=D for DRCT. The two requested DRCT flows use D in place of the initially supplied O. This is ticket scope, not an operational lesson.

Current user-approved Search parameters: gds=D, pcc=DEF, fare=PUB, cid=TST101. Reuse existing DEV fixture LHR-JFK 2026-11-20, 1 ADT, cabin Y.

User steering: prioritize non-D to D. Find same DRCT flights in S/6nvg, A/DFWg32100, K/DEF, E/2eh4 before Result. These four provider/PCC searches are explicitly approved inputs; retain PUB/TST101 and the DRCT route/date. Booking is deferred until this flow is checked.

User expectation clarification: same flights should switch to D even when fare basis differs. Apply to saved LH Result evidence; no rerun. Expectations are recorded only in ticket scope, never learned.

Booking phase resumed by direct user request. Fresh Search and Result captured under runs/2026-10-26-booking; both HTTP 200, Result gds=D. Observed tracking field keys.drct.gdsOfferId. No book/create call made: DRCT endpoint/payload gds_id mapping not yet evidenced by available collections. User asked live for the DRCT fixture. Existing Brightsun/Atlas/Sabre NDC fixtures do not establish DRCT mapping.

User confirmed DRCT uses the Brightsun book/create request structure, with additionalInfo taken from DRCT Result; corrupt ID values there. Executed one POST /drct/v1/book/create with malformed gdsOfferId. HTTP 200 / application 422 Price change; replacement offer ID returned. No price acceptance or retry; booking completion WARN.

User acceptance: mark malformed-offer booking recovery PASS. User states Price change establishes matching the itinerary and sending a new book/create request, with only price changed; this outcome is accepted. This is user-confirmed acceptance, not an additional API execution or an operational lesson. No retry authorized or performed. Supersedes the earlier booking WARN classification.

Fixed-build verification authorized: rerun all non-D to D cases using fresh D/DEF, S/6NVG, A/DFWG32100, K/DEF, E/2EH4 searches on the approved LHR-JFK date. allow_retest=true for this fresh run; allow_retry=false; allow_poll=false. Compare flights against fresh DRCT inventory, preserve opaque keys and earlier evidence. Existing booking Price change acceptance carries forward; no duplicate booking needed for the non-D Result fix.

Final user scope decision: skip K and E due to GDS unavailability. Exclude these cases from assessed counts, preserve historical WARN evidence, and do not convert them to PASS. Final scope comprises the three fixed-build Result cases and carried-forward user-confirmed booking recovery PASS.
