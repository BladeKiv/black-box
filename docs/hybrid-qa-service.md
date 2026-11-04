# Hybrid Black-Box QA service

Implemented 2026-10-27. Codex in this chat or QA Control performs preparation;
a separate Python process validates and executes supported plans. No new model
account, API key, dependency, dashboard screen or database is required.

## What works now

- Local authenticated HTTP service, bound only to 127.0.0.1:8766.
- One worker and at most eight active/queued jobs; OS lock prevents a second
  service writer for this project, even on another port.
- SS-6412 `currency_points_diff`: four approved routes, three currencies,
  twelve Search requests, eight comparisons. Only exact opaque-key matches and
  numeric `meta.rank_v2.points_diff` are compared, with tolerance 0.5.
- Runtime credentials are held in memory, excluded from job records and report
  evidence. No credential is requested in an HTTP URL or CLI argument.
- Each run writes only `cases.json` (the complete plan before any request)
  and `results.jsonl` (one completed case per appended line). No HTML, Markdown,
  CSV, Postman collection or payload files for passed cases are generated.
- QA statuses are `passed`, `failed`, `need_action`; pending is represented by
  a planned case without a result yet. Run precedence: failed, then need_action,
  then passed after all cases finish. Blockers include an exact `action_needed`.
- Failed cases contain credential-free paired comparator excerpts capped at
  2 KiB each, within an 8 KiB failure object. Full responses are unnecessary for
  this comparator. Internal operational helpers retain their legacy statuses;
  these never appear in the case output status.
- No retries, input variation, AirAPI polling or downstream endpoints are
  implemented. Cases continue after failures or blockers. Cancellation prevents
  further requests and marks remaining cases need_action in the partial stream.

## Start and health

Run from the Black-Box project root:

```powershell
python -B -m bb.service
```

In another terminal:

```powershell
python -B -m bb.service_client health
```

The service writes its local URL and generated access key into ignored
`.qa-service/runtime.json`. Keep that directory private to this Windows user;
do not copy it into source control or reports. Windows uses the directory's
inherited user ACLs; POSIX permissions are restricted explicitly.

This is a manually started background process, not an installed Windows service.
Use Ctrl+C in a foreground terminal, or stop only the recorded Python process
when started hidden. Restart does not replay queued/running jobs: it marks them
interrupted. Partial case results are preserved under the fresh ticket run.
Job polling reads local service state; it does not poll AirAPI.

## From this chat

The agent follows AGENTS.md: selected environment, discover Search host/secure
authentication reference, prepare at least five in-scope examples unless an
explicit smaller scope applies, then identify the endpoint flow. The service
scope for SS-6412 explicitly retains its existing four-route exception.

Produce the structured plan without credentials:

```powershell
python -B -m bb.service_client plan --scope tasks/SS-6412-currency-ranking/service-scope.json
```

Save that JSON to a fresh run-preparation file. Before an explicitly requested
live test, set `AIRAPI_ENVIRONMENT=STAGE1`, resolve the matching host into
`AIRAPI_BASE_URL`, and resolve the complete Search header
into `AIRAPI_SEARCH_AUTHORIZATION` through the existing secure runtime source.
Never print the value. Then:

```powershell
python -B -m bb.service_client submit --plan <plan-file>
python -B -m bb.service_client status <job-id>
```

Submission starts execution; it is not a dry run. This build did not submit a
live job. Outputs stay under `tasks/<ticket>/runs/service-<job-id>/`.

## From QA Control

The backend adapter is installed in the sibling Dashboard project. For SS-6412,
the selected profile must match the scope's environment name `STAGE1` and HTTPS
origin. Codex receives the scoped planning prompt with network disabled and
Search/Kibana runtime credentials withheld. It writes the internal input plan under `.qa-service/plans/` (outside the run
folder), then
the backend submits it to the local service and captures its fresh artifacts
as `cases.json` and `results.jsonl` in the dashboard run folder. The adapter
copies the plan and new complete result lines while the service runs. The
dashboard owns validation, pending-case insertion, DB ingestion and UI updates;
its legacy results.json validator must be migrated separately before rollout.

The adapter does not silently fall back to unrestricted agent execution if the
service is unavailable or the plan is rejected. Other tickets keep their existing
agent workflow until a supported service workflow is explicitly added. Restart
the QA Control backend to load this code if it was already running.

The source adapter and a repeatable installer are in `integrations/qa-control/`:

```powershell
python -B integrations/qa-control/install.py <Dashboard-project-path>
```

No dashboard settings, environment profiles, credentials, database or release
approval rules were changed. A cancelled dashboard job requests service
cancellation; an in-flight Search can take up to its 30-second timeout to return.
The worker checks cancellation before issuing another request.

## Scope and authority

`service-scope.json` is a trusted, non-secret machine scope derived from the
existing ticket scope. It pins the environment, HTTPS origin, exact query inputs,
currencies, tolerance and budget. The normalized-text SHA-256 binds it to
`ticket-scope.md`. The service snapshots it at startup and rejects changes until
reviewed and restarted. The AI planner must not edit either scope to bypass a
rejection. Adding a scope file is not permission to run its job.

Search authentication comes only from the caller's runtime. TLS verification is
disabled explicitly under the standing direct AirAPI authorization in AGENTS.md;
this permission is not learned or obtained from the plan. The transport preserves
HTTPS and rejects redirects. Neither configuration discovery nor operational
lessons supply expected behavior.

The service searches operational lessons and records internal WARN/FAIL triage. It does
not execute suggested recovery actions or claim lesson successes. While the
service executes jobs, it is the hosting writer of the operational stores;
do not run a second writer concurrently. The durable QA evidence ledger is
unchanged and retains its separate approval workflow.

## Verification and current limits

Run `python -B -m tests.test_service` for scope enforcement, comparisons,
stream ordering, failure limits, credential checks, API authentication, singleton lock,
cancellation, interrupted jobs and a real Node-adapter-to-Python-service bridge.
The bridge uses a temporary project and missing authentication; it makes no
AirAPI requests. QA Control adds adapter tests to its normal backend suite.

`bb.selftest` snapshots tracked files only: until new files are committed/staged,
run the new test module separately as well. No source files were staged or
committed during this implementation.

The service is deliberately narrow. It does not independently interpret new
tickets, host a model, create bookings, change configuration, add fixtures,
automatically recover after a crash, install a startup task, or clean old jobs.
The AI portion still runs through Codex chat/SDK. Scope restrictions are enforced
by the service API, not an OS security boundary against a local user who can edit
the project or restart the service. Live credential access, actual inventory and
the SDK planner's end-to-end live execution have not been validated by this build.
