# SS-6415 scope intake - 2026-10-21

Source: https://traveldev.atlassian.net/browse/SS-6415, description and both Artiom Startev comments read live. Target: DEV; developer comment confirms DEV deployment.

Intended behavior: VoluntaryChange must handle missing book_info.additionalInfo without panic when regular Amadeus itinerary issue PCC SFOG3210A fans out to Amadeus NDC. Log every provider error and retain successful results from other providers. Normalize passenger keys outside Sabre's documented N.N format to 1.1, 2.1, etc. before Sabre submission.

User clarification: HTTP 200 with a proper error message. Provider logging and Sabre normalization need correlated logs; endpoint success alone does not prove either.

Historical reproduction evidence: linked ELK search contains PROD release_v6.48.3 panic, traceID 1f456979-0ecc-4c0c-8d6b-e38dcb8061fe. Correlated request contains book_info, SFOG3210A and passenger key 2, without additionalInfo. No passenger identity, ticket number or credentials copied.

User supplied ${AIRAPI_LOCAL_REFERENCE} Dev.postman_environment.json for this ticket. Final run uses POST https://api.search.dev.travel-dev.com/v1/exchange, search_params.cid=TST101 in the body, no query CID, and the separately supplied exchange Authorization header. Secrets are excluded from evidence.

User narrowed acceptance to the two stated validation problems: dummy tickets are sufficient; empty responses are acceptable; inspect correlated logs for panic. Successful exchange inventory is not required. This supersedes the earlier proper-error-response acceptance where empty results would otherwise be ambiguous.

Fresh run: runs/2026-10-21-tst101. Both calls return HTTP 200 / results=[]; each has a GDS A nil-pointer panic in DEV logs. Sabre reference 2 is normalized to 1.1; valid 2.1 is preserved. Earlier authentication failures remain in separate directories.

User requested a PCC-only comparison with DFWG32100. runs/2026-10-21-dfwg32100 records 2 PASS / 0 FAIL / 0 WARN: both calls return HTTP 200 / results=[]; six correlated DEV records contain no runtime panic; GDS I logs book_info.additionalInfo is mandatory for GDS I; Sabre normalizes 2 to 1.1 and preserves 2.1. This PCC-specific pass does not close the earlier SFOG3210A panic.
