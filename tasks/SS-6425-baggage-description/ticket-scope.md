# SS-6425 scope intake - 2026-10-21

## Approved checked-baggage extension - 2026-10-21

Current user request and live Chris P comment: for FBA, if allowPieces >= 1, detect the trigger "up to #kg" in checked-baggage DescText and create the template. Supplied example: "Check-in baggage - 25kg (or 2 pieces up to 23kg each for flights to/from the USA or Canada only)". Test the same existing SQ booking on PREPROD and retain carry-on regression evidence. Source evidence must be fresh and trace-correlated.

Execution permissions for this extension: allow_retry=false, allow_poll=false, allow_retest=true, approved_inputs=[SQ CPS9CG]. One read-only Book/Info request; no input variation. Direct standing user TLS bypass applies. Lesson 609bbba636414a1c879738a99b5b2dc0 is candidate-only, not auto-applied. New evidence goes in a separate run; earlier failures/passes remain historical.

Source: https://traveldev.atlassian.net/browse/SS-6425, description read live; comments section contains no comments. Target: PREPROD.

Intended behavior: Extract carry-on allowance from Amadeus NDC DescText: "Cabin baggage - 1 piece Up to 7kg each. Sum of length, width and height of each piece should not exceed 115cm."

Linked historical evidence: traceID c8d58255-cc57-11f1-a510-9600023dbd4f, 2026-10-20, SQ PNR CPS9CG. Travel_OrderCreate_1.1 response contains the stated cabin-baggage description; /ndc/v1/book/create output has carryOn=null on six segments. This is historical evidence, not a PREPROD retest or permission to call book/create.

Related historical reference: tasks/SS-6394-amadeus-ndc-baggage/runs/2026-10-19-preprod-retest/qa-report.md. Existing approvals and TLS exceptions from SS-6394 do not extend to this run.

User authorized read-only book/info and ticket/void/check calls and requested the corresponding AGENTS.md update on 2026-10-21. SS-6425 uses Book/Info only; ticket/void/check is not required by this ticket. No fresh endpoint execution yet. This is scope intake, not a QA result.

2026-10-21 execution: runs/2026-10-21-authorized records the original FAIL: fresh PriceClass descriptions linked to all six segments, but carryOn=null. After the user reported a fix, runs/2026-10-21-fix-retest records 1 PASS / 0 FAIL / 0 WARN: the same six segments now expose 1P, 7 kg, 115 cm, matched to a fresh trace-correlated Travel_OrderRetrieve_1.1 response. Earlier failure evidence is preserved. Scope remains existing-booking Book/Info only.
