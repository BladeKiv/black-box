"""Dispatch for additional WARN exploration and the SS-6437 disabled baseline."""
import base64
import csv
import html
import importlib
import io
import json
import re
from pathlib import Path

ticket=Path(__file__).resolve().parent
root=ticket/'runs'/'2026-11-02-warn-and-disabled'
oracle=importlib.import_module('tasks.SS-6438-upg-ngs-merge.analyze-merge')
tests=[];payloads={};csvrows=[]
captures={}
for planfile,mode in [('new-search-plan.json','enabled_inventory'),('legacy-search-plan.json','legacy_disabled')]:
 for planned in json.loads((root/planfile).read_text()):
  name=planned['scenario_id'];path=root/(name+'.json')
  if not path.exists():continue
  c=json.loads(path.read_text());captures[name]=c
  summary=json.loads((root/(name+'-summary.json')).read_text())
  response=c['response'];body=response['body']
  if mode=='enabled_inventory':
   expected='Observe a positive regular-cheapest UPG merge group under the user-confirmed feature comparator.'
   actual=('No HTTP response: '+str(response['transport_error'])) if response['http_status'] is None else ('HTTP '+str(response['http_status'])+'; '+str(summary['result_count'])+' results; '+str(len(summary['groups']))+' observable UPG groups; '+str(summary.get('regular_mains',0))+' regular-main UPG groups.')
   status='FAIL' if summary.get('failing_groups') else 'PASS' if summary.get('regular_mains',0)>0 else 'WARN'
   scope='Additional enabled inventory search; unresolved coverage excluded by user instruction.'
  else:
   expected=summary['expected_result'];status=summary['status']
   actual='HTTP '+str(summary['http_status'])+'; '+str(summary['results'])+' mains; '+str(summary['upgrade_parents'])+' UPG parents; '+str(summary['upgrade_children'])+' UPG children; '+str(summary['invalid_count'])+' invalid identifiers; '+str(summary['missing_child_parent_count'])+' upgrade parents missing children.'
   scope='SS-6437 legacy identifier baseline; mergeWithRegular=false.'
  test={'id':name,'data':planned['params'],'expected':expected,'actual':actual,'status':status,'scope':scope}
  tests.append(test)
  if status in ('WARN','FAIL'):
   excerpt=body
   if isinstance(body,dict) and isinstance(body.get('results'),list) and body['results']:
    excerpt={k:v for k,v in body.items() if k in ('count','messages')}
    excerpt['results']=[{k:r[k] for k in ('key','gdsOfferId','prices','keys','penalties') if k in r} for r in body['results'][:2]]
   payloads[name]={'request':c['request'],'response_excerpt':{'http_status':response['http_status'],'transport_error':response['transport_error'],'body':excerpt},'full_capture':path.name,'observations':actual}
  p=planned['params']
  csvrows.append({'scenario_id':name,'expected_result':expected,'provider_filter':'AirAPI aggregate','search_url':c['request']['url'],'mode':mode,'cid':planned['cid'],'origin':p['fl[0][o]'],'destination':p['fl[0][d]'],'departure_date':p['fl[0][dt]'],'return_date':p.get('fl[1][dt]',''),'mergeWithRegular':'false' if mode=='legacy_disabled' else 'true','keepBothBagOptions':str(planned['cid']=='AKKDCR').lower()})
counts={s:sum(t['status']==s for t in tests) for s in ('PASS','FAIL','WARN')}
legacy=[t for t in tests if t['id'].startswith('L')]
legacy_signal='PENDING' if not legacy else 'FAIL' if any(t['status']=='FAIL' for t in legacy) else 'WARN' if any(t['status']=='WARN' for t in legacy) else 'PASS'
signal='FAIL' if counts['FAIL'] else 'WARN' if counts['WARN'] else 'PASS'
title='SS-6438 — Build UPG itineraries as main itineraries with NGS children (regular + upgrade options)'
strip='PREPROD | 2026-11-02 | HTTP Search | '+str(len(captures))+' new requests | Enabled inventory / disabled SS-6437 baseline'
intended='Merge-enabled cases follow the confirmed bags/exchange/refund comparator. For mergeWithRegular=false, the user requests the already-tested SS-6437 baseline: BCKDCR main gdsOfferId values must not combine UPG and NGS; AKKDCR upgrade child gdsOfferId values must contain both. Filtering and AKKDCR main-identifier behavior are not added to that legacy baseline.'
summary='Legacy baseline: '+legacy_signal+'. Additional new route/date searches did not establish the missing positive regular-cheapest branches. User requested skipping unresolved coverage after these attempts; attempts remain WARN with paired evidence and are excluded from sign-off. Complete pre-filter candidate visibility remains unavailable. The separate 13-Search post-fix run had zero observed feature violations; those earlier results are not counted as new passes here.'

fields=list(csvrows[0]);out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=fields);w.writeheader();w.writerows(csvrows)
(root/'expected-outcomes.csv').write_text(out.getvalue(),encoding='utf-8')
pre="""for (const key of ['scenario_id','search_url','mode','cid','expected_result']) { const value=pm.iterationData.get(key); if (value===undefined || value==='') throw new Error('Missing CSV field '+key); pm.variables.set(key,value); }
if (!String(pm.variables.get('search_url')).startsWith('http://airapi51.kivops.info/v1/search?')) throw new Error('Outside approved Search host');"""
script="""const body=pm.response.json();
pm.test('Search results[]',()=>pm.expect(body.results).to.be.an('array'));
const mode=pm.iterationData.get('mode'), cid=pm.iterationData.get('cid');
const rs=body.results;
const upg=r=>String(r.gdsOfferId||'').includes(':UPG#');
const parents=rs.filter(upg);
if (mode==='legacy_disabled') {
 if (!parents.length) { console.warn('WARN: no UPG baseline inventory'); pm.test.skip('Legacy inventory available',()=>{}); }
 else if (cid==='BCKDCR') pm.test('SS-6437 main identifiers do not combine UPG and NGS',()=>{ for(const r of rs) pm.expect(upg(r)&&String(r.gdsOfferId||'').includes(':NGS#')).to.equal(false); });
 else pm.test('SS-6437 upgrade children contain UPG and NGS',()=>{ for(const r of parents) { pm.expect(r.ngsItineraries).to.be.an('array').and.not.empty; for(const c of r.ngsItineraries) { pm.expect(upg(c)).to.equal(true); pm.expect(String(c.gdsOfferId||'').includes(':NGS#')).to.equal(true); } } });
} else {
 const groups=rs.filter(r=>r.keys?.upgrade_info!==undefined||(r.ngsItineraries||[]).some(c=>c.keys?.upgrade_info!==undefined));
 const regularMains=groups.filter(r=>r.keys?.upgrade_info===undefined);
 if (!regularMains.length) { console.warn('WARN: positive regular-cheapest branch unavailable, excluded from sign-off per scope'); pm.test.skip('Positive regular-cheapest inventory',()=>{}); }
 else pm.test('Retained groups improve all confirmed features',()=>{for(const r of regularMains) { const opts=[r,...(r.ngsItineraries||[])]; for(let i=1;i<opts.length;i++) { const a=opts[i], b=opts[i-1], f=x=>[x.keys.baggage.allowPieces,x.penalties.exchange,x.penalties.refund]; const af=f(a),bf=f(b); pm.expect(af.every((x,j)=>x>=bf[j])&&af.some((x,j)=>x>bf[j])).to.equal(true); pm.expect(a.prices.totalPrice).to.be.at.least(b.prices.totalPrice); } } });
}"""
collection={'info':{'name':title+' — supplemental inventory and legacy','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json','description':'Read-only AirAPI Search only. CSV mode selects enabled-inventory or SS-6437 legacy assertions. Before running the corresponding rows, manually set and verify the matching config mergeWithRegular value; do not run enabled and disabled rows under the same unverified setting. Credentials resolve from the existing PREPROD environment. Inventory skips mean WARN, never PASS.'},'item':[{'name':'{{scenario_id}} — {{mode}}','request':{'method':'GET','url':'{{search_url}}','header':[{'key':'Authorization','value':'{{search_authorization}}','type':'text'}]},'event':[{'listen':'prerequest','script':{'type':'text/javascript','exec':pre.splitlines()}},{'listen':'test','script':{'type':'text/javascript','exec':script.splitlines()}}]}]}
(root/'collection.json').write_text(json.dumps(collection,indent=2),encoding='utf-8')
md=[title,'',signal+' — '+str(counts['PASS'])+' PASS / '+str(counts['FAIL'])+' FAIL / '+str(counts['WARN'])+' WARN',strip,'','Intended behavior: '+intended,'',summary,'','| ID | Test data | Expected result | Actual result | Status |','|---|---|---|---|---|']
for t in tests:md.append('| '+' | '.join([t['id'],json.dumps(t['data']),t['expected'],t['actual'],t['status']])+' |')
md+=['','Supporting evidence and rerun','', 'All per-scenario JSON files contain paired sanitized requests/responses. payload-evidence.json contains minimal paired WARN/FAIL excerpts. configuration.json records the enabled run settings; configuration-legacy.json records the disabled baseline settings when available. Configuration discovery is separate from endpoint evidence.','', 'Legacy source: tasks/SS-6437/runs/dashboard-6-292970de-c2f8-4a9a-966a-ac8d50be023b/ticket-scope.md, explicitly selected by the user in this chat. No source-code inspection, configuration mutation, booking, downstream calls or Jira writes. No identical-request retry or repeated inventory ladder. No trusted lesson applied.','', 'Expected-outcomes CSV and Postman v2.1 collection are embedded in the HTML as Blob downloads. Run each mode only with its matching verified configuration state. Prior core post-fix report: ../2026-11-02-post-fix/qa-report.html.']
(root/'qa-report.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
e=html.escape
h=(ticket.parents[1]/'templates/airapi-qa-dispatch-template.html').read_text(encoding='utf-8')
h=h.replace('&lt;Ticket title&gt;',e(title)).replace('Run &lt;YYYY-MM-DD&gt;<br>&lt;Endpoint / route / scope&gt;',e(strip)).replace('&lt;PASS / FAIL / WARN&gt;',signal)
for n in ('PASS','FAIL','WARN'):h=h.replace('&lt;0&gt;',str(counts[n]),1)
h=h.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;',e(summary)+'<br><strong>Intended behavior:</strong> '+e(intended))
tbody=''.join('<tr><td>'+e(t['id'])+'</td><td class="test">'+e(json.dumps(t['data']))+'</td><td>'+e(t['expected'])+' → '+e(t['actual'])+'</td><td class="status '+t['status'].lower()+'">'+t['status']+'</td></tr>' for t in tests)
h=re.sub(r'(?s)(<tbody>).*?(</tbody>)',lambda m:m[1]+tbody+m[2],h)
samples=''.join('<section class="failure-sample"><h2>'+e(name)+' · Paired evidence</h2><pre>'+e(json.dumps(payload,indent=2))+'</pre></section>' for name,payload in payloads.items())
h=re.sub(r'(?s)<section class="failure-sample">.*?</section>',lambda m:samples,h)
section='<section class="evidence"><div><h2>Coverage decisions</h2><p>Unresolved positive regular-cheapest and full pre-filter coverage excluded from sign-off by user instruction; attempts remain WARN. Legacy assertions follow the user-selected SS-6437 scope. All captures and configuration snapshots remain separate by mode.</p></div><div><h2>Rerun artifacts</h2><p><button class="download-artifact" type="button" data-file="collection.json">Postman collection</button><br><button class="download-artifact" type="button" data-file="expected-outcomes.csv">Expected-outcome CSV</button></p></div></section>'
h=re.sub(r'(?s)<section class="evidence">.*?</section>',lambda m:section,h)
artifacts={n:{'type':mime,'content':base64.b64encode((root/n).read_bytes()).decode()} for n,mime in [('collection.json','application/json;charset=utf-8'),('expected-outcomes.csv','text/csv;charset=utf-8')]}
h=re.sub(r'(?s)const artifacts = \{.*?\n    \};',lambda m:'const artifacts = '+json.dumps(artifacts)+';',h)
(root/'qa-report.html').write_text(h,encoding='utf-8')
(root/'payload-evidence.json').write_text(json.dumps(payloads,indent=2),encoding='utf-8')
(root/'results.json').write_text(json.dumps({'signal':signal,'legacy_signal':legacy_signal,'counts':counts,'requests':len(captures),'tests':tests,'coverage_exclusions':['Positive regular-cheapest branches not observed after bounded additional Searches','Complete pre-filter candidate set unavailable']},indent=2),encoding='utf-8')
print(json.dumps({'signal':signal,'legacy_signal':legacy_signal,'counts':counts,'requests':len(captures)}))
