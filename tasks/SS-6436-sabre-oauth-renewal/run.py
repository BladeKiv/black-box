"""One authorized STAGE Search and matching Result; no retries."""
import json
from pathlib import Path
from urllib.parse import urlencode, quote
from bb.transport import request

ROOT = Path(__file__).parent
HOST = 'https://api.search.stage.travel-dev.com'

def main():
    env = json.loads((Path.home() / 'Downloads' / 'AirAPI Dev.postman_environment.json').read_text(encoding='utf-8-sig'))
    auth = next(v['value'] for v in env['values'] if v['key'] == 'search_authorization' and v.get('value'))
    query = {'cid':'tst101','gds':'V','pcc':'8Ki0','fare':'PUB','adt':1,'cabin':'Y','fl.0.o':'SFO','fl.0.d':'FRA','fl.0.dt':'2026-11-20'}
    url = HOST + '/v1/search?' + urlencode(query)
    for name in ('search', 'result'):
        response = request(url, headers={'Authorization':str(auth)}, credentials_required=True, timeout=120, verify_tls=False, tls_bypass_authorized=True)
        evidence = {'request':{'method':'GET','url':url},'response':response}
        (ROOT / (name+'-evidence.json')).write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        body = response.get('body')
        print(json.dumps({'step':name,'http_status':response['http_status'],'transport_error':response['transport_error'],'body_type':type(body).__name__}))
        if name == 'search':
            offers = body.get('results',[]) if isinstance(body,dict) else []
            matches = [o for o in offers if o.get('gds')=='V' and o.get('pcc')=='8Ki0' and o.get('key')]
            print(json.dumps({'offers':len(offers),'matching':len(matches)}))
            if not matches:
                break
            selected = matches[0]
            (ROOT/'selected-offer.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
            url = HOST+'/v1/result/ANY/'+quote(selected['key'],safe='')+'?'+urlencode({'cid':'tst101','gds':'V','pcc':'8Ki0','fare':'PUB'})
        elif isinstance(body,dict):
            print(json.dumps({'fields':list(body),'gds':body.get('gds'),'pcc':body.get('pcc'),'same_key':body.get('key')==selected['key'],'trips_count':len(body.get('trips') or []),'price_fields':list((body.get('prices') or {}).keys())}))

if __name__ == '__main__':
    main()
