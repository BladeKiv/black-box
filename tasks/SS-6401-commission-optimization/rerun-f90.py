import os
import sys,json
from pathlib import Path
import run

base=Path(__file__).resolve().parent
source=base/'runs'/'2026-10-15-tstcom-usd1'
target=base/'runs'/'2026-10-15-f90-reproduction'
target.mkdir(parents=True,exist_ok=True)
finding=next(x for x in json.loads((source/'debug-findings.json').read_text()) if x['finding_id']=='F-90')
(target/'historical-f90-finding.json').write_text(json.dumps(finding,indent=2))
rep=finding['representative']; historical={'source_run':source.name,'finding_id':'F-90','requests':rep['requests'],'responses':{}}
for env in ['prod','preprod']:
 raw=json.loads((source/'evidence'/rep['scenario_id']/str(rep['repeat'])/env/'response.json').read_bytes())
 key=rep['difference'][env+'_key']
 historical['responses'][env]=next(x for x in raw['results'] if x.get('key')==key)
(target/'historical-f90-full-results.json').write_text(json.dumps(historical,indent=2))
row=next(x for x in json.loads((source/'scenarios.json').read_text()) if x['scenario_id']=='TC-28')
run.ROOT=target
rows=[row,{'scenario_id':'TC-28-targeted','query':{**row['query'],'gds':'A','pcc':'YVRG32400','val_cr':'BA'}}]
(target/'scenarios.json').write_text(json.dumps(rows,indent=2))
(target/'run-context.json').write_text(json.dumps({'run_date':'2026-10-15','scenario_count':2,'repetitions':3,'planned_requests':12,'filter_scope':'broad Search + focused gds=A/pcc=YVRG32400/val_cr=BA','scope':'Fresh F-90 reproduction: broad and focused Search; full historical and fresh commission_info retained for both trips'},indent=2))
if __name__=='__main__':run.run(rows,3,os.environ['AIRAPI_SEARCH_TOKEN'])
