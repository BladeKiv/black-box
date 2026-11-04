"""Bounded Search inventory exploration authorized by the user continuation."""
import argparse
import importlib
import json
import urllib.parse

transport=importlib.import_module('tasks.SS-6438-upg-ngs-merge.run-search')
analysis=importlib.import_module('tasks.SS-6438-upg-ngs-merge.analyze-merge')
ROOT=transport.ROOT
BASE={'adt':'1','cabin':'C','debug':'1','original_cid':'1'}
ROUTES=[
 ('SFO','FRA','2027-02-25','2027-03-11'),
 ('LAX','MUC','2027-02-25','2027-03-11'),
 ('ORD','FRA','2026-11-20','2026-12-04'),
 ('JFK','LHR','2027-02-25','2027-03-11'),
 ('SFO','CDG','2026-11-20','2026-12-04'),
]
PLAN=[]
for idx,(origin,dest,depart,back) in enumerate(ROUTES,1):
 for cid in ('BCKDCR','AKKDCR'):
  PLAN.append({'id':'R'+str(idx).zfill(2)+('-B' if cid=='BCKDCR' else '-A'),'purpose':'Find regular-cheapest groups and ticket feature-filter examples in round-trip inventory','keepBothBagOptions':cid=='AKKDCR','params':{**BASE,'cid':cid,'fl[0][o]':origin,'fl[0][d]':dest,'fl[0][dt]':depart,'fl[1][o]':dest,'fl[1][d]':origin,'fl[1][dt]':back}})

def summarize(capture):
 body=capture['response']['body']
 if not isinstance(body,dict) or not isinstance(body.get('results'),list):
  return {'http_status':capture['response']['http_status'],'transport_error':capture['response']['transport_error'],'groups':None}
 groups=[]
 for i,main in enumerate(body['results']):
  children=main.get('ngsItineraries',[])
  if 'upgrade_info' not in main.get('keys',{}) and not any('upgrade_info' in c.get('keys',{}) for c in children):continue
  opts=[main]+children
  vectors=[analysis.features(o) for o in opts]
  prices=[o['prices']['totalPrice'] for o in opts]
  groups.append({'result_index':i,'main_source':'UPG' if 'upgrade_info' in main.get('keys',{}) else 'regular','options':[analysis.excerpt(o) for o in opts],'price_order_ok':prices==sorted(prices),'features_ok':all(analysis.improves(a,b) for a,b in zip(vectors[1:],vectors)),'flight_identity_ok':all(analysis.signature(main)==analysis.signature(c) for c in children)})
 return {'http_status':capture['response']['http_status'],'results':len(body['results']),'groups':len(groups),'regular_mains':sum(g['main_source']=='regular' for g in groups),'UPG_mains':sum(g['main_source']=='UPG' for g in groups),'regular_main_examples':[g for g in groups if g['main_source']=='regular'][:3],'retained_violations':[g for g in groups if not all(g[k] for k in ('price_order_ok','features_ok','flight_identity_ok'))]}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('scenario',choices=['prepare','config',*[x['id'] for x in PLAN]])
 args=p.parse_args()
 if args.scenario=='prepare':
  (ROOT/'all-cases-plan.json').write_text(json.dumps(PLAN,indent=2),encoding='utf-8')
  print('Prepared five relevant round-trip examples, paired across the two configured CIDs. No requests executed.')
 elif args.scenario=='config':
  c=transport.execute('/algo/conf','configuration-all-cases',direct=True)
  b=c['response']['body'];print({'merge':b.get('upgrade_config',{}).get('enable_merge'),'ngs':b.get('ngs_jobs',{}).get('enable')})
 else:
  example=next(x for x in PLAN if x['id']==args.scenario)
  c=transport.execute('/v1/search?'+urllib.parse.urlencode(example['params']),args.scenario,direct=True)
  result=summarize(c)
  (ROOT/(args.scenario+'-summary.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
  print(json.dumps({k:v for k,v in result.items() if k not in ('regular_main_examples','retained_violations')} | {'violating_groups':len(result.get('retained_violations',[]))}))
  import runpy
  runpy.run_module('tasks.SS-6438-upg-ngs-merge.log-hunt',run_name='__main__')
