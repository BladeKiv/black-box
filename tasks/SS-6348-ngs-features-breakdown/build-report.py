import base64
import csv
import html
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8-sig'))
def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

meta = read('run-metadata.json')
results = read('search-evidence.json')
# Keep only response fields needed to reproduce and diagnose the ticket.
segment_fields = ['segmentId', 'departureTime', 'arrivalTime', 'flightNumber',
                  'marketingAirline', 'departureAirportCode', 'arrivalAirportCode', 'brandId', 'brandName']
for result in results:
    for trip in result['trips']:
        segments = [{k: s[k] for k in segment_fields if k in s} for s in trip['segments']]
        trip_id = trip['tripId']
        trip.clear()
        trip.update(tripId=trip_id, segments=segments)
save('search-evidence.json', results)

expected = ['1:2', '2:1']
fixture_flights = [['PR105', 'PR2813'], ['PR2818', 'PR104']]
matches = [r for r in results if [[s['marketingAirline'] + s['flightNumber'] for s in t['segments']] for t in r['trips']] == fixture_flights]
assert matches, 'Ticket itinerary unavailable: requires WARN handling before reporting.'
fixture = matches[0]
features = fixture['ngsFeatures']['list']
assert features, 'No fixture features available.'
violations = []
reference_count = 0
feature_count = 0
for index, result in enumerate(results):
    for fi, feature in enumerate(result.get('ngsFeatures', {}).get('list', [])):
        feature_count += 1
        for reference in feature.get('breakdown', []):
            reference_count += 1
            match = re.fullmatch(r'([1-9]\d*):([1-9]\d*)', reference)
            valid = False
            if match:
                ti, si = map(int, match.groups())
                valid = ti <= len(result['trips']) and si <= len(result['trips'][ti - 1]['segments'])
            if not valid:
                violations.append({'result_index': index, 'key': result['key'], 'feature_index': fi,
                                   'feature_id': feature['id'], 'reference': reference})
bad_results = len({v['result_index'] for v in violations})
cases = [
    {'id': 'TC-01', 'data': 'Ticket itinerary: PR105 / PR2813; PR2818 / PR104. S/8KI0, GTT102, 1 ADT, cabin Y, fare SR.',
     'expected': 'Affected COMFORT CLASS feature breakdowns equal ["1:2","2:1"].',
     'actual': f'{len(matches)} matching itinerary; {len(features)} features. Breakdown values: ' + json.dumps([f['breakdown'] for f in features]) + '. Trip IDs: [1,2].',
     'status': 'PASS' if all(f.get('breakdown') == expected for f in features) else 'FAIL'},
    {'id': 'TC-02', 'data': f'All {len(results)} results from the same ticket Search; {feature_count} features, {reference_count} breakdown references.',
     'expected': 'Every returned breakdown reference resolves to an existing trip and segment using confirmed one-based numbering.',
     'actual': f'{len(violations)} invalid references across {bad_results}/{len(results)} results.',
     'status': 'FAIL' if violations else ('PASS' if reference_count else 'WARN')}
]
save('test-results.json', {'cases': cases, 'reference_count': reference_count, 'feature_count': feature_count,
                         'invalid_reference_count': len(violations), 'affected_result_count': bad_results})
save('invalid-references.json', violations)
sample = {'request': meta['request'], 'response': {'http_status': meta['http_status'],
          'body_excerpt': {'count': meta['count'], 'results': [fixture]}},
          'note': 'Response excerpt; unrelated fields omitted. Key preserved exactly as returned.'}
save('latest-evidence.json', sample)

regressions = []
for path in sorted((ROOT / 'regression').glob('TC-*.json')):
    run = json.loads(path.read_text(encoding='utf-8-sig'))
    assert 'val_cr=' not in run['request']['url'], 'Regression must not restrict validating airline'
    options = run['response'].get('body_excerpt', {}).get('results', [])
    invalid = []
    refs = 0
    covered = 0
    by_carrier = {}
    feature_list_states = {}
    for ri, option in enumerate(options):
        carrier = option.get('validatingCarrier', '(missing)')
        stats = by_carrier.setdefault(carrier, {'results': 0, 'features': 0, 'references': 0})
        stats['results'] += 1
        option_refs = 0
        ngs = option.get('ngsFeatures')
        if 'ngsFeatures' not in option:
            state = 'ngsFeatures missing'
        elif ngs is None:
            state = 'ngsFeatures null'
        elif 'list' not in ngs:
            state = 'list missing'
        elif ngs['list'] is None:
            state = 'list null'
        elif ngs['list'] == []:
            state = 'list empty array'
        else:
            state = 'list populated'
        feature_list_states[state] = feature_list_states.get(state, 0) + 1
        for fi, feature in enumerate((ngs or {}).get('list') or []):
            stats['features'] += 1
            for ref in feature.get('breakdown', []):
                refs += 1
                option_refs += 1
                stats['references'] += 1
                match = re.fullmatch(r'([1-9]\d*):([1-9]\d*)', ref) if isinstance(ref, str) else None
                valid = False
                if match:
                    ti, si = map(int, match.groups())
                    trips = option.get('trips', [])
                    valid = ti <= len(trips) and si <= len(trips[ti - 1].get('segments', []))
                if not valid:
                    invalid.append({'result_index': ri, 'key': option.get('key'), 'feature_index': fi, 'reference': ref})
        covered += bool(option_refs)
    status = 'FAIL' if invalid else ('PASS' if refs else 'WARN')
    case = {'id': run['scenario_id'],
            'data': f'{run["origin"]}–{run["destination"]} return; {run["outbound_date"]} / {run["return_date"]}. S/8KI0, GTT102, 1 ADT, Y, SR; no val_cr.',
            'expected': 'Every returned breakdown reference resolves to an existing trip and segment using one-based numbering; at least one reference is required for a conclusive check.',
            'actual': f'{len(options)} results; {covered} with breakdown references; {refs} references; {len(invalid)} invalid. Validating carriers: ' + ', '.join(sorted(by_carrier)) + '.',
            'status': status}
    run.update(case=case, reference_count=refs, covered_result_count=covered, invalid_references=invalid, by_carrier=by_carrier, feature_list_states=feature_list_states)
    regressions.append(run)
    cases.append(case)
save('regression-results.json', [{k: v for k, v in r.items() if k != 'response'} for r in regressions])
save('test-results.json', {'cases': cases, 'reference_count': reference_count + sum(r['reference_count'] for r in regressions),
                         'invalid_reference_count': len(violations) + sum(len(r['invalid_references']) for r in regressions),
                         'baseline_run_utc': meta['run_utc'], 'regression_runs': [r['run_utc'] for r in regressions]})

tests = r'''const data = pm.response.json();
const get = name => pm.iterationData.get(name) || pm.collectionVariables.get(name);
const expected = JSON.parse(get('expected_breakdown'));
const flights = JSON.parse(get('fixture_flights'));
const ids = JSON.parse(get('feature_ids'));
const results = Array.isArray(data.results) ? data.results : [];
const matches = results.filter(r => JSON.stringify((r.trips || []).map(t => (t.segments || []).map(s => s.marketingAirline + s.flightNumber))) === JSON.stringify(flights));
const features = matches.flatMap(r => (r.ngsFeatures?.list || []).filter(f => ids.includes(f.id)));
if (get('check_fixture') === 'true') {
if (!features.length || ids.some(id => !features.some(f => f.id === id))) {
  pm.test.skip('TC-01 WARN: ticket itinerary or affected features unavailable', () => {});
} else {
  pm.test('TC-01: ticket feature breakdown equals expected trip:segment pairs', () => {
    features.forEach(f => pm.expect(f.breakdown).to.eql(expected));
  });
}
}
const invalid = [];
let references = 0;
results.forEach((r, ri) => (r.ngsFeatures?.list || []).forEach((f, fi) => (f.breakdown || []).forEach(ref => {
  references++;
  const m = /^([1-9]\d*):([1-9]\d*)$/.exec(ref);
  if (!m || !r.trips?.[Number(m[1])-1]?.segments?.[Number(m[2])-1]) invalid.push({result_index:ri, feature_index:fi, reference:ref, key:r.key});
})));
const caseId = get('reference_case_id');
if (!references) {
  pm.test.skip(caseId + ' WARN: no breakdown references available', () => {});
} else {
  pm.test(caseId + ': every breakdown references an existing trip and segment', () => pm.expect(invalid).to.eql([]));
}
console.log('SS-6348 evidence summary', {results:results.length, matchingItineraries:matches.length, references, invalid});
'''
setup = "if (!pm.variables.get('authorization')) throw new Error('Set the authorization variable locally to the supplied full Basic header.');\nconst url = pm.iterationData.get('search_url') || pm.collectionVariables.get('search_url');\npm.variables.set('effective_search_url', url);"
defaults = {'scenario_id': 'SS6348-SEARCH', 'expected_result': 'Valid one-based trip:segment references; affected ticket features use ["1:2","2:1"].',
            'provider_filter': 'S/8KI0', 'search_url': meta['request']['url'],
            'fixture_flights': json.dumps(fixture_flights), 'feature_ids': json.dumps([f['id'] for f in features]),
            'expected_breakdown': json.dumps(expected), 'check_fixture': 'true', 'reference_case_id': 'TC-02'}
collection = {'info': {'name': 'SS-6348 ngsFeatures breakdown — AirAPI Search',
                       'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
                       'description': 'Search-only ticket reproduction. Set local authorization to the full Basic header. Run with the matching CSV. WARN means skipped due to unavailable inventory; do not interpret skipped assertions as PASS. Keys remain opaque. TC-01 expected pair applies only to the listed ticket flights and feature IDs.'},
              'variable': [{'key': k, 'value': v} for k, v in defaults.items()],
              'item': [{'name': 'Ticket Search — TC-01 and TC-02',
                        'event': [{'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': setup.splitlines()}},
                                  {'listen': 'test', 'script': {'type': 'text/javascript', 'exec': tests.splitlines()}}],
                        'request': {'method': 'GET', 'header': [{'key': 'Authorization', 'value': '{{authorization}}'}],
                                    'url': '{{effective_search_url}}'}}]}
save('SS-6348.postman_collection.json', collection)
stream = io.StringIO(newline='')
writer = csv.DictWriter(stream, fieldnames=list(defaults))
writer.writeheader()
writer.writerow(defaults)
for run in regressions:
    writer.writerow({**defaults, 'scenario_id': run['scenario_id'], 'search_url': run['request']['url'],
                     'expected_result': run['case']['expected'], 'check_fixture': 'false', 'reference_case_id': run['scenario_id']})
csv_text = stream.getvalue()
(ROOT / 'SS-6348.expected-outcomes.csv').write_text(csv_text, encoding='utf-8')

plan = '''# SS-6348 proposed implementation and verification plan

Intended behavior: `results[].ngsFeatures.list[].breakdown[]` must identify existing segments using one-based `trip:segment` references. The user confirmed this interpretation. For the ticket itinerary, the affected features must contain `["1:2","2:1"]`.

1. Use the saved Search fixture to establish a failing regression for the two-trip, four-segment itinerary: PR105 / PR2813, then PR2818 / PR104. Preserve each fresh Search key verbatim.
2. Developer task: trace where NGS breakdown references are constructed relative to the final response trips. Identify why this itinerary emits trip numbers 2 and 3 when the response contains trips 1 and 2. Black-box evidence establishes the mismatch, not its internal cause.
3. Correct the reference construction at the responsible mapping point so it uses the final response's one-based trip and segment numbering. Do not apply an unconditional subtraction to all output references; first verify the numbering source. Keep each feature attached to its intended segment.
4. Verify the fixture produces `["1:2","2:1"]` for the affected feature IDs. Check all returned breakdown references against existing trips and segments in the same Search response.
5. Deploy through the normal developer workflow, rerun the supplied AirAPI-only collection on the agreed host, and replace the failure evidence only with a separately recorded confirmed run. A missing itinerary or affected feature is WARN, not PASS.

Scope: original ticket Search plus five user-requested regression Searches. The regressions omit val_cr to include other airlines. No application source was inspected and no fix or deployment was performed during QA.

Run artifacts: set the Postman `authorization` variable locally to the supplied full Basic header; import the collection and CSV. Run all six CSV rows: the baseline row evaluates TC-01 and TC-02; each additional row evaluates its own reference-validity case without applying the ticket-specific flight pair. The collection uses `pm.test.skip` with a WARN label when inventory is unavailable; skipped checks are inconclusive.

HTTP status is recorded as an observation, not an invented ticket acceptance criterion. Prior run evidence is retained under runs/; current reports describe only the latest run.
'''
(ROOT / 'implementation-plan.md').write_text(plan, encoding='utf-8')
signal = 'FAIL' if any(c['status'] == 'FAIL' for c in cases) else ('WARN' if any(c['status'] == 'WARN' for c in cases) else 'PASS')
summary = f'Retest on airapi51: {signal}. The ticket itinerary contains {len(features)} affected features; exact expected breakdown ["1:2","2:1"] check: {cases[0]["status"]}. Across {len(results)} results and {reference_count} references, {len(violations)} references are invalid in {bad_results} results.'
if regressions:
    summary += f' Added {len(regressions)} Searches without val_cr: {sum(len(r["response"].get("body_excerpt", {}).get("results", [])) for r in regressions)} results, {sum(r["reference_count"] for r in regressions)} references, {sum(len(r["invalid_references"]) for r in regressions)} invalid. The original retest is retained from {meta["run_utc"]}; additional run times are recorded below. Missing optional features are not counted as validated references.'
table = '\n'.join('| ' + ' | '.join(str(c[k]).replace('|', '\\|') for k in ['id','data','expected','actual','status']) + ' |' for c in cases)
md = f'''# SS-6348 — ngsFeatures incorrect breakdown

Release signal: **{signal}**

Run: {meta['run_utc']} | {meta['request']['url'].split('/v1')[0]} | Search only | S/8KI0 | SFO–DVO 2026-10-23 / DVO–SFO 2026-11-24 | HTTP {meta['http_status']} | {meta['elapsed_seconds']:.2f}s

{summary}

Intended behavior: breakdown references identify existing trips and segments using confirmed one-based numbering. The ticket fixture expects `["1:2","2:1"]`.

| ID | Test data | Expected | Actual | Status |
|---|---|---|---|---|
{table}

## TC-01 and TC-02 paired request/response evidence

The following reduced response supports the current results; unrelated fields and authorization are omitted. Earlier run artifacts are preserved under runs/.

```json
{json.dumps(sample, indent=2)}
```

Full reduced response: `search-evidence.json`. Complete invalid-reference list: `invalid-references.json`.
Rerun: `SS-6348.postman_collection.json` with `SS-6348.expected-outcomes.csv` and a locally supplied authorization variable.
Proposed fix and verification: `implementation-plan.md`.
Source: https://traveldev.atlassian.net/browse/SS-6348. The Jira attachment is historical context, not fresh execution evidence.
'''
regression_details = []
for run in regressions:
    excerpt = run['response']
    if run['invalid_references']:
        indices = sorted({v['result_index'] for v in run['invalid_references']})[:3]
        excerpt = {**excerpt, 'body_excerpt': {'results': [excerpt['body_excerpt']['results'][i] for i in indices]}}
    elif run['reference_count']:
        excerpt = {'http_status': run['response'].get('http_status'), 'by_carrier': run['by_carrier'], 'feature_list_states': run['feature_list_states']}
    detail = {'id': run['scenario_id'], 'run_utc': run['run_utc'], 'elapsed_seconds': run['elapsed_seconds'],
              'request': run['request'], 'response': excerpt}
    regression_details.append(detail)
    md += '\n### ' + run['scenario_id'] + ' regression evidence\n\n```json\n' + json.dumps(detail, indent=2) + '\n```\n'
(ROOT / 'report.md').write_text(md, encoding='utf-8')

template = (ROOT.parents[1] / 'templates/airapi-qa-dispatch-template.html').read_text(encoding='utf-8')
e = html.escape
rendered = template.replace('&lt;Ticket title&gt;', 'SS-6348 · NGS breakdown')
rendered = rendered.replace('&lt;YYYY-MM-DD&gt;', e(meta['run_utc']))
rendered = rendered.replace('&lt;Endpoint / route / scope&gt;', 'airapi51 · Search · S/8KI0 · original retest + 5 airline-unrestricted Searches' if regressions else 'airapi51 · Search · SFO–DVO return · S/8KI0')
rendered = rendered.replace('&lt;PASS / FAIL / WARN&gt;', signal).replace('class="value fail">' + signal, 'class="value ' + signal.lower() + '">' + signal)
for status in ['PASS', 'FAIL', 'WARN']:
    rendered = rendered.replace('&lt;0&gt;', str(sum(c['status'] == status for c in cases)), 1)
rendered = rendered.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;', e(summary) + '<br><strong>Intended behavior:</strong> one-based trip:segment references; ticket fixture expects <code>["1:2","2:1"]</code>.')
rows = ''.join(f'<tr><td>{c["id"]}</td><td class="test">{e(c["data"])}</td><td>{e(c["expected"])} → {e(c["actual"])}</td><td class="status {c["status"].lower()}">{c["status"]}</td></tr>' for c in cases)
rendered = re.sub(r'<tbody>.*?</tbody>', '<tbody>' + rows + '</tbody>', rendered, flags=re.S)
rendered = rendered.replace('&lt;WARN or FAIL test ID&gt;', 'TC-01 / TC-02')
rendered = rendered.replace('&lt;Minimal confirmed explanation of the inconclusive or failing outcome.&gt;', 'Fresh response excerpt supporting the current results. Authorization and unrelated fields are omitted; the key is preserved exactly. Earlier run evidence is retained under runs/.')
rendered = rendered.replace('&lt;exact request method, URL, headers excluding secrets, and payload&gt;', e(json.dumps(sample['request'], indent=2)))
rendered = rendered.replace('&lt;relevant response payload showing the outcome&gt;', e(json.dumps(sample['response'], indent=2)))
if signal == 'PASS':
    rendered = re.sub(r'<section class="failure-sample">.*?</section>', '', rendered, flags=re.S)
for detail in regression_details:
    section = '<section class="evidence"><div><h2>' + detail['id'] + ' · Request and coverage</h2><p>' + e(detail['run_utc']) + '</p><details><summary>Exact request and response evidence</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere">' + e(json.dumps(detail, indent=2)) + '</pre></details></div></section>'
    rendered = rendered.replace('</article>', section + '</article>')
rendered = rendered.replace('&lt;Response count, exact field paths, and other confirmed API facts.&gt;', e(f'HTTP {meta["http_status"]}; {len(results)} results; {feature_count} features; {reference_count} references. Path: results[].ngsFeatures.list[].breakdown[]. {len(violations)} invalid references in {bad_results} results. See implementation-plan.md for the proposed fix and rerun plan.'))
for label, filename in [('collection', 'SS-6348.postman_collection.json'), ('csv', 'SS-6348.expected-outcomes.csv')]:
    rendered = rendered.replace(f'&lt;{label}-file-name&gt;', filename).replace(f'<{label}-file-name>', filename)
    encoded = base64.b64encode((ROOT / filename).read_bytes()).decode()
    rendered = rendered.replace(f'<{label}-base64>', encoded)
assert not re.search(r'&lt;[^;]+&gt;', rendered), 'Unfilled template token'
(ROOT / 'report.html').write_text(rendered, encoding='utf-8')
print(json.dumps({'cases': cases, 'artifacts': sorted(p.name for p in ROOT.iterdir())}, indent=2))
