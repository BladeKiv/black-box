# SS-6412 - Currency ranking

Source: https://traveldev.atlassian.net/browse/SS-6412, read 2026-10-21.
Title: Different rankings on currency switch - investigate.
Developer comment: STAGE1.

Ticket intended behavior: retain the USD anchor for itinerary-quality price units, applying currencyRates and the requested search currency. Compare the same search in USD, GBP and INR.

Ticket search: GET /v1/search?cid=OVA101&original_cid=1&adt=1&debug=true&cabin=Y&fl[0][o]=EWR&fl[0][d]=LGW&fl[0][dt]=2026-12-14&currency=USD&limit=50

STAGE1 host verified from AirAPI Stage1.postman_environment.json: https://api.search.stage1.travel-dev.com

Historical attachment ranks are recorded separately in evidence/historical-attachment-ranks.json. Full opaque keys are compared without transformation. These results do not establish current deployment behavior.
