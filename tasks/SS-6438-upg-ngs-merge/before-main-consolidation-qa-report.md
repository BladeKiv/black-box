SS-6438 — Build UPG itineraries as main itineraries with NGS children (regular + upgrade options)

FAIL — 3 PASS / 2 FAIL / 2 WARN
PREPROD | 2026-11-02 | HTTP Search | 13 Searches · 3,916 main results · merge=true

Intended behavior: Sort eligible regular/UPG candidates by price. Cheapest becomes main NGS#1. Each retained option must be equal or better on bags, exchange and refund, and strictly better on at least one. Regular children require ngs_jobs; other UPG children also require keepBothBagOptions=true. User-confirmed fields are keys.baggage.allowPieces and penalties.exchange/refund; singleton :UPG# is valid.

Expanded inventory testing found 19 feature-filter failures: 10 UPG-main groups on AKKDCR LAX-MUC and nine regular-main groups on AKKDCR JFK-LHR. Earlier five-Search retained-output passes remain historical evidence; the expanded result supersedes the overall release signal. The regular-cheapest/keepBothBagOptions=false positive branch and complete pre-filter candidate completeness remain unverified.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | Ticket example 1 · BCKDCR · keepBothBagOptions=false | UPG-cheapest main; eligible regular children improve all three features monotonically. | 196 UPG-containing groups across six Searches; no retained feature regression; no other UPG children. Representative R02-B reproduces the 1-bag/exchange → 2-bag/exchange → refundable progression. | PASS |
| TC-02 | Ticket example 2 · AKKDCR · keepBothBagOptions=true · R02-A LAX-MUC return | After a 2-bag option is kept, filter a later 1-bag option even if exchange improves. Also filter an option that loses exchange. | FAIL in 10 UPG-main groups. Example: NGS#2 has 2 bags/exchange=false; NGS#3 is retained with 1 bag/exchange=true. A separate group retains a UPG option that loses exchange. | FAIL |
| TC-03 | Ticket example 3 · BCKDCR · regular cheapest · keepBothBagOptions=false | Observe a regular-cheapest group with a retained improving UPG option and eligible regular children. | No qualifying positive regular-main/retained-UPG group found in the six BCKDCR Searches. Regular-only NGS groups are not proof that UPG candidates existed before filtering. | WARN |
| TC-04 | Ticket example 4 · AKKDCR · regular cheapest · keepBothBagOptions=true · R04-A JFK-LHR return | Regular-cheapest main is NGS#1; keep an UPG child only if it does not lose any confirmed feature. | Regular-cheapest branch observed in nine groups; all nine fail. Example: regular main USD 4262.65 has exchange=true; retained UPG child USD 5535.34 has exchange=false. | FAIL |
| TC-05 | 451 UPG-containing groups · 808 returned options | Within each returned group, prices ascend and main is cheapest among retained options. | All 451 groups pass retained price ordering. This does not prove the absolute minimum of an unseen pre-filter candidate set. | PASS |
| TC-06 | All returned UPG groups · configured child-source flags · user-confirmed singleton exception | Children share their main flight sequence; other UPG children require keepBothBagOptions=true; numbering is sequential, with :UPG# allowed for singletons. | All checked groups pass same-flight identity, configured UPG-child eligibility and numbering/singleton rules. | PASS |
| TC-07 | Complete pre-filter candidate elimination/completeness | Evaluate every omitted or retained candidate against the ticket rule using a complete pre-filter candidate set. | The 19 observed retained-group failures conclusively violate the rule. Complete exclusion/retention completeness remains unverified because captures lack a certified pre-filter candidate set. | WARN |

Observed ticket-format examples

Prices USD; dates 2027-02-25 to 2027-03-11; 1 ADT; cabin C. Exchange/refund: 0=false, 1=true. Tables show actual retained results; failing options should have been filtered.

Example 1 — PASS · R02-B

| Option | Price | Bags | Exchange | Refund | Result |
|---|---:|---:|---:|---:|---|
| UPG itin | 6,244.19 | 1 | 0 | 0 | :UPG#:NGS#1 (main) |
| Regular 1 | 6,462.19 | 1 | 1 | 0 | :NGS#2 |
| Regular 2 | 6,841.33 | 2 | 1 | 0 | :NGS#3 |
| Regular 3 | 7,396.69 | 2 | 1 | 1 | :NGS#4 |

Example 2 — FAIL: fewer-bag option retained · R02-A

| Option | Price | Bags | Exchange | Refund | Result |
|---|---:|---:|---:|---:|---|
| UPG itin | 5,851.85 | 1 | 0 | 0 | :UPG#:NGS#1 (main) |
| UPG itin | 6,119.89 | 2 | 0 | 0 | :UPG#:NGS#2 |
| Regular 1 | 6,496.54 | 1 | 1 | 0 | :NGS#3 |
| Regular 2 | 6,876.11 | 2 | 1 | 0 | :NGS#4 |
| Regular 3 | 7,432.09 | 2 | 1 | 1 | :NGS#5 |

Example 4 — FAIL: exchange-losing UPG child retained · R04-A

| Option | Price | Bags | Exchange | Refund | Result |
|---|---:|---:|---:|---:|---|
| Regular 1 | 4,262.65 | 1 | 1 | 0 | :NGS#1 (main) |
| UPG itin | 5,535.34 | 2 | 0 | 0 | :UPG#:NGS#2 |

Example 3: WARN — no positive regular-cheapest/keepBothBagOptions=false group with a retained UPG option was observed.

Supporting evidence and rerun

All M01–M05 and R01–R04-A/B paired sanitized captures are retained. all-cases-analysis.json identifies exact result indices and every failing transition. all-cases-payload-evidence.json contains paired FAIL/WARN excerpts. Run collection.json with expected-outcomes.csv using the existing PREPROD environment. HTML downloads embed both artifacts as Blob content.

Eight additional Searches executed: SFO-FRA return, LAX-MUC return, ORD-FRA return and JFK-LHR return, each paired across BCKDCR/AKKDCR. Four candidate steps per missing branch; no retries, polling, downstream endpoints, booking, configuration mutation or Jira writes. Fifth prepared route was not executed.

Scope: 451 observable UPG-containing groups / 808 retained options. Complete pre-filter candidate sets are unavailable. Regular-only groups without an observable UPG option cannot certify the missing positive UPG merge branch. Configuration discovery remains prerequisite evidence only. No trusted matching operational lesson was applied.
