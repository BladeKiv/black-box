"""SS-6437 legacy checks under an explicitly disabled SS-6438 merge flag."""
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
PLAN=[]
for i,(origin,destination) in enumerate([('SFO','FRA'),('LAX','MUC'),('ORD','FRA')],1):
 for cid in ('BCKDCR','AKKDCR'):
  PLAN.append({'scenario_id':'L'+str(i).zfill(2)+('-B' if cid=='BCKDCR' else '-A'),'cid':cid,'params':{'adt':'1','cabin':'C','fl[0][o]':origin,'fl[0][d]':destination,'fl[0][dt]':'2027-02-25','cid':cid,'debug':'1','original_cid':'1'}})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','config',*[x['scenario_id'] for x in PLAN]]);args=p.parse_args()
 if args.action=='prepare':
  (ROOT/'legacy-search-plan.json').write_text(json.dumps(PLAN,indent=2),encoding='utf-8')
  with (ROOT/'ticket-scope.md').open('a',encoding='utf-8') as f:f.write('\nUser baseline clarification: use SS-6437 already tested. Intended legacy checks from tasks/SS-6437/runs/dashboard-6-292970de-c2f8-4a9a-966a-ac8d50be023b/ticket-scope.md: BCKDCR mains must not contain both UPG and NGS in gdsOfferId; AKKDCR upgrade children must contain both UPG and NGS. Filtering and AKKDCR main-identifier checks were excluded from that baseline and are not added here. Runtime prerequisites: matching mergeWithRegular=false; BCKDCR secondBag=false/keepBothBagOptions=false; AKKDCR secondBag=true/keepBothBagOptions=true. Six relevant OW examples prepared across three routes; execute original SFO-FRA fixture once per CID first. No configuration writes. Await user configuration change because the relevant CID groups are currently enabled. The live clarification is a ticket expectation, not a learned operational answer.\n')
  print('Prepared six legacy examples; original SFO-FRA pair is the first execution target. No Search executed.')
 elif args.action=='config':
  transport.ROOT=ROOT
  c=transport.execute('/algo/conf','configuration-legacy',direct=True)
  configs=c['response']['body']['upgrade_config']['configs']
  print([{'index':i,'cid':[k for k in ('BCKDCR','AKKDCR') if k in x.get('cid',[])],'mergeWithRegular':x.get('mergeWithRegular','[missing]'),'secondBag':x.get('secondBag','[missing]'),'keepBothBagOptions':x.get('keepBothBagOptions','[missing]')} for i,x in enumerate(configs) if any(k in x.get('cid',[]) for k in ('BCKDCR','AKKDCR'))])
 else:
  row=next(x for x in PLAN if x['scenario_id']==args.action)
  c=json.loads((ROOT/'configuration-legacy.json').read_text())['response']['body']
  matches=[x for x in c['upgrade_config']['configs'] if row['cid'] in x.get('cid',[])]
  assert len(matches)==1 and matches[0].get('mergeWithRegular') is False
  both=row['cid']=='AKKDCR'
  assert matches[0].get('keepBothBagOptions') is both and matches[0].get('secondBag') is both
  transport.ROOT=ROOT
  capture=transport.execute('/v1/search?'+urlencode(row['params']),args.action,direct=True)
  response=capture['response'];body=response['body']
  rs=body.get('results',[]) if isinstance(body,dict) else []
  parents=[r for r in rs if ':UPG#' in r.get('gdsOfferId','')]
  children=[x for r in parents for x in r.get('ngsItineraries',[])]
  if not both:
   invalid=[r for r in rs if ':UPG#' in r.get('gdsOfferId','') and ':NGS#' in r.get('gdsOfferId','')]
   expected='No BCKDCR main gdsOfferId combines UPG and NGS.'
  else:
   invalid=[x for x in children if ':UPG#' not in x.get('gdsOfferId','') or ':NGS#' not in x.get('gdsOfferId','')]
   expected='Each AKKDCR upgrade ngsItineraries child gdsOfferId contains both UPG and NGS; observe children to evaluate the baseline.'
  missing_child_parents=[r for r in parents if not r.get('ngsItineraries')] if both else []
  status='FAIL' if invalid or missing_child_parents else 'PASS' if parents and (children or not both) else 'WARN'
  summary={'scenario_id':args.action,'cid':row['cid'],'http_status':response['http_status'],'results':len(rs),'upgrade_parents':len(parents),'upgrade_children':len(children),'invalid_count':len(invalid),'missing_child_parent_count':len(missing_child_parents),'expected_result':expected,'status':status,'paired_request':capture['request'],'invalid_excerpts':[{'key':r['key'],'gdsOfferId':r.get('gdsOfferId')} for r in invalid],'parent_identifiers':list(dict.fromkeys(r.get('gdsOfferId') for r in parents)),'child_identifiers':list(dict.fromkeys(r.get('gdsOfferId') for r in children))}
  (ROOT/(args.action+'-summary.json')).write_text(json.dumps(summary,indent=2),encoding='utf-8')
  if status!='PASS':
   context={'inventory_field':'results','observed_expectation':expected,'response_paths':['$.results[*].gdsOfferId','$.results[*].ngsItineraries[*].gdsOfferId']}
   context.update({'expectation_observed':False} if status=='FAIL' else {'comparable_count':0})
   outcome=classify_outcome(response['http_status'],json.dumps(body),response['transport_error'],context)
   esc=Escalations(store=Store())
   handle_outcome(esc.store,esc,outcome,'SS-6438-legacy-'+args.action,['SS-6438','SS-6437','PREPROD'],'legacy UPG NGS identifier baseline',{'ticket':'SS-6438','environment':'PREPROD','endpoint':'/v1/search','allow_retry':False,'allow_poll':False,'allow_retest':True,'approved_inputs':['legacy-search-plan.json']},retries=0,steps=int(args.action[1:3]))
  print(json.dumps({k:v for k,v in summary.items() if k not in ('invalid_excerpts','paired_request')}))
