# QA workflow optimization review

Reviewed 2026-10-27. Recommendations for user analysis; no workflow, knowledge ledger, lesson trust, or permission changes implemented.

## Verified repair

SS-6348 report.html was missing the two heading CSS rules present in the current shared dispatch template. Synchronized only those rules; evidence, assertions, downloads and test results remain unchanged. Existing artifact verifier reproduced the failure before and passed afterward.

The scanner regression failed because the sandbox prevented Git sh.exe from creating its signal pipe (Win32 error 5), before the hook could run. The unchanged scanner test passed outside that boundary. Full offline suite outside the sandbox: 8 PASS / 2 SKIP / 0 FAIL. Both skips are absent ignored evidence. This is tooling verification, not fresh AirAPI execution or a full secret audit.

## Evidence and limits

Sources: knowledge/lessons/escalations.jsonl (127 events), knowledge/lessons/lessons.jsonl (22 snapshots, 15 unique lessons), bb/escalations.py, bb/lessons.py, AGENTS.md, knowledge/airapi-qa-reuse.md, and the latest SS-6432 report. These are recorded questions, not a verified transcript count of questions actually displayed to the user. Six answer events do not mean the other 54 questions were unanswered: scope decisions belong elsewhere, and answers may not have been recorded.

60 recorded questions. 28 use generic "What scope-approved operational step should handle ...?" wording: CONTRACT_MISMATCH 8, NO_DATA 8, TRANSPORT_ERROR 4, UNEVALUATED 4, and four other reasons once each. Of these 28, 22 have matching_lesson_found=true. This flag means search found a lexical/tag match, not a trusted, applicable lesson.

## Prioritized findings and recommendations

| Priority | Observed friction and source | Recommended direction, pending user design | Practice the user can share |
|---|---|---|---|
| 1 | Generic escalation often precedes a concrete question: transport at lines 1/3; expired fixture at 8/12; authentication at 103/105. handle_outcome constructs the generic question whenever no applicable action exists (bb/escalations.py:53). | One concrete question per unresolved blocker, including what failed, what was already checked, and the exact missing decision. A confirmed defect should produce FAIL evidence; ask only if a further decision is needed. | For each blocker, which checks you perform independently and the exact point where you involve another person. |
| 2 | ask deduplicates only identical run, reason, pattern and scope (bb/escalations.py:17). Currency comparison questions recur at lines 25/29; DRCT missing inventory at 110/112 and 124/126. | Track unresolved blockers across related case/run IDs while retaining each attempt as evidence. A genuinely changed scope, new failure, or resolved-then-recurring blocker must remain distinguishable. | How you recognize the same blocker and what counts as resolution or a new incident. |
| 3 | Lessons are mostly ticket-scoped; all conditions must match exactly (bb/lessons.py:48). Search can match shared words or ticket tags (line 121), so a match may be unusable. | Explain rejection reasons: candidate, wrong scope, disabled action, or exhausted budget. Review generic operational practices separately from ticket-specific observations; never automatically widen trust. | Which troubleshooting actions hold across providers/environments and which require local knowledge. |
| 4 | Fixture/access questions recur across SS-6400, SS-6409, SS-6413, SS-6414 and SS-6432 (question lines 24, 56-57, 64-65, 100, 119). | A compact intake checklist: current environment and endpoint, secure credential source reference, approved inputs, valid fixture, observable output, and existing scope permissions. Discover available local references first. | Your minimum ready-to-test inputs, preferred fixture discovery sources, and fixture expiry rules. Do not share secrets in documentation. |
| 5 | SS-6414 requested REST mode but execution remained SOAP; confirmation questions repeat at 72/75. Configuration and ticket flag spelling also differ (76). | Model the flow explicitly: baseline captured -> operator switch confirmed -> actual protocol verified -> behavior comparison. Configuration readiness is distinct from execution proof. | How you verify deployment readiness, configuration propagation and the actual provider path. |
| 6 | SS-6400 observability questions move from generic cache evidence to files=true and then Kibana location (24, 34, 37, 45). | Maintain scoped observability references: service, environment, log view, method, correlation fields and fallback limits. Confirm that the view supports the intended assertion before executing a long matrix. | One worked example from AirAPI response to provider logs, including how you handle absent trace IDs. |
| 7 | Some questions genuinely change expected behavior: QF allowance interpretation (4), null vs empty (63), public exchange paths (76), fare-basis matching (114). | Keep these live questions. Record the answer once in ticket scope and reuse within that ticket. Never promote it into a global operational lesson. | How you decide acceptable differences and where the authoritative requirement comes from. |
| 8 | Operational report preserves worst historical status per run and does not represent latest ticket acceptance. SS-6432 latest report has fresh passes while older failures remain in the aggregate. | Display attempt history separately from latest assessed ticket state, with explicit supersession and user-confirmed versus executed evidence. | Your retest closure and carry-forward rules, including who signs off exclusions. |
| 9 | Current reuse guide retains statements that TLS exceptions are not standing policy, while AGENTS.md explicitly grants standing AirAPI HTTPS verification bypass. | Reconcile older guidance with the current authority and link to that authority. Do not convert permission into a learned lesson. | How you want standing decisions distinguished from one-run exceptions. |

## Proposed flow to critique

1. Read ticket and existing scope, contract boundaries, and relevant historical evidence.
2. Discover current access/fixtures and confirm observability; bundle only genuinely missing inputs into a concrete question.
3. Establish required provider mode and baseline using execution evidence.
4. Execute only stated or approved cases, preserving opaque keys and paired evidence.
5. On WARN/FAIL, classify the outcome, check applicable operational lessons, and enforce total budgets. Complete allowed diagnostics; escalate one unresolved blocker once.
6. After a fix, rerun the approved exception and preserve earlier evidence. Do not repeat accepted coverage without reason.
7. Publish the dispatch and artifacts; distinguish executed results, user confirmation and exclusions.
8. Record operational reuse outcomes. Knowledge-ledger updates retain the separate preview/confirmation process.

This sequence is a review aid, not a new approved policy. Existing ticket scope and permissions continue to govern every action.

## Best material for the user to provide next

Choose one empty-inventory investigation, one source-log correlation, and one fixed-build retest. For each: trigger -> what you checked -> evidence you used -> next action and why -> stopping condition -> what would require a question. Include an example of an unnecessary agent question and what it should have done instead. These examples can inform the user's proposed solution without prematurely changing the workflow.
