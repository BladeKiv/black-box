SS-6400 — GTT markup cache key ignores cabin, so one cabin's markups are reused for other cabins for up to 30 minutes

**PASS — 7 PASS / 0 FAIL / 0 WARN**

2026-10-22 | 2026-10-22 | fixed build | TC-01–04/07: JFK-LHR 2026-11-20 at 10:27 UTC; TC-05/06: SFO-LHR 2026-12-10, P→F at 10:41 UTC | SBCSFO/GTT101

7 PASS / 0 FAIL / 0 WARN: six execution-based passes plus one user-confirmed acceptance (TC-07). P-first then F verifies First-cabin cache reuse. User confirms the omitted-cabin key already existed within the 30-minute window and accepts the observed reuse. No new requests were made for this status update.

Intended behavior: Different converted cabins and omitted cabin have separate cache entries. Y/Q share Economy, C/J share Business, F/P share First. Different converted cabins receive their own GTT CabinType and markup rules.

| ID | Test data | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | cabin=Y; SBCSFO/GTT101; JFK-LHR 2026-11-20; 1 ADT | Initial Y Search calls GTT with Economy and receives Economy markup rules. | HTTP 200; 503 results. Three GTT calls send Economy (Published/Bulk/Commission); returned flat Value=50.00; 425 results expose oMarkup=50 USD. | PASS |
| TC-02 | cabin=Q; SBCSFO/GTT101; JFK-LHR 2026-11-20; 1 ADT | GTT CabinType=Economy; shares the converted-cabin cache entry with Y. | HTTP 200; 499 results. No new GTT calls after Y; 419 results expose the same 50 USD rules. Equivalent Economy cache reuse observed through suppressed calls. | PASS |
| TC-03 | cabin=C; SBCSFO/GTT101; JFK-LHR 2026-11-20; 1 ADT | GTT CabinType=Business; uses its own converted-cabin cache entry and rules. | HTTP 200; 429 results. Three distinct GTT calls send Business. Responses include Medium 500.00 and Low 50.00 rules; 260 results expose oMarkup=500 USD. | PASS |
| TC-04 | cabin=J; SBCSFO/GTT101; JFK-LHR 2026-11-20; 1 ADT | GTT CabinType=Business; shares the converted-cabin cache entry with C. | HTTP 200; 27 results. No new GTT calls after C; 27 results, including 18 gtt-COMM-1 markup identifiers. Business entry was independently seeded by C; equivalent-cabin call reuse observed. | PASS |
| TC-05 | SFO-LHR 2026-12-10; cabin=F; 1 ADT; SBCSFO/GTT101; order P then F | P and F map to First and share one converted-cabin cache entry; P-first loads First rules and subsequent F reuses them. | HTTP 200; 50 results; 13 expose oMarkup=500 USD and gtt-PUB-1, 37 expose gtt-COMM-1 with amount omitted. F starts after the P-correlated GTT calls; no new calls. Converted First cache reuse observed. | PASS |
| TC-06 | SFO-LHR 2026-12-10; cabin=P; 1 ADT; SBCSFO/GTT101; order P then F | P and F map to First and share one converted-cabin cache entry; P-first loads First rules and subsequent F reuses them. | HTTP 200; 0 results. P nevertheless triggers three First GTT calls, one per fare type; log time 10:41:09 UTC matches P start and ingestion precedes F. First rule response includes Medium 500.00 and Low 50.00. F then reuses the entry without additional calls. | PASS |
| TC-07 | cabin=omitted; SBCSFO/GTT101; JFK-LHR 2026-11-20; 1 ADT | Uses a separate empty-cabin cache entry from all specific cabins. | USER-CONFIRMED PASS (2026-10-22): user confirms the omitted-cabin key already existed within the 30-minute cache window and accepts reuse without a new GTT call. Saved execution: HTTP 200; 498 results; no independent new omitted-cabin GTT call. No fresh cache-expiry or isolation verification performed. | PASS |

Supporting evidence and rerun artifacts

PASS provenance: TC-01–06 are based on saved fixed-build execution and correlated GTT logs; TC-07 is user-confirmed acceptance on 2026-10-22, not fresh execution proof. User instruction: mark warn as passed since this key already existed in 30 min cache window. The saved omitted-cabin observation remains HTTP 200, 498 results and no new GTT call; controlled empty-cabin isolation after expiry was not executed. Previous run reports preserve their historical outcomes. No new API requests, retries, configuration changes or ledger updates for this change. GTT log correlation uses host, time, agency and route because markup traceIDs are empty.

Collection: collection.json; CSV: expected-outcomes.csv.
