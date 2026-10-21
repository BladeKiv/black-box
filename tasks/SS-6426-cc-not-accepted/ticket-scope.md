# SS-6426 scope intake - 2026-10-21

Source: https://traveldev.atlassian.net/browse/SS-6426, description and all three Lana Bates comments read live. Target: PREPROD, compared with PROD per explicit developer QA instructions.

Intended behavior: Build global CC-not-accepted rules once per airline snapshot; merge matching route-scoped rules. OW/RT use the resulting map; MC merges first and last trip maps.

Developer QA instructions: Run equal PROD/PREPROD Search requests with rules=true; compare preData.CCNotAccepted for equality; compare timing process PreSearchActionsCommon for improvement. Internal allocation/CPU claims are developer benchmarks and cannot be certified from response wall time.

Environment references: knowledge/local-environment-references.json. User supplied both Postman environments on 2026-10-21 and requested retention for further operations. TLS verification remains enabled. Credentials are read from original local files and must not be exposed in artifacts.

User-approved inputs: cid=SAL103; omit pcc, fare and gds filters. No fresh endpoint execution yet. This is scope intake, not a QA result.
