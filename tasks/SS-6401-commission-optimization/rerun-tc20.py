import os
import json,sys
from pathlib import Path
import run

base=Path(__file__).resolve().parent
source=base/'runs'/'TSTCOM'
row=next(x for x in json.loads((source/'scenarios.json').read_text(encoding='utf-8')) if x['scenario_id']=='TC-20')
finding=next(x for x in json.loads((source/'debug-findings.json').read_text(encoding='utf-8')) if x['finding_id']=='F-14')
run.ROOT=base/'runs'/'2026-10-15-tc20-f14'
run.ROOT.mkdir(parents=True,exist_ok=True)
(run.ROOT/'scenarios.json').write_text(json.dumps([row],indent=2),encoding='utf-8')
(run.ROOT/'target-finding.json').write_text(json.dumps(finding,indent=2),encoding='utf-8')
run.run([row],3,os.environ['AIRAPI_SEARCH_TOKEN'])
