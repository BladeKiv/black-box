# SS-6401 source and QA boundaries

Source: user-supplied ticket description and comments from https://traveldev.atlassian.net/browse/SS-6401, 2026-10-13. The authenticated Jira page was not independently retrieved.

Intended behavior: Cut commission CPU and allocations without changing which rules match or commissions applied.

Ticket areas: cheaper validating-carrier/fare-owner/passenger/booking-class checks; fare-code matching with ticket-designator stripping; travel-date filtering; fare-owner indexing; grouped backing array; lazy per-fare result maps; flight segment pointer passing; rejection formatting only when tracked. Applying commissions: copy trips only for ticket codes; refresh price element once per commission; construct log fields only for debug logging.

Ticket comments report equivalence dumps, randomized/mutation-checked equivalence tests and interleaved benchmarks. Reported historical profiles show commission CPU share changing from 14.3% to 7.5% under different traffic. Those are ticket-author claims, not this black-box run's verified CPU measurements.

User-authorized oracle: old PROD output is correct. User confirmed identical rule source on both environments and corrected the active CID to TSTCOM. Broad Search-only runs omit gds, pcc, fare and val_cr filters. All exposed commission entries for every passenger and consolidator are compared on identical exposed inputs; only matching final returned results can be assessed. Rejected/retained candidate-filter sets are not exposed by these response objects, so this QA does not claim direct equality of every internal filtering decision.

Observable timings: end-to-end response time; top-level excutionTime; timing[].executionTime for process labels beginning 'Commission service processed '. The label also supplies processed/returned result counts. Durations are wall time, not CPU samples or allocations. Host differences, provider/cache effects and different inventory workloads limit performance attribution.

No application source inspected, rules/configuration mutated, booking endpoints called, or speculative edge-case fixtures added. No QA ledger update authorized.

## 2026-10-15 rerun acceptance

User requested a fresh TSTCOM rerun retaining previous exemptions, with USD 1 tolerance. User explicitly confirmed the tolerance applies to totalPrice/totalTax and passenger breakdowns. Segment fees, other commission values and non-USD amounts remain exact. Prior evidence is preserved in its original run directories; latest evidence is runs/2026-10-15-tstcom-usd1/.

## 2026-10-15 user review of remaining findings

User confirmed PROD duplicates segment references for both trip IDs 1 and 2. Ignore exact duplicate references on PROD only; PREPROD segmentFees.amount/fullAmount must be equal to or lower than PROD, with other fee metadata checked. Missing-PROD/additional-PREPROD commBreakdown objects/entries are accepted; no requirement to introduce a breakdown when none is returned. Accept equal-amount duplicate rules 4989/4926 and their subRule/combKey differences (original F-61/F-71). Extend USD 1 tolerance to priceElement.Assets.Commission.ValuePerPax.<pax>.amount (original F-83/F-89). Original F-90 remains unexempted pending inspection.

Reviewed evidence is a reclassification of the same 180 successful requests, stored in runs/2026-10-15-tstcom-reviewed/. Original report and F-IDs are preserved in runs/2026-10-15-tstcom-usd1/. A separate 12-request Search reproduction uses the original TC-28 query, then gds=A, pcc=YVRG32400 and val_cr=BA; it retains complete historical/fresh selected results with commission_info for both trips. No provider-level endpoint or booking request was added.

## 2026-10-16 F-90 user confirmation

User confirmed TC7A and AJBUPY rules apply the same commission amount for the provided OD and are randomly selected. Mark F-90 PASS. Accept the observed VZC upfront outbound 5561/37750/TC7AIB/TC7A and 4065/28486/AJBUPY/AJBUPY choices for SFO-MUC, and the corresponding return 5556/37713/TC7AOB/TC7A and 4065/28486/AJBUPY/AJBUPY choices for MUC-SFO, only with equal applied amounts and otherwise equal commission fields. This is user-confirmed expected behavior applied to saved evidence, not a fresh API rerun or an independent verification of randomness. Full responses and historical captures remain preserved. No QA ledger change.
