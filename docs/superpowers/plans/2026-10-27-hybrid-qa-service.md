# Hybrid QA service implementation plan

User authorized implementation with agent judgment on 2026-10-27; entry points are this chat and QA Control. Work in the current checkout to retain existing local guidance and artifacts; no commits or publication.

Architecture: existing Codex chat/SDK prepares a structured plan; a separate localhost stdlib Python service validates it against a ticket-local machine scope before any network call. Initially support SS-6412 currency points comparison only. Other tickets retain the existing workflow. No extra AI API integration or dependency.

- [x] Add offline failing tests for scope enforcement, exact-key comparisons, missing data, secret exclusion and authenticated HTTP jobs.
- [x] Implement bb/search_job.py for immutable scope validation, one-request-per-input execution, minimal paired evidence, dispatch/collection/CSV artifacts and operational classification.
- [x] Implement bb/service.py and bb/service_client.py for authenticated loopback jobs, one worker, bounded queue, restart interruption, status/artifact retrieval and chat submission.
- [x] Add the SS-6412 machine scope reflecting the existing approved four-route/three-currency inputs and tolerance 0.5. Its four-example exception is explicit; no fifth live input is authorized.
- [x] Integrate the existing QA Control Codex runner: planner-only for supported tickets, then submit service job, poll, capture fresh artifacts through the existing report validator. Preserve all other tickets and release gates. Modify Dashboard only through approved filesystem access.
- [x] Run offline service tests, existing Black-Box suite, dashboard tests and local HTTP integration. Start the local service without live QA execution. Document launch, credentials and supported scope limitations.

Constraints: no live AirAPI tests in this build, booking endpoints, config mutation, arbitrary commands, raw payload retention, ledger updates, automatic retries or scope expansion. Resolve authentication privately from caller runtime. Pin HTTPS host and input queries in trusted scope; reject changed scope digests and modified inputs. Use the standing explicit AirAPI TLS authority at the call site. Persist job outputs only under fresh tasks/<ticket>/runs/service-<id>. Missing prerequisites produce WARN, never PASS. The AI planner is a Codex role, not an independently hosted model.

Verification: six service checks passed (including Postman replay and real Node/Python HTTP bridge); 51 Dashboard tests passed; existing offline suite 8 PASS / 2 SKIP / 0 FAIL; changed-file scanner zero findings. Independent review confirmed cancellation finding fixed, with no remaining important findings in its targeted follow-up. Live AirAPI/SDK execution was not performed. Service started hidden and authenticated health returned ready, one worker, SS-6412 supported.
