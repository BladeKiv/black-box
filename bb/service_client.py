"""Chat/backend client. Authentication comes from runtime, never CLI arguments."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler

from .search_job import ROOT, PLAN_KEYS, validate_plan
from .transport import NoRedirect


def call(path, data=None, root=ROOT):
    descriptor = json.loads((Path(root) / '.qa-service/runtime.json').read_text(encoding='utf-8'))
    url = descriptor['url']
    parsed = urlsplit(url)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError('Invalid local service descriptor')
    req = Request(url + path, data=json.dumps(data).encode() if data is not None else None,
                  headers={'Authorization': 'Bearer ' + descriptor['access_key'], 'Content-Type': 'application/json'})
    # Local runtime keys must never be sent through an environment HTTP proxy.
    with build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=15) as response:
        return json.loads(response.read())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('health')
    plan = sub.add_parser('plan')
    plan.add_argument('--scope', type=Path, required=True)
    submit = sub.add_parser('submit')
    submit.add_argument('--plan', type=Path, required=True)
    status = sub.add_parser('status')
    status.add_argument('job_id')
    args = parser.parse_args()
    if args.command == 'plan':
        scope = json.loads(args.scope.read_text(encoding='utf-8'))
        result = {k: scope[k] for k in PLAN_KEYS}
    elif args.command == 'health':
        result = call('/health')
    elif args.command == 'submit':
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        if os.environ.get('AIRAPI_ENVIRONMENT') != plan['environment']:
            raise ValueError('AIRAPI_ENVIRONMENT must match the plan environment')
        scope = validate_plan(ROOT, plan)
        if os.environ.get('AIRAPI_BASE_URL', '').rstrip('/') != scope['base_url'].rstrip('/'):
            raise ValueError('AIRAPI_BASE_URL must match the registered scope host')
        result = call('/jobs', {'plan': plan, 'runtime': {'search_authorization': os.environ.get('AIRAPI_SEARCH_AUTHORIZATION', '')}})
    else:
        import re
        if not re.fullmatch(r'[a-f0-9]{32}', args.job_id):
            raise ValueError('Invalid job ID')
        result = call('/jobs/' + args.job_id)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
