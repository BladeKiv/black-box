"""Ticket-scoped read-only checks; explicit execution required, no retries."""
import json
from pathlib import Path
from bb.transport import request
from bb.classify import classify_outcome
from bb.lessons import Store
from bb.escalations import Escalations, handle_outcome
from build_report import normalize

FOLDER = Path(__file__).resolve().parent
CASES = [[8378], [7839], [8378, 8379], [7839, 7840], [8378, 7839]]


def flatten(body):
    rules = body['rules']
    assert isinstance(rules, dict)
    items = [rule for group in rules.values() for rule in group]
    assert all(type(rule['Id']) is int for rule in items)
    assert len({rule['Id'] for rule in items}) == len(items)
    return {rule['Id']: rule for rule in items}


def main():
    assert flatten({'rules': {'a': [{'Id': 1}], 'b': [{'Id': 2}]}}) == {1: {'Id': 1}, 2: {'Id': 2}}
    assert flatten({'rules': {}}) == {}
    refs = json.loads(Path('knowledge/local-environment-references.json').read_text())
    env = json.loads(Path(refs['dev']).read_text(encoding='utf-8-sig'))
    values = {item['key']: item.get('value') for item in env['values'] if item.get('enabled', True)}
    host = values['searchhost'].rstrip('/')
    assert host == 'https://api.search.dev.travel-dev.com'
    baseline = flatten(json.loads((FOLDER / 'baseline-network-check.json').read_text())['response']['body'])
    results = []
    for index, ids in enumerate(CASES, 1):
        assert all(item in baseline for item in ids)
        case = f'TC-{index:02}'
        body = {'ids': ids}
        url = host + '/v1/commission/rules/search'
        response = request(url, method='POST', data=json.dumps(body).encode(),
                           headers={'Authorization': values['search_authorization'], 'Content-Type': 'application/json'},
                           timeout=60, verify_tls=False, tls_bypass_authorized=True, credentials_required=True,
                           allowed_endpoint=('POST', '/v1/commission/rules/search'), context={'inventory_field': None})
        actual = None
        try:
            actual = flatten(response['body'])
            observed = normalize(actual) == normalize({item: baseline[item] for item in ids})
        except (KeyError, TypeError, AssertionError):
            observed = False
        outcome = classify_outcome(response['http_status'], json.dumps(response['body']), response['transport_error'],
                                   {'inventory_field': None, 'expectation_observed': observed})
        if outcome['status'] != 'PASS':
            handle_outcome(Store(), Escalations(), outcome, 'SS-6445-2026-11-03-' + case,
                           ['SS-6445', 'dev'], 'requested top-level rule subset mismatch',
                           {'ticket': 'SS-6445', 'environment': 'dev', 'endpoint': 'POST /v1/commission/rules/search',
                            'allow_retry': False, 'allow_poll': False, 'allow_retest': False, 'approved_inputs': []},
                           retries=0, steps=1)
        evidence = {'request': {'method': 'POST', 'url': url, 'body': body}, 'response': response}
        (FOLDER / (case + '.json')).write_text(json.dumps(evidence, indent=2), encoding='utf-8')
        row = {'id': case, 'ids': ids, 'http_status': response['http_status'],
               'returned_ids': list(actual) if actual is not None else None,
               'full_content_matches': observed, **outcome}
        results.append(row)
        print(json.dumps(row), flush=True)
    (FOLDER / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
