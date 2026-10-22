# SS-6412 - Currency ranking

Source: https://traveldev.atlassian.net/browse/SS-6412, read 2026-10-21.
Title: Different rankings on currency switch - investigate.
Developer comment: STAGE1.

Ticket intended behavior: retain the USD anchor for itinerary-quality price units, applying currencyRates and the requested search currency. Compare the same search in USD, GBP and INR.

Ticket search: GET /v1/search?cid=OVA101&original_cid=1&adt=1&debug=true&cabin=Y&fl[0][o]=EWR&fl[0][d]=LGW&fl[0][dt]=2026-12-14&currency=USD&limit=50

STAGE1 host verified from AirAPI Stage1.postman_environment.json: https://api.search.stage1.travel-dev.com

Historical attachment ranks are recorded separately in evidence/historical-attachment-ranks.json. Full opaque keys are compared without transformation. These results do not establish current deployment behavior.

## Current user-approved retest scope
TST103, original_cid=1; EWR-LHR, JFK-LHR, JFK-CDG, JFK-FRA; 2026-12-14; 1 ADT; Y; limit=50; USD, GBP, INR. Exclude first three independently; exact-key absolute original-position shift <= 2. Ignore meta.rank. One fresh Search per route/currency; no retry, polling or input variation. Retest explicitly requested.

## Superseding criterion - 2026-10-22
User requested fresh searches and points_diff as the sole check: identical opaque keys, abs(target.meta.rank_v2.points_diff - USD.meta.rank_v2.points_diff) <= 0.5. All prior meta.rank/position checks and first-three exclusions are disabled. TST103; same four routes/date/passengers and USD/GBP/INR. One Search per route/currency; no retries, polling or input variation.
