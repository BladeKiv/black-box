"""Additional ticket inventory and merge-disabled baseline checks, Search only."""
import argparse
import importlib
import json
from pathlib import Path
from urllib.parse import urlencode
from bb.classify import classify_outcome
from bb.escalations import Escalations,handle_outcome
from bb.lessons import Store

TICKET=Path(__file__).resolve().parent
ROOT=TICKET/'runs'/'2026-11-02-warn-and-disabled'
transport=importlib.import_module('tasks.SS-6438-upg-ngs-merge.run-search')
oracle=importlib.import_module('tasks.SS-6438-upg-ngs-merge.analyze-merge')
retest=importlib.import_module('tasks.SS-6438-upg-ngs-merge.retest-per-cid')
ROUTES=[('SFO','CDG','2026-11-20','2026-12-04'),('BOS','MUC','2027-04-15','2027-04-29'),('IAD','FRA','2027-04-15','2027-04-29'),('SEA','LHR','2027-04-15','2027-04-29'),('JFK','CDG','2027-04-15','2027-04-29')]
PLAN=[]
for i,(origin,dest,depart,back) in enumerate(ROUTES,1):
 for cid in ('BCKDCR','AKKDCR'):
  PLAN.append({'scenario_id':'N'+str(i).zfill(2)+('-B' if cid=='BCKDCR' else '-A'),'cid':cid,'purpose':'Find positive regular-cheapest UPG merge branches using previously unexecuted Search inputs','params':{'adt':'1','cabin':'C','debug':'1','original_cid':'1','cid':cid,'fl[0][o]':origin,'fl[0][d]':dest,'fl[0][dt]':depart,'fl[1][o]':dest,'fl[1][d]':origin,'fl[1][dt]':back}})

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('scenario',choices=['prepare',*[x['scenario_id'] for x in PLAN]])
 args=parser.parse_args()
 if args.scenario=='prepare':
  ROOT.mkdir(parents=True,exist_ok=True)
  (ROOT/'new-search-plan.json').write_text(json.dumps(PLAN,indent=2),encoding='utf-8')
  (ROOT/'ticket-scope.md').write_text('SS-6438 PREPROD continuation. User requests previously unexecuted Searches to attempt remaining WARNs, then skip unresolved coverage; also requests legacy functionality with mergeWithRegular disabled for some CIDs. Existing feature comparators and singleton clarification remain in parent scope. Five new relevant round-trip examples are prepared across both enabled CIDs (ten potential requests); execute at most four route/date steps per missing positive branch, no retry or polling. Fifth route is reserve only. No configuration mutation. Baseline expectations require live user confirmation and fresh matching-CID discovery before baseline execution. HTTP Search/configuration authorization remains in effect. No state-changing or downstream endpoints. Lessons search found candidate 14720e8ff1ad4bf5b41904cf17725d4e only, not applied.\n',encoding='utf-8')
  store=Store();esc=Escalations(store=store)
  esc.ask(run='SS-6438-20261102-warn-and-disabled',question='For mergeWithRegular=false, should UPG options remain separate from regular NGS groups, with existing keepBothBagOptions behavior unchanged?',reason_code='BASELINE_EXPECTATION',matching_lesson_found=False,tags=['SS-6438','PREPROD'],pattern='legacy baseline expected behavior requires confirmation',scope_conditions={'ticket':'SS-6438','environment':'PREPROD','endpoint':'/v1/search'})
  print('Prepared five new route/date examples paired across CIDs; no Search executed.')
 else:
  plan=next(x for x in PLAN if x['scenario_id']==args.scenario)
  config=json.loads((ROOT/'configuration.json').read_text())['response']['body']
  matches=[x for x in config['upgrade_config']['configs'] if plan['cid'] in x.get('cid',[])]
  assert len(matches)==1 and matches[0].get('mergeWithRegular') is True
  transport.ROOT=ROOT
  capture=transport.execute('/v1/search?'+urlencode(plan['params']),args.scenario,direct=True)
  summary=retest.summarize(capture)
  (ROOT/(args.scenario+'-summary.json')).write_text(json.dumps(summary,indent=2),encoding='utf-8')
  checks=[]
  if summary.get('failing_groups'):checks.append(('FAIL',{'expectation_observed':False},'fresh retained feature rule contradiction'))
  if summary.get('regular_mains',0)==0:checks.append(('WARN',{'comparable_count':0},'positive regular cheapest inventory unavailable'))
  for expected,context,pattern in checks:
   response=capture['response']
   context.update(inventory_field='results',observed_expectation='Positive regular-main/retained-UPG group follows the confirmed three-feature comparator',response_paths=['$.results[*].keys.upgrade_info','$.results[*].ngsItineraries','$.results[*].keys.baggage.allowPieces','$.results[*].penalties.exchange','$.results[*].penalties.refund'])
   outcome=classify_outcome(response['http_status'],json.dumps(response['body']),response['transport_error'],context)
   esc=Escalations(store=Store())
   handle_outcome(esc.store,esc,outcome,'SS-6438-warn-and-disabled-'+args.scenario+'-'+expected,['SS-6438','PREPROD'],pattern,{'ticket':'SS-6438','environment':'PREPROD','endpoint':'/v1/search','allow_retry':False,'allow_poll':False,'allow_retest':False,'approved_inputs':['new-search-plan.json']},retries=0,steps=int(args.scenario[1:3]))
  print(json.dumps({'scenario':args.scenario,'http_status':summary['http_status'],'results':summary['result_count'],'groups':len(summary['groups']),'regular_mains':summary.get('regular_mains'),'failing_groups':summary.get('failing_groups')}))
