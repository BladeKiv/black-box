"""Host-agent handoff records; does not send messages or execute lesson actions."""
from pathlib import Path
import uuid
from .lessons import ROOT, append_event, read_events, now, allowed_action


class Escalations:
    def __init__(self, path=None, store=None):
        self.path = Path(path) if path else ROOT / 'knowledge/lessons/escalations.jsonl'
        self.store = store

    def events(self):
        return read_events(self.path)

    def ask(self, *, run, question, reason_code, matching_lesson_found, tags, pattern, scope_conditions):
        for event in self.events():
            if event['event'] == 'question' and event['run'] == run and event['reason_code'] == reason_code and event['pattern'] == pattern and event['scope_conditions'] == scope_conditions:
                return event['id']
        event = dict(id=uuid.uuid4().hex, event='question', run=run, question=question,
                     reason_code=reason_code, matching_lesson_found=matching_lesson_found,
                     tags=tags, pattern=pattern, scope_conditions=scope_conditions, timestamp=now())
        append_event(self.path, event)
        return event['id']

    def answer(self, escalation_id, answer, *, action, scope_conditions):
        question = next(e for e in self.events() if e['id'] == escalation_id and e['event'] == 'question')
        if scope_conditions != question['scope_conditions']:
            raise ValueError('Human answer must retain question scope')
        # Validate and persist the operational answer immediately as a human lesson.
        lesson = self.store.propose(tags=question['tags'], trigger_pattern=question['pattern'],
                                    situation=question['question'], action=action, outcome=answer,
                                    created_run=question['run'], scope_conditions=scope_conditions,
                                    source='human', human_confirmed=True)
        append_event(self.path, dict(id=escalation_id, event='answer', run=question['run'],
                                    lesson_id=lesson['id'], timestamp=now()))
        return lesson


def handle_outcome(store, escalations, outcome, run, tags, pattern, scope, *, retries=0, steps=0):
    """Select an allowed action. The hosting agent performs it within ticket scope.

    Outcome is deliberately immutable: a lesson never turns WARN into PASS.
    """
    from .lessons import SCOPE_KEYS
    matches = store.search(tags, pattern)
    applicable = [m for m in matches if allowed_action(m, scope, store.config, retries=retries, steps=steps)]
    if outcome['status'] == 'PASS':
        selected = {}
    elif applicable:
        selected = {'lesson_id': applicable[0]['id'], 'action': applicable[0]['action'],
                    'review_required': applicable[0]['review_required']}
    else:
        question = 'What scope-approved operational step should handle ' + outcome['reason_code'] + '?'
        conditions = {k: v for k, v in scope.items() if k in SCOPE_KEYS}
        selected = {'escalation_id': escalations.ask(run=run, question=question,
                    reason_code=outcome['reason_code'], matching_lesson_found=bool(matches),
                    tags=tags, pattern=pattern, scope_conditions=conditions)}
    append_event(escalations.path, dict(id=uuid.uuid4().hex, event='run', run=run,
                 status=outcome['status'], reason_code=outcome['reason_code'], timestamp=now(), **selected))
    return {**outcome, **selected}
