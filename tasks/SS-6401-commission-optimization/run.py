import os
import sys, json, time, urllib.request, urllib.error, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
CID = sys.argv[3] if len(sys.argv)>3 else 'SAL103'
if CID != 'SAL103':
    ROOT = ROOT/'runs'/CID
    ROOT.mkdir(parents=True,exist_ok=True)
BASES = {'prod': 'https://airsearch.api.travelinsides.com', 'preprod': 'http://airapi51.kivops.info'}

def scenarios():
    rows = []
    routes = [('RDU','MUC','AMS','LHR'), ('JFK','LHR','LHR','JFK'), ('LAX','FRA','FRA','LAX'), ('ORD','AMS','AMS','ORD'), ('MAD','FRA','FRA','MAD'), ('CPH','DEN','DEN','CPH'), ('LHR','DXB','DXB','LHR'), ('CDG','JFK','JFK','CDG'), ('MIA','MAD','MAD','MIA'), ('SFO','MUC','MUC','SFO')]
    for i, route in enumerate(routes):
        for variant in range(3):
            q = {'extra':'false','cabin':['Y','C','Y'][variant],'adt':'1','debug':'true','cid':CID}
            if variant == 2: q.update(chd='1',inf='1')
            for leg in range(2):
                q.update({f'fl.{leg}.o':route[leg*2], f'fl.{leg}.d':route[leg*2+1], f'fl.{leg}.dt':['2026-11-20','2026-11-30'][leg]})
            rows.append({'scenario_id':f'TC-{len(rows)+1:02}', 'query':q})
    return rows

def run(rows, repeats, token, labels=None):
    for row in rows:
        for repeat in (labels if labels is not None else range(1,repeats+1)):
            order=int(str(repeat).split('-')[0])
            for env in (['prod','preprod'] if order%2 else ['preprod','prod']):
                folder=ROOT/'evidence'/row['scenario_id']/str(repeat)/env
                if (folder/'meta.json').exists() and not json.loads((folder/'meta.json').read_text()).get('error'): continue
                folder.mkdir(parents=True,exist_ok=True)
                url=BASES[env]+'/v1/search?'+urllib.parse.urlencode(row['query'])
                (folder/'request.json').write_text(json.dumps({'method':'GET','url':url,'headers':{'Authorization':'[REDACTED]'}},indent=2))
                req=urllib.request.Request(url,headers={'Authorization':'Basic '+token})
                start=time.perf_counter(); body=b''; status=None; headers={}; error=None
                stamp=datetime.now(timezone.utc).isoformat()
                try:
                    with urllib.request.urlopen(req,timeout=120) as response:
                        status=response.status; headers=dict(response.headers); body=response.read()
                except urllib.error.HTTPError as exc:
                    status=exc.code; body=exc.read(); headers=dict(exc.headers)
                except Exception as exc: error=type(exc).__name__+': '+str(exc)
                elapsed=time.perf_counter()-start
                (folder/'response.json').write_bytes(body)
                meta={'environment':env,'scenario_id':row['scenario_id'],'repeat':repeat,'started_utc':stamp,'status':status,'response_seconds':elapsed,'bytes':len(body),'headers':{k:v for k,v in headers.items() if k.lower() not in ['set-cookie','authorization','proxy-authorization']},'error':error}
                (folder/'meta.json').write_text(json.dumps(meta,indent=2))
                print(json.dumps({k:meta[k] for k in ['scenario_id','repeat','environment','status','response_seconds','bytes','error']}),flush=True)

if __name__=='__main__':
    rows=scenarios()
    (ROOT/'scenarios.json').write_text(json.dumps(rows,indent=2))
    token=os.environ['AIRAPI_SEARCH_TOKEN']
    if len(sys.argv)>4 and sys.argv[4]=='retry':
        for row in rows:
            for repeat in range(1,4):
                paths=[ROOT/'evidence'/row['scenario_id']/str(repeat)/env/'meta.json' for env in ['prod','preprod']]
                if all(p.exists() for p in paths) and any(json.loads(p.read_text()).get('status')!=200 for p in paths):
                    run([row],1,token,[str(repeat)+'-retry1'])
    else: run(rows[:int(sys.argv[1])],int(sys.argv[2]),token)
