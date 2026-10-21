PASS — SS-6408 live flag matrix
STAGE | 2026-10-19 | TST101 | 1 ADT | cabin=C | val_cr=LH | gds=S | pcc=6NVG | fare=SR | FRA-CDG 2026-11-20; CDG-MUC 2026-11-30

Intended behavior: both flags true retain a one-piece main and two-piece child; false or omitted keepBothBagOptions preserves the secondBag behavior.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-05 | TST101 / SR / C / LH / FRA-CDG; CDG-MUC / secondBag=true / keepBothBagOptions=true | 1-piece main and 2-piece child | 24/24 pairs contain both; first USD 666.40 and 876.40 | PASS |
| TC-06 | 24 parent/child pairs / secondBag=true / keepBothBagOptions=true | Distinct keys, no duplicated pair option | 48 distinct nonempty parent/child keys | PASS |
| TC-07 | 24 parent/child pairs / secondBag=true / keepBothBagOptions=true | Same flights, dates, airports, cabin and fare details | Checked fields match in all 24 pairs | PASS |
| TC-08 | secondBag=true / keepBothBagOptions=false | Only 2-piece upgrade options; no retained 1-piece upgrade variant | HTTP 200; 60 main results; 15 upgrade parents identified via keys.upgrade_info; all allowPieces=2; no upgrade children | PASS |
| TC-09 | secondBag=true / keepBothBagOptions omitted | Default false: only 2-piece upgrades | HTTP 200; 60 main results; 12 upgrade parents, all keys.baggage.allowPieces=2; no upgrade children | PASS |
| TC-10 | secondBag=false / keepBothBagOptions=true | Flag ignored: only 1-piece upgrades | HTTP 200; 60 main results; 12 upgrade parents, all keys.baggage.allowPieces=1; no upgrade children | PASS |
| TC-11 | secondBag=false / keepBothBagOptions=false | Only 1-piece upgrades | HTTP 200; 60 main results; 38 upgrade parents, all keys.baggage.allowPieces=1; no upgrade children | PASS |

Evidence: search-working-url.txt; search-working-response.json; working-pairs.json; search-secondBag-*-response.json and matching summary JSON files.

Confluence documentation acceptance is not covered by these Search results.
