# Runtime credentials and fresh Git history — 2026-10-21

The user authorized backing up the old `.git`, sanitizing commit-eligible files,
discard the old local history, initialize `main`, and commit only after the
staged secret scan passes. No remote or push is authorized for the agent.

The sibling `../Black-Box-git-backup` contains a SHA-256-verified copy of the
original `.git` (1,649 files). It retains the original sensitive history and
must remain private. No existing raw capture is needed in the new Git history.

Cleanup performed:

- Replaced malformed-token literals in SS-6344 with `INVALID_TEST_TOKEN` in
  the runner, collection scripts, and the report's embedded collection download.
- Sanitized collection authentication/body literals to runtime Postman variables.
- Replaced the Atlas session-log loader with BOOKING_USERNAME/BOOKING_PASSWORD
  checks and removed the collection-credential fallback. Its collection path
  is supplied through AIRAPI_POSTMAN_COLLECTION.
- Changed SS-6401 and its rerun entrypoints to AIRAPI_SEARCH_TOKEN; SS-6426 uses
  environment-specific URL/header variables; SS-6416 reads booking credentials
  directly from environment variables.
- Replaced personal repository paths with relative paths and external document
  references with runtime placeholders in commit-eligible files.
- Kept raw token/passenger captures and local environments ignored. Reinitializing
  Git removes their old index/history entries without deleting local evidence.
- Retained approved ticket expectations, scopes, historical results and the QA
  ledger's provenance. Sanitization does not constitute an API retest.

The security guard recognizes explicit fake fixtures, computed header expressions,
and encoded JSON collection downloads. Tests verify that real literal patterns
still block commits, including secrets in staged bytes and earlier Git objects.

Offline checks:

```powershell
python -B -m tests.test_learning
python -B -m tests.test_secrets
python -B -m tests.test_cleanup
```

Additional checks parse eligible Python/JSON and run `node --check` on JavaScript
without executing ticket flows. Staged verification uses both the installed hook
and `scripts/check_secrets.py --staged`; ignored historical captures are outside
that publication scope. The private staged audit contains metadata only.

No live endpoint calls, booking changes, credential-validity checks or push are
performed. Git backup/capture storage still contains the original private data.
