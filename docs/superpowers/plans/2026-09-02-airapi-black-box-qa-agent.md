# AirAPI Black-Box QA Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a project-local AirAPI QA agent that automatically applies strict black-box testing rules, uses a durable confirmed-evidence ledger, and produces reusable report/collection artifacts.

**Architecture:** `AGENTS.md` supplies automatic project-wide routing and safety boundaries. The contract reference supplies stable, evidence-labeled public API knowledge; a separate ledger stores only user-approved confirmed findings. A template supplies the standard QA output shape without encoding implementation assumptions.

**Tech Stack:** Markdown, Postman Collection v2.1 JSON conventions, PowerShell read-only validation.

**Spec:** `docs/superpowers/specs/2026-09-02-airapi-black-box-qa-agent-design.md`

## Global Constraints

- Do not inspect, search, or infer from AirAPI application source code.
- Treat ticket/spec text as the sole source of intended behavior; use contract knowledge only for regression coverage and explicit evidence boundaries.
- Preserve exact HTTP/JSON property spelling and treat Search keys as opaque.
- Label non-ticket behavior as `[assumption]`; never convert a documented gap into an assertion.
- Do not mutate AirAPI configuration, call booking endpoints, or write a memory entry without the user's explicit approval of its exact text.
- Do not modify the existing technical-stop collection or CSV.

---

### Task 1: Establish contract knowledge and durable evidence ledger

**Files:**
- Create: `knowledge/airapi-contract.md`
- Create: `knowledge/airapi-qa-memory.md`

**Interfaces:**
- Consumes: approved PDF-derived public contract statements and the design specification.
- Produces: `knowledge/airapi-contract.md` for all AirAPI QA requests and `knowledge/airapi-qa-memory.md` for confirmed, user-approved observations.

- [ ] **Step 1: Create the contract reference with evidence rules**

Write `knowledge/airapi-contract.md` with these exact sections: `Use and evidence`, `Endpoint map`, `Search`, `Asynchronous Search`, `Selected-itinerary endpoints`, `Read-only configuration discovery`, `Response-schema guardrails`, `Status guardrails`, and `Regression design`. State that the reference records public contracts, that missing fields differ from false/zero/empty values, and that unspecified nested shapes or transport statuses must remain unspecified.

- [ ] **Step 2: Record exact endpoint and schema boundaries**

In the reference, include only these public endpoint relationships:

```text
GET /v1/search -> results[].key
GET /v1/search?async=true -> searchId, status, completed, progress
GET /v1/async/poll?searchId=... -> completed, progress
GET /v1/async/get?searchId=... -> Search-compatible results[]
GET /v1/result/ANY/{key} -> result
GET /v1/ngs-air-pricing/{product_type}/{key} -> shelves
GET /v1/air-pricing/allfares/{product_type}/{key} -> fares
GET /algo/conf -> JSON object root
```

State that Result, NGS Air Pricing, and AllFares are independent sibling consumers of a Search key and that `GET /algo/conf` does not prove that a module executed for a particular request.

- [ ] **Step 3: Create the confirmed-evidence ledger**

Write `knowledge/airapi-qa-memory.md` with an empty ledger and this entry protocol:

```markdown
## Entry format

### YYYY-MM-DD — short title

- Source: ticket ID/spec/API observation
- Scope: endpoint, provider, or regression class
- Confirmed behavior: observable fact only
- QA consequence: regression coverage or assertion rule
- Approval: user approval reference
```

Add a rule that assumptions, hypotheses, credentials, private payloads, and source-code-derived claims are prohibited. Add a rule requiring a two-stage flow: preview the exact entry after manual review, then write it only after explicit confirmation.

- [ ] **Step 4: Validate the knowledge files**

Run:

```powershell
rg -n 'GET /v1/search|GET /v1/async/poll|GET /v1/async/get|GET /v1/result/|GET /v1/ngs-air-pricing/|GET /v1/air-pricing/allfares/|GET /algo/conf' knowledge/airapi-contract.md
rg -n 'assumptions|hypotheses|two-stage|explicit confirmation' knowledge/airapi-qa-memory.md
```

Expected: every endpoint appears in the contract reference and the ledger explicitly prevents unconfirmed knowledge.

- [ ] **Step 5: Commit the focused knowledge baseline**

```powershell
git add knowledge/airapi-contract.md knowledge/airapi-qa-memory.md
git commit -m "docs: add AirAPI black-box QA knowledge base"
```

Expected: only the two knowledge files are staged; existing untracked technical-stop files remain unstaged.

### Task 2: Add automatic agent routing and reusable QA output template

**Files:**
- Create: `AGENTS.md`
- Create: `templates/airapi-qa-deliverable.md`

**Interfaces:**
- Consumes: `knowledge/airapi-contract.md`, `knowledge/airapi-qa-memory.md`, and a user-supplied ticket/spec.
- Produces: a ticket-scoped markdown QA report and an importable Postman Collection v2.1 JSON; does not autonomously persist ticket findings.

- [ ] **Step 1: Write automatic activation rules**

Create `AGENTS.md` with an `AirAPI Black-Box QA Agent` section activated for AirAPI tickets/specifications, API regression analysis, Postman/Newman collection requests, endpoint contract questions, and provider/aggregation QA. Require it to read both `knowledge/` files before producing an answer, while treating the ledger as supplemental confirmed evidence rather than intended behavior.

- [ ] **Step 2: Write hard black-box and handoff rules**

In `AGENTS.md`, prohibit application source inspection, configuration mutation, booking tests, credential exposure, and inference beyond the ticket/contract. Require a QA report with: intended behavior, covered scenarios, `[assumption]` items, and open questions/risks. Require a valid importable Postman collection grouped into Track A (provider-level only when a source endpoint/payload is provided) and Track B (AirAPI aggregation). Require expected-outcome CSV variables where inventory is non-deterministic.

Add the exact handoff rule: stop after delivering the report and collection; only after explicit user approval, preview a proposed ledger entry; write it only after a second explicit user confirmation.

- [ ] **Step 3: Write the output template**

Create `templates/airapi-qa-deliverable.md` with:

```markdown
## QA report

### Summary of intended behavior

### Test scenarios covered

### Assumptions

### Open questions / risks

## Postman collection

- Track A — Provider-level evidence
- Track B — AirAPI aggregation-level evidence

## Manual-review handoff
```

Under `Postman collection`, require `pm.test` assertions, pre-request setup, scenario variables, and an expected-outcome CSV row format of `scenario_id`, `expected_result`, `provider_filter`, `search_url`, and ticket-specific inputs. State that unknown response paths are `[assumption]` and must be parameterized, not guessed.

- [ ] **Step 4: Validate the agent contract and template**

Run:

```powershell
rg -n 'application source|\[assumption\]|Track A|Track B|second explicit|knowledge/airapi-contract.md|knowledge/airapi-qa-memory.md' AGENTS.md templates/airapi-qa-deliverable.md
```

Expected: automatic routing, black-box restrictions, two-stage memory approval, and both tracks are explicitly present.

- [ ] **Step 5: Commit the agent shell and template**

```powershell
git add AGENTS.md templates/airapi-qa-deliverable.md
git commit -m "feat: add automatic AirAPI black-box QA agent"
```

Expected: only the agent rules and template are staged; no pre-existing artifact is included.

### Task 3: Perform a black-box dry-run acceptance check

**Files:**
- Read: `AGENTS.md`
- Read: `knowledge/airapi-contract.md`
- Read: `knowledge/airapi-qa-memory.md`
- Read: `templates/airapi-qa-deliverable.md`

**Interfaces:**
- Consumes: a synthetic ticket stating a response-field change and no response schema.
- Produces: a dry-run checklist proving the agent would label unknown schema details as assumptions, use both tracks correctly, and withhold memory writes.

- [ ] **Step 1: Define the acceptance prompt**

Use this prompt without accessing any application source:

```text
Ticket: A provider option with a technical stop must expose a new duration field. The ticket does not state the response path, unit, provider endpoint, or sandbox guarantee.
```

- [ ] **Step 2: Verify expected agent decisions**

Check that the dry-run output would:

```text
1. Require the missing response path and unit to be labeled [assumption].
2. Put provider verification in Track A only if a provider contract endpoint or payload is supplied.
3. Put the aggregate endpoint scenario in Track B.
4. Use no_match_allowed or equivalent expected-outcome CSV handling for unstable inventory.
5. Stop after report and collection delivery without writing knowledge/airapi-qa-memory.md.
```

- [ ] **Step 3: Verify repository state**

Run:

```powershell
git status --short
```

Expected: the previously existing technical-stop collection and CSV remain unchanged and no unapproved ledger entry exists.

- [ ] **Step 4: Commit only if the dry-run creates a tracked acceptance artifact**

Do not create an acceptance artifact unless the user asks for one. If none is created, make no commit in this task.
