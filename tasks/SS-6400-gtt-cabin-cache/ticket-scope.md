# SS-6400 — PREPROD

Source: https://traveldev.atlassian.net/browse/SS-6400 (read 2026-10-21).
User 2026-10-22: ordinary Search with agency=SBCSFO, cid=GTT101; use http://airapi51.kivops.info with no port for Search.
Intended: converted Economy/Business/First/omitted cabins have separate cache entries; Y/Q, C/J, F/P share their respective converted entry. Verify GTT CabinType and per-cabin markup rules.
Read-only GET /v1/search only. No source inspection or configuration changes.
Fixture: JFK-LHR, 2026-11-20, 1 ADT; hold all inputs constant except cabin.
allow_retry=false; allow_poll=false; allow_retest=false; approved_inputs=[Y,Q,C,J,F,P,omitted]. One request per cabin, sequential within 30 minutes.
No operational lesson selected: search returned no matching SS-6400 scope.

Execution 2026-10-22: restricted request failed before HTTP (WinError 10061). Outside-restriction execution was rejected by automatic approval review because the saved Search credential would be sent over HTTP. No application behavior or remote outage established. Waiting for explicit credential-transmission authorization; approval belongs only in ticket scope.
`nUser 2026-10-22 explicitly approved sending the saved Preprod Search authorization credential to http://airapi51.kivops.info/v1/search over unencrypted HTTP (answer: it is ok).

User 2026-10-22 supplied Kibana searchapi index 5a5702c0-2fb2-11ee-86ef-e76df22fff5b, method=GTT GetMarkups, host.hostname=searchapi51; identifies this host as Preprod and confirms agent-exclusive requests. Empty GTT traceID correlation may use timestamps and matching agency/route. Log review made no additional Search requests.

2026-10-22 user sign-off: mark WARN as PASS because omitted-cabin key already existed within the 30-minute cache window. Applies to overall TC-07 only. Record as user-confirmed acceptance; no new endpoint execution or operational lesson.
