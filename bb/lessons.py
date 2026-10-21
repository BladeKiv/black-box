"""Append-only operational lessons. Single hosting-agent writer per store."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import uuid
from .security import ensure_safe
from .classify import normalize_message

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = ROOT / 'knowledge/lessons/lessons.jsonl'
ACTIONS = {'check_prerequisites', 'retry', 'vary_inputs', 'poll', 'report_warn', 'fresh_retest'}
SCOPE_KEYS = {'ticket', 'environment', 'route', 'provider', 'endpoint', 'async_id_path'}
FORBIDDEN = re.compile(r'(?i)(?:sign.?off|tolerance|null.{0,12}(?:omitted|equival)|expected.behavio[u]?r|accept.{0,8}pass|bypass.{0,8}tls|verify.{0,4}tls|book/create|ticket/issue|credentials?\s*[:=]|authorization\s*[:=])')


def now():
    return datetime.now(timezone.utc).isoformat()


def load_config():
    config = json.loads((Path(__file__).parent / 'config.json').read_text(encoding='utf-8'))
    if any(type(v) is not int or v < 1 for v in config.values()):
        raise ValueError('Budgets must be positive integers')
    return config


def append_event(path, event):
    ensure_safe(event)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + '\n')


def read_events(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def allowed_action(lesson, scope, config, *, retries=0, steps=0):
    if lesson.get('status') != 'trusted' or steps >= config['max_steps']:
        return False
    conditions = lesson.get('scope_conditions', {})
    if not conditions or any(scope.get(k) != v for k, v in conditions.items()):
        return False
    action = lesson['action']
    if action in ('retry', 'poll'):
        return bool(scope.get('allow_retry' if action == 'retry' else 'allow_poll')) and retries < config['max_retries']
    if action == 'vary_inputs':
        return bool(scope.get('approved_inputs'))
    if action == 'fresh_retest':
        return bool(scope.get('allow_retest'))
    return action in ('check_prerequisites', 'report_warn')


class Store:
    def __init__(self, path=DEFAULT_STORE, config=None):
        self.path = Path(path)
        self.config = config or load_config()

    def events(self):
        return read_events(self.path)

    def latest(self):
        return {event['id']: event for event in self.events()}

    def propose(self, *, tags, trigger_pattern, situation, action, outcome,
                created_run, scope_conditions, source='agent', human_confirmed=False, **extra):
        if extra or action not in ACTIONS or source not in ('agent', 'human'):
            raise ValueError('Only operational lesson fields/actions are allowed')
        if not isinstance(scope_conditions, dict) or not scope_conditions or set(scope_conditions) - SCOPE_KEYS:
            raise ValueError('Explicit operational scope conditions required')
        if not all(isinstance(v, str) and v for v in scope_conditions.values()):
            raise ValueError('Scope conditions must be nonempty strings')
        if FORBIDDEN.search(json.dumps([tags, trigger_pattern, situation, outcome, scope_conditions])):
            raise ValueError('Expectations, equivalences and authorizations cannot be learned')
        if human_confirmed and source != 'human':
            raise ValueError('Only a current human answer can confirm a lesson')
        event = dict(id=uuid.uuid4().hex, tags=tags, trigger_pattern=normalize_message(trigger_pattern),
                     situation=situation, action=action, outcome=outcome,
                     status='trusted' if human_confirmed else 'candidate', success_count=0,
                     fail_count=0, source=source, created_run=created_run,
                     timestamp=now(), scope_conditions=scope_conditions, event='proposed')
        append_event(self.path, event)
        return event

    def record_use(self, lesson_id, success, run):
        lesson = dict(self.latest()[lesson_id])
        if lesson['status'] == 'deprecated':
            raise ValueError('Deprecated lessons cannot be applied')
        # Repeated logging of the same reuse must not inflate trust.
        if any(e.get('used_run') == run and e['id'] == lesson_id for e in self.events()):
            return lesson
        lesson['success_count' if success else 'fail_count'] += 1
        previous = lesson['status']
        if lesson['fail_count'] >= self.config['deprecation_failures']:
            lesson['status'] = 'deprecated'
        elif lesson['success_count'] >= self.config['promotion_successes']:
            lesson['status'] = 'trusted'
        lesson.update(timestamp=now(), event='use', used_run=run, success=bool(success), previous_status=previous)
        append_event(self.path, lesson)
        return lesson

    def deprecate(self, lesson_id):
        lesson = dict(self.latest()[lesson_id])
        lesson.update(status='deprecated', event='deprecated', timestamp=now())
        append_event(self.path, lesson)
        return lesson

    def search(self, tags=(), text='', include_deprecated=False):
        terms = set(re.findall(r'\w+', text.lower()))
        matches = []
        for lesson in self.latest().values():
            if lesson['status'] == 'deprecated' and not include_deprecated:
                continue
            haystack = set(re.findall(r'\w+', ' '.join([lesson['trigger_pattern'], lesson['situation'], *lesson['tags']]).lower()))
            score = 3 * len(set(tags) & set(lesson['tags'])) + len(terms & haystack)
            if score or (not tags and not terms):
                total = lesson['success_count'] + lesson['fail_count']
                matches.append({**lesson, 'score': score, 'success_rate': lesson['success_count'] / total if total else 0})
        for lesson in matches:
            lesson['review_required'] = any(
                other['id'] != lesson['id'] and other['trigger_pattern'] == lesson['trigger_pattern']
                and other['scope_conditions'] == lesson['scope_conditions'] and other['action'] != lesson['action']
                for other in matches)
        return sorted(matches, key=lambda l: (-l['success_rate'], -l['score'], l['id']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', type=Path, default=DEFAULT_STORE)
    sub = parser.add_subparsers(dest='command', required=True)
    search = sub.add_parser('search')
    search.add_argument('--tags', nargs='*', default=[])
    search.add_argument('--text', default='')
    propose = sub.add_parser('propose')
    propose.add_argument('--file', type=Path, required=True, help='JSON lesson fields; no credentials or expectations')
    use = sub.add_parser('record-use')
    use.add_argument('--id', required=True)
    use.add_argument('--run', required=True)
    group = use.add_mutually_exclusive_group(required=True)
    group.add_argument('--success', action='store_true')
    group.add_argument('--fail', action='store_true')
    sub.add_parser('list')
    deprecate = sub.add_parser('deprecate')
    deprecate.add_argument('--id', required=True)
    args = parser.parse_args()
    store = Store(args.store)
    if args.command == 'search':
        output = store.search(args.tags, args.text)
    elif args.command == 'propose':
        output = store.propose(**json.loads(args.file.read_text(encoding='utf-8')))
    elif args.command == 'record-use':
        output = store.record_use(args.id, args.success, args.run)
    elif args.command == 'deprecate':
        output = store.deprecate(args.id)
    else:
        output = list(store.latest().values())
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
