import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from bb.security import redact

folder = Path(__file__).parent / 'evidence'
values = {v['key']: v.get('value', '') for v in json.loads((Path.home() / 'Downloads/AirAPI preprod https.postman_environment.json').read_text(encoding='utf-8-sig'))['values'] if v.get('enabled', True)}
cabins = sys.argv[1:]
assert cabins and all(c in ('Y', 'Q', 'C', 'J', 'F', 'P', 'omitted') for c in cabins)
auth = values['search_authorization']
if not auth.startswith(('Basic ', 'Bearer ')):
    auth = 'Basic ' + auth
for cabin in cabins:
    query = {'cid': 'GTT101', 'agency': 'SBCSFO', 'adt': '1', 'fl.0.o': 'JFK', 'fl.0.d': 'LHR', 'fl.0.dt': '2026-11-20', 'debug': 'true', 'rules': 'true', 'files': 'true'}
    if cabin != 'omitted':
        query['cabin'] = cabin
    url = 'http://airapi51.kivops.info/v1/search?' + urllib.parse.urlencode(query)
    assert urllib.parse.urlsplit(url).netloc == 'airapi51.kivops.info'
    folder.mkdir(exist_ok=True)
    (folder / f'{cabin}-request.json').write_text(json.dumps({'method': 'GET', 'url': url}, indent=2))
    start = time.monotonic()
    headers = {'Accept': 'application/json'}
    headers['Authorization'] = auth
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
            output = {'http_status': response.status, 'traceID': response.headers.get('traceid'), 'body': redact(json.loads(response.read()))}
    except urllib.error.HTTPError as error:
        output = {'http_status': error.code, 'body': redact(error.read().decode(errors='replace'))}
    except Exception as error:
        output = {'http_status': None, 'transport_error': str(error)}
    output['seconds'] = round(time.monotonic() - start, 2)
    # Keep only ticket evidence; provider payloads and unrelated configuration stay out of artifacts.
    body = output.get('body', {})
    if isinstance(body, dict):
        output['body'] = {
            'results': [{'cabin': r.get('cabin'), 'fareType': r.get('fareType'), 'prices': {k: r.get('prices', {})[k] for k in ('markupId', 'markupUid', 'oMarkup') if k in r.get('prices', {})}, 'meta': {'agency': r.get('meta', {}).get('agency')}} for r in body.get('results', [])],
            'preData': {k: body.get('preData', {})[k] for k in ('cid', 'CorporateRulesData') if k in body.get('preData', {})},
            'messages': [m for m in body.get('messages', []) if m.get('type') == 'TRACEID'],
            'starUTCTime': body.get('starUTCTime'), 'endUTCTime': body.get('endUTCTime'),
            'req_resp': [{'name': r.get('name')} for r in body.get('req_resp', [])],
        }
    (folder / f'{cabin}-response.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'cabin': cabin, 'http_status': output['http_status'], 'seconds': output['seconds'], 'error': output.get('transport_error'), 'root_keys': list(body) if isinstance(body, dict) else [], 'results_count': len(body.get('results', [])) if isinstance(body, dict) else None, 'traceID': output.get('traceID')}), flush=True)
    if output['http_status'] is None:
        break
