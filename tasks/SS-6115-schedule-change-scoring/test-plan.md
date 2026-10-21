# SS-6115 — Schedule-change scoring test plan

Release signal: NOT EVALUATED — no API tests executed.

Scope/run: STAGE (deployment reported in Jira comments) | POST /v1/schedules | Prepared 2026-10-12 | Eligibility, scoring, ordering and documentation.

The Jira description and all five displayed comments were read, together with the developer-linked Confluence specification updated October 7. The original requirements and documented implementation differ; both are made visible below rather than silently replacing ticket acceptance criteria.

## Intended behavior and clarified rules

The ticket requires time deviation to worsen the score itself, same-day/in-policy alternatives to outrank days-away alternatives, and softer penalties for same-country connection swaps than cross-country swaps. The first result must be the best valid alternative.

The comment adds Closest Departure=True/False to the schedule-policy CSV. True must not admit a connection change outside the policy allow-list or bypass other scoring variables.

The linked specification clarifies:

- Lower score is better. V is `changeConnectionPoints`; U is `changeOperatingMarketing`.
- V=1: identical airport sequence and segment count. V=2: different airports, same segment count. V=3: exactly one added segment. V=4 is described as unsupported; fewer segments produce V=-1. V=6 is not defined. The comment example `1/3/6` must not be interpreted as three known connection scenarios.
- Closest Departure=True promotes only V=2: score using the V=1 column while retaining actual V=2 for policy eligibility. V=1 and V=3 retain regular scores. False uses the regular U×V table.
- For U=1: regular V=1/2/3 scores are 1/4/7. With True, allowed V=2 scores 1. For U=5, promoted V=2 scores 12, so it remains behind U=1 regardless of proximity.
- `scheduleChangePolicyMins` is the larger of departure and arrival differences in minutes. It is not simply departure proximity.
- Per-trip sorting is score ascending, then `scheduleChangePolicyMins` ascending. Full itineraries sort by aggregate score; the exact aggregate formula and full-itinerary tie-break are not documented.
- `scheduleChangePolicy` controls refund eligibility. The representative `quality.scheduleChangePolicyItinerary` uses in-policy first, then score, then time difference. The documented main `results` ranking does not use policy eligibility as its first sort key.
- Expert alternatives can be supplied in `expertTrips[]` to avoid live GDS inventory. Expert mode forces debug; rejected candidates may appear with `quality.excluded=true` and `violations`. Their appearance is not a filtering failure unless offered as valid.

## Specification discrepancies requiring developer/product resolution

1. Time remains a tie-breaker in the documented implementation. A and B can both score 1; this can fix their order without fulfilling the requirement that time deviation contributes to the score.
2. All V=2 reroutes receive the same promotion; no country-aware distinction is documented.
3. The comment's V allow-list example includes 6, which the documented V mapping does not define.
4. Best-first per-trip sorting does not establish best-first full itineraries when aggregate scores tie. The documented representative itinerary may not be present in the size-limited results array.

These are specification findings, not executed API FAILs. Retain the original requirement checks until an explicit scope decision supersedes them. No Jira comments or external messages were posted.

## Reproduction data

Booking `UNDE8FAF1C`; validatingCarrier BR; changed trip 2; original SGN→TPE→LAX→DEN, departure 2026-08-14 12:50.

| Option | Routing | Departure | Historical score | V | scheduleChangePolicyMins | scheduleChangePolicy |
|---|---|---|---|---|---|---|
| A | SGN→TPE→LAX→DEN | 2026-08-08 | 1 | 1 | 8465 | false |
| B | SGN→TPE→SFO→DEN | 2026-08-14 | 4 | 2 | 95 | true |

Required ranking: B before A. Historical dates require replay fixtures; do not present a substituted future-date run as the exact reproduction. Preserve supplied minute values unless the complete original and candidate timestamps justify recalculation.

## Planned test-case results

NOT RUN is a planning marker. Every executed case will receive exactly one PASS, FAIL or WARN verdict.

| ID | Test data / action | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | Replay BR trip 2 with A and B, U=1, V=1/2 explicitly allowed, Closest Departure=True; other policy checks satisfied. | B precedes A. Documented implementation scores both 1 and prefers 95 over 8465 minutes. Assess score contribution separately in TC-02. | Not executed | NOT RUN |
| TC-02 | Otherwise identical valid U/V alternatives with same-day versus days-away deviation. | Original requirement: larger deviation worsens score itself. Equal scores sorted by minutes alone do not satisfy this requirement. | Not executed | NOT RUN |
| TC-03 | Matched same-country LAX→SFO and cross-country reroutes, with equal U, segment count, minutes and other inputs. | Original requirement: same-country change receives softer penalty than cross-country change. No numeric penalty is prescribed by the ticket. | Not executed | NOT RUN |
| TC-04 | Inspect applicable policy CSV rows for both exact Closest Departure values True and False. | New column is supported with both values. Treat configuration inspection separately from endpoint assertions. | Not executed | NOT RUN |
| TC-05 | Allowed U=1,V=2 candidate; Closest Departure=True. | Actual V remains 2 for eligibility; score is 1 rather than regular score 4. | Not executed | NOT RUN |
| TC-06 | Same matched candidate with Closest Departure=False. | Regular U=1,V=2 score is 4. | Not executed | NOT RUN |
| TC-07 | U=1,V=2 closest candidate with policy V allow-list excluding 2, including comment example 1/3/6. | Candidate is rejected despite True. In normal mode absent; in forced debug/expert mode excluded=true with violation evidence, never offered as valid. | Not executed | NOT RUN |
| TC-08 | Allowed U=1,V=1 and U=1,V=3 candidates under True. | Scores remain 1 and 7 respectively; True does not promote the added stop. | Not executed | NOT RUN |
| TC-09 | Allowed U=1 and U=5 reroutes with True, giving U=5 the closer time. | U remains effective: scores 1 versus 12; U=1 ranks ahead of U=5 despite greater deviation. | Not executed | NOT RUN |
| TC-10 | Allowed promoted V=2 candidates that separately violate each active booking-class, cabin, date-flex and JV policy check. Use matched valid controls. | True bypasses none of those checks; invalid candidates remain excluded. Use applicable preconfigured policies, not invented constraints. | Not executed | NOT RUN |
| TC-11 | Equal-score eligible alternatives with known full departure/arrival timestamps and different minutes. | Per-trip order is ascending by scheduleChangePolicyMins; verify reported minutes against the larger departure/arrival difference. | Not executed | NOT RUN |
| TC-12 | In-policy and out-of-policy valid candidates under a documented refund threshold, with controlled scores/minutes. | Representative selection prioritizes in-policy, then score, then minutes. Top-level flag is true only if every changed trip has an in-policy non-excluded option. Do not infer identical policy-first sorting for results. | Not executed | NOT RUN |
| TC-13 | Original two-trip itinerary with unchanged trip 1 and changed trip 2; multiple valid equal-score alternatives for trip 2. | First full itinerary contains the best valid alternative; B precedes A. Capture aggregate scores and array positions to detect lost tie ordering after merge. Unchanged trip is preserved. | Not executed | NOT RUN |
| TC-14 | Compare best returned itinerary with all returned candidates and the representative itinerary; inspect exclusion annotations. | First offered option is valid and no other valid candidate is better under confirmed ranking rules. Never equate a debug-excluded option with an actionable choice. | Not executed | NOT RUN |
| TC-15 | Review published technical document and folder placement. | Document is under SS Smart Search / Endpoints and explains request/response objects, selection, filtering, scoring, sorting, Closest Departure and policy-flag influence. Resolve original-requirement discrepancies before full acceptance. | Not executed | NOT RUN |

TC-10 covers the comment's explicit preservation of other rules, not an unrelated general endpoint validation suite. No speculative malformed-input tests are included.

## Setup and execution

1. Use STAGE. Obtain its approved base URL/authentication convention without exposing credentials; no endpoint execution is part of this plan request.
2. Use POST /v1/schedules with original `trips[]`, tripId, segments, scheduleChange=true on affected segments, cabin, validatingCarrier, paxCnt and issueDate. Include required segment identifiers, airports, timestamps, carriers, flightNumber, bookingClass and cabin. Use documented gds/pcc when applicable.
3. Prefer `expertTrips[]` for controlled score/filter comparisons and historical replay. Validate the exact expert-trip schema before constructing payloads. Account for forced debug in filtering assertions.
4. Select existing policies that cover the required U/V and Closest Departure branches. Record matched ruleId and relevant sanitized CSV fields. Do not mutate policy configuration or inspect application source.
5. Capture sanitized request/response pairs, original and candidate trips, `results[].trips[].quality`, trip scores, actual V/U, policy flags/minutes, exclusions/violations, aggregate score where exposed, and result positions. The exact aggregate score JSON path requires a response sample; do not guess it.
6. For every endpoint FAIL/WARN, include paired request/response evidence, with unavailable responses stated explicitly. Do not book or reissue tickets.
7. After execution, generate the dispatch report and matching HTML using templates/airapi-qa-dispatch-template.html. Keep all artifacts in this ticket directory. The ledger requires separate two-stage approval.

The documentation page and Endpoints folder currently exist; that confirms publication/placement, not runtime correctness or full requirement compliance. The attached policy CSV is listed in Jira; its actual row content has not been verified.

## Sources read

- Jira description and five displayed comments: https://traveldev.atlassian.net/browse/SS-6115
- Developer-linked specification, updated October 7: https://traveldev.atlassian.net/wiki/spaces/PDS/pages/3735879681/POST+v1+schedules+-+Schedule+Change
- Observed Endpoints folder: https://traveldev.atlassian.net/wiki/spaces/PDS/folder/3735846913
- Project boundaries: knowledge/airapi-contract.md and knowledge/airapi-qa-memory.md.

## Acceptance clarification — 2026-10-12

The user clarified that the change targets alternatives with the same segment count and changed connection points. Lower scores rank first; observed equal-score reroutes use time deviation as a tie-breaker. Do not treat equal scores at different deviations as a failure by themselves. TC-02's earlier score-growth expectation is superseded by this clarification; evaluate eligible reroute ordering instead. The original wording above is retained as source history, not the active score-growth oracle. Closest Departure activation, allowed changes and country-aware penalties still require their own evidence.
