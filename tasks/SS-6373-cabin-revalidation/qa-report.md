# SS-6373 — Cabin revalidation

Release signal: PASS — {'PASS': 4, 'FAIL': 0, 'WARN': 0}

PREPROD | 2026-09-30 | AirAPI Search → GET Result | CPH–DEN, 2027-06-30, 1 ADT, cabin C

Intended behavior: Same booking classes: preserve a populated original cabin; use the revalidated declared cabin when the original is empty or null.

Fresh PREPROD Search returned 49 itineraries. Two empty-cabin results adopted C/C/C with unchanged classes and GDS G → S; one selected L05L. A populated-cabin L05L result retained C/C with GDS G → S. Replacement TC-04b retained C/C/F and classes R/R/R with GDS G → S, confirming mixed-cabin preservation through revalidation. Per user clarification, TC-03 is merged into empty-cabin coverage; no separate null test is required or claimed.

| ID | Test data | Expected | Actual | Status |
|---|---|---|---|---|
| TC-02 | TK; 3 segments | Replace empty cabins with C on each matching segment | HTTP 200; classes Z,Z,Z unchanged=True; cabins ["", "", ""] → ["C", "C", "C"]; GDS G → S; revalidation by GDS change=True | PASS |
| TC-02b | TK; 3 segments | Replace empty cabins with C on each matching segment | HTTP 200; classes Z,Z,D unchanged=True; cabins ["", "", ""] → ["C", "C", "C"]; GDS G → S; revalidation by GDS change=True | PASS |
| TC-04 | LH; 2 segments | Preserve populated original cabins with unchanged booking classes | HTTP 200; classes D,D unchanged=True; cabins ["C", "C"] → ["C", "C"]; GDS G → S; revalidation by GDS change=True | PASS |
| TC-04b | AA; 3 segments | Preserve populated original cabins with unchanged booking classes | HTTP 200; classes R,R,R unchanged=True; cabins ["C", "C", "F"] → ["C", "C", "F"]; GDS G → S; revalidation by GDS change=True | PASS |

## Supporting evidence and rerun

Exact Search URL: http://airapi51.kivops.info/v1/search?extra=false&cabin=C&adt=1&debug=true&fare=PUB&cid=SALKIV&gds=G&pcc=DEF&fl.0.dt=2027-06-30&fl.0.o=CPH&fl.0.d=DEN

See paired-evidence.json for paired requests and responses for every case, including the replacement TC-04b. Raw Search and Result captures are stored beside this report. No provider endpoints or booking endpoints were called. Historical ELKM logs are supplemental September 29 production evidence. The earlier exact historical-key request returned C/C/C but is not counted as a fresh original-input test. Returned Search keys were sent to Result unchanged.

Postman: import SS-6373.postman_collection.json, configure Basic authentication locally, and run with expected-outcomes.csv. Refresh original Search snapshots and opaque keys together when inventory changes. An unchanged GDS on a future rerun means the revalidation precondition is unavailable and must be evaluated as WARN. Superseded TC-04b captures and candidate attempts are retained as supporting evidence and excluded from the final active-case totals.

