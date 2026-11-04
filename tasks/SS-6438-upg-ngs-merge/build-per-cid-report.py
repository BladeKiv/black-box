"""Render the fresh per-CID retest dispatch; no endpoint execution."""
import base64
import csv
import html
import importlib
import io
import json
import re
from pathlib import Path
from bb.classify import classify_outcome
from bb.escalations import Escalations,handle_outcome
from bb.lessons import Store

ticket=Path(__file__).resolve().parent
helper=importlib.import_module('tasks.SS-6438-upg-ngs-merge.retest-per-cid')
oracle=helper.oracle
root=helper.ROOT
plan=json.loads((root/'search-plan.json').read_text())
title='SS-6438 — Build UPG itineraries as main itineraries with NGS children (regular + upgrade options)'
run_id='SS-6438-'+root.name
captures={r['scenario_id']:json.loads((root/(r['scenario_id']+'.json')).read_text()) for r in plan}
summaries={n:json.loads((root/(n+'-summary.json')).read_text()) for n in captures}
assert len(captures)==13 and all(c['response']['http_status']==200 for c in captures.values())
config=json.loads((root/'configuration.json').read_text())['response']['body']
config_rows=[]
for cid in ('BCKDCR','AKKDCR'):
 matches=[(i,c) for i,c in enumerate(config['upgrade_config']['configs']) if cid in c.get('cid',[])]
 assert len(matches)==1
 i,c=matches[0];assert c['mergeWithRegular'] is True
 config_rows.append({'cid':cid,'config_index':i,'mergeWithRegular':c['mergeWithRegular'],'keepBothBagOptions':c['keepBothBagOptions']})

groups=[{'scenario_id':n,**g} for n,s in summaries.items() for g in s['groups']]
bad=[g for g in groups if not all(g[k] for k in ('price_order_ok','features_ok','flight_identity_ok','numbering_ok'))]
false_names=[r['scenario_id'] for r in plan if not r['keepBothBagOptions']]
true_names=[r['scenario_id'] for r in plan if r['keepBothBagOptions']]
false_groups=[g for g in groups if g['scenario_id'] in false_names]
upg_true=[g for g in groups if g['scenario_id'] in true_names and g['main_source']=='UPG']
reg_true=[g for g in groups if g['scenario_id'] in true_names and g['main_source']=='regular']
reg_false=[g for g in false_groups if g['main_source']=='regular']
upg_bad=[g for g in upg_true if g['violations']]
reg_bad=[g for g in reg_true if g['violations']]
price_bad=[g for g in groups if not g['price_order_ok']]
other_bad=[g for g in groups if not g['flight_identity_ok'] or not g['numbering_ok']]
for name in false_names:
 for g in summaries[name]['groups']:
  if any('upgrade_info' in x['keys'] for x in g['options'][1:]):other_bad.append(g)
option_count=sum(len(g['options']) for g in groups)
main_count=sum(s['result_count'] for s in summaries.values())

def row(id,data,expected,actual,status,sources):return dict(id=id,data=data,expected=expected,actual=actual,status=status,sources=sources)
tests=[
 row('TC-01','Example 1 · BCKDCR · UPG cheapest · keepBothBagOptions=false','Retain regular improvements under the UPG-cheapest main; each transition improves one feature without losing another.',f'{len(false_groups)} observable UPG-containing groups; {sum(bool(g["violations"]) for g in false_groups)} feature-violating groups.','FAIL' if any(g['violations'] for g in false_groups) else 'PASS',false_names),
 row('TC-02','Example 2 · AKKDCR · UPG cheapest · keepBothBagOptions=true','Filter any later option that loses bags, exchange or refund versus the last retained option.',f'{len(upg_true)} UPG-main groups; {len(upg_bad)} have feature regressions. '+('The LAX-MUC round trip still has retained feature regressions.' if upg_bad else 'No retained feature regression observed.'),'FAIL' if upg_bad else 'PASS' if upg_true else 'WARN',true_names),
 row('TC-03','Example 3 · BCKDCR · regular cheapest · keepBothBagOptions=false','Observe the positive regular-main/retained-UPG merge branch.',f'{len(reg_false)} qualifying regular-main groups with observable UPG options. Regular-only NGS groups do not establish the pre-filter existence of UPG candidates.','PASS' if reg_false else 'WARN',false_names),
 row('TC-04','Example 4 · AKKDCR · regular cheapest · keepBothBagOptions=true','A regular-cheapest main is allowed; an UPG child may not lose any confirmed feature.',f'{len(reg_true)} qualifying regular-main groups; {len(reg_bad)} fail. '+('Retained feature regressions remain.' if reg_bad else 'No retained feature regression observed; availability of this branch is evaluated separately.'),'FAIL' if reg_bad else 'PASS' if reg_true else 'WARN',true_names),
 row('TC-05',f'{len(groups)} observable UPG-containing groups · {option_count} retained USD options','Prices ascend; main is cheapest among retained options.',f'{len(price_bad)} retained price-order violations. Minimum of an unseen pre-filter set is not certified.','FAIL' if price_bad else 'PASS',list(captures)),
 row('TC-06','Returned children · configured eligibility · numbering/singleton rule','Children match their main flights. Other UPG children require keepBothBagOptions=true. Numbered groups are sequential; singleton :UPG# is allowed.',f'{len(other_bad)} same-flight, child-eligibility or numbering violations.','FAIL' if other_bad else 'PASS',list(captures)),
 row('TC-07','Complete pre-filter elimination/retention completeness','Evaluate the full candidate set, including dropped options.',f'{len(bad)} observable failing groups are conclusive; full candidate-set completeness remains unverified because no certified pre-filter candidate set is exposed.','WARN',list(captures)),
]
counts={status:sum(t['status']==status for t in tests) for status in ('PASS','FAIL','WARN')}
signal='FAIL' if counts['FAIL'] else 'WARN' if counts['WARN'] else 'PASS'

def body_excerpt(name,indices):
 results=captures[name]['response']['body']['results'];items=[]
 for index in indices:
  m=results[index];item=oracle.excerpt(m)
  if 'ngsItineraries' in m:item['ngsItineraries']=[oracle.excerpt(x) for x in m['ngsItineraries']]
  items.append(item)
 return {'count':captures[name]['response']['body']['count'],'results':items}
def paired(name,indices):return {'request':captures[name]['request'],'started_at':captures[name]['started_at'],'response_excerpt':{'http_status':captures[name]['response']['http_status'],'body':body_excerpt(name,indices)}}

payloads={}
for t in tests:
 if t['status'] not in ('WARN','FAIL'):continue
 selected=upg_bad if t['id']=='TC-02' else reg_bad if t['id']=='TC-04' else []
 payloads[t['id']]=[]
 for name in t['sources']:
  gs=[g for g in selected if g['scenario_id']==name] if selected else summaries[name]['groups'][:1]
  if selected and not gs:continue
  payloads[t['id']].append(paired(name,[g['result_index'] for g in gs]))

comparisons=[]
for name,oldindex in [('R02-A',2),('R04-A',514)]:
 old=json.loads((ticket/(name+'.json')).read_text())['response']['body']['results'][oldindex]
 matches=[(i,r) for i,r in enumerate(captures[name]['response']['body']['results']) if oracle.signature(old)==oracle.signature(r)]
 detail={'scenario_id':name,'old_result_index':oldindex,'old_main_key':old['key'],'fresh_matching_itineraries':[]}
 for i,r in matches:
  opts=[r]+r.get('ngsItineraries',[]);fs=[oracle.features(x) for x in opts]
  detail['fresh_matching_itineraries'].append({'result_index':i,'main_key':r['key'],'options':[oracle.excerpt(x) for x in opts],'feature_rule_passes':all(oracle.improves(a,b) for a,b in zip(fs[1:],fs))})
 comparisons.append(detail)

# Evaluate the exact flight sequences of every historically failing group separately
# from branch coverage; a removed offending child does not prove fresh candidate availability.
historical=json.loads((ticket/'all-cases-analysis.json').read_text())['failing_groups']
regressions=[]
for old_group in historical:
 name=old_group['scenario_id']
 old=json.loads((ticket/(name+'.json')).read_text())['response']['body']['results'][old_group['result_index']]
 matches=[(i,r) for i,r in enumerate(captures[name]['response']['body']['results']) if oracle.signature(old)==oracle.signature(r)]
 entry={'scenario_id':name,'old_result_index':old_group['result_index'],'matches':[]}
 for i,m in matches:
  options=[m]+m.get('ngsItineraries',[]);fs=[oracle.features(o) for o in options]
  entry['matches'].append({'result_index':i,'main_key':m['key'],'options':[oracle.excerpt(o) for o in options],'feature_rule_passes':all(oracle.improves(a,b) for a,b in zip(fs[1:],fs)),'previous_offending_keys_retained':[v['current']['key'] for v in old_group['violations'] if any(o['key']==v['current']['key'] for o in options)]})
 regressions.append(entry)
regression_matches=sum(len(x['matches'])==1 for x in regressions)
regression_bad=sum(any(not m['feature_rule_passes'] for m in x['matches']) for x in regressions)
tests.append(row('TC-08','Exact flight sequences of the 19 historically failing groups','Find the same itineraries and verify their current retained options satisfy the confirmed feature rule.',f'{regression_matches}/19 exact flight sequences matched; {regression_bad} matched groups retain feature regressions. Removed children do not establish availability of an unobserved positive branch.','FAIL' if regression_bad else 'PASS' if regression_matches==len(regressions) else 'WARN',['R02-A','R04-A']))
if tests[-1]['status'] in ('FAIL','WARN'):
 payloads['TC-08']=[paired(name,[m['result_index'] for x in regressions if x['scenario_id']==name for m in x['matches']]) for name in ('R02-A','R04-A')]
counts={status:sum(t['status']==status for t in tests) for status in ('PASS','FAIL','WARN')}
signal='FAIL' if counts['FAIL'] else 'WARN' if counts['WARN'] else 'PASS'

store=Store();esc=Escalations(store=store)
known={e.get('run') for e in esc.events() if e.get('event')=='run'}
for t in tests:
 if t['status']!='WARN':continue
 case_run=run_id+'-'+t['id']
 if case_run in known:continue
 c=captures[t['sources'][0]]['response']
 outcome=classify_outcome(c['http_status'],json.dumps(c['body']),c['transport_error'],{'inventory_field':'results','comparable_count':0,'observed_expectation':t['expected'],'response_paths':['$.results[*].keys.upgrade_info','$.results[*].ngsItineraries']})
 handle_outcome(store,esc,outcome,case_run,['SS-6438','PREPROD'],'regular cheapest keepBoth false positive inventory unavailable' if t['id']=='TC-03' else 'complete prefilter candidate set unavailable',{'ticket':'SS-6438','environment':'PREPROD','endpoint':'/v1/search','allow_retry':False,'allow_poll':False,'allow_retest':True,'approved_inputs':['search-plan.json']},retries=0,steps=1)

collection=json.loads((ticket/'collection.json').read_text())
collection['info']['description']='Fresh PREPROD retest after the per-CID flag migration. Read-only AirAPI Search only. Run with expected-outcomes.csv (13 rows). Prerequisite: the matching upgrade_config.configs[] entry has mergeWithRegular=true; the old global enable_merge is not used. Existing environment supplies search_authorization at runtime. Singleton :UPG# is accepted. Missing regular-cheapest inventory is WARN; complete pre-filter candidate sets are not certified by retained-output assertions.'
oldrows=list(csv.DictReader((ticket/'expected-outcomes.csv').open(encoding='utf-8',newline='')))
fields=list(oldrows[0])+['mergeWithRegular','upgrade_config_index']
for r in oldrows:
 cfg=next(c for c in config_rows if c['cid']==r['cid']);r.update(mergeWithRegular='true',upgrade_config_index=str(cfg['config_index']))
out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=fields);w.writeheader();w.writerows(oldrows)
(root/'expected-outcomes.csv').write_text(out.getvalue(),encoding='utf-8')
(root/'collection.json').write_text(json.dumps(collection,indent=2),encoding='utf-8')

start=min(c['started_at'] for c in captures.values());end=max(c['finished_at'] for c in captures.values())
strip=f'PREPROD | 2026-11-02 | HTTP Search | 13 fresh calls · {main_count:,} main results | per-CID mergeWithRegular=true'
matched=sum(bool(x['fresh_matching_itineraries']) for x in comparisons)
comparison_bad=sum(any(not m['feature_rule_passes'] for m in x['fresh_matching_itineraries']) for x in comparisons)
summary=f'Fresh PREPROD retest: {len(groups)} observable UPG-containing groups / {option_count} retained options. {len(upg_bad)} UPG-main groups and {len(reg_bad)} regular-main groups violate the confirmed feature rule. {matched}/2 concrete examples and {regression_matches}/19 historical failing flight sequences were matched; {regression_bad} matched historical groups retain feature regressions. Full candidate-set completeness and branches lacking qualifying fresh inventory remain unverified.'
intended='The cheapest eligible regular or UPG option is main NGS#1. Each later retained option must be no worse on bags, exchange and refund and better on at least one. Bags=keys.baggage.allowPieces; exchange/refund=penalties.exchange/refund. Regular children require ngs_jobs and the matching mergeWithRegular setting; other UPG children additionally require keepBothBagOptions=true. Singleton :UPG# is valid under the user clarification.'
md=[title,'',signal+' — '+str(counts['PASS'])+' PASS / '+str(counts['FAIL'])+' FAIL / '+str(counts['WARN'])+' WARN',strip,'','Intended behavior: '+intended,'',summary,'','| ID | Test data | Expected result | Actual result | Status |','|---|---|---|---|---|']
for t in tests:md.append('| '+' | '.join(t[k] for k in ('id','data','expected','actual','status'))+' |')
md+=['','Supporting evidence and rerun','', 'Fresh configuration.json: AKKDCR config[2] and BCKDCR config[3] both mergeWithRegular=true; keepBothBagOptions true/false respectively. The global enable_merge field is absent. Configuration discovery is prerequisite evidence only.','', f'Run interval UTC: {start} to {end}. All 13 Search URLs replayed once without input changes; no retries, polling, downstream endpoints, configuration mutation, booking or Jira changes.','', 'Per-case paired captures: M01–M05.json and R01–R04-A/B.json. analysis.json includes fresh group evaluations; failure-searches-and-keys.json includes exact fresh keys and traces; previous-failures-comparison.json matches the two previously supplied concrete itineraries. payload-evidence.json contains all WARN/FAIL excerpts.','', 'Run collection.json with expected-outcomes.csv in Postman. Both are embedded as Blob downloads in the matching HTML dispatch. Earlier run evidence is preserved separately; no old result is counted as a fresh PASS. No trusted matching operational lesson applied.']
(root/'qa-report.md').write_text('\n'.join(md)+'\n',encoding='utf-8')

e=html.escape
template=(ticket.parents[1]/'templates/airapi-qa-dispatch-template.html').read_text(encoding='utf-8')
template=template.replace('&lt;Ticket title&gt;',e(title)).replace('Run &lt;YYYY-MM-DD&gt;<br>&lt;Endpoint / route / scope&gt;',e(strip)).replace('&lt;PASS / FAIL / WARN&gt;',signal)
for value in (counts['PASS'],counts['FAIL'],counts['WARN']):template=template.replace('&lt;0&gt;',str(value),1)
template=template.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;',e(summary)+'<br><strong>Intended behavior:</strong> '+e(intended))
tbody=''.join('<tr><td>'+e(t['id'])+'</td><td class="test">'+e(t['data'])+'</td><td>'+e(t['expected'])+' → '+e(t['actual'])+'</td><td class="status '+t['status'].lower()+'">'+t['status']+'</td></tr>' for t in tests)
template=re.sub(r'(?s)(<tbody>).*?(</tbody>)',lambda m:m[1]+tbody+m[2],template)
samples=[]
for t in tests:
 if t['id'] not in payloads:continue
 samples.append('<section class="failure-sample"><h2>'+e(t['id'])+' · '+t['status']+' · Paired payload evidence</h2><p>'+e(t['actual'])+'</p><pre>'+e(json.dumps(payloads[t['id']],indent=2))+'</pre></section>')
template=re.sub(r'(?s)<section class="failure-sample">.*?</section>',lambda m:'\n'.join(samples),template)
section='<section class="evidence"><div><h2>Fresh configuration and evidence</h2><p>Per-CID mergeWithRegular=true for AKKDCR config[2] and BCKDCR config[3]. Global enable_merge absent. Thirteen fresh paired captures, analysis.json, previous-failures-comparison.json and failure-searches-and-keys.json. Configuration discovery does not prove request execution. Earlier evidence remains separate.</p></div><div><h2>Rerun artifacts</h2><p><button class="download-artifact" type="button" data-file="collection.json">Postman collection</button><br><button class="download-artifact" type="button" data-file="expected-outcomes.csv">Expected-outcome CSV</button></p></div></section>'
template=re.sub(r'(?s)<section class="evidence">.*?</section>',lambda m:section,template)
artifacts={n:{'type':mime,'content':base64.b64encode((root/n).read_bytes()).decode()} for n,mime in [('collection.json','application/json;charset=utf-8'),('expected-outcomes.csv','text/csv;charset=utf-8')]}
template=re.sub(r'(?s)const artifacts = \{.*?\n    \};',lambda m:'const artifacts = '+json.dumps(artifacts)+';',template)
(root/'qa-report.html').write_text(template,encoding='utf-8')
(root/'results.json').write_text(json.dumps({'run':run_id,'signal':signal,'counts':counts,'searches':13,'main_results':main_count,'groups':len(groups),'options':option_count,'failing_groups':len(bad),'tests':tests,'configuration':config_rows,'started_at':start,'finished_at':end},indent=2),encoding='utf-8')
(root/'analysis.json').write_text(json.dumps({'runs':[{'scenario_id':n,'keepBothBagOptions':next(r['keepBothBagOptions'] for r in plan if r['scenario_id']==n),**s} for n,s in summaries.items()],'failing_groups':bad},indent=2),encoding='utf-8')
(root/'payload-evidence.json').write_text(json.dumps(payloads,indent=2),encoding='utf-8')
(root/'previous-failures-comparison.json').write_text(json.dumps(comparisons,indent=2),encoding='utf-8')
(root/'all-previous-failures-comparison.json').write_text(json.dumps(regressions,indent=2),encoding='utf-8')
failure_keys=[]
for g in bad:
 n=g['scenario_id'];c=captures[n];trace=next((m['value'] for m in c['response']['body'].get('messages',[]) if m.get('type')=='TRACEID'),None)
 failure_keys.append({'scenario_id':n,'status':'FAIL','search_request':c['request'],'captured_at':c['started_at'],'trace_id':trace,'main_response_path':'results['+str(g['result_index'])+']','main_key':g['options'][0]['key'],'violations':g['violations']})
(root/'failure-searches-and-keys.json').write_text(json.dumps({'environment':'PREPROD','cid':'AKKDCR','groups':len(bad),'failures':failure_keys},indent=2),encoding='utf-8')
print(json.dumps({'signal':signal,'counts':counts,'searches':13,'main_results':main_count,'groups':len(groups),'options':option_count,'failing_groups':len(bad),'previous_example_matches':[len(x['fresh_matching_itineraries']) for x in comparisons]}))
