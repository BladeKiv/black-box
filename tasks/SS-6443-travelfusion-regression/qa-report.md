# SS-6443 — TravelFusion regression

PASS — 2 PASS / 0 FAIL / 0 WARN

STAGE | 2026-11-02 | Search → Result | SFO-FRA | gds=F · pcc=DEF · fare=PUB · cid=TST101

Search returned HTTP 200 with 57 offers, including 37 TravelFusion (F) offers. Result for a selected F/DEF offer returned HTTP 200, preserving the opaque key and F/DEF identifiers, with populated itinerary segments and price data.

Intended behavior: Search returns usable TravelFusion offers; Result resolves an unchanged Search key into itinerary and price data.

| ID | Test data | Expected | Actual | Status |
|---|---|---|---|---|
| TC-01 | SFO-FRA · 2026-11-20 · 1 ADT · Y · gds=F · pcc=DEF · fare=PUB · cid=TST101 | Usable TravelFusion Search offers | HTTP 200; 37 F offers among 57 total | PASS |
| TC-02 | Unchanged key from selected F/DEF Search offer | Result resolves the TravelFusion offer into itinerary and prices | HTTP 200; same key; F/DEF; populated segments; numeric totalPrice | PASS |

## Evidence and scope

- sfo-DEF-PUB-search-evidence.json and sfo-DEF-PUB-result-evidence.json retain the selected pair.
- Search also returned 20 E offers; provider exclusivity was not asserted.
- Earlier empty/mismatched attempts are retained in earlier-attempts and their original evidence files. Current counts apply only to the final uppercase run.
- PROD login expiry, stale-session recovery, logs and mutex behavior were not tested. No booking, ticketing or configuration changes. No operational lessons applied; ledger unchanged.
