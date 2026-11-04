"""Fresh Search retest after the per-CID configuration migration."""
import argparse
import importlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from bb.classify import classify_outcome
from bb.escalations import Escalations,handle_outcome
from bb.lessons import Store

TICKET=Path(__file__).resolve().parent
ROOT=TICKET/'runs'/os.environ.get('SS6438_RUN_NAME','2026-11-02-per-cid-merge')
transport=importlib.import_module('tasks.SS-6438-upg-ngs-merge.run-search')
oracle=importlib.import_module('tasks.SS-6438-upg-ngs-merge.analyze-merge')
previous=json.loads((TICKET/'all-cases-analysis.json').read_text())
PLAN=[{'scenario_id':r['scenario_id'],'cid':r['cid'],'keepBothBagOptions':r['keepBothBagOptions'],'request':r['request']} for r in previous['runs']]

def summarize(capture):
 response=capture['response'];body=response['body']
 if not isinstance(body,dict) or not isinstance(body.get('results'),list):
  return {'http_status':response['http_status'],'transport_error':response['transport_error'],'groups':[],'result_count':None}
 groups=[]
 for index,main in enumerate(body['results']):
  children=main.get('ngsItineraries',[])
  if 'upgrade_info' not in main.get('keys',{}) and not any('upgrade_info' in c.get('keys',{}) for c in children):continue
  options=[main]+children
  fs=[oracle.features(o) for o in options];prices=[o['prices']['totalPrice'] for o in options]
  violations=[{'option_index':i,'previous':oracle.excerpt(options[i-1]),'current':oracle.excerpt(options[i]),'lost_features':[k for k,a,b in zip(('bags','exchange','refund'),fs[i],fs[i-1]) if a<b]} for i in range(1,len(options)) if not oracle.improves(fs[i],fs[i-1])]
  groups.append({'result_index':index,'main_source':'UPG' if 'upgrade_info' in main.get('keys',{}) else 'regular','options':[oracle.excerpt(o) for o in options],'signature':oracle.signature(main),'price_order_ok':prices==sorted(prices),'features_ok':not violations,'flight_identity_ok':all(oracle.signature(main)==oracle.signature(o) for o in children),'numbering_ok':all(o.get('gdsOfferId','').endswith(':NGS#'+str(i+1)) for i,o in enumerate(options)) if children else main.get('gdsOfferId')==':UPG#','violations':violations})
 return {'http_status':response['http_status'],'result_count':len(body['results']),'groups':groups,'regular_mains':sum(g['main_source']=='regular' for g in groups),'failing_groups':sum(not all(g[k] for k in ('price_order_ok','features_ok','flight_identity_ok','numbering_ok')) for g in groups)}

def log_outcome(scenario,capture,summary):
 response=capture['response'];store=Store();esc=Escalations(store=store)
 scope={'ticket':'SS-6438','environment':'PREPROD','endpoint':'/v1/search','allow_retry':False,'allow_poll':False,'allow_retest':True,'approved_inputs':['runs/'+ROOT.name+'/search-plan.json']}
 checks=[]
 if summary.get('failing_groups'):checks.append(('retained-rules',{'expectation_observed':False},'retained group contradicts confirmed price feature identity or numbering rule'))
 if not summary['groups']:checks.append(('inventory',{'comparable_count':0},'no observable UPG merge group in requested Search'))
 for suffix,context,pattern in checks:
  context.update(inventory_field='results',response_paths=['$.results[*].ngsItineraries','$.results[*].keys.baggage.allowPieces','$.results[*].penalties.exchange','$.results[*].penalties.refund'],observed_expectation='Prices ascend; features are equal or better on all three fields and strictly improve on at least one; configured child eligibility and singleton clarification apply')
  outcome=classify_outcome(response['http_status'],json.dumps(response['body']),response['transport_error'],context)
  handle_outcome(store,esc,outcome,'SS-6438-'+ROOT.name+'-'+scenario+'-'+suffix,['SS-6438','PREPROD'],pattern,scope,retries=0,steps=1)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('scenario',choices=['prepare',*[x['scenario_id'] for x in PLAN]])
 args=parser.parse_args()
 if args.scenario=='prepare':
  ROOT.mkdir(parents=True,exist_ok=True)
  (ROOT/'search-plan.json').write_text(json.dumps(PLAN,indent=2),encoding='utf-8')
  (ROOT/'ticket-scope.md').write_text('SS-6438 PREPROD full retest, explicitly requested after configuration migration. Source task scope and user-confirmed comparators/singleton rule remain in ../../ticket-scope.md. Fresh per-CID flags are upgrade_config.configs[].mergeWithRegular: true for AKKDCR config index 2 and BCKDCR index 3; keepBothBagOptions true/false respectively. The global enable_merge field is absent and is not a prerequisite. Thirteen existing Search examples are prepared, once each, no retries/polling/input changes/downstream calls. Fresh configuration.json precedes execution. Read-only HTTP Search and authenticated configuration reads retain direct user authorization. Credentials resolve only at runtime from the PREPROD local Postman environment. No service-scope.json supports this ticket. Lesson 14720e8ff1ad4bf5b41904cf17725d4e is candidate only; no trusted matching lesson applied. Prior results stay separate.\n',encoding='utf-8')
  print('Prepared 13 exact Search replays; no Search executed.')
 else:
  config=json.loads((ROOT/'configuration.json').read_text())['response']['body']
  row=next(r for r in PLAN if r['scenario_id']==args.scenario)
  matches=[x for x in config['upgrade_config']['configs'] if row['cid'] in x.get('cid',[])]
  assert len(matches)==1 and matches[0].get('mergeWithRegular') is True
  assert matches[0].get('keepBothBagOptions') is row['keepBothBagOptions']
  parsed=urlsplit(row['request']['url']);assert parsed.scheme=='http' and parsed.netloc=='airapi51.kivops.info' and parsed.path=='/v1/search'
  transport.ROOT=ROOT
  capture=transport.execute(parsed.path+'?'+parsed.query,args.scenario,direct=True)
  summary=summarize(capture)
  (ROOT/(args.scenario+'-summary.json')).write_text(json.dumps(summary,indent=2),encoding='utf-8')
  log_outcome(args.scenario,capture,summary)
  print(json.dumps({'scenario':args.scenario,'http_status':summary['http_status'],'results':summary['result_count'],'groups':len(summary['groups']),'regular_mains':summary.get('regular_mains'),'failing_groups':summary.get('failing_groups')}))
