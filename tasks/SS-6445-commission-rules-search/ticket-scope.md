# SS-6445 /v1/commission/rules - possibility to request specific rules

Source: https://traveldev.atlassian.net/browse/SS-6445 read 2026-11-03.
Intended behavior: retrieve specific requested commission rules using POST /v1/commission/rules/search with JSON {"ids":[563,1900]}, per developer comment. Existing GET /v1/commission/rules returns all rules.
Environment: DEV, explicitly confirmed by user 2026-11-03.
Flow: GET all rules as read-only baseline; POST requested subsets; compare returned IDs and complete rule objects with baseline. No flight Search or downstream endpoint belongs to this flow, so five Search examples are inapplicable. Prepare five relevant rule-filter examples: [563,1900], [563], [1900], another existing singleton, another existing pair. Resolve the latter from baseline before execution.
Scope: positive existing-ID retrieval only; no unknown, malformed, missing, empty or duplicate-ID edge cases. No exact HTTP-code expectation beyond usable successful responses. No ordering requirement.
allow_retry: false
allow_poll: false
allow_retest: false
approved_inputs: positive existing IDs from baseline and ticket example [563,1900].
Budgets: one baseline GET and up to five independent POST examples; each case has one request, zero retries. Max operational steps per case: 4.
Authentication: runtime local DEV Postman environment reference in knowledge/local-environment-references.json; no secret persistence. Standing user HTTPS TLS-bypass authorization supplied explicitly.
Lessons: search SS-6445/dev/commission returned no matches. No service-scope.json exists for this ticket.

Preparation observations: initial sandbox connection refusal had no HTTP response. A separate network-access check reached DEV successfully (HTTP 200); no application-response retry performed. Baseline rules has 16 top-level objects across group keys 81 and 95. Ticket-example POST returned empty rules; ID mapping clarification requested live. Environment answer DEV is ticket scope only and is not learned as operational permission.

User confirmed ids selects top-level rules[].Id on 2026-11-03. Five prepared positive examples: [8378], [7839], [8378,8379], [7839,7840], [8378,7839]. Approved replacements use existing DEV IDs. Expected exact requested ID set and unchanged rule content relative to baseline; no assertion about other top-level metadata or ordering.

User-approved comparator (2026-11-03): FlightApplicationGroup.Rules[].codeshare.Airlines[].Marketing and .Operating compare by code membership and counts, ignoring order. All other fields and arrays remain exact. This expectation is stored in ticket scope only, never operational lessons. Re-evaluate saved responses; no API rerun.
