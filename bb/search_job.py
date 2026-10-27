"""Controlled Search-only execution. Ticket scope, never an AI plan, grants inputs."""
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlencode, urlsplit

from .classify import classify_outcome
from .security import ensure_safe
from .transport import request

ROOT = Path(__file__).resolve().parents[1]
PLAN_KEYS = {'ticket', 'workflow', 'environment', 'scope_sha256', 'examples'}
ARTIFACTS = ('results.json', 'qa-report.html', 'qa-report.md', 'report-data.json',
             'collection.json', 'expected-outcomes.csv', 'paired-evidence.json', 'plan.json', 'run-notes.md')


class JobCancelled(Exception):
    pass


def ticket_folder(root, ticket):
    if not isinstance(ticket, str) or not re.fullmatch(r'SS-[0-9]+', ticket):
        raise ValueError('Invalid ticket key')
    folders = [p for p in (Path(root) / 'tasks').glob(ticket + '*')
               if p.is_dir() and (p.name == ticket or p.name.startswith(ticket + '-'))]
    if len(folders) != 1 or not folders[0].resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Exactly one project-local ticket folder is required')
    return folders[0]


def validate_plan(root, plan):
    if not isinstance(plan, dict) or set(plan) != PLAN_KEYS:
        raise ValueError('Plan must contain only ticket, workflow, environment, scope_sha256 and examples')
    folder = ticket_folder(root, plan['ticket'])
    scope_file = folder / 'service-scope.json'
    if not scope_file.is_file() or not scope_file.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Ticket has no service-supported scope; use the existing QA workflow')
    scope = json.loads(scope_file.read_text(encoding='utf-8'))
    ensure_safe(scope)
    if scope.get('workflow') != 'currency_points_diff':
        raise ValueError('Unsupported endpoint flow')
    if any(plan.get(k) != scope.get(k) for k in PLAN_KEYS):
        raise ValueError('Plan differs from approved ticket service scope')
    # Normalize checkout line endings so scope binding survives Windows Git clones.
    digest = hashlib.sha256((folder / 'ticket-scope.md').read_text(encoding='utf-8').encode('utf-8')).hexdigest()
    if scope['scope_sha256'] != digest:
        raise ValueError('Ticket scope changed; review service scope before executing')
    host = urlsplit(scope['base_url'])
    if host.scheme != 'https' or not host.hostname or host.username or host.password or host.path not in ('', '/') or host.query or host.fragment:
        raise ValueError('Scope requires a credential-free HTTPS origin')
    if scope.get('currencies') != ['USD', 'GBP', 'INR'] or not numeric(scope.get('tolerance')) or scope['tolerance'] < 0:
        raise ValueError('Invalid currency comparison scope')
    examples = scope['examples']
    if not isinstance(examples, list) or not 1 <= len(examples) <= 10:
        raise ValueError('One to ten approved examples required')
    if len(examples) < 5 and not scope.get('preparation_exception'):
        raise ValueError('Fewer than five examples requires an explicit scope exception')
    ids = []
    for example in examples:
        if set(example) != {'id', 'query'} or not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', example['id']):
            raise ValueError('Invalid example identifier')
        query = example['query']
        if not isinstance(query, dict) or not query or any(not isinstance(k, str) or not isinstance(v, str) for k, v in query.items()):
            raise ValueError('Search inputs must be string query parameters')
        if any(k.lower() in ('currency', 'async') or re.search(r'(?i)auth|password|token|secret|cookie|login', k) for k in query):
            raise ValueError('Credentials, currency and async inputs cannot be supplied in example queries')
        ids.append(example['id'])
    if len(set(ids)) != len(ids) or len(examples) * 3 != scope.get('max_requests'):
        raise ValueError('Duplicate examples or invalid request budget')
    return scope


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def index_points(results):
    if not isinstance(results, list):
        return None
    indexed = {}
    for result in results:
        if not isinstance(result, dict) or not isinstance(result.get('key'), str) or not result['key'] or result['key'] in indexed:
            return None
        meta = result.get('meta')
        rank = meta.get('rank_v2') if isinstance(meta, dict) else None
        score = rank.get('points_diff') if isinstance(rank, dict) else None
        indexed[result['key']] = score
    return indexed


def compare_points(baseline, target, tolerance):
    left, right = index_points(baseline), index_points(target)
    if left is None or right is None:
        return {'status': 'WARN', 'reason_code': 'UNEVALUATED', 'matched': 0,
                'detail': 'Missing/invalid results or duplicate opaque keys; comparison is ambiguous.'}
    keys = left.keys() & right.keys()
    if not keys:
        return {'status': 'WARN', 'reason_code': 'NO_DATA', 'matched': 0,
                'detail': 'No identical opaque keys available across currencies.'}
    deltas = [abs(left[k] - right[k]) for k in keys if numeric(left[k]) and numeric(right[k])]
    invalid = len(keys) - len(deltas)
    failures = sum(delta > tolerance for delta in deltas)
    status = 'FAIL' if failures else 'WARN' if invalid else 'PASS'
    return {'status': status, 'reason_code': 'CONTRACT_MISMATCH' if failures else 'UNEVALUATED' if invalid else 'OK',
            'matched': len(keys), 'evaluated': len(deltas), 'invalid_scores': invalid,
            'failures': failures, 'max_delta': max(deltas, default=None),
            'unmatched_usd': len(left) - len(keys), 'unmatched_target': len(right) - len(keys),
            'detail': 'Only identical opaque keys and numeric meta.rank_v2.points_diff are compared.'}


def evidence_response(response, credential):
    """Keep only the HTTP result and ticket comparator inputs, never arbitrary payloads."""
    body = response.get('body')
    results = body.get('results') if isinstance(body, dict) else None
    projected = [] if isinstance(results, list) else None
    for item in results if isinstance(results, list) else []:
        if not isinstance(item, dict):
            projected.append(None)
            continue
        key = item.get('key')
        # A credential reflected into an opaque key cannot be safely persisted or compared.
        private_parts = [credential, credential.split()[-1]] if credential else []
        if isinstance(key, str) and any(part and part in key for part in private_parts):
            key = None
        meta = item.get('meta')
        rank = meta.get('rank_v2') if isinstance(meta, dict) else None
        score = rank.get('points_diff') if isinstance(rank, dict) else None
        projected.append({'key': key, 'meta': {'rank_v2': {'points_diff': score if numeric(score) else None}}})
    return {'http_status': response.get('http_status'), 'reason_code': response.get('reason_code', 'UNEVALUATED'),
            'transport_error': 'Transport failed; details withheld' if response.get('transport_error') else None,
            'body': {'results': projected}}


def execute_job(root, plan, credential, job_id, *, transport=request, cancelled=lambda: False):
    scope = validate_plan(root, plan)
    if not re.fullmatch(r'[a-f0-9]{32}', job_id):
        raise ValueError('Invalid job ID')
    folder = ticket_folder(root, scope['ticket']) / 'runs' / ('service-' + job_id)
    if not folder.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Output resolves outside project')
    folder.mkdir(parents=True, exist_ok=False)
    dump = lambda name, data: (folder / name).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    dump('plan.json', plan)
    captures, cases = [], []
    from .lessons import Store
    from .escalations import Escalations, handle_outcome
    lessons = Store(Path(root) / 'knowledge/lessons/lessons.jsonl')
    escalations = Escalations(Path(root) / 'knowledge/lessons/escalations.jsonl', lessons)
    matches = lessons.search([scope['ticket'], scope['environment']], 'currency points_diff comparison prerequisites')
    operational_scope = {'ticket': scope['ticket'], 'environment': scope['environment'], 'endpoint': '/v1/search',
                         'allow_retry': False, 'allow_poll': False, 'allow_retest': False, 'approved_inputs': []}
    (folder / 'run-notes.md').write_text('Lesson search matches (not applied): ' + (', '.join(m['id'] for m in matches) or 'none') +
        '\nNo operational actions/retries are executed by this workflow. Missing prerequisites remain WARN.\n', encoding='utf-8')
    for example in scope['examples']:
        pair = {}
        for currency in scope['currencies']:
            if cancelled():
                raise JobCancelled()
            url = scope['base_url'].rstrip('/') + '/v1/search?' + urlencode({**example['query'], 'currency': currency})
            headers = {'Accept': 'application/json'}
            headers['Authorization'] = credential
            response = transport(url, headers=headers,
                                 credentials_required=True, verify_tls=False, tls_bypass_authorized=True, timeout=30) if credential else {
                                     'http_status': None, 'reason_code': 'AUTH_MISSING', 'body': None}
            evidence = {'request': {'method': 'GET', 'url': url, 'executed': bool(credential)}, 'response': evidence_response(response, credential)}
            pair[currency] = evidence
            captures.append(evidence)
            dump('paired-evidence.json', captures)
        for currency in scope['currencies'][1:]:
            baseline, target = pair['USD']['response'], pair[currency]['response']
            blocker = next((r for r in (baseline, target) if r['http_status'] is None or not 200 <= r['http_status'] < 300 or
                            r['reason_code'] not in ('OK', 'UNEVALUATED', 'NO_DATA')), None)
            comparison = {'status': 'WARN', 'reason_code': blocker['reason_code'], 'detail': 'Search prerequisites or transport prevented evaluation.'} if blocker else compare_points(baseline['body']['results'], target['body']['results'], scope['tolerance'])
            # Evaluate ticket expectation explicitly; operational classification never supplies it.
            classified = classify_outcome(200, '{}', context={'inventory_field': None,
                'expectation_observed': comparison['status'] == 'PASS'}) if comparison['status'] != 'WARN' else {'status': 'WARN', 'reason_code': comparison['reason_code']}
            cases.append({'id': example['id'] + '-' + currency, 'title': example['id'] + ' USD/' + currency,
                          'status': classified['status'], 'reason_code': comparison['reason_code'],
                          'test_data': {'query': example['query'], 'currencies': ['USD', currency]},
                          'expected': 'Exact opaque keys: abs(target.meta.rank_v2.points_diff - USD.meta.rank_v2.points_diff) <= ' + str(scope['tolerance']),
                          'actual': json.dumps(comparison, allow_nan=False), 'evidence': [pair['USD'], pair[currency]]})
            handle_outcome(lessons, escalations, {'status': comparison['status'], 'reason_code': comparison['reason_code'], 'retryable': False},
                           scope['ticket'] + '-service-' + job_id + '-' + cases[-1]['id'],
                           [scope['ticket'], scope['environment']], 'currency points_diff ' + comparison['reason_code'],
                           operational_scope, retries=0, steps=2)
    report = {'ticket': scope['ticket'], 'environment': scope['environment'], 'base_url': scope['base_url'],
              'intended_behavior': scope['intended_behavior'], 'job_id': job_id, 'cases': cases}
    dump('paired-evidence.json', captures)
    dump('results.json', report)
    write_artifacts(folder, scope, cases, captures)
    return report, folder


def write_artifacts(folder, scope, cases, captures):
    from templates.render_dispatch import render
    # Postman keeps exact-key comparator parity with the controlled Python runner.
    script = '''let rows = null;
try { if (pm.response.code >= 200 && pm.response.code < 300) rows = pm.response.json().results ?? null; } catch {}
const c = pm.iterationData.get('currency');
if (c === 'USD') pm.collectionVariables.set('baseline', JSON.stringify(rows));
else {
 const baseline = JSON.parse(pm.collectionVariables.get('baseline') || 'null');
 const index = xs => { if (!Array.isArray(xs)) return null; const m = new Map(); for (const r of xs) { if (!r || typeof r.key !== 'string' || !r.key || m.has(r.key)) return null; m.set(r.key, r.meta?.rank_v2?.points_diff); } return m; };
 const a = index(baseline), b = index(rows);
 const keys = a && b ? [...a.keys()].filter(k => b.has(k)) : [];
 const values = keys.map(k => [a.get(k), b.get(k)]);
 const valid = values.filter(pair => pair.every(v => typeof v === 'number' && Number.isFinite(v)));
 const tolerance = Number(pm.iterationData.get('tolerance'));
 if (valid.some(([x,y]) => Math.abs(x-y) > tolerance)) pm.test('points_diff exceeds approved tolerance', () => { throw new Error('CONTRACT_MISMATCH'); });
 else if (!keys.length || valid.length !== keys.length) pm.test.skip('WARN: unavailable or ambiguous comparator inputs', () => {});
 else pm.test('Exact-key points_diff within approved tolerance', () => pm.expect(true).to.eql(true));
}'''
    setup = "if (pm.iterationData.get('currency') === 'USD') pm.collectionVariables.unset('baseline');\nif (!pm.variables.get('search_authorization')) throw new Error('Set Search authorization locally');"
    collection = {'info': {'name': scope['ticket'] + ' controlled currency comparison',
                           'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
                  'item': [{'name': 'Search', 'request': {'method': 'GET', 'url': '{{search_url}}',
                           'header': [{'key': 'Authorization', 'value': '{{search_authorization}}'}]},
                           'event': [{'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': setup.splitlines()}},
                                     {'listen': 'test', 'script': {'type': 'text/javascript', 'exec': script.splitlines()}}]}]}
    (folder / 'collection.json').write_text(json.dumps(collection, indent=2) + '\n', encoding='utf-8')
    with (folder / 'expected-outcomes.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['scenario_id', 'expected_result', 'provider_filter', 'search_url', 'currency', 'tolerance'])
        writer.writeheader()
        for example, group in zip(scope['examples'], [captures[i:i+3] for i in range(0, len(captures), 3)]):
            for currency, capture in zip(scope['currencies'], group):
                writer.writerow({'scenario_id': example['id'] + '-' + currency, 'expected_result': scope['intended_behavior'],
                                 'provider_filter': example['query'].get('gds', ''), 'search_url': capture['request']['url'],
                                 'currency': currency, 'tolerance': scope['tolerance']})
    data = {'title': scope['ticket'] + ' ' + scope['title'], 'date': datetime.now(timezone.utc).isoformat(),
            'scope': scope['environment'] + ' | GET /v1/search | currency_points_diff | one request per input; no retries',
            'summary': str(len(cases)) + ' currency comparisons evaluated by the controlled service. See each case for its observed result.',
            'intended': scope['intended_behavior'], 'limits': 'Only matched opaque keys and points_diff are assessed. Unmatched inventory is excluded. ' + scope.get('preparation_exception', ''),
            'collection': 'collection.json', 'rows': [{'id': c['id'], 'data': json.dumps(c['test_data']), 'expected': c['expected'], 'actual': c['actual'], 'status': c['status']} for c in cases],
            'evidence': [{'id': c['id'] + '-' + str(i+1), **e} for c in cases if c['status'] != 'PASS' for i, e in enumerate(c['evidence'])]}
    (folder / 'report-data.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    render(folder)
