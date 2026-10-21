# SS-6348 proposed implementation and verification plan

Intended behavior: `results[].ngsFeatures.list[].breakdown[]` must identify existing segments using one-based `trip:segment` references. The user confirmed this interpretation. For the ticket itinerary, the affected features must contain `["1:2","2:1"]`.

1. Use the saved Search fixture to establish a failing regression for the two-trip, four-segment itinerary: PR105 / PR2813, then PR2818 / PR104. Preserve each fresh Search key verbatim.
2. Developer task: trace where NGS breakdown references are constructed relative to the final response trips. Identify why this itinerary emits trip numbers 2 and 3 when the response contains trips 1 and 2. Black-box evidence establishes the mismatch, not its internal cause.
3. Correct the reference construction at the responsible mapping point so it uses the final response's one-based trip and segment numbering. Do not apply an unconditional subtraction to all output references; first verify the numbering source. Keep each feature attached to its intended segment.
4. Verify the fixture produces `["1:2","2:1"]` for the affected feature IDs. Check all returned breakdown references against existing trips and segments in the same Search response.
5. Deploy through the normal developer workflow, rerun the supplied AirAPI-only collection on the agreed host, and replace the failure evidence only with a separately recorded confirmed run. A missing itinerary or affected feature is WARN, not PASS.

Scope: original ticket Search plus five user-requested regression Searches. The regressions omit val_cr to include other airlines. No application source was inspected and no fix or deployment was performed during QA.

Run artifacts: set the Postman `authorization` variable locally to the supplied full Basic header; import the collection and CSV. Run all six CSV rows: the baseline row evaluates TC-01 and TC-02; each additional row evaluates its own reference-validity case without applying the ticket-specific flight pair. The collection uses `pm.test.skip` with a WARN label when inventory is unavailable; skipped checks are inconclusive.

HTTP status is recorded as an observation, not an invented ticket acceptance criterion. Prior run evidence is retained under runs/; current reports describe only the latest run.
