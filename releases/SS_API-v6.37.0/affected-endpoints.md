# SS_API-v6.37.0 — affected endpoint evidence

| Endpoint | Confirmed release scope | Tickets | Release evidence |
| --- | --- | --- | --- |
| `GET /v1/search` | Technical-stop `elapsedTime`; fare-level `keys.commission_info.fareCalculation[].routingInversion` | SS-6290, SS-6258 | PASS |
| `POST /v1/commission/{{cid}}/validation/dump-pub/true?pcc={PCC}` | PCC-specific CMS commission validation | SS-6296 | PASS |

## Future regression scope

Create endpoint-level regression coverage for the endpoints above to detect
behavioral regressions after future releases. The test data, environment, and
credentials workflow remains to be agreed before automation is added.
