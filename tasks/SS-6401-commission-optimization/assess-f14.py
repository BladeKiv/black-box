import json
from analyze import RUN,dump,usd_breakdown_equal
from report import display_snapshot,filtered_snapshots

data=json.loads((RUN/'comparison.json').read_text(encoding='utf-8'))
historical=json.loads((RUN/'target-finding.json').read_text(encoding='utf-8'))
observations=[];rows=[]
for pair in data['pairs']:
    hits=[];exact=0
    for d in pair['differences']:
        if d['input'].get('validatingCarrier')!='MS' or d['input'].get('cons')!='VZU':continue
        snapshots=[d['prod'],d['preprod']]
        if not all(s.get('tickets') for s in snapshots):continue
        breakdowns=[s['tickets'][0].get('passengers',{}).get('ADT',{}).get('commBreakdown',{}) for s in snapshots]
        if not all(set(b)&{'backend','upfront'} for b in breakdowns) or breakdowns[0]==breakdowns[1] or usd_breakdown_equal(*breakdowns):continue
        hits.append(d)
        amounts=[sorted(v['amount'] for entries in b.values() for v in entries) for b in breakdowns]
        if sorted(amounts)==[[1],[125.2]]:exact+=1
        prod,preprod=filtered_snapshots(*snapshots)
        observations.append({'repeat':pair['repeat'],'requests':pair['requests'],'matched_input':d['input'],'prod_key':d['prod_key'],'preprod_key':d['preprod_key'],'prod':display_snapshot(prod),'preprod':display_snapshot(preprod),'original_input_exact':dump(d['input'])==dump(historical['representative']['difference']['input'])})
    rows.append({'repeat':pair['repeat'],'matched_results':pair['matched'],'f14_pattern_hits':len(hits),'exact_125_2_vs_1_hits':exact,'status':'FAIL' if hits else 'WARN','actual':'Historical F-14 breakdown mismatch reproduced' if hits else 'Target mismatch not captured; no fix conclusion'})
summary={'summary':f"Historical F-14 reproduced in {sum(r['f14_pattern_hits']>0 for r in rows)}/{len(rows)} TC-20 paired repetitions: {sum(r['f14_pattern_hits'] for r in rows)} MS/VZU first-ticket ADT breakdown mismatches, including {sum(r['exact_125_2_vs_1_hits'] for r in rows)} observations of the original USD 125.20 versus USD 1 amounts. The direction varies across repetitions. Customer total/aggregate commission comparisons are retained separately in each payload.",'target':'F-14 from 2026-10-13 TSTCOM report','intended_behavior':'Equivalent first-ticket ADT commission breakdown for comparable Search results under accepted exclusions and USD 3 tolerance.','results':rows}
(RUN/'target-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
(RUN/'f14-reproduction.json').write_text(json.dumps(observations,indent=2),encoding='utf-8')
md=['# TC-20 rerun targeting historical F-14','',summary['summary'],'','Scope: 2026-10-15; LHR-DXB / DXB-LHR, 2026-11-20 / 2026-11-30, cabin C, ADT=1, cid=TSTCOM; no GDS/PCC/fare/carrier filters. Six fresh Search requests, three interleaved PROD/PREPROD pairs. Historical October 13 evidence is unchanged.','','Intended behavior: '+summary['intended_behavior'],'','| Repetition | Test data | Expected | Actual | Status |','|---|---|---|---|---|']
for r in rows:md.append(f"| {r['repeat']} | TC-20, {r['matched_results']} matched results | Equivalent first-ticket ADT breakdown | {r['f14_pattern_hits']} matching F-14 discrepancies; {r['exact_125_2_vs_1_hits']} original-amount observations | {r['status']} |")
md+=['','Full request/response pairs: evidence/. Targeted opaque keys, fare context, complete passenger/price excerpts: f14-reproduction.json. Sanitized payload excerpts for every failing pair and rerunnable collection/CSV: qa-report.html. No source or configuration changes. No Newman run. Both directions of the discrepancy were observed; this is not proof of an optimization-specific root cause.']
(RUN/'f14-rerun.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps(summary))
