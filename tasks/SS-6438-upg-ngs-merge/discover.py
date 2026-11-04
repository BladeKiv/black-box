"""Read-only prerequisite discovery; never logs authentication values."""
import json
from pathlib import Path
from bb.transport import request

ROOT = Path(__file__).resolve().parent
env = json.loads((Path.home() / 'Downloads' / 'AirAPI preprod https.postman_environment.json').read_text(encoding='utf-8-sig'))
values = {v['key']: v.get('value') for v in env['values'] if v.get('enabled', True)}
host = 'https://airapi51.kivops.info'
# Current user correction: remove port from the saved PREPROD HTTPS host.
result = request(host + '/algo/conf', headers={'Authorization': values['search_authorization']}, verify_tls=False, tls_bypass_authorized=True, credentials_required=True, timeout=60)
body = result.get('body')
(ROOT / 'configuration-discovery.json').write_text(json.dumps({'request': {'method': 'GET', 'url': host + '/algo/conf'}, 'response': result}, indent=2), encoding='utf-8')
print(json.dumps({'host': host, 'http_status': result['http_status'], 'transport_error': result.get('transport_error'), 'root_type': type(body).__name__}))
if isinstance(body, dict):
    print('Root keys: ' + ', '.join(body.keys()))
    def walk(obj, path=''):
        if isinstance(obj, dict):
            for key, val in obj.items():
                child = path + '.' + key
                if key in ('ngs_jobs', 'upgrade_config', 'enable_merge'):
                    print(json.dumps({'path': child, 'value': val}))
                else:
                    walk(val, child)
        elif isinstance(obj, list):
            for i, val in enumerate(obj):
                walk(val, path + '[' + str(i) + ']')
    walk(body)
