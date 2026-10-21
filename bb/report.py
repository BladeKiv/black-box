"""Aggregate hosting-agent records, not live API execution evidence."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
from .lessons import Store
from .escalations import Escalations


def summarize(store, escalations):
    events = escalations.events()
    runs = {}
    weeks = defaultdict(set)
    reason_codes = Counter()
    severity = {'PASS': 0, 'WARN': 1, 'FAIL': 2}
    for event in events:
        if event['event'] != 'run':
            continue
        run = runs.setdefault(event['run'], {'status': event['status'], 'escalated': False})
        if severity[event['status']] > severity[run['status']]:
            run['status'] = event['status']
        run['escalated'] |= bool(event.get('escalation_id'))
        year, week, _ = datetime.fromisoformat(event['timestamp']).isocalendar()
        weeks[f'{year}-W{week:02}'].add(event['run'])
        reason_codes[event['reason_code']] += 1
    lesson_events = store.events()
    return {'weekly': {week: {'tasks': len(ids), 'escalated_tasks': sum(runs[i]['escalated'] for i in ids),
                             'escalation_rate': sum(runs[i]['escalated'] for i in ids) / len(ids)}
                       for week, ids in sorted(weeks.items())},
            'top_reason_codes': reason_codes.most_common(), 'runs': runs,
            'tasks_by_status': dict(Counter(r['status'] for r in runs.values())),
            'lessons_used': sum(e['event'] == 'use' for e in lesson_events),
            'lessons_promoted': sum(e['status'] == 'trusted' and e.get('previous_status') == 'candidate' for e in lesson_events),
            'lessons_deprecated': sum(e['status'] == 'deprecated' and (e['event'] == 'deprecated' or e.get('previous_status') != 'deprecated') for e in lesson_events),
            'human_questions': sum(e['event'] == 'question' for e in events)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lessons')
    parser.add_argument('--escalations')
    args = parser.parse_args()
    store = Store(args.lessons) if args.lessons else Store()
    print(json.dumps(summarize(store, Escalations(args.escalations, store)), indent=2))


if __name__ == '__main__':
    main()
