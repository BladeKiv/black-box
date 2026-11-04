# Provider field documentation supplied by user, 2026-10-26
Source: atlas-baggage-field-docs.png (user attachment).
- baggageWeight, KG: 0 = No Free baggage; -1 = No limitation on weight; >0 = Maximum weight.
- baggagePiece: 0 = No limitation; >0 = Maximum pieces.
- baggageSize: individual dimensions or total linear dimensions; empty means no limitation.
- passengerType: 0 Adult, 1 Child, 2 Infant.

Saved fresh retest: Alaska overhead source has 1 piece, -1 weight, 56*36*23cm. AirAPI retains 1 piece and 115cm/45in, omits numeric weight limits and negative weight text. PASS for the scoped no-weight-limit representation; no requirement to emit a literal unlimited phrase was supplied.
Alaska/Frontier checked source has weight 0 (no free baggage) alongside piece 0. The combined source supports their no-free-checked-baggage 0PC output; piece 0 alone was not treated as zero entitlement.
Status correction based on provider documentation and already executed retest, not a new endpoint run or user sign-off. Prior reports retained.
