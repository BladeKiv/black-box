"""Render the final scoped dispatch from saved captures; no network activity."""
import base64
import csv
import html
import importlib
import io
import json
import re
from pathlib import Path
from bb.classify import classify_outcome
from bb.escalations import Escalations, handle_outcome
from bb.lessons import Store

ROOT=Path(__file__).resolve().parent
TITLE='SS-6438 — Build UPG itineraries as main itineraries with NGS children (regular + upgrade options)'
RUN='SS-6438-20261102-merge-enabled'
analysis=importlib.import_module('tasks.SS-6438-upg-ngs-merge.analyze-merge')
runs=analysis.analyze()
groups=[g for r in runs for g in r['groups']]
false_runs=[r for r in runs if not r['keepBothBagOptions']]
true_runs=[r for r in runs if r['keepBothBagOptions']]
false_groups=[g for r in false_runs for g in r['groups']]
true_groups=[g for r in true_runs for g in r['groups']]
config=json.loads((ROOT/'configuration-merge-enabled.json').read_text())
assert config['response']['body']['upgrade_config']['enable_merge'] is True
assert all(g[k] for g in groups for k in ('price_order_ok','main_minimum_retained','features_ok','flight_identity_ok'))
assert all(g['numbering_ok'] is not False for g in groups)
assert len(groups)==60 and sum(len(g['options']) for g in groups)==158
assert sum(g['regular_children'] for g in groups)==64
assert sum(g['upg_children'] for g in groups)==34
assert all(g['upg_children']==0 for g in false_groups)
assert sum(g['main_source']=='regular' for g in groups)==0
singleton=[g for g in groups if not g['children_count']]
assert len(singleton)==8 and all(g['options'][0]['gdsOfferId']==':UPG#' for g in singleton)

def test(id,data,expected,actual,status='PASS',sources=None):
    return dict(id=id,data=data,expected=expected,actual=actual,status=status,sources=sources or [])
tests=[
 test('TC-01','M01/M03 · BCKDCR · keepBothBagOptions=false · SFO-FRA / LAX-MUC','UPG-cheapest main with qualifying regular children; numbered main is NGS#1 when children exist.','26 UPG groups: 18 with regular children, 8 valid singletons; 26 regular children total. All 18 multi-option groups use main :UPG#:NGS#1.',sources=['M01','M03']),
 test('TC-02','M02/M04/M05 · AKKDCR · keepBothBagOptions=true · SFO-FRA / LAX-MUC / ORD-FRA','Retain eligible regular and other UPG options; cheapest returned option is main NGS#1.','34 groups: all UPG mains; 34 two-bag UPG children and 38 regular children. All 34 mains are NGS#1 with sequential child identifiers.',sources=['M02','M04','M05']),
 test('TC-03','60 returned UPG-containing groups · 158 retained USD options','Prices ascend within each group; main is cheapest among returned options.','60/60 main minima and 98/98 retained transitions satisfy prices.totalPrice ordering.',sources=[r['scenario_id'] for r in runs]),
 test('TC-04','User-confirmed bags / exchange / refund fields · 98 retained transitions','Each retained child is no worse on all three features and better on at least one than the last kept option.','98/98 transitions strictly improve the confirmed feature vector. No equal-feature or feature-losing retained transition.',sources=[r['scenario_id'] for r in runs]),
 test('TC-05','60 group mains and 98 children; exact flights, airports and departure/arrival times','Children belong to the same itinerary; one returned main for each exact flight sequence in these groups.','98/98 child flight sequences match their main. No other top-level result shares any of the 60 group flight sequences.',sources=[r['scenario_id'] for r in runs]),
 test('TC-06','BCKDCR · 26 groups · keepBothBagOptions=false','Other UPG options are not retained as NGS children.','0 UPG children across 26 groups; the retained children are regular options.',sources=['M01','M03']),
 test('TC-07','Eight singleton BCKDCR UPG groups in M01/M03','User clarification: :UPG# alone is valid when no children remain.','8/8 singleton mains have gdsOfferId=:UPG# and no retained children.',sources=['M01','M03']),
 test('TC-08','M01/M03 · BCKDCR · keepBothBagOptions=false','Ticket example 3: a qualifying regular-cheapest option becomes main; UPG/regular improvements become children.','0 regular-cheapest groups among the 26 observed groups. User confirmed no example is available; branch untested.','WARN',['M01','M03']),
 test('TC-09','M02/M04/M05 · AKKDCR · keepBothBagOptions=true','Ticket example 4: a qualifying regular-cheapest option becomes main; eligible UPG/regular improvements become children.','0 regular-cheapest groups among the 34 observed groups. User confirmed no example is available; branch untested.','WARN',['M02','M04','M05']),
 test('TC-10','Five final Search responses · candidate elimination/completeness','Verify excluded equal-feature higher-price and feature-losing candidates against the complete pre-filter candidate set.','Final retained chains satisfy the rule, but responses do not provide a certified pre-filter candidate baseline. Complete elimination and retention completeness are unverified.','WARN',[r['scenario_id'] for r in runs]),
]

# Independent exact-flight duplicate check; no decoding or normalization of Search keys.
for run in runs:
    raw=json.loads((ROOT/(run['scenario_id']+'.json')).read_text())['response']['body']['results']
    for group in run['groups']:
        main=raw[group['result_index']]
        assert sum(analysis.signature(o)==analysis.signature(main) for o in raw)==1

store=Store(); escalations=Escalations(store=store)
for t in tests:
    if t['status']=='WARN':
        scope={'ticket':'SS-6438','environment':'PREPROD','endpoint':'/v1/search','allow_retry':False,'allow_poll':False,'allow_retest':False,'approved_inputs':[]}
        captured=json.loads((ROOT/(t['sources'][0]+'.json')).read_text())['response']
        outcome=classify_outcome(captured['http_status'],json.dumps(captured['body']),captured['transport_error'],{'inventory_field':'results','comparable_count':0,'observed_expectation':t['expected'],'response_paths':['$.results','$.results[*].ngsItineraries','$.results[*].keys.upgrade_info']})
        assert outcome['status']=='WARN'
        t['reason_code']=outcome['reason_code']
        t['response_paths']=['$.results[*].keys.upgrade_info','$.results[*].ngsItineraries','$.results[*].gdsOfferId'] if t['id']!='TC-10' else ['$.results','$.results[*].ngsItineraries']
        handle_outcome(store,escalations,outcome,RUN+'-'+t['id'],['SS-6438','PREPROD'],'regular cheapest inventory unavailable' if t['id']!='TC-10' else 'prefilter candidate baseline unavailable',scope,retries=0,steps=1)

for pattern,question,reason in [
 ('feature comparison response paths','Use keys.baggage.allowPieces, penalties.exchange and penalties.refund for the feature comparison?','EXPECTATION_CLARIFICATION'),
 ('singleton upg numbering','When filtering leaves a UPG main with no children, is :UPG# alone correct?','EXPECTATION_CLARIFICATION'),
 ('regular cheapest example unavailable','Do you have a PREPROD Search example where a regular option is cheaper than UPG?','NO_DATA')]:
    escalations.ask(run=RUN,question=question,reason_code=reason,matching_lesson_found=False,tags=['SS-6438','PREPROD'],pattern=pattern,scope_conditions={'ticket':'SS-6438','environment':'PREPROD','endpoint':'/v1/search'})
# These answers define expectations/coverage and remain in ticket-scope.md, never lessons.

fields=['scenario_id','expected_result','provider_filter','search_url','cid','origin','destination','departure_date','keepBothBagOptions','bags_path','exchange_path','refund_path','price_path','children_path','upgrade_path']
out=io.StringIO(newline=''); writer=csv.DictWriter(out,fieldnames=fields); writer.writeheader()
for r in runs:
    from urllib.parse import parse_qs,urlsplit
    q=parse_qs(urlsplit(r['request']['url']).query)
    writer.writerow(dict(scenario_id=r['scenario_id'],expected_result='cheapest retained main; strictly improving retained feature chain; eligible child sources',provider_filter='AirAPI aggregate',search_url=r['request']['url'],cid=q['cid'][0],origin=q['fl[0][o]'][0],destination=q['fl[0][d]'][0],departure_date=q['fl[0][dt]'][0],keepBothBagOptions=str(r['keepBothBagOptions']).lower(),bags_path='keys.baggage.allowPieces',exchange_path='penalties.exchange',refund_path='penalties.refund',price_path='prices.totalPrice',children_path='ngsItineraries',upgrade_path='keys.upgrade_info'))
(ROOT/'expected-outcomes.csv').write_text(out.getvalue(),encoding='utf-8')
pre="""const required=['scenario_id','search_url','expected_result','keepBothBagOptions','bags_path','exchange_path','refund_path','price_path','children_path','upgrade_path'];
for (const key of required) { const v=pm.iterationData.get(key); if (v===undefined || v==='') throw new Error('CSV row missing '+key); pm.variables.set(key,v); }
if (!String(pm.variables.get('search_url')).startsWith('http://airapi51.kivops.info/v1/search?')) throw new Error('Search URL outside the approved host/endpoint');"""
collection={'info':{'name':TITLE,'schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json','description':'AirAPI only. Run the single Search request using expected-outcomes.csv (five rows). PREPROD merge/ngs prerequisites must be enabled before running. Existing environment supplies search_authorization; no credential values are embedded. Known singleton exception is ticket-scoped. Skipped inventory checks mean WARN, not PASS. Complete pre-filter candidate elimination is not certified by these retained-output checks.'},'item':[{'name':'{{scenario_id}} — merge retained-output checks','event':[{'listen':'prerequest','script':{'type':'text/javascript','exec':pre.splitlines()}},{'listen':'test','script':{'type':'text/javascript','exec':(ROOT/'postman-check.js').read_text().splitlines()}}],'request':{'method':'GET','header':[{'key':'Authorization','value':'{{search_authorization}}','type':'text'}],'url':'{{search_url}}'}}]}
(ROOT/'collection.json').write_text(json.dumps(collection,indent=2),encoding='utf-8')
counts={s:sum(t['status']==s for t in tests) for s in ('PASS','FAIL','WARN')}
assert counts=={'PASS':7,'FAIL':0,'WARN':3}
summary='Five fresh PREPROD Searches returned 1,087 main results. All checked retained-output rules pass across 60 UPG-containing groups and 158 options: 64 regular children and 34 UPG children. Regular-cheapest branches and complete pre-filter candidate elimination remain unverified.'
intended='For an itinerary with UPG options, choose the cheapest eligible regular or UPG option as main NGS#1; retain successive options only when all three features are at least equal and one is better. Regular children require ngs_jobs; other UPG children also require keepBothBagOptions=true. A singleton UPG main may remain :UPG# under the user clarification.'
strip='PREPROD | 2026-11-02 | HTTP Search | 5 calls · 3 routes · 2 CIDs | merge=true'
md=[TITLE,'','WARN — PARTIAL COVERAGE | 7 PASS / 0 FAIL / 3 WARN',strip,'','Intended behavior: '+intended,'',summary,'','| ID | Test data | Expected result | Actual result | Status |','|---|---|---|---|---|']
for t in tests: md.append('| '+' | '.join(t[k] for k in ('id','data','expected','actual','status'))+' |')
md += ['','Supporting evidence and rerun','', 'M01.json–M05.json contain paired sanitized requests/responses. merge-analysis.json contains per-group feature/price excerpts. configuration-merge-enabled.json verifies only prerequisites, not per-request execution. The earlier blocked preparation is preserved in initial-blocked-qa-report.md/html and initial-blocked-results.json.','', 'Run collection.json with expected-outcomes.csv in Postman using the existing PREPROD environment. No provider-level tracks. Downloads are embedded in the HTML dispatch.','', 'Comparators: keys.baggage.allowPieces, penalties.exchange, penalties.refund; prices.totalPrice in USD. Search keys remain opaque. Same-flight check uses returned airports, times, marketing airline and flight number. Singleton exception and regular-cheapest WARN decisions were confirmed live by the user.','', 'No retry, polling, downstream endpoints, configuration mutation, booking, or Jira write was performed. No matching operational lesson applied. Prior transport failures were from the inherited localhost proxy; direct HTTP access succeeded under the current explicit user authorization.']
(ROOT/'qa-report.md').write_text('\n'.join(md)+'\n',encoding='utf-8')

def evidence_for(test):
    evidence=[]
    for name in test['sources']:
        r=next(x for x in runs if x['scenario_id']==name)
        if test['id'] in ('TC-08','TC-09'):
            result_excerpt=[g['options'][0] for g in r['groups']]
        else:
            result_excerpt=[{**g['options'][0],'ngsItineraries':g['options'][1:]} for g in r['groups'][:1]]
        raw=json.loads((ROOT/(name+'.json')).read_text())['response']['body']
        evidence.append({'request':r['request'],'response_excerpt':{'http_status':r['http_status'],'body':{'count':raw['count'],'results':result_excerpt}},'observations':{'body_top_level_fields':list(raw),'qualifying_groups':len(r['groups']),'regular_mains':sum(g['main_source']=='regular' for g in r['groups']),'complete_prefilter_candidate_set':'not exposed in captured response'}})
    return evidence

e=html.escape
template=(ROOT.parents[1]/'templates/airapi-qa-dispatch-template.html').read_text(encoding='utf-8')
template=template.replace('&lt;Ticket title&gt;',e(TITLE)).replace('Run &lt;YYYY-MM-DD&gt;<br>&lt;Endpoint / route / scope&gt;',e(strip))
template=template.replace('class="value fail">&lt;PASS / FAIL / WARN&gt;','class="value warn">WARN · PARTIAL')
for count in ('7','0','3'):template=template.replace('&lt;0&gt;',count,1)
template=template.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;',e(summary)+'<br><strong>Intended behavior:</strong> '+e(intended))
tbody='\n'.join('<tr><td>'+e(t['id'])+'</td><td class="test">'+e(t['data'])+'</td><td>'+e(t['expected'])+' → '+e(t['actual'])+'</td><td class="status '+t['status'].lower()+'">'+t['status']+'</td></tr>' for t in tests)
template=re.sub(r'(?s)(<tbody>).*?(</tbody>)',lambda m:m[1]+tbody+m[2],template)
samples=[]
for t in tests:
    if t['status']!='WARN':continue
    samples.append('<section class="failure-sample"><h2>'+e(t['id'])+' · Paired payload evidence</h2><p>'+e(t['actual'])+'</p><pre>'+e(json.dumps(evidence_for(t),indent=2))+'</pre></section>')
template=re.sub(r'(?s)<section class="failure-sample">.*?</section>',lambda m:'\n'.join(samples),template)
evidence='<section class="evidence"><div><h2>Evidence and limits</h2><p>M01–M05 paired captures; merge-analysis.json; configuration-merge-enabled.json. Comparators and singleton behavior were confirmed live. Regular-cheapest inventory and complete pre-filter candidate sets are unavailable. No retries or downstream calls. Initial blocked-run evidence is preserved separately.</p></div><div><h2>Rerun artifacts</h2><p><button class="download-artifact" type="button" data-file="collection.json">Postman collection</button><br><button class="download-artifact" type="button" data-file="expected-outcomes.csv">Expected-outcome CSV</button></p></div></section>'
template=re.sub(r'(?s)<section class="evidence">.*?</section>',lambda m:evidence,template)
artifacts={name:{'type':mime,'content':base64.b64encode((ROOT/name).read_bytes()).decode()} for name,mime in [('collection.json','application/json;charset=utf-8'),('expected-outcomes.csv','text/csv;charset=utf-8')]}
template=re.sub(r'(?s)const artifacts = \{.*?\n    \};',lambda m:'const artifacts = '+json.dumps(artifacts)+';',template)
(ROOT/'qa-report.html').write_text(template,encoding='utf-8')
(ROOT/'results.json').write_text(json.dumps({'run':RUN,'signal':'WARN','counts':counts,'searches':5,'groups':60,'options':158,'tests':tests},indent=2),encoding='utf-8')
(ROOT/'warn-evidence.json').write_text(json.dumps({t['id']:evidence_for(t) for t in tests if t['status']=='WARN'},indent=2),encoding='utf-8')
print(json.dumps({'counts':counts,'artifacts':['qa-report.md','qa-report.html','results.json','collection.json','expected-outcomes.csv','warn-evidence.json']}))
