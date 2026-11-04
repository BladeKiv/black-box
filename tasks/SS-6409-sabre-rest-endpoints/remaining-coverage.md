# SS-6409 remaining coverage - 2026-10-22

User requested the remaining ticket points. Previous eight PASS checks remain limited to their documented scope. This extension does not authorize configuration mutation or booking/ticket writes.

## Round 2 - empty lists

User applies this sabre_rest configuration, preserving unrelated settings:

```json
{
  "enable": true,
  "enable_revalidate": true,
  "flight_shop": {"cid": [], "projects": []},
  "flight_shop_lite": {"cid": [], "projects": []}
}
```

Once user confirms readiness: read /algo/conf, then one Search per TST101/TST102/TST104 using the same PUB/S/6NVG LHR-JFK 2026-11-20 Y/1 ADT fixture. Expected all returned options use confirmed default marker bargainFinderMax. This is fresh execution of empty-list/default and config-only route switching, compared to preserved original evidence. allow_retry=false; allow_poll=false; allow_retest=true only for the three named CIDs in this configuration round; approved_inputs fixed as above. Maximum four steps per case; no automatic input variations.

## Subsequent rounds

- Overlap: put a single valid CID into both lists. Expected priority requires the live answer to the exact meaning of first in list. Configure only after resolving priority; no guessed expectation.
- Project routing: isolate each project block from CID matches, then test unlisted project and project overlap. Requires the actual project value and Search parameter or evidenced CID-to-project relationship.
- PCC support: inspect config to establish absence of pcc selectors; runtime proof of ignored/unsupported pcc selectors requires an agreed observable contract. Existing pcc=6NVG is a provider-search input, not proof that new routing blocks support PCC selectors.
- No fallback on error: use a safe user-supplied provider-error fixture and require response/timing evidence of selected route and no default call. Empty inventory and malformed input alone do not prove provider-error behavior.
- Revalidation/checkout: requires an actual documented read-only request shape and observable evidence of provider execution. Previous GET Result retrievals do not certify this. No booking creation/change/cancellation/ticketing calls.
- Data gaps: saved-field-gap-analysis.json records additional analysis of original captures, not fresh endpoint execution. flightShop/flightShopLite omit mileage, have empty meal values and maxSeats=9 throughout. Default has mileage and varying meals/seat counts. SS-6330 documents these gaps; no acceptance waiver has been inferred. Full nested value parity cannot be claimed from matching top-level field sets.

No speculative error cases, malformed PCC inputs or other non-ticket edge cases are added. Update report/collection/CSV after each completed live round, retaining run provenance. No ledger write.
