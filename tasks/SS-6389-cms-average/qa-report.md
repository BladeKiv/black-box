# SS-6389 QA dispatch

Release signal: PASS for both executed cases.

2026-10-12 | DEV Search | TOJ101 / LH / C / S / 6NVG | 2 PASS / 0 FAIL / 0 WARN

Both requested averaging cases PASS: 9%/7% produced 8%/8% in 8 qualifying results; 9%/9% produced 9%/9% in 16 qualifying results. Other fare blocks retained missing commissions fields. Explicit 0% rule input was not tested.

Intended behavior: exclude commissionless fares from CMS averaging; update commissioned fares to the average.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | Exact supplied DEV Search; TOJ101; LH; C; S/6NVG; configured 9%/7% | Configured rates 9% and 7% average to 8% on the two matching fares; other fares remain without commission fields. | 8 qualifying results checked; both GTT upfront.percent arrays [8]; 0 mismatches; other fare blocks still omit commissions. | PASS |
| TC-02 | Exact supplied DEV Search; configured Average rates 9%/9% | Both matching fares receive 9%; other fares retain missing commissions fields | HTTP 200; 50 results; 16 qualifying results; both percent arrays [9]; no other fares gained commission; 0 mismatches | PASS |

Exact Search URL: search-request.json. Mixed-rate evidence: submitted-rule-response.json, mixed-rates-validation.json. Equal-rate evidence: equal-rates-response.json, equal-rates-validation.json. Opaque keys are preserved. Earlier unmatched-rule runs are historical setup evidence. Configured input rates are user-confirmed; response rates are agent-verified. Missing commissions fields were not relabeled explicit zero. No explicit-0% rule input or additional edge cases were executed. No configuration mutations or booking calls performed by agent. Collection/CSV embedded as Blob downloads in HTML; Newman not run.
