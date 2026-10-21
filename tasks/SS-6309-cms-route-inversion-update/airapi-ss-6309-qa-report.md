# AirAPI QA report — SS-6309 CMS route inversion update

> **Release signal:** `FAIL`
> **Run:** 2026-09-07 · **Scope:** Dev Search, new effective-country and area cascade branches

## What we observed

The new effective-country repro (`NYC → WAW // WAW → SJU`) and new area repro
(`GLA → NYC // NYC → ABV`) both returned Search inventory. Their sampled fare
records exposed `keys.commission_info.fareCalculation`, but the ticket's
observable route-inversion flag, `routingInversion`, was absent. The new
inversion behavior therefore cannot be verified.

## Executed tests

| ID | Test case | Test data | Expected result | Actual result | Status |
| --- | --- | --- | --- | --- | --- |
| TC-19 | Effective-country repro | `NYC-WAW // WAW-SJU`, 14/20 Oct 2026 | WAW-SJU fare has `routingInversion: true` | `200 OK`, 231 results; sampled fare has no `routingInversion` property | FAIL |
| TC-22 | Area-cascade repro | `GLA-NYC // NYC-ABV`, 14/20 Oct 2026 | NYC-ABV fare has `routingInversion: true` | `200 OK`, 290 results; sampled fare has no `routingInversion` property | FAIL |

## Failure evidence

### TC-19

~~~text
GET /v1/search?adt=1&debug=true&fare=PUB&cid=TST101&gds=S&pcc=6NVG&fl.0.o=NYC&fl.0.d=WAW&fl.0.dt=2026-10-14&fl.1.o=WAW&fl.1.d=SJU&fl.1.dt=2026-10-20
~~~

~~~json
{
  "keys": {
    "commission_info": {
      "fareCalculation": {
        "ADT": [{
          "code": "…",
          "departure": "NYC",
          "arrival": "WAW",
          "segments": ["…"]
        }]
      }
    }
  }
}
~~~

`routingInversion` is absent from the sampled fare record.

### TC-22

~~~text
GET /v1/search?adt=1&debug=true&fare=PUB&cid=TST101&gds=S&pcc=6NVG&fl.0.o=GLA&fl.0.d=NYC&fl.0.dt=2026-10-14&fl.1.o=NYC&fl.1.d=ABV&fl.1.dt=2026-10-20
~~~

~~~json
{
  "keys": {
    "commission_info": {
      "fareCalculation": {
        "ADT": [{
          "code": "…",
          "departure": "GLA",
          "arrival": "NYC",
          "segments": ["…"]
        }]
      }
    }
  }
}
~~~

`routingInversion` is absent from the sampled fare record.

## Evidence and rerun

- [Postman collection](/./tasks/SS-6309-cms-route-inversion-update/airapi-ss-6309-route-inversion.postman_collection.json)
- [Expected-outcome CSV](/./tasks/SS-6309-cms-route-inversion-update/airapi-ss-6309-route-inversion-scenarios.csv)

## Manual-review handoff

No QA-evidence ledger entry has been proposed or written.
