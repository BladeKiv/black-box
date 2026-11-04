"""Controlled Search-only execution. Ticket scope, never an AI plan, grants inputs."""
import os
from time import monotonic
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
ARTIFACTS = ('cases.json', 'results.jsonl')


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


def truncate(text, limit=2048):
    data = text.encode('utf-8')
    if len(data) <= limit:
        return text
    kept = max(0, limit - 48)
    prefix = data[:kept].decode('utf-8', errors='ignore')
    return prefix + '...[truncated ' + str(len(data) - len(prefix.encode('utf-8'))) + ' bytes]'


def excerpt(value):
    return truncate(json.dumps(value, ensure_ascii=False, allow_nan=False))


def execute_job(root, plan, credential, job_id, *, transport=request, cancelled=lambda: False, base_url=None):
    scope = validate_plan(root, plan)
    # The selected runtime URL must agree with the immutable ticket scope.
    selected_url = base_url if base_url is not None else os.environ.get('AIRAPI_BASE_URL', '')
    if selected_url.rstrip('/') != scope['base_url'].rstrip('/'):
        raise ValueError('AIRAPI_BASE_URL must match the selected service environment')
    if not re.fullmatch(r'[a-f0-9]{32}', job_id):
        raise ValueError('Invalid job ID')
    folder = ticket_folder(root, scope['ticket']) / 'runs' / ('service-' + job_id)
    if not folder.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Output resolves outside project')
    folder.mkdir(parents=True, exist_ok=False)
    expected = 'Exact opaque keys: abs(target.meta.rank_v2.points_diff - USD.meta.rank_v2.points_diff) <= ' + str(scope['tolerance'])
    planned = []
    for example in scope['examples']:
        for currency in scope['currencies'][1:]:
            planned.append({'case_id': 'TC-' + str(len(planned) + 1),
                'title': example['id'] + ' USD/' + currency,
                'steps': ['GET /v1/search in USD (shared baseline) and ' + currency,
                          'Compare numeric meta.rank_v2.points_diff for unchanged identical opaque keys'],
                'test_data': {'query': example['query'], 'currencies': ['USD', currency]}, 'expected': expected})
    (folder / 'cases.tmp').write_text(json.dumps({'v': 1, 'task': scope['ticket'],
        'environment': scope['environment'], 'intended_behavior': scope['intended_behavior'],
        'cases': planned}, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    (folder / 'cases.tmp').replace(folder / 'cases.json')
    (folder / 'results.jsonl').touch(exist_ok=False)
    from .lessons import Store
    from .escalations import Escalations, handle_outcome
    lessons = Store(Path(root) / 'knowledge/lessons/lessons.jsonl')
    escalations = Escalations(Path(root) / 'knowledge/lessons/escalations.jsonl', lessons)
    lessons.search([scope['ticket'], scope['environment']], 'currency points_diff comparison prerequisites')
    operational_scope = {'ticket': scope['ticket'], 'environment': scope['environment'], 'endpoint': '/v1/search',
                         'allow_retry': False, 'allow_poll': False, 'allow_retest': False, 'approved_inputs': []}
    cases = []
    stopped = False
    def capture(example, currency):
        url = selected_url.rstrip('/') + '/v1/search?' + urlencode({**example['query'], 'currency': currency})
        if credential:
            try:
                response = transport(url, headers={'Accept': 'application/json', 'Authorization': str(credential)},
                    credentials_required=True, verify_tls=False, tls_bypass_authorized=True, timeout=30)
            except Exception:
                response = {'http_status': None, 'reason_code': 'TRANSPORT_ERROR', 'body': None}
        else:
            response = {'http_status': None, 'reason_code': 'AUTH_MISSING', 'body': None}
        return {'request': {'method': 'GET', 'url': url}, 'response': evidence_response(response, credential)}

    for example in scope['examples']:
        baseline = None
        for currency in scope['currencies'][1:]:
            started = monotonic()
            stopped = stopped or cancelled()
            target = None
            if not stopped:
                if baseline is None:
                    baseline = capture(example, 'USD')
                stopped = cancelled()
                if not stopped:
                    target = capture(example, currency)
            if stopped:
                comparison = {'status': 'WARN', 'reason_code': 'CANCELLED', 'detail': 'Run cancelled before comparison completed.'}
            else:
                left, right = baseline['response'], target['response']
                blocker = next((r for r in (left, right) if r['http_status'] is None or
                    not 200 <= r['http_status'] < 300 or r['reason_code'] not in ('OK', 'UNEVALUATED', 'NO_DATA')), None)
                comparison = {'status': 'WARN', 'reason_code': blocker['reason_code'],
                    'detail': 'Search access or transport prevented evaluation.'} if blocker else compare_points(left['body']['results'], right['body']['results'], scope['tolerance'])
            status = {'PASS': 'passed', 'FAIL': 'failed', 'WARN': 'need_action'}[comparison['status']]
            case = {'case_id': planned[len(cases)]['case_id'], 'status': status,
                    'duration_ms': int((monotonic() - started) * 1000), 'actual': comparison['detail']}
            if status == 'passed':
                case['actual'] = json.dumps({k: v for k, v in comparison.items() if k not in ('status', 'detail')}, allow_nan=False)
            elif status == 'failed':
                case['actual'] = json.dumps({k: v for k, v in comparison.items() if k != 'status'}, allow_nan=False)
                left_points = index_points(baseline['response']['body']['results'])
                right_points = index_points(target['response']['body']['results'])
                case['failure'] = {'assertion': expected,
                    'request': {'method': 'GET', 'url': truncate(target['request']['url']),
                                'body_excerpt': excerpt({'USD': baseline['request'], currency: target['request']})},
                    'response': {'status': target['response']['http_status'],
                                 'body_excerpt': excerpt({'comparisons': [{'USD': left_points[k], currency: right_points[k], 'key': k}
                                     for k in left_points.keys() & right_points.keys()
                                     if numeric(left_points[k]) and numeric(right_points[k]) and abs(left_points[k] - right_points[k]) > scope['tolerance']]})}}
                limit = 2048
                while len(json.dumps(case['failure'], ensure_ascii=False).encode('utf-8')) > 8192:
                    limit //= 2
                    for side in ('request', 'response'):
                        case['failure'][side]['body_excerpt'] = truncate(case['failure'][side]['body_excerpt'], limit)
                    case['failure']['request']['url'] = truncate(case['failure']['request']['url'], limit)
            else:
                reason = comparison['reason_code']
                need = ('Provide Search authentication through the selected profile' if reason == 'AUTH_MISSING' else
                        'Authorize a new run after cancellation' if reason == 'CANCELLED' else
                        'Provide comparable Search inventory with unique identical keys and numeric points_diff' if reason in ('NO_DATA', 'UNEVALUATED') else
                        'Restore Search access through the selected profile')
                case['action_needed'] = need + ' on ' + scope['environment'] + ' to evaluate ' + case['case_id'] + '.'
            # Close each append before executing the next case so the dashboard can ingest it.
            ensure_safe(case)
            with (folder / 'results.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(case, ensure_ascii=False, allow_nan=False) + '\n')
            cases.append(case)
            classified = classify_outcome(200, '{}', context={'inventory_field': None,
                'expectation_observed': comparison['status'] == 'PASS'}) if comparison['status'] != 'WARN' else {'status': 'WARN', 'reason_code': comparison['reason_code']}
            handle_outcome(lessons, escalations, {**classified, 'retryable': False},
                scope['ticket'] + '-service-' + job_id + '-' + case['case_id'],
                [scope['ticket'], scope['environment']], 'currency points_diff ' + comparison['reason_code'],
                operational_scope, retries=0, steps=2 if target else 0)
    if stopped:
        raise JobCancelled()
    status = 'failed' if any(c['status'] == 'failed' for c in cases) else 'need_action' if any(c['status'] == 'need_action' for c in cases) else 'passed'
    return {'ticket': scope['ticket'], 'environment': scope['environment'], 'base_url': selected_url,
            'status': status, 'cases': cases}, folder
