"""Ticket-scoped HTTP reads, explicitly requested by the user on 2026-11-02."""
import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from bb.security import redact
from bb.transport import NoRedirect

ROOT = Path(__file__).resolve().parent
HOST = 'http://airapi51.kivops.info'
COMMON = {'adt':'1', 'debug':'1', 'original_cid':'1', 'cabin':'C', 'fl[0][o]':'SFO', 'fl[0][d]':'FRA', 'fl[0][dt]':'2027-02-25'}
EXAMPLES = [
    {'id':'M01', 'purpose':'SFO-FRA; configured keepBothBagOptions=false; cheapest-main and regular children', 'params':{**COMMON, 'cid':'BCKDCR'}},
    {'id':'M02', 'purpose':'SFO-FRA; configured keepBothBagOptions=true; regular and other UPG children', 'params':{**COMMON, 'cid':'AKKDCR'}},
    {'id':'M03', 'purpose':'LAX-MUC; configured keepBothBagOptions=false; cheapest-main and filtering', 'params':{**COMMON, 'cid':'BCKDCR', 'fl[0][o]':'LAX', 'fl[0][d]':'MUC'}},
    {'id':'M04', 'purpose':'LAX-MUC; configured keepBothBagOptions=true; cheapest-main and filtering', 'params':{**COMMON, 'cid':'AKKDCR', 'fl[0][o]':'LAX', 'fl[0][d]':'MUC'}},
    {'id':'M05', 'purpose':'ORD-FRA; configured keepBothBagOptions=true; equal-feature/feature-losing filtering', 'params':{**COMMON, 'cid':'AKKDCR', 'fl[0][o]':'ORD'}},
]

def execute(path, name, *, direct=False, public=False):
    assert path.split('?')[0] in ('/v1/search', '/algo/conf')
    destination = ROOT / (name + '.json')
    if destination.exists():
        raise SystemExit('Existing capture; no automatic repeat permitted')
    env = json.loads((Path.home() / 'Downloads' / 'AirAPI preprod https.postman_environment.json').read_text(encoding='utf-8-sig'))
    values = {v['key']:v.get('value') for v in env['values'] if v.get('enabled', True)}
    assert values['searchhost'] == 'https://airapi51.kivops.info:8080'
    assert values.get('search_authorization')
    capture = {'request':{'method':'GET', 'url':HOST + path}, 'started_at':datetime.now(timezone.utc).isoformat(), 'response':{'http_status':None, 'body':None, 'transport_error':None}}
    opener = urllib.request.build_opener(NoRedirect(), *([urllib.request.ProxyHandler({})] if direct else []))
    raw = None
    try:
        req = urllib.request.Request(HOST + path, headers={} if public else {'Authorization':values['search_authorization']}, method='GET')
        with opener.open(req, timeout=180) as response:
            capture['response']['http_status'] = response.status
            raw = response.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as exc:
        capture['response']['http_status'] = exc.code
        raw = exc.read().decode('utf-8', errors='replace')
    except (OSError, ValueError) as exc:
        capture['response']['transport_error'] = str(exc)
    if raw is not None:
        try:
            capture['response']['body'] = json.loads(raw)
        except ValueError:
            capture['response']['body'] = {'raw':raw}
    capture['finished_at'] = datetime.now(timezone.utc).isoformat()
    if path == '/algo/conf' and capture['response']['http_status'] == 200:
        body = capture['response']['body']
        capture['response']['body'] = {k:body[k] for k in ('upgrade_config','ngs_jobs') if k in body}
    capture = redact(capture)
    destination.write_text(json.dumps(capture, indent=2), encoding='utf-8')
    body = capture['response']['body']
    print(json.dumps({'capture':destination.name, 'http_status':capture['response']['http_status'], 'transport_error':capture['response']['transport_error'], 'root_keys':list(body) if isinstance(body, dict) else None, 'results_count':len(body['results']) if isinstance(body, dict) and isinstance(body.get('results'), list) else None}))
    return capture

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'config', *[e['id'] for e in EXAMPLES]])
    parser.add_argument('--direct', action='store_true')
    parser.add_argument('--public', action='store_true')
    args = parser.parse_args()
    assert not args.public or args.action == 'config'
    if args.action == 'prepare':
        (ROOT / 'search-examples.json').write_text(json.dumps(EXAMPLES, indent=2), encoding='utf-8')
        print('Prepared five ticket-relevant examples; not executed.')
    elif args.action == 'config':
        capture = execute('/algo/conf', 'configuration-http-public' if args.public else 'configuration-http-direct' if args.direct else 'configuration-http', direct=args.direct, public=args.public)
        body = capture['response']['body']
        def show(obj, path=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    child = path + '.' + key
                    if key in ('ngs_jobs','upgrade_config','enable_merge'):
                        print(json.dumps({'path':child,'value':value}))
                    else:
                        show(value, child)
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    show(value, path + '[' + str(i) + ']')
        show(body)
    else:
        example = next(e for e in EXAMPLES if e['id'] == args.action)
        execute('/v1/search?' + urllib.parse.urlencode(example['params']), args.action, direct=args.direct)
