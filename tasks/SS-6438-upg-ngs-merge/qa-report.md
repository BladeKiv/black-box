SS-6438 — Build UPG itineraries as main itineraries with NGS children (regular + upgrade options)

PASS — 8 PASS / 0 FAIL / 0 WARN in the included scope
PREPROD | 2026-11-02 | 13 merge-enabled + 2 disabled baseline + 1 extra=false Searches | BCKDCR / AKKDCR

Intended behavior: With matching mergeWithRegular=true, the cheapest retained option is the main, and each retained child improves bags, exchange or refund without losing another feature. Other UPG children require keepBothBagOptions=true. With mergeWithRegular=false, preserve the user-selected SS-6437 identifier baseline: BCKDCR mains do not combine UPG and NGS; AKKDCR upgrade children contain both markers. The user-confirmed singleton :UPG# exception applies. Explicit extra=false suppresses NGS options despite mergeWithRegular=true; feature metadata is evaluated separately.

PASS within the approved executed scope: enabled merge behavior and the disabled SS-6437 baseline. All 19 previously failing itineraries were matched and no longer show retained-feature regressions. Unsuccessful inventory searches and unobservable scenarios are excluded from the result table and totals by user instruction.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | Example 1 · BCKDCR · UPG cheapest · keepBothBagOptions=false | Retain regular improvements under the UPG-cheapest main; each transition improves one feature without losing another. | 198 observed UPG-containing groups; no retained-feature violations. | PASS |
| TC-02 | Example 2 · AKKDCR · UPG cheapest · keepBothBagOptions=true | Filter any later option that loses bags, exchange or refund versus the last retained option. | 236 observed UPG-main groups; no retained-feature violations. | PASS |
| TC-05 | 434 observable UPG-containing groups · 784 retained USD options | Prices ascend; main is cheapest among retained options. | 434 groups / 784 retained USD options; no price-order violations within the returned groups. | PASS |
| TC-06 | Returned children · configured eligibility · numbering/singleton rule | Children match their main flights. Other UPG children require keepBothBagOptions=true. Numbered groups are sequential; singleton :UPG# is allowed. | 0 same-flight, child-eligibility or numbering violations. | PASS |
| TC-08 | Exact flight sequences of the 19 historically failing groups | Find the same itineraries and verify their current retained options satisfy the confirmed feature rule. | All 19 previously failing exact flight sequences matched; their current retained options satisfy the confirmed feature rule. | PASS |
| L01-B | {"adt": "1", "cabin": "C", "fl[0][o]": "SFO", "fl[0][d]": "FRA", "fl[0][dt]": "2027-02-25", "cid": "BCKDCR", "debug": "1", "original_cid": "1"} | No BCKDCR main gdsOfferId combines UPG and NGS. | HTTP 200; 209 mains; 13 UPG parents; 0 UPG children; 0 invalid identifiers; 0 upgrade parents missing children. | PASS |
| L01-A | {"adt": "1", "cabin": "C", "fl[0][o]": "SFO", "fl[0][d]": "FRA", "fl[0][dt]": "2027-02-25", "cid": "AKKDCR", "debug": "1", "original_cid": "1"} | Each AKKDCR upgrade ngsItineraries child gdsOfferId contains both UPG and NGS; observe children to evaluate the baseline. | HTTP 200; 211 mains; 13 UPG parents; 13 UPG children; 0 invalid identifiers; 0 upgrade parents missing children. | PASS |
| EXTRA-01 | BCKDCR · mergeWithRegular=true · extra=false · SFO-FRA 2027-02-25 · 1 ADT / C | extra=false returns no NGS options even when the matching CID has mergeWithRegular=true. | 199 results; ngsItineraries is absent from every result; no NGS offer identifiers. ngsFeatures/ngsMap metadata remains present and is not counted as an itinerary option. | PASS |

Scope exclusions

- Positive regular-cheapest merge branches with keepBothBagOptions=false and true.
- Complete pre-filter candidate-set elimination/retention completeness.

Supporting evidence and rerun

Enabled checks: runs/2026-11-02-post-fix/ (13 paired Search captures, configuration-enabled.json, all-previous-failures-comparison.json). Disabled SS-6437 baseline: runs/2026-11-02-warn-and-disabled/L01-B.json, L01-A.json, configuration-legacy.json. Enabled and disabled modes were tested at different verified configuration states.

Earlier failure and unsuccessful exploration evidence remains archived and is not relabeled PASS. This consolidation performs no live requests. No configuration, booking, Jira or knowledge-ledger changes.

Run collection.json with expected-outcomes.csv grouped by mode, under the matching manually verified configuration. Downloads are embedded in the HTML dispatch.
