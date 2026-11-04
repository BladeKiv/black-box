"""Offline dispatch for the explicit extra=false override check."""
import html
import json
import re
from pathlib import Path
from bb.classify import classify_outcome

ticket=Path(__file__).resolve().parent
root=ticket/'runs'/'2026-11-02-extra-false'
c=json.loads((root/'EXTRA-01.json').read_text());b=c['response']['body'];rs=b['results']
assert c['response']['http_status']==200 and len(rs)>0
assert all('ngsItineraries' not in r for r in rs)
assert not any(':NGS#' in r.get('gdsOfferId','') for r in rs)
cfg=json.loads((root/'configuration.json').read_text())
assert next(x for x in cfg['response']['body']['upgrade_config']['configs'] if 'BCKDCR' in x.get('cid',[]))['mergeWithRegular'] is True
assert cfg['finished_at']<=c['started_at']
outcome=classify_outcome(200,json.dumps(b),None,{'expectation_observed':True,'response_paths':['$.results[*].ngsItineraries','$.results[*].gdsOfferId']})
assert outcome['status']=='PASS'
test={'id':'EXTRA-01','data':'BCKDCR · mergeWithRegular=true · extra=false · SFO-FRA 2027-02-25 · 1 ADT / C','expected':'extra=false returns no NGS options even when the matching CID has mergeWithRegular=true.','actual':str(len(rs))+' results; ngsItineraries is absent from every result; no NGS offer identifiers. ngsFeatures/ngsMap metadata remains present and is not counted as an itinerary option.','status':'PASS','sources':['EXTRA-01']}
result={'signal':'PASS','counts':{'PASS':1,'FAIL':0,'WARN':0},'searches':1,'tests':[test],'request':c['request'],'response_observations':{'http_status':200,'results':len(rs),'ngsItineraries_field_count':0,'ngs_offer_identifier_count':0,'ngsFeatures_field_count':sum('ngsFeatures' in r for r in rs),'ngsMap_present':'ngsMap' in b},'configuration_source':'configuration.json','capture':'EXTRA-01.json'}
(root/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='')
title='SS-6438 — Build UPG itineraries as main itineraries with NGS children (regular + upgrade options)'
strip='PREPROD | 2026-11-02 | BCKDCR | mergeWithRegular=true | extra=false | 1 Search'
md=title+'\n\nPASS — 1 PASS / 0 FAIL / 0 WARN\n'+strip+'\n\nIntended behavior: '+test['expected']+'\n\n| ID | Test data | Expected result | Actual result | Status |\n|---|---|---|---|---|\n| '+' | '.join(test[k] for k in ('id','data','expected','actual','status'))+' |\n\nEvidence: EXTRA-01.json (paired request/response), configuration.json. Exact CID BCKDCR confirmed live by user. No retry, polling, downstream call or configuration mutation. No trusted operational lesson applied.\n'
(root/'qa-report.md').write_text(md,encoding='utf-8',newline='')
e=html.escape
h=(ticket.parents[1]/'templates/airapi-qa-dispatch-template.html').read_text()
h=h.replace('&lt;Ticket title&gt;',e(title)).replace('Run &lt;YYYY-MM-DD&gt;<br>&lt;Endpoint / route / scope&gt;',e(strip)).replace('class="value fail">&lt;PASS / FAIL / WARN&gt;','class="value pass">PASS')
for n in ('1','0','0'):h=h.replace('&lt;0&gt;',n,1)
h=h.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;',e('Intended behavior: '+test['expected']+' '+test['actual']))
row='<tr><td>EXTRA-01</td><td class="test">'+e(test['data'])+'</td><td>'+e(test['expected'])+' → '+e(test['actual'])+'</td><td class="status pass">PASS</td></tr>'
h=re.sub(r'(?s)(<tbody>).*?(</tbody>)',lambda m:m[1]+row+m[2],h)
h=re.sub(r'(?s)<section class="failure-sample">.*?</section>','',h)
h=re.sub(r'(?s)<section class="evidence">.*?</section>','<section class="evidence"><div><h2>Evidence</h2><p>EXTRA-01.json paired request/response; configuration.json confirms BCKDCR mergeWithRegular=true before Search. No NGS options returned; feature metadata remains present.</p></div><div><h2>Rerun</h2><p>This case is included in the consolidated main report collection and expected-outcome CSV.</p></div></section>',h)
h=re.sub(r'(?s)const artifacts = \{.*?\n    \};','const artifacts = {};',h)
(root/'qa-report.html').write_text(h,encoding='utf-8',newline='')
print(json.dumps({'status':'PASS','results':len(rs),'ngsItineraries_fields':0,'ngs_offer_identifiers':0}))
