# Playbooks and verified test inputs

`python -B -m bb.playbooks` is a stdlib-only preparation tool. It never sends
requests, selects expectations, grants permissions, retries, or modifies the
lessons/escalations stores. Ticket text and `ticket-scope.md` remain authoritative.

## Lookup

```powershell
python -B -m bb.playbooks search --tags baggage atlas /v1/search --text "baggage mapping" --top 3
python -B -m bb.playbooks testdata --provider atlas --env dev
python -B -m bb.playbooks stats
python -B -m bb.playbooks list
```

Only approved playbooks are searched. Ranking is
`(3 * tag overlap + 2 * provider/endpoint overlap + keyword overlap) * confidence * freshness`.
Tags and provider/endpoint matches are case-insensitive exact matches against
`--tags`; keywords are words in `--text` intersecting title, summary and pitfalls.
Confidence is helped/used, or 0.5 before first use. Freshness halves every 180
days since `last_verified`, with future verification dates treated as age zero.
The minimum weighted score is 0.5. Ties sort by ID. Compact JSON includes only
id, title, endpoint_flow, case_patterns, testdata_refs and pitfalls, and is capped
at 12,000 UTF-8 bytes (approximately 3,000 English tokens). Oversized matches
are omitted whole. No match is normal and does not expand ticket scope.

Testdata lookup returns only `ok` entries. `D+30` and `D-2` resolve against the
machine's local calendar date at lookup; callers running elsewhere should use
the intended local timezone. Output adds `date` for `date_rule` and resolves
relative dates recursively inside `params`. Stored inputs never contain fixed
dates; verification timestamps are historical metadata, not travel dates.

## Distillation and review

```powershell
python -B -m bb.playbooks distill --run tasks/SS-123/runs/example --task SS-123 --approved
python -B -m bb.playbooks approve PB-search-001
python -B -m bb.playbooks reject PB-search-002
python -B -m bb.playbooks deprecate PB-search-001
python -B -m bb.playbooks record-use PB-search-003 --helped true --run unique-reuse-id
```

`--approved` asserts that the user approved the source run; it is not inferred
from passing results. Dashboard callers must supply it only after user approval.
Approval of a source run does not approve the resulting playbook.
All cases must have exactly one completed result in plan order. The run folder
must contain `cases.json`, `results.jsonl`, and a nonempty `ticket-scope.md`.
No historical runs are distilled automatically.

The plan's optional `family` chooses the PB family (default `endpoint-flow`),
and optional `providers` lists provider slugs. Executed case `steps` must contain
explicit HTTP method/path strings, such as `GET /v1/search`. Distillation retains
only endpoint identities and patterns consisting of endpoint flow plus names
of needed input parameters. It does not copy titles, steps prose, expected
results, assertions, request/response excerpts or ticket text.

Used inputs come from each case's `test_data.params` (or flat `test_data`, excluding
provider/env/description metadata), with `test_data.provider`
or a single plan provider, and the plan's `environment`. Inputs need a travel
date; fixed ISO dates are converted to offsets against the distillation date.
Passed/failed cases count as executed; a need_action case must explicitly set
`actual.request_executed: true` before its planned inputs enter the registry.
Missing-access cases therefore cannot promote unexecuted planned data.
Distill promptly after approval so `verified_at` accurately records that review.
For historical runs, review relative offsets before approval. Selected-itinerary
keys are replaced by `{key}` in endpoint paths; never put reusable Search keys,
authentication material or personal data in the registry.

Failed/need_action results contribute only a fixed pitfall sentence keyed by
`actual.reason_code`, when it is a known classifier reason. Otherwise the existing
classifier evaluates the failure response status/excerpt and the observed failed
assertion. Unknown need_action causes remain UNEVALUATED rather than guessing.
Stats count need_action reasons across distilled tasks, not live API outcomes.

Distillation creates one candidate per task, even if that task is requested
again from another run. Rejected playbooks are deprecated rather than deleted.
Approval promotes referenced candidate data to `ok`; stale entries stay stale.
Record-use requires an approved playbook and a unique nonempty `--run`; repeated
identical use is idempotent and contradictory reuse results are rejected.

Dashboard review uses `list` for validated playbook and registry snapshots.
`edit <PB-id> --stdin` reads one complete playbook JSON object from standard input;
only candidate guidance fields can change. Lifecycle, provenance, references and
usage counters are preserved. Unsafe edits are rejected without echoing values.
`testdata mark-ok --provider <p> --env <e> --id <id>` restores reviewed stale data;
candidate data must first be approved through its source playbook.
Distillation also accepts the Dashboard's `task_key` and result `result` aliases.

## Storage and validation

Playbooks live in `knowledge/playbooks/PB-<family>-<nnn>.json`; testdata registries
are arrays in `knowledge/testdata/<provider>-<env>.json`. References use
`<provider>-<env>.json#<entry-id>`. Family, provider and environment names are
lowercase slugs. `--root <directory>` before the subcommand selects an isolated
knowledge directory, useful for offline tools and tests.

Playbook fields are id, status (candidate/approved/deprecated), family, tags,
providers, endpoints, endpoint_flow, case_patterns (`pattern`, `needs`),
testdata_refs, pitfalls, source_tasks, last_verified, times_used, times_helped.
Optional title and summary support search; family is the fallback title.
Testdata fields are id, provider, env, description, params, date_rule,
verified_at, verified_run, status. The registry additionally supports `candidate`
for newly distilled entries, which are excluded from lookup until approval.

```powershell
python -B -m bb.playbooks testdata add --file reviewed-testdata.json
python -B -m bb.playbooks testdata mark-stale --provider atlas --env dev --id TD-example
```

`add` takes one complete testdata object and rejects duplicate IDs. Directly
adding `ok` data is a reviewer action; agents should use distill. Writes reject
credential/personal-data patterns using the same `bb.security.ensure_safe` as
lessons, and recursively reject expected-value, tolerance, comparator, permission
and extra-edge-case fields/text. Mechanical checks cannot prove the meaning of
arbitrary prose; human review before approval remains necessary.

A shared OS-released writer lock serializes mutations. JSON snapshots and the
JSONL event journal use atomic replacement; malformed store files fail loudly.
Atomicity is per file, not a multi-file transaction. After interruption, inspect
candidate data before approval and rerun the command; never edit the journal.
No existing lessons or escalations behavior is changed.

Offline checks: `python -B -m unittest tests.test_playbooks` and
`python -B -m tests.test_learning`.
