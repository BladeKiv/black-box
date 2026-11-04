"""Build the dispatch from captured evidence; makes no network requests."""
import html
import json
import re
from pathlib import Path
from bb.classify import classify_outcome
from bb.escalations import Escalations, handle_outcome
from bb.lessons import Store

ROOT = Path(__file__).resolve().parent
TITLE = 'SS-6438 — Build UPG itineraries as main itineraries with NGS children (regular + upgrade options)'
RUN = 'SS-6438-20261102-http-prerequisites'
config = json.loads((ROOT / 'configuration-http-direct.json').read_text())
search = json.loads((ROOT / 'S02.json').read_text())
transport = json.loads((ROOT / 'S01.json').read_text())
assert config['response']['body']['upgrade_config']['enable_merge'] is False
results = search['response']['body']['results']
upgrades = sum('upgrade_info' in r.get('keys', {}) for r in results)
assert upgrades == 0
rows = [
    {'id':'TC-01', 'data':'PREPROD GET /algo/conf', 'expected':'Ticket prerequisite: upgrade_config.enable_merge=true; ngs_jobs enabled for eligible CID/OD.', 'actual':'HTTP 200; upgrade_config.enable_merge=false; upgrade_config.enable=true; ngs_jobs.enable=true. Merge matrix blocked.', 'status':'WARN', 'capture':config, 'context':{'inventory_field':None,'comparable_count':0}, 'pattern':'merge test prerequisite disabled in current environment', 'path':'$.upgrade_config.enable_merge'},
    {'id':'TC-02', 'data':'S02: TST101; C; LH/S/6NVG/SR; FRA-CDG 2026-11-20, CDG-MUC 2026-11-30', 'expected':'A qualifying group with UPG options is required to evaluate cheapest-main and progressive feature filtering.', 'actual':f'HTTP 200; {len(results)} PUB results; {upgrades} UPG results; no ngsItineraries fields. TST101 is absent from the returned UPG/ngs CID lists.', 'status':'WARN', 'capture':search, 'context':{'inventory_field':'results','comparable_count':0}, 'pattern':'nonqualifying search inventory has no upgrade candidates', 'path':'$.results[*].keys.upgrade_info; $.results[*].ngsItineraries'},
    {'id':'TC-03', 'data':'S01: initial HTTP Search through inherited localhost proxy', 'expected':'Reach Search and obtain evaluable response data.', 'actual':'No HTTP response; WinError 10061 from inherited proxy route. Direct HTTP access later succeeded independently in S02.', 'status':'WARN', 'capture':transport, 'context':{'inventory_field':'results'}, 'pattern':'inherited localhost proxy refuses connection', 'path':'$.response.transport_error'},
]
store = Store()
esc = Escalations(store=store)
for row in rows:
    response = row['capture']['response']
    outcome = classify_outcome(response['http_status'], json.dumps(response['body']), response['transport_error'], row['context'])
    assert outcome['status'] == row['status']
    scope = {'ticket':'SS-6438','environment':'PREPROD','endpoint':'/algo/conf' if row['id']=='TC-01' else '/v1/search','allow_retry':False,'allow_poll':False,'allow_retest':False,'approved_inputs':[]}
    outcome = handle_outcome(store, esc, outcome, RUN+'-'+row['id'], ['SS-6438','PREPROD'], row['pattern'], scope, retries=0, steps=1)
    row['reason_code'] = outcome['reason_code']
    row['response_paths'] = row['path']
esc.ask(run=RUN, question='May I also read /algo/conf over HTTP using existing PREPROD authentication, or can you provide an eligible CID/OD?', reason_code='ACCESS_SCOPE_CLARIFICATION', matching_lesson_found=False, tags=['SS-6438','PREPROD'], pattern='authenticated http configuration access requires direct user decision', scope_conditions={'ticket':'SS-6438','environment':'PREPROD','endpoint':'/algo/conf'})
esc.ask(run=RUN, question='PREPROD has upgrade_config.enable_merge=false. Please have it enabled and tell me when ready so I can test the merge behavior.', reason_code='PREREQUISITE_DISABLED', matching_lesson_found=False, tags=['SS-6438','PREPROD'], pattern='merge prerequisite disabled', scope_conditions={'ticket':'SS-6438','environment':'PREPROD','endpoint':'/algo/conf'})

intended = 'For an itinerary with UPG options, the cheapest eligible regular or UPG option becomes main NGS#1. Regular children require ngs_jobs; other UPG children also require keepBothBagOptions=true. Subsequent retained options must be equal or better on all bags/exchange/refund features and strictly better on at least one. Equal-feature higher-price and feature-losing options are dropped.'
summary = 'Merge testing is blocked: PREPROD reports upgrade_config.enable_merge=false. Direct HTTP Search works, but the TST101 reconnaissance returned only regular PUB fares and cannot evaluate the merge. Five configuration-relevant BCKDCR/AKKDCR examples are prepared and unexecuted.'
strip = 'PREPROD | 2026-11-02 | http://airapi51.kivops.info | Search-only ticket; configuration prerequisites separate'
md = [TITLE, '', 'WARN — BLOCKED | 0 PASS / 0 FAIL / 3 WARN', strip, '', 'Intended behavior: '+intended, '', summary, '', '| ID | Test data | Expected result | Actual result | Status |', '|---|---|---|---|---|']
for r in rows:
    md.append('| '+' | '.join(r[k] for k in ('id','data','expected','actual','status'))+' |')
md.extend(['', 'Supporting evidence: configuration-http-direct.json, S02.json, S01.json. Request/response excerpts are embedded in the matching HTML dispatch.', '', 'Configuration eligibility: BCKDCR keepBothBagOptions=false; AKKDCR keepBothBagOptions=true; ngs_jobs includes US-Europe routes. Configuration discovery does not prove per-request merge execution. No merge checks, downstream requests, configuration changes, or Jira writes were performed. Search keys were not decoded or rewritten.', '', 'Current HTTP Search and authenticated HTTP configuration access were explicitly authorized by the user. Earlier transport errors came through an unavailable localhost proxy. The initial query flag parameters are not evidence of effective configuration.', '', 'Operational lesson search returned no matching ticket/endpoint conditions; no lesson applied. The access decision remains in ticket scope, never learned.'])
(ROOT / 'qa-report.md').write_text('\n'.join(md)+'\n', encoding='utf-8')

template = (ROOT.parents[1] / 'templates/airapi-qa-dispatch-template.html').read_text(encoding='utf-8')
e = html.escape
template = template.replace('&lt;Ticket title&gt;', e(TITLE))
template = template.replace('Run &lt;YYYY-MM-DD&gt;<br>&lt;Endpoint / route / scope&gt;', e(strip))
template = template.replace('class="value fail">&lt;PASS / FAIL / WARN&gt;', 'class="value warn">WARN · BLOCKED')
for count in ('0','0','3'):
    template = template.replace('&lt;0&gt;', count, 1)
template = template.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;', e(summary)+'<br><strong>Intended behavior:</strong> '+e(intended))
tbody = '\n'.join('<tr><td>'+e(r['id'])+'</td><td class="test">'+e(r['data'])+'</td><td>'+e(r['expected'])+' → '+e(r['actual'])+'</td><td class="status warn">WARN</td></tr>' for r in rows)
template = re.sub(r'(?s)(<tbody>).*?(</tbody>)', lambda m:m[1]+tbody+m[2], template)
samples = []
for r in rows:
    response = r['capture']['response']
    if r['id']=='TC-01':
        b=response['body']
        response={'http_status':response['http_status'],'body':{'upgrade_config':{k:b['upgrade_config'][k] for k in ('enable','enable_merge')},'ngs_jobs':{'enable':b['ngs_jobs']['enable']}}}
    elif r['id']=='TC-02':
        response={'http_status':response['http_status'], 'count':len(results), 'UPG_count':upgrades, 'ngsItineraries_field_count':sum('ngsItineraries' in x for x in results), 'first_result_excerpt':{k:results[0][k] for k in ('key','fareType','prices')}, 'first_result_key_fields':list(results[0]['keys'])}
    samples.append('<section class="failure-sample"><h2>'+e(r['id'])+' · Payload evidence</h2><p>'+e(r['actual'])+'</p><h2>Request</h2><pre>'+e(json.dumps(r['capture']['request'],indent=2))+'</pre><h2>Response</h2><pre>'+e(json.dumps(response,indent=2))+'</pre></section>')
template = re.sub(r'(?s)<section class="failure-sample">.*?</section>', lambda m:'\n'.join(samples), template)
evidence='<section class="evidence"><div><h2>Evidence</h2><p>configuration-http-direct.json; S02.json; S01.json. Configuration is prerequisite discovery only. No merge behavior is certified.</p></div><div><h2>Prepared coverage</h2><p>Five BCKDCR/AKKDCR examples in merge-search-examples.json; none executed. No configuration, booking, or Jira changes. No matching operational lessons applied.</p></div></section>'
template=re.sub(r'(?s)<section class="evidence">.*?</section>', lambda m:evidence, template)
template=re.sub(r"(?s)const artifacts = \{.*?\n    \};", 'const artifacts = {};', template)
assert not re.search(r'&lt;(?:0|Ticket|Expected|Input|Request|Response)', template)
(ROOT / 'qa-report.html').write_text(template, encoding='utf-8')
(ROOT / 'results.json').write_text(json.dumps({'run':RUN,'signal':'WARN','counts':{'PASS':0,'FAIL':0,'WARN':3},'tests':[{k:v for k,v in r.items() if k not in ('capture','context','pattern','path')} for r in rows]},indent=2), encoding='utf-8')
print('Built Markdown/HTML dispatch: 0 PASS / 0 FAIL / 3 WARN; merge matrix unexecuted.')
