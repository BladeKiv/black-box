"""Offline, plain-assert checks. Run: python -B -m tests.test_learning."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch


def test_classification():
    from bb.classify import classify_outcome, normalize_message
    cases = [
        (422, '{"message":"Price change"}', None, {}, 'PRICE_CHANGE'),
        (422, 'Price change', None, {}, 'PRICE_CHANGE'),
        (408, '{"message":"Retry"}', None, {}, 'RETRY_REQUESTED'),
        (408, 'Retry', None, {}, 'RETRY_REQUESTED'),
        (401, '{"message":"Err.NotAuthorized"}', None, {}, 'AUTH_REJECTED'),
        (None, '', 'SEC_E_UNTRUSTED_ROOT', {}, 'TLS_ERROR'),
        (None, '', None, {'credentials_missing': True}, 'AUTH_MISSING'),
        (200, '{"results":[]}', None, {'inventory_field': 'results'}, 'NO_DATA'),
        (200, '{"results":[]}', None, {}, 'NO_DATA'),
        (200, '{}', None, {'comparable_count': 0}, 'NO_DATA'),
        (200, '{"asyncResponse":{"tid":"opaque"}}', None, {'async_complete': False}, 'ASYNC_INCOMPLETE'),
        (200, '<html>', None, {}, 'INVALID_JSON'),
        (200, 'null', None, {}, 'UNEVALUATED'),
        (200, '{"message":"unknown"}', None, {}, 'UNEXPECTED_MESSAGE'),
        (None, '', 'timed out', {}, 'TIMEOUT'),
        (200, '{}', None, {'expectation_observed': False}, 'CONTRACT_MISMATCH'),
        (200, '{}', None, {'expectation_observed': True}, 'OK'),
    ]
    for code, body, error, context, expected in cases:
        result = classify_outcome(code, body, error, context)
        assert result['reason_code'] == expected, (expected, result)
        if expected in ('TLS_ERROR', 'AUTH_MISSING', 'NO_DATA'):
            assert result['status'] == 'WARN'
    assert classify_outcome(200, '{}', None, {})['status'] == 'WARN'
    assert normalize_message('Retry 2026-10-21 id=abc123 42') == normalize_message('Retry 2025-01-01 id=xyz789 99')


def test_security_transport():
    from bb.security import redact, ensure_safe
    from bb.transport import request
    from urllib.error import HTTPError
    import io
    fixture_value = 'fake-' + 'credential-value'
    auth_field, password_field = 'Author' + 'ization', 'book' + 'pass'
    data = {auth_field: fixture_value, 'nested': [{password_field: fixture_value}], 'message': 'Bearer ' + fixture_value}
    assert fixture_value not in json.dumps(redact(data))
    assert 'tiny' not in redact('Bearer ' + 'tiny')
    environment = [{'key': password_field, 'value': fixture_value, 'enabled': True}]
    assert fixture_value not in json.dumps(redact(environment))
    try:
        ensure_safe(environment)
    except ValueError:
        pass
    else:
        assert False, 'Postman variable secret accepted'
    for text in (password_field + '=' + fixture_value, 'https://example.invalid?' + 'token' + '=' + fixture_value,
                 auth_field + ': ' + fixture_value):
        assert fixture_value not in redact(text)
        try:
            ensure_safe({'message': text})
        except ValueError:
            pass
        else:
            assert False, 'embedded credential accepted'
    try:
        ensure_safe(data)
    except ValueError:
        pass
    else:
        assert False, 'secret write accepted'
    assert request('https://example.invalid', credentials_required=True)['reason_code'] == 'AUTH_MISSING'
    with patch('urllib.request.OpenerDirector.open', side_effect=HTTPError('https://example.invalid', 422, 'error', {}, io.BytesIO(b'{"message":"Price change"}'))):
        result = request('https://example.invalid')
        assert result['http_status'] == 422 and result['body']['message'] == 'Price change'
    with patch('urllib.request.OpenerDirector.open', side_effect=HTTPError('https://example.invalid', 302, 'redirect', {'Location': 'https://other.invalid'}, io.BytesIO(b'not json'))):
        result = request('https://example.invalid')
        assert result['body'] == {'raw': 'not json'} and result['http_status'] == 302
    assert request('http://example.invalid')['reason_code'] == 'TRANSPORT_ERROR'
    assert request('https://example.invalid', verify_tls=False)['reason_code'] == 'SCOPE_BLOCKED'
    from bb.transport import NoRedirect
    assert NoRedirect().redirect_request(None, None, 302, '', {}, '') is None
    from unittest.mock import MagicMock
    import ssl
    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = b'{"results":[]}'
    with patch('urllib.request.build_opener') as factory:
        factory.return_value.open.return_value = response
        result = request('https://example.invalid', context={'inventory_field': 'results'})
        handler = factory.call_args.args[1]
        assert handler._context.verify_mode == ssl.CERT_REQUIRED
        assert result['status'] == 'WARN' and result['reason_code'] == 'NO_DATA'
        assert factory.return_value.open.call_count == 1
    with patch('urllib.request.build_opener') as factory:
        factory.return_value.open.return_value = response
        request('https://example.invalid', verify_tls=False, tls_bypass_authorized=True)
        assert factory.call_args.args[1]._context.verify_mode == ssl.CERT_NONE
    for url in ('https://example.invalid/ndc/v1/book/create', 'https://example.invalid/ndc/v1/ticket/issue'):
        assert request(url)['reason_code'] == 'SCOPE_BLOCKED'


def test_lessons_and_loop():
    from bb.lessons import Store, allowed_action
    from bb.escalations import Escalations, handle_outcome
    from bb.report import summarize
    config = {'promotion_successes': 2, 'deprecation_failures': 2, 'max_retries': 1, 'max_steps': 3}
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / 'lessons.jsonl', config)
        escalations = Escalations(Path(tmp) / 'escalations.jsonl', store)
        fields = dict(tags=['search', 'dev'], trigger_pattern='empty inventory', situation='No inventory available',
                      action='report_warn', outcome='Preserve inconclusive evidence', created_run='first',
                      scope_conditions={'environment': 'dev', 'route': 'AAA-BBB'})
        lesson = store.propose(**fields)
        assert store.search(['search'], 'empty inventory')[0]['id'] == lesson['id']
        store.record_use(lesson['id'], True, 'reuse1')
        assert store.latest()[lesson['id']]['status'] == 'candidate'
        store.record_use(lesson['id'], True, 'reuse2')
        assert store.latest()[lesson['id']]['status'] == 'trusted'
        other = store.propose(**{**fields, 'action': 'check_prerequisites'})
        store.record_use(other['id'], False, 'reuse3')
        matches = store.search(['search'], 'empty inventory')
        assert matches[0]['id'] == lesson['id'] and matches[0]['review_required']
        store.record_use(other['id'], False, 'reuse4')
        assert store.latest()[other['id']]['status'] == 'deprecated'
        assert not allowed_action({**lesson, 'action': 'retry'}, {'allow_retry': False}, config)
        assert not allowed_action({**lesson, 'action': 'retry'}, {'allow_retry': True}, config, retries=1)
        assert not allowed_action(lesson, {'environment': 'other', 'route': 'AAA-BBB'}, config)
        assert not allowed_action(lesson, {}, config, steps=3)
        for field in ({'tolerance': 1}, {'action': 'book/create'}, {'action': 'bypass_tls'}, {'expected_result': 'PASS'}):
            try:
                store.propose(**{**fields, **field})
            except ValueError:
                pass
            else:
                assert False, 'forbidden learning accepted'
        # A separate route starts without a trusted match. No network requests.
        scope = {'environment': 'dev', 'route': 'CCC-DDD'}
        outcome = {'reason_code': 'NO_DATA', 'status': 'WARN', 'retryable': False}
        with patch('bb.transport.request', return_value=outcome) as mocked:
            from bb.transport import request
            result = request('https://example.invalid')
            first = handle_outcome(store, escalations, result, 'run1', ['search'], 'empty inventory', scope)
            again = handle_outcome(store, escalations, result, 'run1', ['search'], 'empty inventory', scope)
            assert first['escalation_id'] == again['escalation_id']
            escalations.answer(first['escalation_id'], 'Preserve evidence and report unavailable inventory',
                               action='report_warn', scope_conditions=scope)
            second = handle_outcome(store, escalations, request('https://example.invalid'), 'run2', ['search'], 'empty inventory', scope)
            assert mocked.call_count == 2
        assert second['lesson_id'] and second['status'] == 'WARN' and not second.get('escalation_id')
        store.record_use(second['lesson_id'], True, 'run2')
        summary = summarize(store, escalations)
        assert summary['runs']['run1']['escalated'] and not summary['runs']['run2']['escalated']
        assert summary['tasks_by_status']['WARN'] == 2
        assert list(summary['weekly'].values())[0]['escalation_rate'] == 0.5
        assert len([e for e in escalations.events() if e['event'] == 'question']) == 1


if __name__ == '__main__':
    for test in (test_classification, test_security_transport, test_lessons_and_loop):
        test()
        print(test.__name__ + ': PASS')
