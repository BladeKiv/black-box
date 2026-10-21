import os
import concurrent.futures
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN = ROOT / 'runs' / '2026-10-21-authorized'

CASES = {
    'OW': [('JFK', 'LHR', '2026-11-20')],
    'RT': [('JFK', 'LHR', '2026-11-20'), ('LHR', 'JFK', '2026-11-30')],
    'MC': [('JFK', 'LHR', '2026-11-20'), ('LHR', 'CDG', '2026-11-25'), ('CDG', 'JFK', '2026-11-30')],
}


def query(legs):
    q = {'cid': 'SAL103', 'adt': '1', 'cabin': 'Y', 'debug': 'true', 'rules': 'true'}
    for i, (origin, destination, date) in enumerate(legs):
        q.update({f'fl.{i}.o': origin, f'fl.{i}.d': destination, f'fl.{i}.dt': date})
    assert not {'pcc', 'fare', 'gds'} & q.keys()
    return q


def fetch(env, name, repeat):
    folder = RUN / name / str(repeat) / env
    folder.mkdir(parents=True, exist_ok=True)
    if (folder / 'response.json').exists():
        return json.loads((folder / 'response.json').read_text())
    vals = {'searchhost': os.environ[f'AIRAPI_{env.upper()}_SEARCH_URL'], 'search_authorization': os.environ[f'AIRAPI_{env.upper()}_AUTHORIZATION']}
    url = vals['searchhost'].rstrip('/') + '/v1/search?' + urllib.parse.urlencode(query(CASES[name]))
    assert env != 'preprod' or urllib.parse.urlparse(url).hostname == 'airapi51.kivops.info'
    (folder / 'request.json').write_text(json.dumps({'method': 'GET', 'url': url, 'headers': {'Authorization': '[REDACTED]'}}, indent=2))
    req = urllib.request.Request(url, headers={'Authorization': vals['search_authorization'], 'Accept': 'application/json'})
    started = time.perf_counter()
    output = {'started_utc': datetime.now(timezone.utc).isoformat(), 'tls_verification': False}
    try:
        with urllib.request.urlopen(req, timeout=120, context=ssl._create_unverified_context()) as res:
            data = json.loads(res.read())
            pre = data.get('preData') or {}
            output.update(http_status=res.status, traceID=res.headers.get('Traceid'), preData={k: pre[k] for k in ('cid', 'CCNotAccepted') if k in pre}, timing=[t for t in data.get('timing', []) if t.get('process') == 'PreSearchActionsCommon'], results_count=len(data.get('results') or []))
    except urllib.error.HTTPError as exc:
        output.update(http_status=exc.code, body=exc.read().decode('utf-8', errors='replace'))
    except Exception as exc:
        output.update(http_status=None, transport_error=type(exc).__name__ + ': ' + str(exc))
    output['response_seconds'] = time.perf_counter() - started
    (folder / 'response.json').write_text(json.dumps(output, indent=2))
    print(json.dumps({'case': name, 'repeat': repeat, 'env': env, 'http_status': output['http_status'], 'timing': output.get('timing'), 'error': output.get('transport_error')}), flush=True)
    return output


if __name__ == '__main__':
    assert query(CASES['MC'])['fl.2.d'] == 'JFK'
    for name in CASES:
        for repeat in range(1, 4):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(lambda env: fetch(env, name, repeat), ('prod', 'preprod')))
