# AirAPI black-box QA evidence ledger

Consolidated 2026-10-19 from saved reports. Approval: user instruction in this
chat on 2026-10-19, "make the changes now and update the necesary files" expressly
authorizes this consolidation now. Future updates retain the AGENTS.md approval
workflow unless the user explicitly overrides it.

Ticket/spec text remains the sole intended-behavior source. These historical
observations are not a global behavior contract or proof of current deployment
state. No endpoint was executed for this consolidation. See [reuse guide](airapi-qa-reuse.md).

## Evidence index

Paths are relative to the repository root. Preserve previous evidence and reuse
only within the named scope. Report PASS does not cover exclusions.

### SS-6115

- Source: [SS-6115-schedule-change-scoring/qa-report.md](../tasks/SS-6115-schedule-change-scoring/qa-report.md)
- Observed result: 2026-10-12 STAGE: 16 PASS = 13 executed checks + 3 user-sign-off passes.
- QA consequence and limits: Lower scores precede time tie-breaks. Synthetic scoring fixtures; TC-03, TC-07 and TC-10-JV not API-verified.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6258

- Source: [SS-6258-routing-classification/airapi-ss-6258-qa-report.md](../tasks/SS-6258-routing-classification/airapi-ss-6258-qa-report.md)
- Observed result: 4 PASS; 453 boolean routingInversion flags: 301 false / 152 true.
- QA consequence and limits: Flag under keys.commission_info.fareCalculation; displayed fares retain physical order. Numeric logging proposal superseded.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6290

- Source: [SS-6290-tech-stop-elapsed-time/airapi-tech-stop-elapsed-time-qa-report.md](../tasks/SS-6290-tech-stop-elapsed-time/airapi-tech-stop-elapsed-time-qa-report.md)
- Observed result: Historical task Markdown: FAIL for missing elapsedTime. Release index separately records PASS.
- QA consequence and limits: Conflicting historical versions: preserve both. Resolve exact release report and approved offset formula before reuse; no fresh retest performed.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6296

- Source: [SS-6296-cms-dump-validation-pcc/airapi-ss-6296-qa-report.md](../tasks/SS-6296-cms-dump-validation-pcc/airapi-ss-6296-qa-report.md)
- Observed result: 5 PASS: W2GM/6NVG no applied commission; 8C4T fee amount 10, deduct false, aggregate commission zero.
- QA consequence and limits: Historical rule state only. Aggregate zero does not imply absence of non-deductable fees.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6309

- Source: [SS-6309-cms-route-inversion-update/airapi-ss-6309-qa-report.md](../tasks/SS-6309-cms-route-inversion-update/airapi-ss-6309-qa-report.md)
- Observed result: TC-19 and TC-22 FAIL: inventory returned but routingInversion absent.
- QA consequence and limits: 26 importable scenarios are not 26 executed passes. Missing required flag is FAIL despite available inventory.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6332

- Source: [SS-6332-ndc-mapping/qa-report.md](../tasks/SS-6332-ndc-mapping/qa-report.md)
- Observed result: 12 executed PASS across 11 Search calls; report remains IN PROGRESS.
- QA consequence and limits: Search-only gds/pcc/cons assertions. Missing-cabin and exact pricing not certified. Excluded CID/source_cons wildcard positive cases are withdrawn. Later user overall sign-off in memory does not supply missing execution.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6340

- Source: [ss-6340/qa-report.md](../tasks/ss-6340/qa-report.md)
- Observed result: 15 PASS: DEV OW/RT/MC crossed with five passenger mixes; two rows reuse earlier live evidence.
- QA consequence and limits: Submit selected Search object unchanged to Result; retain complete keys.brightsun. Errors 112/113 excluded. No booking in this ticket.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6341

- Source: [ss-6341/qa-report.md](../tasks/ss-6341/qa-report.md)
- Observed result: 2026-10-01 DEV: 6 PASS booking scenarios, five additional plus one earlier capture.
- QA consequence and limits: References: data.additionalInfo.recLoc and brightsunReference. On observed 422 Price change, update only trip.total_price from data.response.total_price and retry once. TC-07 vendor mapping excluded. Old booking permission does not authorize new bookings.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6344

- Source: [ss-6344/qa-report.md](../tasks/ss-6344/qa-report.md)
- Observed result: 2026-10-01 DEV: 4 PASS for malformed token/offer IDs in Result and book/create.
- QA consequence and limits: Observable recovery retained airports, dates, airlines, flight numbers, checked baggage and before exchange/refund permissions. Same-flight timing changes user-accepted. Internal Search not directly visible; expired-token/no-match/vendor mapping untested.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6348

- Source: [SS-6348-ngs-features-breakdown/report.md](../tasks/SS-6348-ngs-features-breakdown/report.md)
- Observed result: 7 PASS: baseline 560 plus broader 7,514 references, zero invalid.
- QA consequence and limits: Resolve populated one-based trip:segment references against actual segments. Broader searches omit val_cr. Missing optional features are not validated coverage.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6373

- Source: [SS-6373-cabin-revalidation/qa-report.md](../tasks/SS-6373-cabin-revalidation/qa-report.md)
- Observed result: 2026-09-30 PREPROD: 4 PASS.
- QA consequence and limits: Same booking classes: replace empty cabins; preserve populated/mixed cabins. GDS G to S establishes ticket-approved revalidation precondition; unchanged GDS inconclusive. Null merged with empty only under ticket clarification.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6389

- Source: [SS-6389-cms-average/qa-report.md](../tasks/SS-6389-cms-average/qa-report.md)
- Observed result: 2026-10-12 DEV: 2 PASS. 9%/7% produced 8%/8% in 8 qualifying results; 9%/9% produced 9%/9% in 16.
- QA consequence and limits: Other commissions remained missing; explicit zero-percent input untested. Inspect returned fare blocks before identifying a needed rule change.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6390

- Source: [SS-6390-atlas-baggage/qa-report.md](../tasks/SS-6390-atlas-baggage/qa-report.md)
- Observed result: DEV dimension fix verified: 9 PASS. PREPROD 2026-10-13 existing-booking retrieval remains WARN.
- QA consequence and limits: Source 55*40*24 cm mapped to total 119 cm / 46 in; 46 or 47 accepted for this case. DEV cash 408 Retry explicitly accepted. PREPROD certificate failure preceded application response; see runs/2026-10-13-preprod-book-info/qa-report.md.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6394

- Source: [SS-6394-amadeus-ndc-baggage/runs/2026-10-19-preprod-retest/qa-report.md](../tasks/SS-6394-amadeus-ndc-baggage/runs/2026-10-19-preprod-retest/qa-report.md)
- Observed result: 2026-10-19 PREPROD: 15 PASS / 0 FAIL / 0 WARN; 15 fresh source pairs / 43 segments. AF fix verified.
- QA consequence and limits: AF both segments: checked 158 cm / 62 in; carry-on 115 cm / 45 in. Earlier 2026-10-16 distinct-airline 17 PASS / 1 FAIL / 2 WARN preserved. New scope does not resolve unretrievable 6E/OS cases. CHD/JNF, PriceClass fallback and personal-item exclusion not certified. TLS exception run-specific.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6401

- Source: [SS-6401-commission-optimization/runs/2026-10-15-tstcom-reviewed/qa-report.md](../tasks/SS-6401-commission-optimization/runs/2026-10-15-tstcom-reviewed/qa-report.md)
- Observed result: Reviewed 180 PASS / 0 FAIL / 0 WARN; 30 scenarios x 3 paired repetitions.
- QA consequence and limits: Reclassification of saved requests, not fresh execution. Exact TSTCOM allowances in ticket-scope.md only. F-90 equivalence limited to named SFO-MUC/MUC-SFO OD with equal applied amounts/other fields; user-approved expectation, not proof of randomness. No CPU/allocation or internal candidate-filter verification.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

### SS-6408

- Source: [SS-6408-bag-options/qa-report.md](../tasks/SS-6408-bag-options/qa-report.md)
- Observed result: 2026-10-19 STAGE: 7 PASS, TC-05 through TC-11.
- QA consequence and limits: Both flags true: 24 one-piece parent/two-piece child pairs, 48 distinct keys, matching flight/fare fields. secondBag true + keepBoth false/omitted: two-piece upgrade parents/no children. secondBag false + keepBoth true/false: one-piece upgrade parents/no children. Confluence documentation untested; supersedes setup-only memory for this scope.
- Approval: 2026-10-19 consolidation instruction above; historical test acceptance remains as documented in source.

## Additional provenance boundaries

- Release evidence: `releases/SS_API-v6.37.0/affected-endpoints.md` records
  SS-6290, SS-6296 and SS-6258 confirmed release PASS. This does not erase the
  earlier SS-6290 task Markdown failure. Consult both versions before reporting.
- SS-6266 appears in older memory but has no ticket directory in this checkout.
  Retrieve original evidence before reuse; partial commission-debug outcomes
  must not be promoted to PASS.
- Future entries need date, source, scope, observed fact, sanitized evidence paths,
  QA consequence, exclusions, supersession and approval reference. Do not store
  credentials, private payloads, hypotheses or source-code-derived claims here.
