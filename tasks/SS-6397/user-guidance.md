# SS-6397: user-provided Result request

Recorded 2026-10-19. This is request guidance, not executed QA evidence.

- Environment: AirAPI Stage.
- Method: GET.
- Endpoint and exact opaque key: see `user-result-request.json`. Preserve the key unchanged; do not decode, rebuild or substitute it.
- Headers: `X-Kiv-Cust-direct: true` and `X-Kiv-Cust-browser: desktop`.
- Authorization —  the complete shared Search authorization value supplied privately through `AIRAPI_SEARCH_AUTHORIZATION`. The dashboard stores it in its ignored `storage/search-authorization.txt`; do not duplicate or print it in task artifacts.
- This Result request uses Search authorization, not booking credentials. Missing `booklogin`/`bookpass` does not block it.
- Use the exact Stage destination only when Stage is the selected QA environment. Never silently switch an environment to fit this fixture.
- If the stored key has expired or no longer resolves, report the observed blocker and use ticket-authorized fresh Search-to-Result guidance; do not call this fixture a fresh successful test.
- For Stage log correlation use the configured Kibana Discover mapping and the traceID/time window of the actual response.

No endpoint request was executed when this guidance was saved. Preserve prior run evidence and generate any future results in a new run directory.
