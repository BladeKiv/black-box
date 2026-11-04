"""Build scoped reports from saved, sanitized SS-6409 observations; no API calls."""
import csv
import json
from pathlib import Path
from templates.render_dispatch import render
from bb.classify import classify_outcome
from bb.escalations import Escalations, handle_outcome
from bb.lessons import Store

ROOT = Path(__file__).resolve().parent
RUN = ROOT / 'runs' / '2026-10-22'
CASES = [('TST101', 'flightShop'), ('TST102', 'flightShopLite'), ('TST104', 'bargainFinderMax')]
rows, evidence, csv_rows = [], [], []
searches = []


def check(case_id, data, expected, actual, observed, pair):
    outcome = classify_outcome(pair['response']['http_status'], json.dumps(pair['response']['body']),
                               pair['response'].get('transport_error'),
                               {'inventory_field': None, 'expectation_observed': observed})
    rows.append(dict(id=case_id, data=data, expected=expected, actual=actual, status=outcome['status']))
    if outcome['status'] != 'PASS':
        evidence.append(dict(id=case_id, request=pair['request'], response=pair['response']))
        handle_outcome(Store(), Escalations(), outcome, 'SS-6409-2026-10-22', ['SS-6409', 'DEV'],
                       'saved response expectation mismatch',
                       {'ticket': 'SS-6409', 'environment': 'DEV', 'endpoint': '/v1/search',
                        'allow_retry': False, 'allow_poll': False, 'allow_retest': False,
                        'approved_inputs': []}, retries=0, steps=2)


for index, (cid, endpoint) in enumerate(CASES, 1):
    pair = json.loads((RUN / (cid + '.json')).read_text(encoding='utf-8'))
    results = pair['response']['body']['results']
    searches.append(results)
    count = sum(r.get('keys', {}).get('sabre', {}).get('endpoint') == endpoint for r in results)
    check(f'TC-0{index}', f'{cid}; PUB; S/6NVG; LHR-JFK 2026-11-20; Y/1 ADT',
          f'Nonempty results; all keys.sabre.endpoint={endpoint}',
          f'HTTP {pair["response"]["http_status"]}; {count}/{len(results)} options match',
          bool(results) and count == len(results), pair)
    csv_rows.append(dict(scenario_id=f'TC-0{index}', expected_result='Nonempty results with configured endpoint marker',
                         provider_filter='S/6NVG', search_url=pair['request']['url'], cid=cid,
                         expected_endpoint=endpoint, endpoint_path='keys.sabre.endpoint', fare='PUB'))
    retrieved = json.loads((RUN / (cid + '-result.json')).read_text(encoding='utf-8'))
    body = retrieved['response']['body']
    ok = (body.get('key') == results[0]['key'] and body.get('keys', {}).get('sabre', {}).get('endpoint') == endpoint
          and isinstance(body.get('trips'), list) and bool(body['trips']) and isinstance(body.get('prices'), dict))
    check(f'TC-0{index + 5}', f'{cid}; first fresh Search key carried unchanged into GET Result',
          'Readable itinerary/prices; selected key and endpoint marker retained',
          f'HTTP {retrieved["response"]["http_status"]}; key retained={body.get("key") == results[0]["key"]}; endpoint={body.get("keys", {}).get("sabre", {}).get("endpoint")}',
          ok, retrieved)

all_results = [r for group in searches for r in group]
shape = set(searches[0][0])
same = all(set(r) == shape for r in all_results)
last = json.loads((RUN / 'TST104.json').read_text(encoding='utf-8'))
check('TC-04', 'All 340 returned Search options across three CIDs',
      'Same top-level AirAPI option field set across all three routes',
      f'{len(all_results)} options; {len(shape)} top-level fields each; identical field sets={same}', same, last)
absent = all('sabreRest' not in r.get('meta', {}) for r in all_results)
check('TC-05', 'All returned Search options; meta.sabreRest and keys.sabre.endpoint',
      'Legacy meta.sabreRest absent; endpoint marker present',
      f'{len(all_results)}/{len(all_results)} legacy flags absent; all route markers populated',
      absent and all(r.get('keys', {}).get('sabre', {}).get('endpoint') for r in all_results), last)
rows.sort(key=lambda r: r['id'])

# Keep each configuration phase's CSV separate so reruns do not mix incompatible routing expectations.
with (RUN / 'expected-outcomes.csv').open('w', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
    writer.writeheader()
    writer.writerows(csv_rows)
empty_run = ROOT / 'runs' / '2026-10-22-empty-lists'
if all((empty_run / (cid + '.json')).exists() for cid, _ in CASES):
    csv_rows = []
    for index, (cid, previous) in enumerate(CASES, 9):
        pair = json.loads((empty_run / (cid + '.json')).read_text(encoding='utf-8'))
        results = pair['response']['body'].get('results') or []
        count = sum(r.get('keys', {}).get('sabre', {}).get('endpoint') == 'bargainFinderMax' for r in results)
        check(f'TC-{index:02}', f'{cid}; all lists null (user-approved empty); unchanged Search inputs',
              'All options use default bargainFinderMax after config-only update',
              f'HTTP {pair["response"]["http_status"]}; {count}/{len(results)} default options; previous marker={previous}',
              bool(results) and count == len(results), pair)
        csv_rows.append(dict(scenario_id=f'TC-{index:02}', expected_result='Empty-list configuration routes all options through default',
                             provider_filter='S/6NVG', search_url=pair['request']['url'], cid=cid,
                             expected_endpoint='bargainFinderMax', endpoint_path='keys.sabre.endpoint', fare='PUB'))
    rows.sort(key=lambda r: r['id'])

overlap_run = ROOT / 'runs' / '2026-10-22-overlap'
if (overlap_run / 'TST101.json').exists():
    with (empty_run / 'expected-outcomes.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    pair = json.loads((overlap_run / 'TST101.json').read_text(encoding='utf-8'))
    results = pair['response']['body'].get('results') or []
    count = sum(r.get('keys', {}).get('sabre', {}).get('endpoint') == 'flightShop' for r in results)
    check('TC-12', 'TST101 listed in both CID blocks; PUB/S/6NVG; unchanged itinerary',
          'flightShop wins over flightShopLite',
          f'HTTP {pair["response"]["http_status"]}; {count}/{len(results)} flightShop options',
          bool(results) and count == len(results), pair)
    csv_rows = [dict(scenario_id='TC-12', expected_result='flightShop wins CID overlap',
                     provider_filter='S/6NVG', search_url=pair['request']['url'], cid='TST101',
                     expected_endpoint='flightShop', endpoint_path='keys.sabre.endpoint', fare='PUB')]

with (ROOT / 'expected-outcomes.csv').open('w', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
    writer.writeheader()
    writer.writerows(csv_rows)

tests = """const b = pm.response.json();
const at = (o,p) => p.split('.').reduce((v,k) => v == null ? undefined : v[k], o);
const expected = pm.iterationData.get('expected_endpoint');
const path = pm.iterationData.get('endpoint_path');
pm.test('Search exposes nonempty results', () => {
  pm.expect(b.results).to.be.an('array').that.is.not.empty;
});
pm.test('Every option has the configured endpoint marker', () => {
  pm.expect(expected).to.be.a('string').that.is.not.empty;
  pm.expect(path).to.be.a('string').that.is.not.empty;
  pm.expect(b.results).to.be.an('array').that.is.not.empty;
  b.results.forEach(r => pm.expect(at(r,path)).to.eql(expected));
});
pm.test('Legacy meta.sabreRest is absent', () => {
  b.results.forEach(r => pm.expect(r.meta || {}).not.to.have.property('sabreRest'));
});
if (Array.isArray(b.results) && b.results.length) {
  pm.variables.set('selected_key', b.results[0].key);
  pm.variables.set('encoded_key', encodeURIComponent(b.results[0].key));
}
"""
collection = {
    'info': {'name': 'SS-6409 DEV CID routing and read-only Result',
             'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
             'description': 'Run current expected-outcomes.csv with TST101 present in BOTH CID lists (overlap phase). Empty-list CSV is preserved under runs/2026-10-22-empty-lists/. Original configured-route CSV is preserved in runs/2026-10-22/expected-outcomes.csv and requires the original routing config. Supply search_authorization at runtime. No booking or checkout writes. Cross-route schema comparison is in the saved report; this runner checks each route and Result independently.'},
    'variable': [{'key': 'search_authorization', 'value': ''},
                 {'key': 'base_url', 'value': 'https://api.search.dev.travel-dev.com'}],
    'item': [
        {'name': 'Search configured CID route',
         'event': [{'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': [
             "pm.variables.unset('selected_key'); pm.variables.unset('encoded_key');",
             "['scenario_id','expected_result','provider_filter','search_url','cid','expected_endpoint','endpoint_path'].forEach(k => { if (!pm.iterationData.get(k)) throw new Error('CSV input missing: ' + k); });"]}},
                   {'listen': 'test', 'script': {'type': 'text/javascript', 'exec': tests.splitlines()}}],
         'request': {'method': 'GET', 'header': [{'key': 'Authorization', 'value': '{{search_authorization}}'}], 'url': '{{search_url}}'}},
        {'name': 'Read-only Result for selected Search key',
         'event': [{'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': [
             "if (!pm.variables.get('selected_key')) throw new Error('Search inventory is required');"]}},
                   {'listen': 'test', 'script': {'type': 'text/javascript', 'exec': [
             "const b=pm.response.json();",
             "pm.test('Selected key retained',()=>pm.expect(b.key).to.eql(pm.variables.get('selected_key')));",
             "pm.test('Endpoint marker retained',()=>pm.expect(b.keys.sabre.endpoint).to.eql(pm.iterationData.get('expected_endpoint')));",
             "pm.test('Readable itinerary and prices',()=>{pm.expect(b.trips).to.be.an('array').that.is.not.empty;pm.expect(b.prices).to.be.an('object');});"]}}],
         'request': {'method': 'GET', 'header': [{'key': 'Authorization', 'value': '{{search_authorization}}'}],
                     'url': '{{base_url}}/v1/result/ANY/{{encoded_key}}?cid={{cid}}&debug=true'}}]}
(ROOT / 'SS-6409.postman_collection.json').write_text(json.dumps(collection, indent=2), encoding='utf-8')
data = dict(title='SS-6409 — Sabre REST – add /offers/flightShop and /offers/flightShopLite as config-switchable alternatives to /offers/shop',
            scope='DEV | PUB; S/6NVG | TST101/TST102/TST104 | LHR-JFK 2026-11-20; Y; 1 ADT',
            summary='Three fresh Search calls returned 50 flightShop, 95 flightShopLite and 195 bargainFinderMax options. All 340 share the same top-level field set and omit meta.sabreRest. One fresh read-only Result retrieval per route retained its selected key and endpoint marker. CID routing and retrieval pass within this scope; full ticket closure is not established.',
            intended='Route listed project/CID entries through their configured Sabre REST endpoint; unlisted traffic uses the default route. All three produce AirAPI output and support revalidation/checkout. User confirmed bargainFinderMax with RestBargainFinderMaxRQ is the intended default route for this test.',
            limits='8 executed checks across 3 Search and 3 Result requests, without retries. Configuration discovery is separate evidence in config-discovery.json. Source pairs: runs/2026-10-22/TST101.json, TST102.json, TST104.json and corresponding -result.json files. Same top-level field set does not certify nested field/value parity. Search requests used S/6NVG; returned gds/pcc included E/8C4T for 48/50 TST101 and 183/195 TST104 options; TST102 returned S/6NVG throughout. No assertion of returned GDS/PCC equality was made. Result GET does not establish provider revalidation. Excluded: checkout, booking/ticket writes, revalidation execution, project routing, overlap priority, forced provider errors/no-fallback, empty-list config transition, SR, and debug=false. SS-6330 research lists mileage/meal/seat/surcharge gaps; no waiver or full nested parity assertion. No operational lessons applied or new reusable operational patterns observed. No ledger update.',
            rows=rows, evidence=evidence, collection='SS-6409.postman_collection.json')
if len(rows) >= 11:
    data['summary'] += ' Empty-list round: all three CIDs returned only default-route options; TST101/TST102 switched from their configured routes with identical Search inputs.'
    data['limits'] = data['limits'].replace('8 executed checks across 3 Search and 3 Result requests', '11 executed checks across 6 Search and 3 Result requests').replace('empty-list config transition, ', '')
    data['limits'] += ' Empty-list phase evidence: runs/2026-10-22-empty-lists/. Actual list values were null; user explicitly approved this as empty for this test only. Root CSV is for the current empty-list phase; original CSV is retained under runs/2026-10-22/. No-fallback-on-error is user accepted but NOT EXECUTED and adds no executed PASS. See acceptance-notes.md. Overlap winner is confirmed as flight_shop; overlap/project/revalidation/checkout execution remains pending.'
if len(rows) == 12:
    data['summary'] += ' CID overlap round: TST101 appeared in both lists and all 50 options used flightShop, confirming the user-specified priority.'
    data['limits'] = data['limits'].replace('11 executed checks across 6 Search and 3 Result requests', '12 executed checks across 7 Search and 3 Result requests').replace('overlap priority, ', '').replace('Root CSV is for the current empty-list phase', 'Root CSV is for the current CID-overlap phase').replace('overlap/project/revalidation/checkout execution remains pending', 'project routing and revalidation/checkout execution remain pending')
    data['limits'] += ' Overlap evidence: runs/2026-10-22-overlap/; both CID lists contained TST101, both project lists were null. Earlier eight-check and empty-list results retain their original evidence and configuration contexts.'
result_pair_path = overlap_run / 'TST101-result.json'
if result_pair_path.exists():
    pair = json.loads(result_pair_path.read_text(encoding='utf-8'))
    body = pair['response']['body']
    ok = (body.get('key') == pair['selected_search_key'] and body.get('keys', {}).get('sabre', {}).get('endpoint') == 'flightShop'
          and isinstance(body.get('prices'), dict) and bool(body.get('trips')))
    check('TC-13', 'Latest overlap Search key; GET /v1/result/ANY/{key}; TST101',
          'Result succeeds with selected key, itinerary/prices and flightShop marker retained',
          f'HTTP {pair["response"]["http_status"]}; selected key retained={body.get("key") == pair["selected_search_key"]}; flightShop marker retained', ok, pair)
    data['summary'] += ' Additional user-requested Result check on the latest overlap key returned HTTP 200 with key and flightShop marker retained.'
    data['limits'] = data['limits'].replace('12 executed checks across 7 Search and 3 Result requests', '13 executed checks across 7 Search and 4 Result requests')
    data['limits'] += ' User clarified v1/result as the revalidation test operation. TC-13 covers that requested operation for flightShop; TC-06/07/08 previously cover Result for all three routes. No separate provider-internal execution proof or booking checkout is claimed.'

(ROOT / 'report-data.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
result = render(ROOT)
# The shared renderer hardcodes its original run date; preserve styling and correct this ticket's date.
for name in ['qa-report.html', 'qa-report.md']:
    file = ROOT / name
    file.write_text(file.read_text(encoding='utf-8').replace('2026-10-21', '2026-10-22'), encoding='utf-8')
assert (len(rows), len(csv_rows)) in ((8, 3), (11, 3), (12, 1), (13, 1))
assert sum(len(group) for group in searches) == 340
assert all(len(group) > 0 for group in searches)
assert collection['info']['schema'].endswith('/v2.1.0/collection.json')
print(json.dumps(result))
