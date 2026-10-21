# Learning layer implementation plan

Source: user-supplied three-phase specification, 2026-10-21.

1. Add stdlib-only classification/security and transport; assert seeded outcomes,
   redaction, TLS defaults, HTTP failures, and redirect rejection using mocks.
2. Add append-only lessons, scoped action selection, escalation/answer logging,
   run reporting, candidate seeds, config and agent instructions. Test lifecycle,
   conflicts, forbidden learning, budgets and two-run escalation reduction.
3. Add a full working-tree/history scanner, staged-content hook and ignore rules.
   Produce a metadata-only security report; preserve existing evidence.
4. Only if history is clean: create feature/learning-layer, stage reviewed files
   and commit by module group. Never push. History findings stop Phase 3.

Existing user modifications and tickets are preserved. No live API requests.
No lesson defines expectations, tolerances, authorization or TLS exceptions.
Verification after each module group: python -B -m tests.test_learning.
