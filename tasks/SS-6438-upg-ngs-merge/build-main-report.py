"""Consolidate accepted executed coverage; preserve excluded attempt evidence."""
import base64
import csv
import html
import io
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
enabled=ROOT/'runs'/'2026-11-02-post-fix'
legacy=ROOT/'runs'/'2026-11-02-warn-and-disabled'
evidence=json.loads((enabled/'results.json').read_text())
baseline_source=legacy/'before-main-consolidation-results.json'
baseline=json.loads((baseline_source if baseline_source.exists() else legacy/'results.json').read_text())
assert evidence['failing_groups']==0 and baseline['legacy_signal']=='PASS'
tests=[]
for source,directory in [(evidence,enabled),(baseline,legacy)]:
 for item in source['tests']:
  if item['status']!='PASS':continue
  row=dict(item);row['source_run']=directory.name
  if isinstance(row['data'],dict):row['data']=json.dumps(row['data'])
  tests.append(row)
assert len(tests)==7
extra_dir=ROOT/'runs'/'2026-11-02-extra-false'
extra_result=extra_dir/'results.json'
if extra_result.exists():
 extra=json.loads(extra_result.read_text())
 assert extra['counts']=={'PASS':1,'FAIL':0,'WARN':0}
 tests.extend({**t,'source_run':extra_dir.name} for t in extra['tests'])
included_cases=len(tests)
included_searches=15+(1 if extra_result.exists() else 0)
tests[0]['actual']='198 observed UPG-containing groups; no retained-feature violations.'
tests[1]['actual']='236 observed UPG-main groups; no retained-feature violations.'
for row in tests:
 if row['id']=='TC-05':row['actual']='434 groups / 784 retained USD options; no price-order violations within the returned groups.'
 if row['id']=='TC-08':row['actual']='All 19 previously failing exact flight sequences matched; their current retained options satisfy the confirmed feature rule.'
exclusions=['Positive regular-cheapest merge branches with keepBothBagOptions=false and true.','Complete pre-filter candidate-set elimination/retention completeness.']
title='SS-6438 — Build UPG itineraries as main itineraries with NGS children (regular + upgrade options)'
strip='PREPROD | 2026-11-02 | 13 merge-enabled + 2 disabled baseline'+(' + 1 extra=false' if extra_result.exists() else '')+' Searches | BCKDCR / AKKDCR'
summary='PASS within the approved executed scope: enabled merge behavior and the disabled SS-6437 baseline. All 19 previously failing itineraries were matched and no longer show retained-feature regressions. Unsuccessful inventory searches and unobservable scenarios are excluded from the result table and totals by user instruction.'
intended='With matching mergeWithRegular=true, the cheapest retained option is the main, and each retained child improves bags, exchange or refund without losing another feature. Other UPG children require keepBothBagOptions=true. With mergeWithRegular=false, preserve the user-selected SS-6437 identifier baseline: BCKDCR mains do not combine UPG and NGS; AKKDCR upgrade children contain both markers. The user-confirmed singleton :UPG# exception applies.'
if extra_result.exists():intended+=' Explicit extra=false suppresses NGS options despite mergeWithRegular=true; feature metadata is evaluated separately.'

rows=list(csv.DictReader((enabled/'expected-outcomes.csv').open(encoding='utf-8',newline='')))
for row in rows:row['mode']='merge_enabled'
legacyrows=[r for r in csv.DictReader((legacy/'expected-outcomes.csv').open(encoding='utf-8',newline='')) if r['mode']=='legacy_disabled']
for row in legacyrows:
 row['upgrade_config_index']='3' if row['cid']=='BCKDCR' else '2'
 row.update(bags_path='keys.baggage.allowPieces',exchange_path='penalties.exchange',refund_path='penalties.refund',price_path='prices.totalPrice',children_path='ngsItineraries',upgrade_path='keys.upgrade_info')
rows+=legacyrows
if extra_result.exists():
 from urllib.parse import parse_qs,urlsplit
 capture=json.loads((extra_dir/'EXTRA-01.json').read_text())
 q=parse_qs(urlsplit(capture['request']['url']).query)
 erow=dict(rows[0]);erow.update(scenario_id='EXTRA-01',expected_result='No NGS options with extra=false despite mergeWithRegular=true',search_url=capture['request']['url'],mode='extra_false',cid='BCKDCR',origin=q['fl[0][o]'][0],destination=q['fl[0][d]'][0],departure_date=q['fl[0][dt]'][0],return_date='',mergeWithRegular='true',keepBothBagOptions='false',upgrade_config_index='3',extra='false')
 rows.append(erow)
fields=list(dict.fromkeys(k for row in rows for k in row))
out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader();writer.writerows(rows)
csvtext=out.getvalue()
collection=json.loads((enabled/'collection.json').read_text())
collection['info']['description']='Consolidated approved scope: 13 merge-enabled Search rows and two merge-disabled SS-6437 baseline rows. Run CSV rows grouped by mode, manually verifying matching CID mergeWithRegular=true for merge_enabled or false for legacy_disabled before each group. BCKDCR secondBag/keepBothBagOptions=false; AKKDCR both true. No configuration changes are performed by this collection. The positive regular-cheapest and complete pre-filter checks are excluded from sign-off; unsuccessful exploratory Searches are not included. Existing PREPROD environment supplies search_authorization at runtime.'
if extra_result.exists():collection['info']['description']+=' Includes one extra_false row: BCKDCR mergeWithRegular=true with extra=false must expose no NGS child options or offer identifiers. Metadata is not counted as itinerary options.'
core=(ROOT/'postman-check.js').read_text()
# Excluded coverage checks are removed from the consolidated rerun, not relabeled PASS.
core=core.split('  const regularMainCount=')[0]+'}\n'
legacytest="""const body=pm.response.json();
pm.test('Search results[]',()=>pm.expect(body.results).to.be.an('array'));
const parents=body.results.filter(r=>String(r.gdsOfferId||'').includes(':UPG#'));
if (!parents.length) { console.warn('WARN: legacy UPG inventory unavailable'); pm.test.skip('Legacy UPG inventory available',()=>{}); }
else if (pm.iterationData.get('cid')==='BCKDCR') pm.test('SS-6437 BCKDCR main identifiers',()=>{for(const r of body.results)pm.expect(String(r.gdsOfferId||'').includes(':UPG#')&&String(r.gdsOfferId||'').includes(':NGS#')).to.equal(false);});
else pm.test('SS-6437 AKKDCR child identifiers',()=>{for(const r of parents){pm.expect(r.ngsItineraries).to.be.an('array').and.not.empty;for(const c of r.ngsItineraries){pm.expect(String(c.gdsOfferId||'').includes(':UPG#')).to.equal(true);pm.expect(String(c.gdsOfferId||'').includes(':NGS#')).to.equal(true);}}});"""
extra_test="""const body=pm.response.json();
pm.test('extra=false suppresses NGS options',()=>{pm.expect(body.results).to.be.an('array');for(const r of body.results){pm.expect((r.ngsItineraries||[]).length).to.equal(0);pm.expect(String(r.gdsOfferId||'').includes(':NGS#')).to.equal(false);}});"""
check="if (pm.iterationData.get('mode')==='merge_enabled') {\n"+core+"\n} else if (pm.iterationData.get('mode')==='extra_false') {\n"+extra_test+"\n} else {\n"+legacytest+"\n}"
collection['item'][0]['name']='{{scenario_id}} — {{mode}}'
for event in collection['item'][0]['event']:
 if event['listen']=='test':event['script']['exec']=check.splitlines()
pre=collection['item'][0]['event'][0]['script']['exec']
pre.append("if (!['merge_enabled','legacy_disabled','extra_false'].includes(pm.iterationData.get('mode'))) throw new Error('Missing or invalid CSV mode');")
collectiontext=json.dumps(collection,indent=2)

md=[title,'','PASS — '+str(included_cases)+' PASS / 0 FAIL / 0 WARN in the included scope',strip,'','Intended behavior: '+intended,'',summary,'','| ID | Test data | Expected result | Actual result | Status |','|---|---|---|---|---|']
for t in tests:md.append('| '+' | '.join(t[k] for k in ('id','data','expected','actual','status'))+' |')
md+=['','Scope exclusions','',*['- '+x for x in exclusions],'','Supporting evidence and rerun','', 'Enabled checks: runs/2026-11-02-post-fix/ (13 paired Search captures, configuration-enabled.json, all-previous-failures-comparison.json). Disabled SS-6437 baseline: runs/2026-11-02-warn-and-disabled/L01-B.json, L01-A.json, configuration-legacy.json. Enabled and disabled modes were tested at different verified configuration states.','', 'Earlier failure and unsuccessful exploration evidence remains archived and is not relabeled PASS. This consolidation performs no live requests. No configuration, booking, Jira or knowledge-ledger changes.','', 'Run collection.json with expected-outcomes.csv grouped by mode, under the matching manually verified configuration. Downloads are embedded in the HTML dispatch.']
markdown='\n'.join(md)+'\n'
e=html.escape
h=(ROOT.parents[1]/'templates/airapi-qa-dispatch-template.html').read_text(encoding='utf-8')
h=h.replace('&lt;Ticket title&gt;',e(title)).replace('Run &lt;YYYY-MM-DD&gt;<br>&lt;Endpoint / route / scope&gt;',e(strip))
h=h.replace('class="value fail">&lt;PASS / FAIL / WARN&gt;','class="value pass">PASS')
for count in (str(included_cases),'0','0'):h=h.replace('&lt;0&gt;',count,1)
h=h.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;',e(summary)+'<br><strong>Intended behavior:</strong> '+e(intended))
tbody=''.join('<tr><td>'+e(t['id'])+'</td><td class="test">'+e(t['data'])+'</td><td>'+e(t['expected'])+' → '+e(t['actual'])+'</td><td class="status pass">PASS</td></tr>' for t in tests)
h=re.sub(r'(?s)(<tbody>).*?(</tbody>)',lambda m:m[1]+tbody+m[2],h)
h=re.sub(r'(?s)<section class="failure-sample">.*?</section>','',h)
section='<section class="evidence"><div><h2>Scope and evidence</h2><p><strong>Excluded:</strong> positive regular-cheapest branches and complete pre-filter candidate-set comparison. Enabled evidence: 2026-11-02-post-fix; disabled baseline: L01-B/L01-A in 2026-11-02-warn-and-disabled. Earlier unsuccessful exploration remains archived and is not counted as passing. No live request was made for this consolidation.</p></div><div><h2>Rerun artifacts</h2><p><button class="download-artifact" type="button" data-file="collection.json">Postman collection</button><br><button class="download-artifact" type="button" data-file="expected-outcomes.csv">Expected-outcome CSV</button><br>Run enabled and disabled CSV modes separately under their matching verified configuration.</p></div></section>'
h=re.sub(r'(?s)<section class="evidence">.*?</section>',lambda m:section,h)
artifacts={'collection.json':{'type':'application/json;charset=utf-8','content':base64.b64encode(collectiontext.encode()).decode()},'expected-outcomes.csv':{'type':'text/csv;charset=utf-8','content':base64.b64encode(csvtext.encode()).decode()}}
h=re.sub(r'(?s)const artifacts = \{.*?\n    \};',lambda m:'const artifacts = '+json.dumps(artifacts)+';',h)
result={'signal':'PASS','counts':{'PASS':included_cases,'FAIL':0,'WARN':0},'included_searches':included_searches,'tests':tests,'scope_exclusions':exclusions,'source_runs':[enabled.name,legacy.name]+([extra_dir.name] if extra_result.exists() else []),'note':'User-requested consolidation of supported passes only; excluded attempts retain their original outcomes in archived evidence. No new execution by this report builder.'}
for destination in (ROOT,legacy):
 for name in ('qa-report.md','qa-report.html','results.json','collection.json','expected-outcomes.csv'):
  path=destination/name;archive=destination/('before-main-consolidation-'+name)
  if path.exists() and not archive.exists():archive.write_bytes(path.read_bytes())
 for name,content in [('qa-report.md',markdown),('qa-report.html',h),('results.json',json.dumps(result,indent=2)),('collection.json',collectiontext),('expected-outcomes.csv',csvtext)]:
  (destination/name).write_text(content,encoding='utf-8',newline='')
print(json.dumps({'included_cases':included_cases,'included_searches':included_searches,'counts':result['counts'],'report_paths':[str(ROOT/'qa-report.html'),str(legacy/'qa-report.html')]}))
