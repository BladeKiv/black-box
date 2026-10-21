import base64, csv, html, io, json, re
from pathlib import Path

D = Path(__file__).parent
def read(name):
    return json.loads((D / name).read_text(encoding='utf-8-sig'))
def segments(j):
    return {(t['tripId'], s['segmentId']): s for t in j['trips'] for s in t['segments']}
def compact(j):
    return {k: j[k] for k in ('key', 'gds', 'pcc', 'cons') if k in j} | {'segments': [dict(tripId=t, segmentId=s, **{k:v[k] for k in ('flightNumber','departureAirportCode','arrivalAirportCode','departureTime','bookingClass','cabin') if k in v}) for (t,s),v in segments(j).items()]}
search = read('search-response.json')
search_request = read('search-request.json')
rows, evidence, csv_rows = [], [], []
for case in ('TC-02','TC-02b','TC-04','TC-04b'):
    original, result = read(case+'-original.json'), read(case+'-response.json')
    before, after = segments(original), segments(result)
    same = before.keys() == after.keys() and all(all(before[k].get(f)==after[k].get(f) for f in ('flightNumber','departureAirportCode','arrivalAirportCode','departureTime','bookingClass')) for k in before)
    empty = case.startswith('TC-02')
    expected = 'Replace empty cabins with C on each matching segment' if empty else 'Preserve populated original cabins with unchanged booking classes'
    revalidated = original.get('gds') != result.get('gds')
    observed = same and all(after[k].get('cabin')=='C' if empty else after[k].get('cabin')==before[k].get('cabin') for k in before)
    status = 'PASS' if same and revalidated and observed else ('FAIL' if same and revalidated and not observed else 'WARN')
    actual = f"HTTP {read(case+'-meta.json')['status']}; classes {','.join(v['bookingClass'] for v in before.values())} unchanged={same}; cabins {json.dumps([v.get('cabin') for v in before.values()])} → {json.dumps([v.get('cabin') for v in after.values()])}; GDS {original.get('gds')} → {result.get('gds')}; revalidation by GDS change={revalidated}"
    rows.append([case, f"{original['validatingCarrier']}; {len(before)} segments", expected, actual, status])
    evidence.append({'scenario_id':case,'search_request':search_request,'search_response_selected':compact(original),'result_request':read(case+'-request.json'),'result_response':compact(result)|{'revalidate':result.get('keys',{}).get('revalidate')}})
    csv_rows.append(dict(scenario_id=case,expected_result=expected,provider_filter='G/DEF',search_url=search_request['url'],original_key=original['key'],original_gds=original['gds'],original_segments=json.dumps(compact(original)['segments'],separators=(',',':')),expected_cabins=json.dumps(['C']*len(before) if empty else [v['cabin'] for v in before.values()],separators=(',',':')),require_revalidation='true'))
null_count = sum(any('cabin' in s and s['cabin'] is None for s in segments(j).values()) for j in search['results'])
assert null_count == 0
(D/'results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
(D/'paired-evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
out=io.StringIO(newline='')
writer=csv.DictWriter(out,fieldnames=list(csv_rows[0])); writer.writeheader(); writer.writerows(csv_rows)
(D/'expected-outcomes.csv').write_text(out.getvalue(),encoding='utf-8')
setup="""['original_key','original_gds','original_segments','expected_cabins','search_url'].forEach(k => { if (!pm.iterationData.get(k)) throw new Error('Supply CSV row: '+k); });
pm.variables.set('original_key', pm.iterationData.get('original_key'));"""
tests="""const j=pm.response.json();
const original=JSON.parse(pm.iterationData.get('original_segments'));
const expected=JSON.parse(pm.iterationData.get('expected_cabins'));
const actual=(j.trips||[]).flatMap(t=>(t.segments||[]).map(s=>({...s,tripId:t.tripId})));
pm.test('Same itinerary, segments, and booking classes',()=>{pm.expect(actual.length).to.eql(original.length); original.forEach(o=>{const a=actual.find(s=>s.tripId===o.tripId&&s.segmentId===o.segmentId);pm.expect(a).to.be.an('object');['flightNumber','departureAirportCode','arrivalAirportCode','departureTime','bookingClass'].forEach(k=>pm.expect(a[k]).to.eql(o[k]));});});
pm.test('Revalidation occurred: original GDS changed',()=>pm.expect(j.gds).not.to.eql(pm.iterationData.get('original_gds')));
pm.test(pm.iterationData.get('expected_result'),()=>original.forEach((o,i)=>{const a=actual.find(s=>s.tripId===o.tripId&&s.segmentId===o.segmentId);pm.expect(a.cabin).to.eql(expected[i]);}));"""
collection={'info':{'name':'SS-6373 PREPROD cabin revalidation','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json','description':'Run with expected-outcomes.csv. Keys may expire; refresh Search and CSV original segment data together. Per user clarification, null is covered by empty-cabin testing; no separate null test is required. Tests cover AirAPI only. Configure basic authentication locally; credentials are not included.'},'auth':{'type':'basic','basic':[{'key':'username','value':'{{username}}','type':'string'},{'key':'password','value':'{{password}}','type':'string'}]},'variable':[{'key':'base_url','value':'http://airapi51.kivops.info'},{'key':'product_type','value':'SALKIV'},{'key':'username','value':''},{'key':'password','value':''}],'item':[{'name':'Search original inventory','request':{'method':'GET','url':search_request['url'],'header':[]},'event':[{'listen':'test','script':{'type':'text/javascript','exec':["pm.test('Search returns results array',()=>pm.expect(pm.response.json().results).to.be.an('array'));" ]}}]},{'name':'Revalidate CSV original key','request':{'method':'GET','url':'{{base_url}}/v1/result/{{product_type}}/{{original_key}}','header':[]},'event':[{'listen':'prerequest','script':{'type':'text/javascript','exec':setup.splitlines()}},{'listen':'test','script':{'type':'text/javascript','exec':tests.splitlines()}}]}]}
collection_text=json.dumps(collection,indent=2)
(D/'SS-6373.postman_collection.json').write_text(collection_text,encoding='utf-8')
summary='Fresh PREPROD Search returned 49 itineraries. Two empty-cabin results adopted C/C/C with unchanged classes and GDS G → S; one selected L05L. A populated-cabin L05L result retained C/C with GDS G → S. Replacement TC-04b retained C/C/F and classes R/R/R with GDS G → S, confirming mixed-cabin preservation through revalidation. Per user clarification, TC-03 is merged into empty-cabin coverage; no separate null test is required or claimed.'
intended='Same booking classes: preserve a populated original cabin; use the revalidated declared cabin when the original is empty or null.'
counts={s:sum(r[-1]==s for r in rows) for s in ('PASS','FAIL','WARN')}
signal='FAIL' if counts['FAIL'] else ('WARN' if counts['WARN'] else 'PASS')
md=f'# SS-6373 — Cabin revalidation\n\nRelease signal: {signal} — {counts}\n\nPREPROD | 2026-09-30 | AirAPI Search → GET Result | CPH–DEN, 2027-06-30, 1 ADT, cabin C\n\nIntended behavior: {intended}\n\n{summary}\n\n| ID | Test data | Expected | Actual | Status |\n|---|---|---|---|---|\n'
md+='\n'.join('| '+' | '.join(r)+' |' for r in rows)
md+='\n\n## Supporting evidence and rerun\n\nExact Search URL: '+search_request['url']+'\n\nSee paired-evidence.json for paired requests and responses for every case, including the replacement TC-04b. Raw Search and Result captures are stored beside this report. No provider endpoints or booking endpoints were called. Historical ELKM logs are supplemental September 29 production evidence. The earlier exact historical-key request returned C/C/C but is not counted as a fresh original-input test. Returned Search keys were sent to Result unchanged.\n\nPostman: import SS-6373.postman_collection.json, configure Basic authentication locally, and run with expected-outcomes.csv. Refresh original Search snapshots and opaque keys together when inventory changes. An unchanged GDS on a future rerun means the revalidation precondition is unavailable and must be evaluated as WARN. Superseded TC-04b captures and candidate attempts are retained as supporting evidence and excluded from the final active-case totals.\n\n'
for e in evidence:
    if next(r for r in rows if r[0]==e['scenario_id'])[-1] in ('WARN','FAIL'):
        md+='### '+e['scenario_id']+' paired evidence\n\n```json\n'+json.dumps(e,indent=2)+'\n```\n\n'
(D/'qa-report.md').write_text(md,encoding='utf-8')
template=(D.parents[1]/'templates/airapi-qa-dispatch-template.html').read_text(encoding='utf-8-sig')
template=template.replace('&lt;Ticket title&gt;','SS-6373 · Cabin revalidation').replace('&lt;YYYY-MM-DD&gt;','2026-09-30').replace('&lt;Endpoint / route / scope&gt;','PREPROD · Search → Result · CPH–DEN · 2027-06-30')
template=template.replace('class="value fail">&lt;PASS / FAIL / WARN&gt;',f'class="value {signal.lower()}">{signal}')
for s in ('PASS','FAIL','WARN'):
    template=template.replace(f'class="value {s.lower()}">&lt;0&gt;',f'class="value {s.lower()}">{counts[s]}')
template=template.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;',html.escape('Intended behavior: '+intended+' '+summary))
table=''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in (r[0],r[1],r[2]+' → '+r[3]))+f'<td class="status {r[-1].lower()}">{r[-1]}</td></tr>' for r in rows)
template=re.sub(r'<tbody>.*?</tbody>','<tbody>'+table+'</tbody>',template,flags=re.S)
warn=''.join('<section class="failure-sample"><h2>'+e['scenario_id']+' · Paired payload evidence</h2><pre>'+html.escape(json.dumps(e,indent=2))+'</pre></section>' for e in evidence if next(r for r in rows if r[0]==e['scenario_id'])[-1] in ('WARN','FAIL'))
template=re.sub(r'<section class="failure-sample">.*?</section>',lambda _:warn,template,flags=re.S)
template=template.replace('&lt;Response count, exact field paths, and other confirmed API facts.&gt;',html.escape('Cabin path: trips[].segments[].cabin. Classes: trips[].segments[].bookingClass. Revalidation criterion confirmed by user: original GDS changes. Full paired evidence stored locally. TC-03 merged into empty-cabin coverage. Historical-key output check is supplemental.'))
for name,content,placeholder in [('SS-6373.postman_collection.json',collection_text,'collection'),('expected-outcomes.csv',out.getvalue(),'csv')]:
    template=template.replace('&lt;'+placeholder+'-file-name&gt;',name).replace('<'+placeholder+'-file-name>',name).replace('<'+placeholder+'-base64>',base64.b64encode((D/name).read_bytes()).decode())
(D/'qa-report.html').write_text(template,encoding='utf-8')
assert counts=={'PASS':4,'FAIL':0,'WARN':0}, counts
assert not re.search(r'<(?:collection|csv)-|&lt;(?:Ticket|Input|Expected|Actual|0)',template)
assert collection['info']['schema'].endswith('/v2.1.0/collection.json')
print(json.dumps({'release_signal':signal,**counts,'null_inventory':null_count,'files':'report, HTML, collection, CSV, paired evidence'}))


