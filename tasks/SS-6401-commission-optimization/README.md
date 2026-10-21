# SS-6401 commission comparison

Release signal: **PASS**. [Main report](runs/2026-10-15-tstcom-reviewed/qa-report.html): **180 PASS, 0 FAIL, 0 WARN** checks from the saved 180-request matrix.

F-90 is closed as PASS following user confirmation on 2026-10-16: TC7A and AJBUPY are equivalent equal-amount commission choices for the tested OD. Saved evidence was re-evaluated; no new API calls were made for this update. This does not independently establish random selection behavior.

[Saved fresh verification](runs/2026-10-15-f90-reproduction/qa-report.html): **12 PASS, 0 FAIL, 0 WARN** checks across the earlier 12 Search requests. Complete historical and fresh commission_info objects for both trips and all consolidators remain in the main report and [paired results](runs/2026-10-15-f90-reproduction/commission-info-evidence.json).

- [Main Postman collection](runs/2026-10-15-tstcom-reviewed/SS-6401.postman_collection.json)
- [Main expected-outcome CSV](runs/2026-10-15-tstcom-reviewed/expected-outcomes.csv)
- [Reproduction Postman collection](runs/2026-10-15-f90-reproduction/SS-6401.postman_collection.json)
- [Reproduction expected-outcome CSV](runs/2026-10-15-f90-reproduction/expected-outcomes.csv)

Assertions retain equal-amount and OD scope checks. Report downloads are embedded through Blob downloads, use the established dispatch CSS, and are written as UTF-8. The previous main URL serves the updated report too. Earlier versions remain preserved as internal-notes/before-public-update snapshots. Criteria and confirmation history are recorded in ticket-scope.md. No QA ledger update or Newman run.

Rebuild saved outputs: analyze.py <run-directory-name>, then report.py <run-directory-name>; rebuild reproduction before main. rerun-f90.py reads its credential component from AIRAPI_SEARCH_TOKEN and resumes previously captured requests.
