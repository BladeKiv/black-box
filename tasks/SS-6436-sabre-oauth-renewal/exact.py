"""Execute the user's exact working Search and one matching Result."""
import json
from pathlib import Path
from urllib.parse import quote, urlencode
from bb.transport import request

P = Path(__file__).parent
HOST = 'https://api.search.stage.travel-dev.com'
URL = HOST+'/v1/search?extra=false&cabin=T&adt=1&debug=true&fare=PUB&cid=TST101&gds=V&pcc=8KI0&fl.0.o=LAX&fl.0.d=MAD&fl.0.dt=2026-11-14'

def main():
    values = json.loads((Path.home() / 'Downloads' / 'AirAPI Dev.postman_environment.json').read_text(encoding='utf-8-sig'))['values']
    auth = next(x['value'] for x in values if x['key']=='search_authorization' and x.get('value'))
    url = URL
    for step in ('search','result'):
        r = request(url,headers={'Authorization':str(auth)},credentials_required=True,timeout=120,verify_tls=False,tls_bypass_authorized=True)
        (P/('exact-'+step+'.json')).write_text(json.dumps({'request':{'method':'GET','url':url},'response':r},indent=2))
        b = r.get('body') or {}
        if step=='search':
            offers = b.get('results',[]) if isinstance(b,dict) else []
            matches = [x for x in offers if x.get('gds')=='V' and x.get('pcc')=='8KI0' and x.get('key')]
            print(json.dumps(dict(step=step,http=r['http_status'],count=len(offers),matching=len(matches))),flush=True)
            if not matches:
                break
            selected = matches[0]
            (P/'exact-selected.json').write_text(json.dumps(selected,indent=2))
            url = HOST+'/v1/result/ANY/'+quote(selected['key'],safe='')+'?'+urlencode(dict(cid='TST101',gds='V',pcc='8KI0',fare='PUB',debug='true'))
        else:
            print(json.dumps(dict(step=step,http=r['http_status'],fields=list(b) if isinstance(b,dict) else [],same_key=b.get('key')==selected['key'],gds=b.get('gds'),pcc=b.get('pcc'),trips=len(b.get('trips') or []),totalPrice=(b.get('prices') or {}).get('totalPrice'))),flush=True)

if __name__=='__main__':
    main()
