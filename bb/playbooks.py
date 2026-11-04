"""Operational preparation guidance; ticket expectations always remain in ticket scope."""
import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
import re

from .classify import classify_outcome
from .lessons import ROOT, read_events
from .security import ensure_safe
from .service import instance_lock, write_json

DEFAULT_ROOT = ROOT / 'knowledge'
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
PB_ID = re.compile(r'PB-([a-z0-9]+(?:-[a-z0-9]+)*)-\d{3,}')
FORBIDDEN = re.compile(r'(?<![a-z])(?:expected|expectation|tolerance|comparator|allowance|permission|authorization)|extra.?edge.?case|allow_(?:retry|poll|retest)|approved_inputs|sign.?off', re.I)
ENDPOINT = re.compile(r'\b(GET|POST|PUT|PATCH|DELETE)\s+(/(?:v\d+/|ndc/|algo/)[A-Za-z0-9_/{}/.\-]+)')
DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
REASONS = {
    'NO_DATA': 'usable inventory was unavailable',
    'AUTH_MISSING': 'runtime authentication was unavailable',
    'AUTH_REJECTED': 'authentication was rejected',
    'TLS_ERROR': 'transport certificate validation failed',
    'TIMEOUT': 'the request timed out',
    'TRANSPORT_ERROR': 'the transport failed',
    'ASYNC_INCOMPLETE': 'asynchronous retrieval was incomplete',
    'INVALID_JSON': 'the response was not JSON',
    'PRICE_CHANGE': 'a price change interrupted the flow',
    'RETRY_REQUESTED': 'the provider requested another attempt',
    'CONTRACT_MISMATCH': 'a ticket assertion failed',
    'UNEXPECTED_MESSAGE': 'the provider returned an unrecognized message',
    'HTTP_ERROR': 'an HTTP error interrupted the flow',
    'UNEVALUATED': 'the outcome could not be evaluated',
}
BOOK_FIELDS = {'id', 'status', 'family', 'title', 'summary', 'tags', 'providers', 'endpoints',
               'endpoint_flow', 'case_patterns', 'testdata_refs', 'pitfalls', 'source_tasks',
               'last_verified', 'times_used', 'times_helped'}
DATA_FIELDS = {'id', 'provider', 'env', 'description', 'params', 'date_rule', 'verified_at', 'verified_run', 'status'}


def safe(value):
    ensure_safe(value)
    def walk(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if FORBIDDEN.search(str(key)):
                    raise ValueError('Expected-value or authority fields are prohibited')
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, str) and FORBIDDEN.search(item):
            raise ValueError('Expected-value or authority text is prohibited')
    walk(value)
    json.dumps(value, allow_nan=False)


def strings(value):
    return isinstance(value, list) and all(isinstance(s, str) and s.strip() for s in value)


def stamp(value):
    if not isinstance(value, str):
        raise ValueError('Verification date required')
    return datetime.fromisoformat(value.replace('Z', '+00:00')).date()


def resolve_rule(rule, today=None):
    if not isinstance(rule, str) or not re.fullmatch(r'D[+-]\d{1,4}', rule):
        raise ValueError('Relative date must use D+N or D-N')
    return ((today or date.today()) + timedelta(days=int(rule[1:]))).isoformat()


def validate_book(book):
    safe(book)
    required = BOOK_FIELDS - {'title', 'summary'}
    if not isinstance(book, dict) or not required <= book.keys() or book.keys() - BOOK_FIELDS:
        raise ValueError('Malformed playbook fields')
    if not isinstance(book['id'], str) or not PB_ID.fullmatch(book['id']) or PB_ID.fullmatch(book['id'])[1] != book['family']:
        raise ValueError('Invalid playbook id/family')
    if book['status'] not in ('candidate', 'approved', 'deprecated'):
        raise ValueError('Invalid playbook status')
    for key in ('tags', 'providers', 'endpoints', 'endpoint_flow', 'testdata_refs', 'pitfalls', 'source_tasks'):
        if not strings(book[key]):
            raise ValueError('Playbook lists must contain strings')
    for key in ('title', 'summary'):
        if key in book and not isinstance(book[key], str):
            raise ValueError('Invalid playbook text')
    if not isinstance(book['case_patterns'], list):
        raise ValueError('Case patterns must be a list')
    for pattern in book['case_patterns']:
        if (not isinstance(pattern, dict) or set(pattern) != {'pattern', 'needs'}
                or not isinstance(pattern['pattern'], str) or not pattern['pattern'].strip()
                or not strings(pattern['needs'])):
            raise ValueError('Malformed case pattern')
    stamp(book['last_verified'])
    if any(type(book[k]) is not int or book[k] < 0 for k in ('times_used', 'times_helped')) or book['times_helped'] > book['times_used']:
        raise ValueError('Invalid usage counts')
    return book


def validate_data(entry):
    safe(entry)
    if not isinstance(entry, dict) or set(entry) != DATA_FIELDS:
        raise ValueError('Malformed testdata fields')
    for key in ('id', 'provider', 'env', 'description', 'verified_run'):
        if not isinstance(entry[key], str) or not entry[key].strip():
            raise ValueError('Testdata text fields must be nonempty')
    if not all(SLUG.fullmatch(entry[k]) for k in ('provider', 'env')):
        raise ValueError('Provider/environment must be lowercase slugs')
    if entry['status'] not in ('ok', 'stale', 'candidate') or not isinstance(entry['params'], dict):
        raise ValueError('Invalid testdata status/params')
    stamp(entry['verified_at'])
    resolve_rule(entry['date_rule'])
    def check(item):
        if isinstance(item, dict):
            for child in item.values():
                check(child)
        elif isinstance(item, list):
            for child in item:
                check(child)
        elif isinstance(item, str):
            if DATE.search(item):
                raise ValueError('Fixed dates cannot be stored as test inputs')
            if item.startswith(('D+', 'D-')):
                resolve_rule(item)
    check(entry['params'])
    return entry


class Store:
    def __init__(self, root=DEFAULT_ROOT):
        self.root = Path(root)
        self.books = self.root / 'playbooks'
        self.data = self.root / 'testdata'
        self.log = self.books / 'events.jsonl'

    @contextmanager
    def writer(self):
        self.books.mkdir(parents=True, exist_ok=True)
        lock = instance_lock(self.books)
        try:
            yield
        finally:
            lock.close()

    def all(self):
        books = []
        for path in sorted(self.books.glob('PB-*.json')):
            book = validate_book(json.loads(path.read_text(encoding='utf-8')))
            if path.stem != book['id']:
                raise ValueError('Playbook filename/id mismatch')
            books.append(book)
        return books

    def get(self, book_id):
        if not PB_ID.fullmatch(book_id):
            raise ValueError('Invalid playbook id')
        return next(b for b in self.all() if b['id'] == book_id)

    def events(self):
        events = read_events(self.log)
        for event in events:
            safe(event)
            if not isinstance(event, dict) or event.get('event') not in ('use', 'distill'):
                raise ValueError('Malformed playbook event')
            if not isinstance(event.get('id'), str) or not PB_ID.fullmatch(event['id']) or not isinstance(event.get('run'), str) or not event['run']:
                raise ValueError('Malformed playbook event identity')
            if event['event'] == 'use' and type(event.get('helped')) is not bool:
                raise ValueError('Malformed usage event')
            if event['event'] == 'distill' and (not isinstance(event.get('task'), str) or not isinstance(event.get('need_action'), dict)
                    or any(k not in REASONS or type(v) is not int or v < 0 for k, v in event['need_action'].items())):
                raise ValueError('Malformed distill event')
        return events

    def write_events(self, events):
        # Replace the complete journal atomically so a terminated writer cannot leave a partial line.
        safe(events)
        temporary = self.log.with_suffix('.tmp')
        temporary.write_text(''.join(json.dumps(e, allow_nan=False) + '\n' for e in events), encoding='utf-8')
        temporary.replace(self.log)

    def save(self, book):
        validate_book(book)
        with self.writer():
            self.all()
            self.events()
            if (self.books / (book['id'] + '.json')).exists():
                raise ValueError('Existing playbooks must use lifecycle commands')
            write_json(self.books / (book['id'] + '.json'), book)
        return book

    def registry(self, provider, env):
        if not all(isinstance(v, str) and SLUG.fullmatch(v) for v in (provider, env)):
            raise ValueError('Invalid provider/environment')
        path = self.data / f'{provider}-{env}.json'
        entries = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        if not isinstance(entries, list):
            raise ValueError('Testdata registry must be an array')
        ids = set()
        for entry in entries:
            validate_data(entry)
            if entry['provider'] != provider or entry['env'] != env or entry['id'] in ids:
                raise ValueError('Testdata identity mismatch or duplicate')
            ids.add(entry['id'])
        return path, entries

    def add_testdata(self, entry):
        validate_data(entry)
        with self.writer():
            self.all()
            self.events()
            path, entries = self.registry(entry['provider'], entry['env'])
            if any(e['id'] == entry['id'] for e in entries):
                raise ValueError('Duplicate testdata id')
            self.data.mkdir(parents=True, exist_ok=True)
            write_json(path, entries + [entry])
        return entry

    def edit(self, book_id, replacement):
        validate_book(replacement)
        with self.writer():
            book = self.get(book_id)
            self.events()
            if book['status'] != 'candidate':
                raise ValueError('Only candidates can be edited')
            editable = {'title', 'summary', 'tags', 'providers', 'endpoints', 'endpoint_flow', 'case_patterns', 'pitfalls'}
            if any(replacement.get(k) != v for k, v in book.items() if k not in editable) or replacement['id'] != book_id:
                raise ValueError('Lifecycle and provenance fields cannot be edited')
            write_json(self.books / (book_id + '.json'), replacement)
        return replacement

    def snapshot(self):
        entries = []
        for path in sorted(self.data.glob('*.json')):
            raw = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(raw, list):
                raise ValueError('Malformed registry')
            for entry in raw:
                validate_data(entry)
                if path.name != f"{entry['provider']}-{entry['env']}.json":
                    raise ValueError('Registry identity mismatch')
                entries.append(entry)
        return dict(playbooks=self.all(), testdata=entries)

    def mark_stale(self, provider, env, entry_id):
        return self.mark_status(provider, env, entry_id, 'stale')

    def mark_status(self, provider, env, entry_id, status):
        if status not in ('ok', 'stale'):
            raise ValueError('Invalid reviewed status')
        with self.writer():
            self.all()
            self.events()
            path, entries = self.registry(provider, env)
            entry = next(e for e in entries if e['id'] == entry_id)
            if entry['status'] == 'candidate':
                raise ValueError('Approve the source playbook first')
            entry['status'] = status
            write_json(path, entries)
        return entry

    def testdata(self, provider, env, today=None):
        def resolve(item):
            if isinstance(item, dict):
                return {k: resolve(v) for k, v in item.items()}
            if isinstance(item, list):
                return [resolve(v) for v in item]
            if isinstance(item, str) and re.fullmatch(r'D[+-]\d{1,4}', item):
                return resolve_rule(item, today)
            return item
        return [dict(e, date=resolve_rule(e['date_rule'], today), params=resolve(e['params']))
                for e in self.registry(provider, env)[1] if e['status'] == 'ok']

    def transition(self, book_id, action):
        if action not in ('approve', 'reject', 'deprecate'):
            raise ValueError('Unknown lifecycle action')
        with self.writer():
            book = self.get(book_id)
            if action == 'approve' and book['status'] != 'candidate':
                raise ValueError('Only candidates can be approved')
            if action == 'reject' and book['status'] != 'candidate':
                raise ValueError('Only candidates can be rejected')
            updates = []
            if action == 'approve':
                for path in sorted(self.data.glob('*.json')):
                    entries = json.loads(path.read_text(encoding='utf-8'))
                    if not isinstance(entries, list):
                        raise ValueError('Malformed testdata registry')
                    for entry in entries:
                        validate_data(entry)
                        ref = path.name + '#' + entry['id']
                        if ref in book['testdata_refs'] and entry['status'] == 'candidate':
                            entry['status'] = 'ok'
                    updates.append((path, entries))
                available = {p.name + '#' + e['id'] for p, entries in updates for e in entries}
                if set(book['testdata_refs']) - available:
                    raise ValueError('Unresolved testdata reference')
            book['status'] = 'approved' if action == 'approve' else 'deprecated'
            self.events()
            for path, entries in updates:
                write_json(path, entries)
            write_json(self.books / (book_id + '.json'), book)
        return book

    def record_use(self, book_id, helped, run):
        if type(helped) is not bool or not isinstance(run, str) or not run.strip():
            raise ValueError('A boolean and unique nonempty run id are required')
        safe(run)
        with self.writer():
            book = self.get(book_id)
            if book['status'] != 'approved':
                raise ValueError('Only approved playbooks can be used')
            events = self.events()
            previous = next((e for e in events if e['event'] == 'use' and e['id'] == book_id and e['run'] == run), None)
            if previous and previous['helped'] != helped:
                raise ValueError('Reuse id already has a different outcome')
            if not previous:
                events.append(dict(event='use', id=book_id, helped=helped, run=run))
                self.write_events(events)
            uses = [e for e in events if e['event'] == 'use' and e['id'] == book_id]
            book.update(times_used=len(uses), times_helped=sum(e['helped'] for e in uses))
            write_json(self.books / (book_id + '.json'), book)
        return book

    def search(self, tags=(), text='', top=3, today=None):
        if type(top) is not int or top < 1:
            raise ValueError('top must be positive')
        self.events()
        tags = {t.lower() for t in tags}
        terms = set(re.findall(r'\w+', text.lower()))
        matches = []
        for book in self.all():
            if book['status'] != 'approved':
                continue
            words = set(re.findall(r'\w+', ' '.join([book.get('title', book['family']), book.get('summary', ''), *book['pitfalls']]).lower()))
            score = 3 * len(tags & {t.lower() for t in book['tags']})
            score += 2 * len(tags & {t.lower() for t in book['providers'] + book['endpoints']})
            score += len(terms & words)
            confidence = book['times_helped'] / book['times_used'] if book['times_used'] else 0.5
            age = max(0, ((today or date.today()) - stamp(book['last_verified'])).days)
            score *= confidence * 0.5 ** (age / 180)
            if score >= 0.5:
                matches.append((score, book))
        output = []
        for _, book in sorted(matches, key=lambda pair: (-pair[0], pair[1]['id']))[:top]:
            compact = {k: book[k] for k in ('id', 'endpoint_flow', 'case_patterns', 'testdata_refs', 'pitfalls')}
            compact['title'] = book.get('title', book['family'])
            # A byte cap also bounds multilingual output without adding a tokenizer dependency.
            if len(json.dumps(output + [compact], ensure_ascii=False).encode('utf-8')) > 12000:
                continue
            output.append(compact)
        return output

    def stats(self):
        self.all()
        events = self.events()
        uses = {(e['id'], e['run']): e for e in events if e['event'] == 'use'}
        reasons = Counter()
        for event in events:
            if event['event'] == 'distill':
                reasons.update(event['need_action'])
        return dict(used=len(uses), helped=sum(e['helped'] for e in uses.values()), need_action=dict(reasons))

    def distill(self, run, task, *, approved=False, today=None):
        if approved is not True:
            raise ValueError('Run approval must be explicitly asserted with --approved')
        today = today or date.today()
        run = Path(run)
        plan = json.loads((run / 'cases.json').read_text(encoding='utf-8'))
        if not (run / 'results.jsonl').is_file():
            raise ValueError('Results file required')
        results = read_events(run / 'results.jsonl')
        scope = (run / 'ticket-scope.md').read_text(encoding='utf-8')
        if not scope.strip() or not isinstance(plan, dict) or plan.get('task', plan.get('task_key')) != task or plan.get('v') != 1:
            raise ValueError('Task/scope/plan mismatch')
        cases = plan.get('cases')
        if not isinstance(cases, list) or not cases or not all(isinstance(c, dict) for c in cases):
            raise ValueError('Cases required')
        ids = [c.get('case_id') for c in cases]
        if any(not isinstance(i, str) or not re.fullmatch(r'TC-\d+', i) for i in ids) or len(set(ids)) != len(ids):
            raise ValueError('Invalid or duplicate case ids')
        if not all(isinstance(r, dict) for r in results):
            raise ValueError('Malformed results')
        results = [dict(r, status=r.get('status', r.get('result'))) for r in results]
        if [r.get('case_id') for r in results] != ids or any(r.get('status') not in ('passed', 'failed', 'need_action') for r in results):
            raise ValueError('Every case needs exactly one result, in plan order')
        family = plan.get('family', 'endpoint-flow')
        if not isinstance(family, str) or not SLUG.fullmatch(family):
            raise ValueError('Invalid family')
        providers = plan.get('providers', [])
        if not strings(providers):
            raise ValueError('Invalid providers')
        flow, patterns, entries, pitfalls = [], [], [], []
        reasons = Counter()
        for case, result in zip(cases, results):
            steps = case.get('steps')
            data = case.get('test_data', {})
            if not strings(steps) or not isinstance(data, dict):
                raise ValueError('Invalid steps/test_data')
            # Only method/path identities survive; titles, prose and assertions are never learned.
            case_flow = []
            for method, path in ENDPOINT.findall(' '.join(steps)):
                path = re.sub(r'(/(?:result|ngs-air-pricing|allfares)/[^/]+/).*', r'\1{key}', path)
                endpoint = method + ' ' + path
                if endpoint not in case_flow:
                    case_flow.append(endpoint)
                if endpoint not in flow:
                    flow.append(endpoint)
            params = data.get('params', {k: v for k, v in data.items() if k not in ('provider', 'env', 'description')})
            if not isinstance(params, dict):
                raise ValueError('Testdata params must be an object')
            pattern = dict(pattern=' -> '.join(case_flow), needs=sorted(params))
            if case_flow and pattern not in patterns:
                patterns.append(pattern)
            actual = result.get('actual', {})
            executed = result['status'] in ('passed', 'failed') or (isinstance(actual, dict) and actual.get('request_executed') is True)
            if params and executed:
                provider = data.get('provider', providers[0] if len(providers) == 1 else None)
                env = plan.get('environment')
                if not provider or not env:
                    raise ValueError('Used test data requires provider and environment')
                first_rule = []
                def relative(item):
                    if isinstance(item, dict):
                        return {k: relative(v) for k, v in item.items()}
                    if isinstance(item, list):
                        return [relative(v) for v in item]
                    if isinstance(item, str) and DATE.fullmatch(item):
                        rule = f'D{(date.fromisoformat(item) - today).days:+d}'
                        first_rule.append(rule)
                        return rule
                    if isinstance(item, str) and re.fullmatch(r'D[+-]\d{1,4}', item):
                        first_rule.append(item)
                    return item
                params = relative(params)
                if not first_rule:
                    raise ValueError('Used test data needs a relative travel date')
                fingerprint = hashlib.sha256(json.dumps([task, case['case_id'], params], sort_keys=True).encode()).hexdigest()[:16]
                entries.append(validate_data(dict(id='TD-' + fingerprint, provider=provider, env=env,
                    description='Used inputs for ' + task + ' ' + case['case_id'], params=params,
                    date_rule=first_rule[0], verified_at=today.isoformat(), verified_run=run.name, status='candidate')))
                if provider not in providers:
                    providers = providers + [provider]
            if result['status'] != 'passed':
                actual = result.get('actual', {})
                reason = actual.get('reason_code') if isinstance(actual, dict) else None
                if reason not in REASONS:
                    failure = result.get('failure', {})
                    response = failure.get('response', {})
                    reason = classify_outcome(response.get('status'), response.get('body_excerpt', '{}'),
                        context={'expectation_observed': False} if result['status'] == 'failed' else {})['reason_code']
                pitfall = reason + ': ' + REASONS[reason]
                if pitfall not in pitfalls:
                    pitfalls.append(pitfall)
                if result['status'] == 'need_action':
                    reasons[reason] += 1
        if not flow:
            raise ValueError('No explicit HTTP endpoint flow found in executed case steps')
        book = dict(id='PB-' + family + '-001', status='candidate', family=family, tags=[family], providers=providers,
                    endpoints=[s.split(' ', 1)[1] for s in flow], endpoint_flow=flow, case_patterns=patterns,
                    testdata_refs=[f"{e['provider']}-{e['env']}.json#{e['id']}" for e in entries],
                    pitfalls=pitfalls, source_tasks=[task], last_verified=today.isoformat(), times_used=0, times_helped=0)
        validate_book(book)
        with self.writer():
            books, events = self.all(), self.events()
            existing = next((b for b in books if task in b['source_tasks']), None)
            if existing:
                return existing
            previous = next((e for e in events if e['event'] == 'distill' and e['task'] == task), None)
            reserved = [b['id'] for b in books] + [e['id'] for e in events]
            number = max([int(i.rsplit('-', 1)[1]) for i in reserved if PB_ID.fullmatch(i)[1] == family] or [0]) + 1
            book['id'] = previous['id'] if previous else f'PB-{family}-{number:03d}'
            validate_book(book)
            event = dict(event='distill', id=book['id'], task=task, run=run.name, need_action=dict(reasons))
            if previous and previous != event:
                raise ValueError('Interrupted distillation must be recovered from the same run')
            registries = {}
            for entry in entries:
                key = (entry['provider'], entry['env'])
                if key not in registries:
                    registries[key] = self.registry(*key)
                path, rows = registries[key]
                previous_data = next((e for e in rows if e['id'] == entry['id']), None)
                if previous_data and previous_data != entry:
                    raise ValueError('Conflicting testdata id')
                if not previous_data:
                    rows.append(entry)
            self.data.mkdir(parents=True, exist_ok=True)
            for path, rows in registries.values():
                write_json(path, rows)
            if not previous:
                self.write_events(events + [event])
            write_json(self.books / (book['id'] + '.json'), book)
        return book


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT, help='Knowledge directory')
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('--tags', nargs='*', default=[])
    search.add_argument('--text', default='')
    search.add_argument('--top', type=int, default=3)
    data = commands.add_parser('testdata')
    data.add_argument('action', nargs='?', choices=['add', 'mark-stale', 'mark-ok'])
    data.add_argument('--provider')
    data.add_argument('--env')
    data.add_argument('--file', type=Path)
    data.add_argument('--id')
    distill = commands.add_parser('distill')
    distill.add_argument('--run', type=Path, required=True)
    distill.add_argument('--task', required=True)
    distill.add_argument('--approved', action='store_true', help='Assert explicit user approval of this run')
    for action in ('approve', 'reject', 'deprecate', 'record-use'):
        command = commands.add_parser(action)
        command.add_argument('id')
        if action == 'record-use':
            command.add_argument('--helped', choices=['true', 'false'], required=True)
            command.add_argument('--run', required=True)
    commands.add_parser('stats')
    commands.add_parser('list')
    edit = commands.add_parser('edit')
    edit.add_argument('id')
    edit.add_argument('--stdin', action='store_true', required=True)
    args = parser.parse_args()
    store = Store(args.root)
    try:
        if args.command == 'search':
            output = store.search(args.tags, args.text, args.top)
        elif args.command == 'testdata':
            if args.action == 'add':
                if not args.file:
                    parser.error('testdata add requires --file')
                output = store.add_testdata(json.loads(args.file.read_text(encoding='utf-8')))
            else:
                if not args.provider or not args.env or (args.action in ('mark-stale', 'mark-ok') and not args.id):
                    parser.error('testdata requires --provider --env (and --id for mark-stale)')
                output = (store.mark_status(args.provider, args.env, args.id, 'ok' if args.action == 'mark-ok' else 'stale') if args.action else store.testdata(args.provider, args.env))
        elif args.command == 'list':
            output = store.snapshot()
        elif args.command == 'edit':
            import sys
            output = store.edit(args.id, json.load(sys.stdin))
        elif args.command == 'distill':
            output = store.distill(args.run, args.task, approved=args.approved)
        elif args.command == 'record-use':
            output = store.record_use(args.id, args.helped == 'true', args.run)
        elif args.command == 'stats':
            output = store.stats()
        else:
            output = store.transition(args.id, args.command)
    except (ValueError, KeyError, StopIteration, OSError, TypeError):
        parser.exit(1, 'Playbook operation rejected: invalid, unsafe, missing or malformed input/store; no values logged.\n')
    print(json.dumps(output, ensure_ascii=False, separators=(',', ':')))


if __name__ == '__main__':
    main()
