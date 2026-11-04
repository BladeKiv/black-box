"""Read original requests from stdin; retain only baggage evidence, never passengers."""
import base64
import hashlib
import json
from pathlib import Path
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bb.transport import NoRedirect

URL = 'https://airapi51.kivops.info:8090/atlas/v1/book/info'
env = json.loads((Path.home() / 'Downloads' / 'AirAPI preprod https.postman_environment.json').read_text(encoding='utf-8-sig'))
values = {x['key']: x.get('value') for x in env['values']}
collection = json.loads((Path.home() / 'Downloads' / 'Atlas APIs.postman_collection.json').read_text(encoding='utf-8-sig'))
folder = next(x for x in collection['item'] if x['name'] == 'SERVICE APIs PROD ENV')
item = next(x for x in folder['item'] if x['name'] == '/atlas/v1/book/info')
headers = {x['key']: x['value'] for x in item['request'].get('header', []) if not x.get('disabled') and x['key'].lower() != 'authorization'}
headers['Authorization'] = 'Basic ' + base64.b64encode((values['booklogin'] + ':' + values['bookpass']).encode()).decode()
headers['Content-Type'] = 'application/json'
assert all('{{' not in v for v in headers.values()), 'Unresolved header variable'
# Standing direct user TLS-bypass authorization, confirmed in AGENTS.md.
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))
if '--aircairo' in sys.argv:
    fixture = json.loads((ROOT / 'tasks/SS-6390-atlas-baggage/runs/2026-10-13-preprod-book-info/book-info-8090-body.json').read_text(encoding='utf-8-sig'))
    comparable = json.loads(json.dumps(fixture))
    del comparable['additionalInfo']['fid']
    del comparable['additionalInfo']['sessionID']
    assert hashlib.sha256(json.dumps(comparable, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest() == '92bae388bbb6af77bb8245261d0425cffede4f7c85999fc9bc0324b4e5d82deb'
    fixture['additionalInfo']['fid'] = 'MGjjMdTOo5bnlttlJAXpqIBojgB9xdPxgixcOCLuJhBshh3lxaM5ehMj8drSA-iw943qIy9ejyK1Hl5n3AMt0b1Jt6TNGiwV'
    fixture['additionalInfo']['sessionID'] = 'bda882fd-4982-4c7b-beba-600fc2dd4bff'
    cases = [{'request': fixture}]
else:
    cases = json.load(sys.stdin)
evidence_path = Path(__file__).with_name('payload-evidence.json')
out = json.loads(evidence_path.read_text(encoding='utf-8')) if '--append' in sys.argv else []
for case in cases:
    body = case['request']
    pnr = body['additionalInfo']['pnrCode']
    assert pnr in {'US74GX', 'ER0XZ8', 'ZXCMYU', 'ML0MPQ'}
    started = datetime.now(timezone.utc).isoformat()
    response, status, error = {}, None, None
    try:
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=headers, method='POST')
        with opener.open(req, timeout=35) as r:
            status = r.status
            response = json.load(r)
    except urllib.error.HTTPError as e:
        status = e.code
        try: response = json.loads(e.read())
        except ValueError: response = {'non_json': True}
    except (OSError, ValueError) as e:
        error = type(e).__name__ + ': ' + str(e)
    segments = response.get('data', {}).get('response', {}).get('pnrInfo', {}).get('segments', [])
    fields = ['tripId', 'segmentNumber', 'departureAirportCode', 'arrivalAirportCode', 'marketingAirlineCode', 'baggageAllowance', 'baggage', 'carryOnAllowance', 'carryOn']
    evidence = {'pnr': pnr, 'started_utc': started, 'request': {'method': 'POST', 'url': URL, 'body': {'additionalInfo': {k: v for k, v in body['additionalInfo'].items() if k in ['pnrCode', 'orderNo', 'segments']}, 'data': body.get('data'), 'gds': {k: v for k, v in body.get('gds', {}).items() if k in ['backoffice_id', 'gds_pcc']}}, 'note': 'Original logged request replayed unchanged; unrelated and personal fields excluded from evidence.'}, 'response': {'http_status': status, 'status': response.get('status'), 'code': response.get('code'), 'name': response.get('name'), 'traceID': response.get('traceID', response.get('Traceid')), 'segments': [{k: s[k] for k in fields if k in s} for s in segments], 'transport_error': error}}
    out.append(evidence)
    print(json.dumps({'pnr': pnr, **evidence['response']}), flush=True)
evidence_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
