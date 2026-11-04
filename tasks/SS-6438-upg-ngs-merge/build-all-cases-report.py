"""Generate the expanded ticket dispatch from saved Search evidence only."""
import base64
import csv
import html
import importlib
import io
import json
import re
from pathlib import Path
from urllib.parse import parse_qs,urlsplit

ROOT=Path(__file__).resolve().parent
mod=importlib.import_module('tasks.SS-6438-upg-ngs-merge.analyze-merge')
hunt=importlib.import_module('tasks.SS-6438-upg-ngs-merge.search-all-cases')
TITLE='SS-6438 — Build UPG itineraries as main itineraries with NGS children (regular + upgrade options)'
RUN='SS-6438-20261102-all-cases'
names=['M01','M02','M03','M04','M05']+[x['id'] for x in hunt.PLAN if (ROOT/(x['id']+'.json')).exists()]
captures={n:json.loads((ROOT/(n+'.json')).read_text()) for n in names}
runs=[]
for name,c in captures.items():
 assert c['response']['http_status']==200
 rs=c['response']['body']['results'];groups=[]
 for index,main in enumerate(rs):
  children=main.get('ngsItineraries',[])
  if 'upgrade_info' not in main.get('keys',{}) and not any('upgrade_info' in x.get('keys',{}) for x in children):continue
  opts=[main]+children;fs=[mod.features(x) for x in opts];prices=[x['prices']['totalPrice'] for x in opts]
  assert all(x.get('currency')=='USD' for x in opts)
  violations=[]
  for i in range(1,len(opts)):
   if not mod.improves(fs[i],fs[i-1]):violations.append({'option_index':i,'previous':mod.excerpt(opts[i-1]),'current':mod.excerpt(opts[i]),'lost_features':[f for f,a,b in zip(['bags','exchange','refund'],fs[i],fs[i-1]) if a<b]})
  groups.append({'result_index':index,'main_source':'UPG' if 'upgrade_info' in main.get('keys',{}) else 'regular','options':[mod.excerpt(x) for x in opts],'price_order_ok':prices==sorted(prices),'flight_identity_ok':all(mod.signature(main)==mod.signature(x) for x in children),'numbering_ok':all(x.get('gdsOfferId','').endswith(':NGS#'+str(i+1)) for i,x in enumerate(opts)) if children else main.get('gdsOfferId')==':UPG#','violations':violations})
 q=parse_qs(urlsplit(c['request']['url']).query)
 runs.append({'scenario_id':name,'cid':q['cid'][0],'keepBothBagOptions':q['cid'][0]=='AKKDCR','request':c['request'],'result_count':len(rs),'groups':groups})
groups=[g for r in runs for g in r['groups']]
bad=[{'scenario_id':r['scenario_id'],**g} for r in runs for g in r['groups'] if g['violations']]
assert len(names)==13 and len(groups)==451 and len(bad)==19
assert all(g['price_order_ok'] and g['flight_identity_ok'] and g['numbering_ok'] for g in groups)
assert all('upgrade_info' not in o['keys'] for r in runs if not r['keepBothBagOptions'] for g in r['groups'] for o in g['options'][1:])
assert sum(g['main_source']=='regular' for g in groups)==9
upg_bad=[g for g in bad if g['main_source']=='UPG'];reg_bad=[g for g in bad if g['main_source']=='regular']
assert len(upg_bad)==10 and len(reg_bad)==9
option_count=sum(len(g['options']) for g in groups)
false_groups=[g for r in runs if not r['keepBothBagOptions'] for g in r['groups']]
true_groups=[g for r in runs if r['keepBothBagOptions'] for g in r['groups']]

def test(id,data,expected,actual,status):return dict(id=id,data=data,expected=expected,actual=actual,status=status)
tests=[
 test('TC-01','Ticket example 1 · BCKDCR · keepBothBagOptions=false','UPG-cheapest main; eligible regular children improve all three features monotonically.',f'{len(false_groups)} UPG-containing groups across six Searches; no retained feature regression; no other UPG children. Representative R02-B reproduces the 1-bag/exchange → 2-bag/exchange → refundable progression.','PASS'),
 test('TC-02','Ticket example 2 · AKKDCR · keepBothBagOptions=true · R02-A LAX-MUC return','After a 2-bag option is kept, filter a later 1-bag option even if exchange improves. Also filter an option that loses exchange.','FAIL in 10 UPG-main groups. Example: NGS#2 has 2 bags/exchange=false; NGS#3 is retained with 1 bag/exchange=true. A separate group retains a UPG option that loses exchange.','FAIL'),
 test('TC-03','Ticket example 3 · BCKDCR · regular cheapest · keepBothBagOptions=false','Observe a regular-cheapest group with a retained improving UPG option and eligible regular children.','No qualifying positive regular-main/retained-UPG group found in the six BCKDCR Searches. Regular-only NGS groups are not proof that UPG candidates existed before filtering.','WARN'),
 test('TC-04','Ticket example 4 · AKKDCR · regular cheapest · keepBothBagOptions=true · R04-A JFK-LHR return','Regular-cheapest main is NGS#1; keep an UPG child only if it does not lose any confirmed feature.','Regular-cheapest branch observed in nine groups; all nine fail. Example: regular main USD 4262.65 has exchange=true; retained UPG child USD 5535.34 has exchange=false.','FAIL'),
 test('TC-05',f'{len(groups)} UPG-containing groups · {option_count} returned options','Within each returned group, prices ascend and main is cheapest among retained options.','All 451 groups pass retained price ordering. This does not prove the absolute minimum of an unseen pre-filter candidate set.','PASS'),
 test('TC-06','All returned UPG groups · configured child-source flags · user-confirmed singleton exception','Children share their main flight sequence; other UPG children require keepBothBagOptions=true; numbering is sequential, with :UPG# allowed for singletons.','All checked groups pass same-flight identity, configured UPG-child eligibility and numbering/singleton rules.','PASS'),
 test('TC-07','Complete pre-filter candidate elimination/completeness','Evaluate every omitted or retained candidate against the ticket rule using a complete pre-filter candidate set.','The 19 observed retained-group failures conclusively violate the rule. Complete exclusion/retention completeness remains unverified because captures lack a certified pre-filter candidate set.','WARN'),
]
counts={s:sum(t['status']==s for t in tests) for s in ('PASS','FAIL','WARN')}
assert counts=={'PASS':3,'FAIL':2,'WARN':2}

def group_body(name,index):
 r=captures[name]['response']['body']['results'][index]
 return {**mod.excerpt(r),**({'ngsItineraries':[mod.excerpt(x) for x in r['ngsItineraries']]} if 'ngsItineraries' in r else {})}

def paired(name,indices):
 c=captures[name]
 return {'request':c['request'],'response_excerpt':{'http_status':c['response']['http_status'],'body':{'count':c['response']['body']['count'],'results':[group_body(name,i) for i in indices]}}}
payloads={
 'TC-02':[paired('R02-A',[g['result_index'] for g in upg_bad])],
 'TC-03':[paired(r['scenario_id'],[g['result_index'] for g in r['groups'][:2]]) for r in runs if not r['keepBothBagOptions']],
 'TC-04':[paired('R04-A',[g['result_index'] for g in reg_bad])],
 'TC-07':[paired(n,[next(r for r in runs if r['scenario_id']==n)['groups'][0]['result_index']] if next(r for r in runs if r['scenario_id']==n)['groups'] else []) for n in names],
}

examples=[('Example 1 — PASS','R02-B',0),('Example 2 — FAIL: fewer-bag option retained','R02-A',2),('Example 4 — FAIL: exchange-losing UPG child retained','R04-A',514)]
def table_rows(name,index):
 r=captures[name]['response']['body']['results'][index]
 rows=[];reg=0
 for o in [r]+r.get('ngsItineraries',[]):
  upg='upgrade_info' in o.get('keys',{})
  if not upg:reg+=1
  option='UPG itin' if upg else 'Regular '+str(reg)
  f=mod.features(o)
  rows.append([option,f"{o['prices']['totalPrice']:,.2f}",str(f[0]),str(int(f[1])),str(int(f[2])),o.get('gdsOfferId','')+(' (main)' if o is r else '')])
 return rows

# Preserve the previous five-Search dispatch before superseding it.
for name in ('qa-report.md','qa-report.html','results.json','expected-outcomes.csv','collection.json'):
 archive=ROOT/('initial-five-searches-'+name)
 if not archive.exists():archive.write_bytes((ROOT/name).read_bytes())

oldrows=list(csv.DictReader((ROOT/'initial-five-searches-expected-outcomes.csv').open(encoding='utf-8',newline='')))
fields=list(oldrows[0])+['return_date']
for r in runs:
 if r['scenario_id'].startswith('M'):continue
 q=parse_qs(urlsplit(r['request']['url']).query)
 row=dict(oldrows[0]);row.update(scenario_id=r['scenario_id'],search_url=r['request']['url'],cid=r['cid'],origin=q['fl[0][o]'][0],destination=q['fl[0][d]'][0],departure_date=q['fl[0][dt]'][0],return_date=q['fl[1][dt]'][0],keepBothBagOptions=str(r['keepBothBagOptions']).lower())
 oldrows.append(row)
out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader();writer.writerows(oldrows)
(ROOT/'expected-outcomes.csv').write_text(out.getvalue(),encoding='utf-8')
collection=json.loads((ROOT/'initial-five-searches-collection.json').read_text())
collection['info']['description']=collection['info']['description'].replace('(five rows)','(thirteen rows; eight additional round-trip searches)').replace('Complete pre-filter candidate elimination is not certified by these retained-output checks.','The retained-output assertions detect the observed LAX-MUC and JFK-LHR feature-loss failures. Complete pre-filter candidate elimination remains unverified.')
(ROOT/'collection.json').write_text(json.dumps(collection,indent=2),encoding='utf-8')

strip='PREPROD | 2026-11-02 | HTTP Search | 13 Searches · 3,916 main results · merge=true'
summary='Expanded inventory testing found 19 feature-filter failures: 10 UPG-main groups on AKKDCR LAX-MUC and nine regular-main groups on AKKDCR JFK-LHR. Earlier five-Search retained-output passes remain historical evidence; the expanded result supersedes the overall release signal. The regular-cheapest/keepBothBagOptions=false positive branch and complete pre-filter candidate completeness remain unverified.'
intended='Sort eligible regular/UPG candidates by price. Cheapest becomes main NGS#1. Each retained option must be equal or better on bags, exchange and refund, and strictly better on at least one. Regular children require ngs_jobs; other UPG children also require keepBothBagOptions=true. User-confirmed fields are keys.baggage.allowPieces and penalties.exchange/refund; singleton :UPG# is valid.'
md=[TITLE,'','FAIL — 3 PASS / 2 FAIL / 2 WARN',strip,'','Intended behavior: '+intended,'',summary,'','| ID | Test data | Expected result | Actual result | Status |','|---|---|---|---|---|']
for t in tests:md.append('| '+' | '.join(t[k] for k in ('id','data','expected','actual','status'))+' |')
md+=['','Observed ticket-format examples','', 'Prices USD; dates 2027-02-25 to 2027-03-11; 1 ADT; cabin C. Exchange/refund: 0=false, 1=true. Tables show actual retained results; failing options should have been filtered.','']
for title,name,index in examples:
 md += [title+' · '+name,'','| Option | Price | Bags | Exchange | Refund | Result |','|---|---:|---:|---:|---:|---|']
 for row in table_rows(name,index):md.append('| '+' | '.join(row)+' |')
 md+=['']
md += ['Example 3: WARN — no positive regular-cheapest/keepBothBagOptions=false group with a retained UPG option was observed.','', 'Supporting evidence and rerun','', 'All M01–M05 and R01–R04-A/B paired sanitized captures are retained. all-cases-analysis.json identifies exact result indices and every failing transition. all-cases-payload-evidence.json contains paired FAIL/WARN excerpts. Run collection.json with expected-outcomes.csv using the existing PREPROD environment. HTML downloads embed both artifacts as Blob content.','', 'Eight additional Searches executed: SFO-FRA return, LAX-MUC return, ORD-FRA return and JFK-LHR return, each paired across BCKDCR/AKKDCR. Four candidate steps per missing branch; no retries, polling, downstream endpoints, booking, configuration mutation or Jira writes. Fifth prepared route was not executed.','', 'Scope: 451 observable UPG-containing groups / '+str(option_count)+' retained options. Complete pre-filter candidate sets are unavailable. Regular-only groups without an observable UPG option cannot certify the missing positive UPG merge branch. Configuration discovery remains prerequisite evidence only. No trusted matching operational lesson was applied.']
(ROOT/'qa-report.md').write_text('\n'.join(md)+'\n',encoding='utf-8')

e=html.escape
template=(ROOT.parents[1]/'templates/airapi-qa-dispatch-template.html').read_text(encoding='utf-8')
template=template.replace('&lt;Ticket title&gt;',e(TITLE)).replace('Run &lt;YYYY-MM-DD&gt;<br>&lt;Endpoint / route / scope&gt;',e(strip)).replace('&lt;PASS / FAIL / WARN&gt;','FAIL')
for count in ('3','2','2'):template=template.replace('&lt;0&gt;',count,1)
template=template.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;',e(summary)+'<br><strong>Intended behavior:</strong> '+e(intended))
tbody='\n'.join('<tr><td>'+e(t['id'])+'</td><td class="test">'+e(t['data'])+'</td><td>'+e(t['expected'])+' → '+e(t['actual'])+'</td><td class="status '+t['status'].lower()+'">'+t['status']+'</td></tr>' for t in tests)
template=re.sub(r'(?s)(<tbody>).*?(</tbody>)',lambda m:m[1]+tbody+m[2],template)
samples=[]
for t in tests:
 if t['status'] not in ('FAIL','WARN'):continue
 samples.append('<section class="failure-sample"><h2>'+e(t['id'])+' · '+t['status']+' · Paired payload evidence</h2><p>'+e(t['actual'])+'</p><pre>'+e(json.dumps(payloads[t['id']],indent=2))+'</pre></section>')
tables=[]
for title,name,index in examples:
 rows=table_rows(name,index)
 tables.append('<h2>'+e(title+' · '+name)+'</h2><div class="table-wrap"><table><thead><tr>'+''.join('<th>'+x+'</th>' for x in ('Option','Price (USD)','Bags','Exchange','Refund','Result'))+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+e(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>')
template=re.sub(r'(?s)<section class="failure-sample">.*?</section>',lambda m:'\n'.join(tables+samples),template)
section='<section class="evidence"><div><h2>Evidence and coverage limits</h2><p>all-cases-analysis.json; all-cases-payload-evidence.json; 13 paired Search captures. Example 3 remains WARN. No complete pre-filter candidate baseline. Current failures supersede the earlier overall release signal; prior artifacts are preserved under initial-five-searches-*.</p></div><div><h2>Rerun artifacts</h2><p><button class="download-artifact" type="button" data-file="collection.json">Postman collection</button><br><button class="download-artifact" type="button" data-file="expected-outcomes.csv">Expected-outcome CSV</button></p></div></section>'
template=re.sub(r'(?s)<section class="evidence">.*?</section>',lambda m:section,template)
artifacts={n:{'type':mime,'content':base64.b64encode((ROOT/n).read_bytes()).decode()} for n,mime in [('collection.json','application/json;charset=utf-8'),('expected-outcomes.csv','text/csv;charset=utf-8')]}
template=re.sub(r'(?s)const artifacts = \{.*?\n    \};',lambda m:'const artifacts = '+json.dumps(artifacts)+';',template)
(ROOT/'qa-report.html').write_text(template,encoding='utf-8')
(ROOT/'all-cases-analysis.json').write_text(json.dumps({'runs':runs,'failing_groups':bad},indent=2),encoding='utf-8')
(ROOT/'all-cases-payload-evidence.json').write_text(json.dumps(payloads,indent=2),encoding='utf-8')
(ROOT/'results.json').write_text(json.dumps({'run':RUN,'signal':'FAIL','counts':counts,'searches':13,'main_results':3916,'groups':451,'options':option_count,'failing_groups':19,'tests':tests},indent=2),encoding='utf-8')
print(json.dumps({'counts':counts,'searches':len(names),'groups':len(groups),'options':option_count,'failing_groups':len(bad),'regular_main_failing_groups':len(reg_bad)}))
