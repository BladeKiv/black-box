"""User-approved later-date regression, within the cumulative step budget."""
import json
from pathlib import Path
from urllib.parse import urlencode, quote
from bb.transport import request
from bb.classify import classify_outcome
from bb.escalations import Escalations, handle_outcome
from bb.lessons import Store, load_config

P = Path(__file__).parent
HOST = 'https://api.search.stage.travel-dev.com'

def main():
    env = json.loads((Path.home() / 'Downloads' / 'AirAPI Dev.postman_environment.json').read_text(encoding='utf-8-sig'))
    auth = next(v['value'] for v in env['values'] if v['key']=='search_authorization' and v.get('value'))
    examples = [('LAX','LHR','2027-01-15'),('LAX','MAD','2027-02-15'),('LAX','LHR','2027-03-15'),('LAX','MAD','2027-04-15'),('LAX','LHR','2027-05-15')]
    (P/'later-date-examples.json').write_text(json.dumps(examples,indent=2))
    steps = 1
    limit = load_config()['max_steps']
    scope = dict(ticket='SS-6436',environment='STAGE',endpoint='/v1/search',allow_retry=False,allow_poll=False,allow_retest=False,approved_inputs=examples)
    for origin,destination,date in examples:
        if steps >= limit-1:
            break
        query = dict(cid='tst101',gds='V',pcc='8Ki0',fare='PUB',adt=1,cabin='Y')
        query.update({'fl.0.o':origin,'fl.0.d':destination,'fl.0.dt':date})
        url = HOST+'/v1/search?'+urlencode(query)
        r = request(url,headers={'Authorization':str(auth)},credentials_required=True,timeout=120,verify_tls=False,tls_bypass_authorized=True)
        steps += 1
        name = origin+'-'+destination+'-'+date
        (P/(name+'-search.json')).write_text(json.dumps({'request':{'method':'GET','url':url},'response':r},indent=2))
        b = r.get('body') or {}
        offers = b.get('results',[]) if isinstance(b,dict) else []
        matches = [x for x in offers if x.get('gds')=='V' and x.get('pcc')=='8Ki0' and x.get('key')]
        print(json.dumps(dict(route=name,http_status=r['http_status'],offers=len(offers),matching=len(matches))),flush=True)
        if not matches:
            o = classify_outcome(r['http_status'],json.dumps(b),r['transport_error'],dict(inventory_field='results',comparable_count=0,expectation_observed=False))
            handle_outcome(Store(),Escalations(),o,'SS-6436-'+name,['SS-6436','STAGE'],'Search results unavailable at results for V/8Ki0',scope,retries=0,steps=steps)
            continue
        selected = matches[0]
        (P/'selected-offer.json').write_text(json.dumps(selected,indent=2))
        url = HOST+'/v1/result/ANY/'+quote(selected['key'],safe='')+'?'+urlencode(dict(cid='tst101',gds='V',pcc='8Ki0',fare='PUB'))
        r = request(url,headers={'Authorization':str(auth)},credentials_required=True,timeout=120,verify_tls=False,tls_bypass_authorized=True)
        steps += 1
        (P/(name+'-result.json')).write_text(json.dumps({'request':{'method':'GET','url':url},'response':r},indent=2))
        b = r.get('body') or {}
        print(json.dumps(dict(result_http=r['http_status'],fields=list(b) if isinstance(b,dict) else [],steps=steps)),flush=True)
        break
    assert steps <= limit

if __name__=='__main__':
    main()
