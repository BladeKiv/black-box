"""Serialize operational classification of each saved exploration outcome."""
import json
from pathlib import Path
from bb.classify import classify_outcome
from bb.escalations import Escalations,handle_outcome
from bb.lessons import Store

ROOT=Path(__file__).resolve().parent
store=Store();esc=Escalations(store=store)
known={e.get('run') for e in esc.events() if e.get('event')=='run'}
for path in sorted(ROOT.glob('R??-?-summary.json')):
 name=path.name.removesuffix('-summary.json')
 s=json.loads(path.read_text());c=json.loads((ROOT/(name+'.json')).read_text())['response']
 scope={'ticket':'SS-6438','environment':'PREPROD','endpoint':'/v1/search','allow_retry':False,'allow_poll':False,'allow_retest':False,'approved_inputs':['all-cases-plan.json']}
 checks=[]
 if s.get('retained_violations'):checks.append(('filter','retained option loses a confirmed feature',{'expectation_observed':False}))
 if s.get('regular_mains')==0:checks.append(('inventory','regular cheapest inventory unavailable',{'comparable_count':0}))
 for kind,pattern,context in checks:
  run='SS-6438-20261102-all-cases-'+name+'-'+kind
  if run in known:continue
  context.update(inventory_field='results',response_paths=['$.results[*].ngsItineraries[*].keys.baggage.allowPieces','$.results[*].ngsItineraries[*].penalties.exchange','$.results[*].ngsItineraries[*].penalties.refund'],observed_expectation='Each retained option is at least equal on all three user-confirmed features and strictly better on one' if kind=='filter' else 'A regular-cheapest group with an observable UPG option is required for ticket examples 3/4')
  outcome=classify_outcome(c['http_status'],json.dumps(c['body']),c['transport_error'],context)
  result=handle_outcome(store,esc,outcome,run,['SS-6438','PREPROD'],pattern,scope,retries=0,steps=int(name[1:3]))
  print(name,kind,result['status'],result['reason_code'])
