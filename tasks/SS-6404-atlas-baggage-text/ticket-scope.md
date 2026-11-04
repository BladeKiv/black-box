# SS-6404 Atlas - logic for "baggageFullTextA" and "baggageFullTextD" + carry on

Source: https://traveldev.atlassian.net/browse/SS-6404 (read live 2026-10-26).
Intended behavior: Use the same template generation logic as Amadeus NDC for Atlas baggage and carry-on, incorporating pieces, weight and size into baggageFullTextA and baggageFullTextD. Ticket examples use FBA/FBD for checked baggage and COA/COD for carry-on, alongside numeric allowance fields.

Authorized scope: PREPROD, HTTPS port 8090, POST /atlas/v1/book/info only, existing bookings. Fresh source correlation from Kibana. No configuration, Search, booking creation, ticketing or cancellation calls.
allow_retry: false
allow_poll: false
allow_retest: false
approved_inputs: existing Atlas Book/Info requests selected from user-filtered Kibana records; selection pending.
TLS bypass: standing direct user authorization, explicitly applied at execution.

Setup status: Jira read; local PREPROD environment located; saved prior Atlas fixture has masked orderNo and is not replayable. User confirmed Atlas port 8090 and will set Kibana filters. Kibana opened at login; no API requests executed.
Operational lesson search: performed for SS-6404 PREPROD Atlas book/info baggage; no matching trusted lesson applicable to this ticket and endpoint. No lesson applied.

Live Kibana discovery: user-filtered Atlas records, last 15 days; narrowed to method CheckBookingStatus. Successful logged candidates: AS US74GX, SM ER0XZ8, 6E ZXCMYU, F9 ML0MPQ. Raw JSON confirms masked orderNo. Historical log observations are setup evidence only, not PREPROD execution. Live clarification pending on replayability of masked requests.

User operational clarification: replay logged request unchanged; backoffice_id/PNR resolves masked orderNo. Approved initial inputs: AS US74GX, SM ER0XZ8, 6E ZXCMYU, F9 ML0MPQ, one retrieval each.

Alaska negative-weight finding: user requested paired request, AirAPI response and provider source evidence for their review; no sentinel acceptance or rejection provided. Classify this case WARN pending review, never PASS or FAIL by inference.
Executed remaining original logged requests: AS US74GX, 6E ZXCMYU, F9 ML0MPQ.

Retest explicitly authorized by user: retest. Same four original requests; one fresh retrieval per booking, no retries or input variation. allow_retest: true for this requested run. Previous artifacts preserved in runs/2026-10-26-initial.

2026-10-26 provider documentation supplied directly by user screenshot: baggageWeight is KG; 0 means no free baggage, -1 means no limitation on weight, positive means maximum weight. baggagePiece 0 means no piece limitation; positive means maximum pieces. Empty baggageSize means no limitation. This defines provider field semantics, not an operational lesson. Applied to saved fresh retest: Alaska weight -1 has no numeric weight limit in output; carry-on PASS. AS/F9 checked rows have both piece 0 and weight 0, so no-free-baggage rule supports their 0PC output. No new API execution.
