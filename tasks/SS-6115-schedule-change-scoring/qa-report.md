# SS-6115 QA dispatch

Release signal: PASS — 13 executed-check passes and 3 user-sign-off passes.

Run: 2026-10-12 | STAGE POST /v1/schedules | UA + BA / S / 1A1J | 16 PASS, 0 FAIL, 0 WARN.

16 PASS: 13 supported by executed checks and 3 accepted through explicit user sign-off (TC-03, TC-07, TC-10-JV). Eligible reroutes retain closest-time ordering; promotion, regular scoring, carrier scoring and cabin/date/class filtering were observed. TC-02 is PASS with no payload section. No additional API execution was performed for the signed-off cases.

Intended behavior, clarified by the user: when segment count stays the same and connection points change, consider time deviation in ranking; lower scores rank first. Equal-score reroutes may use time deviation as a tie-breaker. Promotion and preserved score/filter variables were executed. Disallowed V=2 under True, enabled-JV filtering and country-aware penalties remain unverified.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| RUN-01 | UA / S / 1A1J; two changed trips; normal mode | Returned choices contain no excluded trips | HTTP 200; 30 itineraries; 60 trips; 0 excluded | PASS |
| TC-02 | Three-segment reroute MSP-FRA-BRU-NBO to MSP-ORD-BRU-NBO; ruleId=2; U=2,V=2; identical counterpart trip | Lower scores first; equal-score eligible reroutes ordered by smaller time deviation | Matched score-5 alternatives occur in ascending deviation order: 20 / 1450 / 2990 minutes. PASS covers observed ordering, not activation of Closest Departure | PASS |
| TC-11a | All 60 normal-response trips | Minutes = max(abs(first departure delta), abs(last arrival delta)) | 60 calculations checked; 0 mismatches | PASS |
| TC-11b | Fresh run, trip 1, U=1,V=1,score=1 | Equal-score alternatives prefer smaller minute deviation | Returned positions 1 / 2 / 3: 1440 / 1567 / 2970 minutes; trip 2 identical | PASS |
| RUN-02 | Minimal UA expert request; explicit HK; one candidate | Usable scored response for controlled comparisons | HTTP 200; one candidate; U=1,V=1; score=1; 30 min; ruleId=2; excluded=false. Earlier multi-candidate requests remain empty-body evidence | PASS |
| TC-03 | Returned UA alternatives; country-aware penalty comparison | Same-country reroute receives softer penalty than cross-country reroute | User sign-off: accepted as PASS; no additional API execution. No matched same-country/cross-country pair with controlled other score inputs established | PASS |
| TC-12 | Normal response quality and representative trips | Top-level policy flag reflects in-policy non-excluded options for every changed trip | Top-level true; representative trip 1 true /20 min and trip 2 true /23 min; both non-excluded | PASS |
| TC-05 | BA expert reroute JFK-LHR-CDG to JFK-LGW-CDG; U=1,V=2; 30 min | True behavior: preserve actual V=2, score as V=1 | ruleId=46; V=2; score=1; excluded=false. Attachment identifies BA as True; deployed rule numbering differs | PASS |
| TC-06 | UA expert reroute; class H; U=1,V=2; 30 min | False behavior retains regular score 4 | ruleId=2; score=4; excluded=false; attachment UA rules 1/2 are False | PASS |
| TC-07 | BA True-behavior request plus attached policy allow-lists | V=2 is excluded when not explicitly allowed under True | User sign-off: accepted as PASS; no additional API execution. All attached True rows allow V=2; no restrictive True fixture available. Positive BA request remains eligible; negative branch not evaluated | PASS |
| TC-08 | BA unchanged routing and one-extra-stop; single candidate per request | True does not promote V=1 or added-stop V=3; regular scores 1 and 7 | ruleId=46; U=1,V=1 score=1; U=1,V=3 score=7; both excluded=false | PASS |
| TC-09 | BA reroutes, U=1 at 120 min vs U=5 at 30 min, separate requests | Carrier dimension retained: scores 1 versus 12 despite closer U=5 | Both ruleId=46 and non-excluded; scores 1 and 12. Combined response ordering not tested | PASS |
| TC-10-cabin | BA promoted reroute; segment 2 changed from Y to C | Cabin violation remains excluded under True | score=1; excluded=true; CabinFilterTerm reported (also booking-class violations) | PASS |
| TC-10-flex | BA promoted reroute; departure shifted +3 days and 30 min | Date-flex violation remains excluded under True | score=1; 4350 min; excluded=true; ReprotectionFlexTerm reported | PASS |
| TC-10-booking | BA promoted reroute; economy cabin with booking class J | Unacceptable booking class remains excluded under True | score=1; excluded=true; BclassFilterTerm reported | PASS |
| TC-10-JV | GET /algo/conf schedule_change plus BA control request | JV rejection remains enforced when enabled | User sign-off: accepted as PASS; no additional API execution. STAGE schedule_change.enable_jv=false; no enabled-JV fixture tested. Configuration was not changed | PASS |

Scope limits: no restrictive True row was found in the ticket attachment; every True row lists V=2. The deployed BA ruleId is 46, while attachment BA/Y rows are 48-50, so attachment numbering is not treated as the active configuration. Promotion is demonstrated by endpoint scores. GET /algo/conf exposes schedule_change.enable_jv=false; no configuration was changed. TC-09 verifies score preservation across separate requests, not combined response order. Expert fixtures are synthetic and do not claim live flight schedules. Cabin rejection also has booking-class violations. BR exact replay, V=6 mapping, country comparison and unchanged-trip regression remain unexecuted.

## Paired evidence and rerun

TC-03 user-sign-off PASS: request-normal.json + normal-response.json. TC-07 user-sign-off PASS: tc05-true-request.json + tc05-true-response.json, alongside policy-ticket-attachment.csv (no negative fixture). TC-10-JV user-sign-off PASS: schedule-change-config-evidence.json plus BA control pair. Successful expert setup: request-expert-minimal.json + expert-minimal-response.json. Original empty-body attempts remain preserved; their cause is not established. Other executed cases have matching tc*-request.json and tc*-response.json files; assertions recorded in policy-checks.json.

Import SS-6115.postman_collection.json, supply auth_login/auth_password privately, and select the matching request and CSV row. Collection assertions were authored after direct HTTP execution; Newman was not run. All credentials omitted from artifacts.

