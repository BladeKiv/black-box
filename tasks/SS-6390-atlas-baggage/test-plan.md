# SS-6390 — Atlas baggage and carryOn breakdown

Release signal: FAIL — see qa-report.md and qa-report.html for the completed six-step DEV run.

Scope/run: DEV sandbox | Atlas AirAPI Book | Prepared 2026-10-12 | Ticket mapping and explicit examples only.

## Executed scope superseding the preparation below

The user supplied `${AIRAPI_LOCAL_REFERENCE} APIs.postman_collection.json` and instructed use of SERVICE APIs TEST ENV only, with exactly Search → Result → Book/Create → Book/Info → Ticket/Create (cash) → Book/Info. This flow was executed once on the established DEV host, using the imported NYC → MAD route with its expired date moved to 2026-11-11. The selected live itinerary was EI EWR → DUB → MAD for one ADT. No additional inventory matrix or ticket retry was executed. The planned example cases below remain coverage targets, not executed PASS results. Previous-task DEV booking authentication was recovered in-process; credentials are absent from deliverables. Full observed results and evidence are in the dispatch report.

## Intended behavior

Starting at Book, return `baggage` and `carryOn` in book format at `data.response.pnrInfo.segments[]`, as evidenced by the ticket's expected `new.json` attachment. Match Atlas `segmentNo` to output `segmentNumber`; source `passengerType: 0` maps to `ADT`.

For `StandardCheckInBaggage`, preserve kilograms, round kilograms × 2.20462 to pounds, extract total centimetres from `L+W+H<=158cm`, and round centimetres ÷ 2.54 to inches. `baggageAllowance` is unpadded; `baggage.ADT.numberOfPcs` is two-digit padded. For `CabinBaggageOverheadLocker`, preserve kilograms, leave pounds null, sum dimensions such as `55*35*25cm`, and round their total ÷ 2.54 to inches. Carry-on piece counts are unpadded. Both full-text fields are explicitly null where Atlas has no equivalent. Do not treat missing fields as null or `{}`.

## Ticket-scoped test cases

| ID | Test data | Expected result | Actual result | Execution state |
|---|---|---|---|---|
| TC-01 | Source segment 1, passengerType 0; checked 1 piece, 15 kg, `L+W+H<=158cm`; carry-on 1 piece, 7 kg, `55*35*25cm` | Correct segment/ADT mapping. Checked allowance `1P`, numberOfPcs `01P`, weightKg 15, weightLb 33, lengthCm 158, lengthInch 62. Carry-on allowance/numberOfPcs `1P`, weightKg 7, weightLb null, lengthCm 115, lengthInch 45. Full-text fields null. | No live response captured | NOT RUN |
| TC-02 | Ticket zero-baggage example, log `e140cd528b7578e5dce66136fcc795a5` | baggageAllowance `0P`; baggage.ADT.numberOfPcs `00P`; all six remaining ADT baggage fields null; carryOnAllowance null; carryOn `{}`. | No live response captured | NOT RUN |
| TC-03 | Ticket two-piece example, log `e3e308c2a1a042f6b7cd3a969bbabb94` | Checked allowance `2P`, numberOfPcs `02P`, weights 23 kg/51 lb, dimensions 158 cm/62 inches. Carry-on allowance/numberOfPcs `1P`, weightKg 10, weightLb null, dimensions 115 cm/45 inches. Full-text fields null. | No live response captured | NOT RUN |

NOT RUN is a preparation state, not an executed-test status. Executed cases must receive exactly PASS, FAIL or WARN with actual evidence.

## Execution boundary and setup observations

- User explicitly authorized DEV sandbox booking on 2026-10-12. PREPROD and PROD booking are prohibited. No configuration mutation or application-source inspection is authorized.
- Preserve fresh Search keys unchanged through the Atlas setup flow. Do not reuse expired historical keys or substitute Brightsun inputs.
- The ticket's Kibana log URL redirects to a username/password login page in the in-app browser. This is an access observation, not an Atlas test outcome.
- Local booking examples found are Brightsun examples. The current process exposes no environment-variable names matching BOOKING, ATLAS or AIRAPI. No credentials were printed.
- A live question requests the location of the approved Atlas DEV collection/environment or an authenticated session. Endpoint, booking request schema and authentication are required before execution.
- Ticket attachment `new.json` is expected-output evidence, not a fresh DEV PASS. Its carry-on dimensions are null; the mapping-table dimension case needs a source row with `55*35*25cm` to evaluate the expected 115 cm/45 inches.
- Capture sanitized paired requests/responses, exact Search URLs/keys and observed segment fields. Mapping comparisons require matching source baggage data; do not infer source data from the output alone.
- After execution, generate the Markdown and HTML dispatch sheets using `templates/airapi-qa-dispatch-template.html`, with an AirAPI-only Postman v2.1 collection and expected-outcome CSV embedded for Blob downloads. No ledger update without its separate two-stage approval.

## Sources

- Jira description, mapping tables and expected attachment: https://traveldev.atlassian.net/browse/SS-6390
- Example mapping log: https://elkm.travel-dev.com/s/searchapi/goto/f7e880feeebb66bc6771b57686704704
- Zero-baggage log: https://elkm.travel-dev.com/s/searchapi/goto/e140cd528b7578e5dce66136fcc795a5
- Two-piece log: https://elkm.travel-dev.com/s/searchapi/goto/e3e308c2a1a042f6b7cd3a969bbabb94
- Project contract and evidence ledger read; ledger is empty.
