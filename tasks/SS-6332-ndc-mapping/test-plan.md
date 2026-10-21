# SS-6332 — Search mapping test plan

Execution in progress: twelve active checks PASS, zero FAIL. K01 passed: all 200 PUB options skipped NDC mapping with source_fare=["SR"]. Next requested configuration: restore source_fare=["PUB"] and remove only the Y entry from tax_delta_by_cabin; keep S/C/F entries and all other settings unchanged. Search remains cabin=Y.

Source: https://traveldev.atlassian.net/browse/SS-6332, read in Jira on 2026-09-18. Title: Pre-map non-NDC content to a NDC provider. Jira shows In Testing and a DEV deployment comment.

Environment: https://api.search.dev.travel-dev.com. User scope: synchronous Search only; cid=TST101; only UA configured; assert mapped gds, pcc, and cons. The user applies configuration changes between rounds.

## Intended behavior

ndc_mapping precedes cons_mapping and commission processing. It requires enabled=true and CID OR project eligibility. Per user clarification, CID eligibility uses explicit values only; projects supports "*". A qualifying priced ticket must have UA as validating carrier and every marketing carrier, through-fare pricing, one cabin, matching explicit source consolidator, a matching nested GDS/PCC pair, an allowed fare type, and a configured cabin. Operating carriers do not affect eligibility. Source checks use values before mapping. A missing PTC delta defaults to zero; a delta that would make any passenger's oBaseTax negative prevents mapping of the whole option. Eligible options receive the configured target consolidator, GDS, and PCC and bypass cons_mapping. Ineligible options continue through existing mapping rules.

## Execution method

1. Confirm exact request/authentication and response paths, source and target triples, and active config. Keep credentials out of saved artifacts and logs.
2. Run current UA configuration first. Require actual eligible inventory before asserting a mapped triple; zero matching options cannot pass a mapping test.
3. Request a disabled baseline, then change one configuration condition at a time. Record each user-confirmed configuration state with its Search evidence.
4. Match observations using explicit itinerary/passenger/fare attributes. Search keys remain opaque. Do not infer a pre-mapping source triple from an already-mapped response.
5. For skip cases, account for downstream cons_mapping: the expected final triple must be confirmed from baseline/configuration, not assumed to equal the raw source triple.
6. Run inventory-dependent cases only when the response establishes their prerequisites. An attempted case that cannot be conclusively evaluated is WARN, with paired sanitized request/response evidence.
7. Produce the matching HTML dispatch report from the project template, Postman v2.1 collection, and expected-outcome CSV after execution. Every executed case receives exactly one PASS, FAIL, or WARN.

## Planned mapping coverage

All rows below derive from explicit ticket rules. Planned rows have no execution verdict yet. Exact values will be bound to confirmed configuration and inventory.

| ID | Test data / configuration | Expected Search mapping result | Actual result | Status |
|---|---|---|---|---|
| M01 | TST101, eligible UA through fare, one configured cabin, matching source criteria | All three fields equal the configured target gds/pcc/cons | Not run | Pending execution |
| M02 | Same eligible inventory, enabled=false | No ndc_mapping effect; confirmed baseline final triple | Not run | Pending execution |
| M03 | CID matches; project does not match | Mapping occurs because eligibility uses OR | Not run | Pending execution |
| M04 | CID does not match; project matches | Mapping occurs because eligibility uses OR | Not run | Pending execution |
| M05 | Neither CID nor project matches | No ndc_mapping effect | Not run | Pending execution |
| M06 | projects=["*"] with CID nonmatching | Mapping occurs via project eligibility | 200/200 UA options mapped (D01) | PASS |
| M07 | Non-UA validating carrier, only UA configured | No ndc_mapping effect | Not run | Pending execution |
| M08 | UA validating carrier with at least one non-UA marketing carrier | No ndc_mapping effect | Not run | Pending execution |
| M09 | UA validating and all-UA marketing, non-UA operating carrier | Mapping occurs if other criteria pass | Not run | Pending execution |
| M10 | UA broken-fare pricing | No ndc_mapping effect | Not run | Pending execution |
| M11 | UA itinerary with mixed cabins | No ndc_mapping effect | Not run | Pending execution |
| M12 | Exact source_cons match and mismatch | Map for match; skip for mismatch | Matching GTT mapped; mismatched VZU skipped (A01/G01) | PASS |
| M13 | Matching source GDS and its listed PCC | Mapping occurs | Not run | Pending execution |
| M14 | Matching GDS with unlisted PCC; then nonmatching GDS | No ndc_mapping effect in either variant | Not run | Pending execution |
| M15 | PCC listed only under a different GDS | No ndc_mapping effect; PCCs cannot cross GDS entries | 200/200 skipped NDC mapping (I01) | PASS |
| M16 | pcc=["*"] under the matching GDS | Mapping occurs; other GDS values remain ineligible | Not run | Pending execution |
| M17 | Actual source fare type included, excluded, then source_fare=["*"] | Map for included/wildcard; skip for excluded | Not run | Pending execution |
| M18 | Cabin entry exists, then is removed | Map with entry; skip without entry | Not run | Pending execution |
| M19 | Passenger PTC absent from configured cabin delta map | Mapping still occurs; missing PTC does not block it | Not run | Pending execution |
| M20 | Configured delta greater than observed source oBaseTax for one passenger | Entire option remains unmapped, including a multi-pax variant | Not run | Pending execution |
| M21 | Separate/split priced tickets with different eligibility | Each priced ticket maps independently according to its own criteria | Not run | Pending execution |
| M22 | Eligible mapped option plus an otherwise matching cons_mapping rule | Final triple retains NDC mapping, subject to confirmed commission behavior | Not run | Pending execution |
| M23 | Eligible mapped option, no target commission distribution/rule | Mapped option still returned | Not run | Pending execution |

Rows with variants become separate execution records. Inventory-dependent rows require observable prerequisites; configuration alone cannot establish coverage.

## Configuration rounds to request

- Round A: current UA configuration and a Search returning eligible UA inventory; capture target triples.
- Round B: enabled=false for the same Search; establish source inventory and downstream baseline. Restore enabled=true.
- Round C: CID/project eligibility variants, keeping all carrier settings fixed. A projects wildcard must be removed for a meaningful CID rejection test.
- Round D: source_cons, nested source_distributions, source_fare, and cabin-entry variants, changing one criterion per run.
- Round E: missing PTC delta and excessive delta using confirmed passenger tax evidence; then downstream cons_mapping conflict/no-commission-rule variants where their final effects are observable.
- Restore the original user-confirmed configuration after testing; the user performs every configuration change.

## Scope boundary

The mapping-focused plan does not certify exact tax subtraction, markup/commission arithmetic, exclude-airline behavior, or internal pipeline flags. Those are ticket requirements but require additional observable fields and expectations beyond the requested gds/pcc/cons assertions. Search-only evidence may establish their effects where specifically configured, but cannot prove internal implementation. No booking calls are needed.
