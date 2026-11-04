"""Build artifacts from saved evidence; never sends requests."""
import base64
import csv
import html
import json
import re
from pathlib import Path
from bb.classify import classify_outcome

P = Path(__file__).resolve().parent
TITLE = 'SS-6445 /v1/commission/rules - possibility to request specific rules'


def normalize(value, path=()):
    if isinstance(value, dict):
        return {k: normalize(v, path + (k,)) for k, v in value.items()}
    if isinstance(value, list):
        if len(path) >= 2 and path[-2:] in [('Airlines', 'Marketing'), ('Airlines', 'Operating')]:
            return sorted(value)
        return [normalize(v, path) for v in value]
    return value


def rules(body):
    return {r['Id']: r for group in body['rules'].values() for r in group}


def main():
    assert normalize({'Airlines': [{'Operating': ['BA', 'AA', 'BA']}]}) == {'Airlines': [{'Operating': ['AA', 'BA', 'BA']}]}
    assert normalize({'other': [2, 1]}) == {'other': [2, 1]}
    baseline = rules(json.loads((P / 'baseline-network-check.json').read_text())['response']['body'])
    rows = json.loads((P / 'results.json').read_text())
    for row in rows:
        evidence = json.loads((P / (row['id'] + '.json')).read_text())
        actual = rules(evidence['response']['body'])
        expected = {i: baseline[i] for i in row['ids']}
        row['full_content_matches'] = normalize(actual) == normalize(expected)
        row.update(classify_outcome(evidence['response']['http_status'], json.dumps(evidence['response']['body']),
                                   evidence['response']['transport_error'],
                                   {'inventory_field': None, 'expectation_observed': row['full_content_matches']}))
    (P / 'results.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    counts = {s: sum(r['status'] == s for r in rows) for s in ['PASS', 'FAIL', 'WARN']}
    # The documented sample is retained as WARN because its IDs are not present in this DEV baseline.
    counts['WARN'] += 1
    signal = 'FAIL' if counts['FAIL'] else 'WARN'
    csv_name = 'expected-outcomes.csv'
    with (P / csv_name).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['scenario_id', 'expected_result', 'provider_filter', 'search_url', 'ids_json', 'rules_path', 'rule_id_field'])
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(scenario_id=row['id'], expected_result='exact requested IDs and baseline content', provider_filter='',
                                 search_url='https://api.search.dev.travel-dev.com/v1/commission/rules/search',
                                 ids_json=json.dumps(row['ids']), rules_path='rules', rule_id_field='Id'))
    setup = "const ids = pm.iterationData.get('ids_json') || '[8378]'; JSON.parse(ids); pm.variables.set('ids_json', ids); pm.variables.set('search_url', pm.iterationData.get('search_url') || pm.environment.get('searchhost') + '/v1/commission/rules/search');"
    test = """const body = pm.response.json();
const path = pm.iterationData.get('rules_path') || 'rules';
const field = pm.iterationData.get('rule_id_field') || 'Id';
const grouped = path.split('.').reduce((v,k) => v[k], body);
const actual = Object.values(grouped).flat();
const ids = JSON.parse(pm.variables.get('ids_json'));
pm.test('Successful HTTP response', () => pm.expect(pm.response.code).to.be.within(200,299));
pm.test('Exactly the requested IDs', () => pm.expect(actual.map(r=>r[field]).sort((a,b)=>a-b)).to.eql(ids.slice().sort((a,b)=>a-b)));
const baseline = JSON.parse(pm.collectionVariables.get('baseline_rules'));
function norm(v, path=[]) {
 if (Array.isArray(v)) {
  const pair=path.slice(-2).join('.');
  if (pair==='Airlines.Marketing' || pair==='Airlines.Operating') return v.slice().sort();
  return v.map(x=>norm(x,path));
 }
 if (v && typeof v==='object') return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,norm(x,path.concat(k))]));
 return v;
}
pm.test('Rule content equals baseline with approved airline-code ordering comparator', () => {
 actual.forEach(r => pm.expect(norm(r)).to.eql(norm(baseline[r[field]])));
});"""
    collection = {'info': {'name': TITLE, 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
                            'description': 'Read-only DEV rule lookup. Run with matching CSV. Set search_authorization securely in the selected environment. Saved baseline comparison is dated 2026-11-03; later configuration changes require a reviewed new baseline.'},
                  'auth': {'type': 'bearer', 'bearer': [{'key': 'token', 'value': '{{search_authorization}}', 'type': 'string'}]},
                  'variable': [{'key': 'baseline_rules', 'value': json.dumps({str(i): baseline[i] for row in rows for i in row['ids']})}],
                  'item': [{'name': 'Requested commission rules', 'event': [
                      {'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': [setup]}},
                      {'listen': 'test', 'script': {'type': 'text/javascript', 'exec': test.splitlines()}}],
                      'request': {'method': 'POST', 'header': [{'key': 'Content-Type', 'value': 'application/json'}],
                                  'url': '{{search_url}}', 'body': {'mode': 'raw', 'raw': '{"ids": {{ids_json}}}', 'options': {'raw': {'language': 'json'}}}}}]}
    collection_name = 'SS-6445.postman_collection.json'
    (P / collection_name).write_text(json.dumps(collection, indent=2), encoding='utf-8')
    expected_text = 'Exactly requested IDs; matching rule content, comparing Marketing/Operating code membership and counts.'
    report_rows = [(r['id'], json.dumps(r['ids']), expected_text,
                    f"HTTP {r['http_status']}; returned {r['returned_ids']}; content {'matches' if r['full_content_matches'] else 'differs'}.", r['status']) for r in rows]
    report_rows.append(('TC-06', '[563, 1900] (ticket sample)', 'Retrieve documented sample rules when available.',
                        'HTTP 200; rules={}; neither ID is present in DEV baseline (NO_DATA).', 'WARN'))
    summary = 'All five available-ID lookups returned exactly the requested rules and matching content under the user-approved airline-code comparator. The documented sample IDs are unavailable on DEV.'
    intended = 'POST /v1/commission/rules/search retrieves specified top-level commission rule Id values supplied in the JSON ids array.'
    strip = '2026-11-03 · DEV · 1 successful baseline GET + 6 POST lookups · no application retries'
    sample = json.loads((P / 'ticket-example.json').read_text())
    request_text = json.dumps(sample['request'], indent=2)
    response_text = json.dumps({'http_status': sample['response']['http_status'], 'body': sample['response']['body']}, indent=2)
    md = f'# {TITLE}\n\nRelease signal: {signal} — {counts["PASS"]} PASS / {counts["FAIL"]} FAIL / {counts["WARN"]} WARN\n\n{strip}\n\n{summary}\n\nIntended behavior: {intended}\n\n| ID | Test data | Expected result | Actual result | Status |\n|---|---|---|---|---|\n'
    md += '\n'.join('| ' + ' | '.join(row) + ' |' for row in report_rows)
    md += '\n\nTC-06 paired evidence\n\nRequest:\n```json\n' + request_text + '\n```\nResponse:\n```json\n' + response_text + '\n```\n'
    md += '\nEvidence: TC-01.json through TC-05.json, ticket-example.json, baseline-network-check.json. Original strict comparisons were re-evaluated from saved responses after user approved unordered Marketing/Operating arrays; no fresh requests. All other arrays, missing fields and value types remain exact. Initial sandbox refusal is retained in baseline.json as an operational incident, superseded by the successful network-access baseline. Lessons search found none; none applied.\n\nExcluded: malformed/empty/duplicate/unknown-ID behavior, ordering requirements, performance, other environments, flight Search and booking. No ledger update. Postman baseline is a dated snapshot.\n'
    (P / 'qa-report.md').write_text(md, encoding='utf-8')
    t = Path('templates/airapi-qa-dispatch-template.html').read_text(encoding='utf-8')
    t = t.replace('&lt;Ticket title&gt;', html.escape(TITLE))
    t = t.replace('Run &lt;YYYY-MM-DD&gt;<br>&lt;Endpoint / route / scope&gt;', html.escape(strip))
    t = t.replace('class="value fail">&lt;PASS / FAIL / WARN&gt;', 'class="value ' + signal.lower() + '">' + signal)
    for status, num in counts.items():
        t = t.replace(f'class="value {status.lower()}">&lt;0&gt;', f'class="value {status.lower()}">{num}')
    t = t.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;', html.escape(summary + ' Intended behavior: ' + intended))
    table = ''.join('<tr><td>' + html.escape(a) + '</td><td class="test">' + html.escape(b) + '</td><td>' + html.escape(c + ' → ' + d) + '</td><td class="status ' + e.lower() + '">' + e + '</td></tr>' for a,b,c,d,e in report_rows)
    t = re.sub(r'<tbody>.*?</tbody>', '<tbody>' + table + '</tbody>', t, flags=re.S)
    t = t.replace('&lt;WARN or FAIL test ID&gt;', 'TC-06').replace('&lt;Minimal confirmed explanation of the inconclusive or failing outcome.&gt;', 'NO_DATA: documented sample IDs are absent from this DEV baseline.')
    t = t.replace('&lt;exact request method, URL, headers excluding secrets, and payload&gt;', html.escape(request_text)).replace('&lt;relevant response payload showing the outcome&gt;', html.escape(response_text))
    t = t.replace('&lt;Response count, exact field paths, and other confirmed API facts.&gt;', html.escape('Baseline: 16 rules in rules.81 and rules.95. IDs: rules[group][].Id. Five positive checks; identical content except approved Marketing/Operating array permutations. No speculative edge cases, booking, performance or other environments tested. See ticket-scope.md and saved paired evidence. Initial sandbox refusal resolved with network access; no lesson applied.'))
    for placeholder, name in [('collection', collection_name), ('csv', csv_name)]:
        t = t.replace('&lt;' + placeholder + '-file-name&gt;', name).replace('<' + placeholder + '-file-name>', name)
        t = t.replace('<' + placeholder + '-base64>', base64.b64encode((P / name).read_bytes()).decode())
    assert '&lt;' not in t and '<collection-' not in t
    (P / 'qa-report.html').write_text(t, encoding='utf-8')
    print(json.dumps({'signal': signal, **counts}))


if __name__ == '__main__':
    main()
