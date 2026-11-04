SS-6438 — Build UPG itineraries as main itineraries with NGS children (regular + upgrade options)

WARN — PARTIAL COVERAGE | 7 PASS / 0 FAIL / 3 WARN
PREPROD | 2026-11-02 | HTTP Search | 5 calls · 3 routes · 2 CIDs | merge=true

Intended behavior: For an itinerary with UPG options, choose the cheapest eligible regular or UPG option as main NGS#1; retain successive options only when all three features are at least equal and one is better. Regular children require ngs_jobs; other UPG children also require keepBothBagOptions=true. A singleton UPG main may remain :UPG# under the user clarification.

Five fresh PREPROD Searches returned 1,087 main results. All checked retained-output rules pass across 60 UPG-containing groups and 158 options: 64 regular children and 34 UPG children. Regular-cheapest branches and complete pre-filter candidate elimination remain unverified.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | M01/M03 · BCKDCR · keepBothBagOptions=false · SFO-FRA / LAX-MUC | UPG-cheapest main with qualifying regular children; numbered main is NGS#1 when children exist. | 26 UPG groups: 18 with regular children, 8 valid singletons; 26 regular children total. All 18 multi-option groups use main :UPG#:NGS#1. | PASS |
| TC-02 | M02/M04/M05 · AKKDCR · keepBothBagOptions=true · SFO-FRA / LAX-MUC / ORD-FRA | Retain eligible regular and other UPG options; cheapest returned option is main NGS#1. | 34 groups: all UPG mains; 34 two-bag UPG children and 38 regular children. All 34 mains are NGS#1 with sequential child identifiers. | PASS |
| TC-03 | 60 returned UPG-containing groups · 158 retained USD options | Prices ascend within each group; main is cheapest among returned options. | 60/60 main minima and 98/98 retained transitions satisfy prices.totalPrice ordering. | PASS |
| TC-04 | User-confirmed bags / exchange / refund fields · 98 retained transitions | Each retained child is no worse on all three features and better on at least one than the last kept option. | 98/98 transitions strictly improve the confirmed feature vector. No equal-feature or feature-losing retained transition. | PASS |
| TC-05 | 60 group mains and 98 children; exact flights, airports and departure/arrival times | Children belong to the same itinerary; one returned main for each exact flight sequence in these groups. | 98/98 child flight sequences match their main. No other top-level result shares any of the 60 group flight sequences. | PASS |
| TC-06 | BCKDCR · 26 groups · keepBothBagOptions=false | Other UPG options are not retained as NGS children. | 0 UPG children across 26 groups; the retained children are regular options. | PASS |
| TC-07 | Eight singleton BCKDCR UPG groups in M01/M03 | User clarification: :UPG# alone is valid when no children remain. | 8/8 singleton mains have gdsOfferId=:UPG# and no retained children. | PASS |
| TC-08 | M01/M03 · BCKDCR · keepBothBagOptions=false | Ticket example 3: a qualifying regular-cheapest option becomes main; UPG/regular improvements become children. | 0 regular-cheapest groups among the 26 observed groups. User confirmed no example is available; branch untested. | WARN |
| TC-09 | M02/M04/M05 · AKKDCR · keepBothBagOptions=true | Ticket example 4: a qualifying regular-cheapest option becomes main; eligible UPG/regular improvements become children. | 0 regular-cheapest groups among the 34 observed groups. User confirmed no example is available; branch untested. | WARN |
| TC-10 | Five final Search responses · candidate elimination/completeness | Verify excluded equal-feature higher-price and feature-losing candidates against the complete pre-filter candidate set. | Final retained chains satisfy the rule, but responses do not provide a certified pre-filter candidate baseline. Complete elimination and retention completeness are unverified. | WARN |

Supporting evidence and rerun

M01.json–M05.json contain paired sanitized requests/responses. merge-analysis.json contains per-group feature/price excerpts. configuration-merge-enabled.json verifies only prerequisites, not per-request execution. The earlier blocked preparation is preserved in initial-blocked-qa-report.md/html and initial-blocked-results.json.

Run collection.json with expected-outcomes.csv in Postman using the existing PREPROD environment. No provider-level tracks. Downloads are embedded in the HTML dispatch.

Comparators: keys.baggage.allowPieces, penalties.exchange, penalties.refund; prices.totalPrice in USD. Search keys remain opaque. Same-flight check uses returned airports, times, marketing airline and flight number. Singleton exception and regular-cheapest WARN decisions were confirmed live by the user.

No retry, polling, downstream endpoints, configuration mutation, booking, or Jira write was performed. No matching operational lesson applied. Prior transport failures were from the inherited localhost proxy; direct HTTP access succeeded under the current explicit user authorization.
