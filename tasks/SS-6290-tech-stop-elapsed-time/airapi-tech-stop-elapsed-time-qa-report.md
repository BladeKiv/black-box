# AirAPI QA report — technical-stop `elapsedTime`

For the visual dispatch-sheet version, open
[airapi-tech-stop-elapsed-time-qa-report.html](/./tasks/SS-6290-tech-stop-elapsed-time/airapi-tech-stop-elapsed-time-qa-report.html).

> **Release signal:** `FAIL`
> **Run:** 2026-09-02 · **Scope:** DJT → TPA Search

## What we observed

For an option with one or more technical stops, AirAPI must provide
`elapsedTime` for the leg ending at each technical stop. The value is the
number of minutes from the preceding point's departure to that stop's arrival.
The rule must work globally, independent of provider; the reported gap is on
Amadeus options.

The supplied URL without credentials returned `401 Unauthorized` on
2026-09-02. A subsequent read-only authenticated call to the supplied host
returned `200 OK` with 215 options. The response exposed `results`, and each
observed option exposed `trips[].segments[].stop` and
`trips[].segments[].duration`.

The response mapping supplied during testing identifies original provider data
at `keys.original_info.gds`. A fresh authenticated response contained 208
options: 115 with `keys.original_info.gds=A`, 18 with `E`, and 75 without an
original-GDS value. It contained 28 positive-stop segments: 10 from original
GDS `A`, 3 from `E`, and 15 with no original-GDS value. None of the 28 segments
exposed `elapsedTime`.

One reproduced original-GDS `A` segment had these observable values:

| Field | Value |
| --- | --- |
| `departureTime` | `2027-03-20 14:15` |
| `stop` | `1` |
| `stops[0].locationCode` | `ISP` |
| `stops[0].arrivalDateTime` | `2027-03-20 17:05` |
| Expected `elapsedTime` | `170` minutes |
| Observed `elapsedTime` | missing |

The expected value is the elapsed time from the segment's departure to the
technical stop's arrival: 14:15 to 17:05 = 170 minutes. This **reproduces the
ticket defect** for original-GDS `A`.

The same field is also absent on all 18 observed positive-stop segments whose
original GDS is not `A`. Their expected values cannot be compared until the
field exists, but the missing-field behavior demonstrates that the gap is not
limited to the reproduced original-GDS `A` sample.

## Executed tests

| ID | Test case | Test data | Expected result | Actual result | Status |
| --- | --- | --- | --- | --- | --- |
| TC-01 | Authorized Search access | Supplied host, route, date, customer, and authorized Basic-auth environment | `200 OK` and JSON Search payload | `200 OK`; 208 options returned | PASS |
| TC-02 | Original-GDS `A` technical-stop duration | Segment DJT departure `2027-03-20 14:15`; first stop ISP arrival `2027-03-20 17:05` | `elapsedTime` exists and equals 170 minutes | `elapsedTime` is missing | FAIL |
| TC-03 | Other-provider technical-stop duration | 18 positive-stop segments whose original GDS is not `A` | `elapsedTime` exists for every technical stop and equals the calculated minutes | `elapsedTime` is missing on all 18 observed segments | FAIL |

## Evidence and rerun

- Live evidence: 208 options, 28 positive-stop segments, and missing
  `elapsedTime` on every observed positive-stop segment.
- [Postman collection](/./tasks/SS-6290-tech-stop-elapsed-time/airapi-tech-stop-elapsed-time-live.postman_collection.json)
- [Expected-outcome CSV](/./tasks/SS-6290-tech-stop-elapsed-time/airapi-tech-stop-elapsed-time-live-scenarios.csv)

## Manual-review handoff

Review the live-shape collection and CSV, set the authorized credentials, then
run it in Postman Runner. No QA-evidence ledger entry has been proposed or
written.
