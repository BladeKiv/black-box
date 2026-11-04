# SS-6413 STAGE verification - 2026-10-23

Source: Jira description and Chris P DEV QA comment read live 2026-10-23.
Intended behavior: encode request currency in itinerary key; subsequent searches in another currency must not change the currency retrieved by Result or NGS Air Pricing for the original key. Keys remain opaque and unchanged.
Ticket example: JFK-LHR, 2026-11-25; GBP Search followed by USD Search, then retrieve original key.
Target: https://api.search.stage.travel-dev.com from local Stage environment.
No API requests executed: Stage environment has no populated search authorization or booking credentials, and no AIRAPI/Search token runtime variable is present.
Pending: authorized credential reference, CID/product_type, observable currency response paths or documented key check.
allow_retry=false; allow_poll=false; allow_retest=false; approved_inputs=[ticket GBP/USD sequence].
Operational lesson search returned no matching lessons. Escalation 05335e532ab741fc908ec11ba5bfedf5 logged. No provider tracks, configuration mutations, booking or ticketing calls.
