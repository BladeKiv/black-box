# SS-6416 PREPROD scope - 2026-10-21

Current user clarifications: retain PREPROD port 8089; rerun Book/Info and retrieve actual information using HTTPS with TLS bypass. QF SYD-PER: user requested actual fields, without selecting a numeric expected interpretation. That segment is observation-only; do not certify its 4-piece aggregation or conflicting source dimensions. Final fresh run: runs/2026-10-21-preprod-live; LX 200 but 3P rather than ticket-required 2P (FAIL), AA 409 Booking already flown (WARN), QF first-two-segment personal-item exclusion and source mapping checks PASS. QF SYD-PER actually returns 4P / 7 kg / 105 cm; final three segments return explicit null baggage/carry-on. Fresh sources correlated by response traceID. Restricted-network connection refusals were not application responses or proof of a service outage.

Source: Jira description read live 2026-10-21. User confirms same PREPROD environment as SS-6425. Existing-booking POST /ndc/v1/book/info only.

Intended behavior: exclude the personal item from carry-on allowance. Linked LX example expects 2 pieces rather than 3; linked AA example expects 1 rather than 2. Third QF example requires checking distinct checked/carry-on allowances on each segment against provider source associations.

Approved inputs: only the three linked existing bookings (LX 2L2FGK, AA BRGQ35, QF C6426L). Preserve passenger types. No booking creation or modifications, no provider requests, no speculative edge cases. Read existing provider logs for source correlation only.

Execution permissions: allow_retry=false, allow_poll=false, allow_retest=true, approved_inputs=[LX,AA,QF]. One Book/Info request per fixture. No input variation or endpoint retries. Standing direct user TLS bypass applies explicitly at call site.

Lesson search: 609bbba636414a1c879738a99b5b2dc0 is a candidate for SS-6425 only and is not trusted/applied to SS-6416. No applicable trusted lesson found.
