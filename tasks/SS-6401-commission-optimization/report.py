import json,csv,base64,html,re,statistics,math,collections,copy
from pathlib import Path
from analyze import ROOT,RUN,dump,equivalent_rules,pair_equal,same_lowest_choice,usd_breakdown_equal,prod_segments

def esc(s): return html.escape(str(s))
def display_snapshot(x):
    if isinstance(x,list):return [display_snapshot(v) for v in x]
    if isinstance(x,dict):return {k:display_snapshot(v) for k,v in x.items() if k!='oComm'}
    return x
def commission_objects(snapshot,path=''):
    objects=[{'path':path+'keys.commission_info','present':'commission_info' in snapshot}]
    if 'commission_info' in snapshot: objects[0]['object']=snapshot['commission_info']
    for i,ticket in enumerate(snapshot.get('tickets') or []):
        objects.extend(commission_objects(ticket,path+f'tickets[{i}].'))
    return objects
def unmatched_commission_objects(prod,preprod,path=''):
    sides=[[],[]]; infos=[prod.get('commission_info'),preprod.get('commission_info')]
    fares=[(info or {}).get('fareCalculation',{}) for info in infos]
    filtered=[{},{}]; indices=[{},{}]
    for pax in sorted(fares[0].keys()|fares[1].keys()):
        lists=[f.get(pax,[]) for f in fares]
        for i in range(max(map(len,lists))):
            pair=[rows[i] if i<len(rows) else None for rows in lists]
            commissions=[(f or {}).get('commissions',{}) for f in pair]
            names={name for name in commissions[0].keys()|commissions[1].keys() if name not in commissions[0] or name not in commissions[1] or not pair_equal(commissions[0][name],commissions[1][name])}
            if not names:continue
            for side,fare in enumerate(pair):
                if fare is None:continue
                selected={k:copy.deepcopy(v) for k,v in fare.items() if k!='commissions'}
                selected['commissions']={name:copy.deepcopy(commissions[side][name]) for name in sorted(names) if name in commissions[side]}
                filtered[side].setdefault(pax,[]).append(selected)
                indices[side].setdefault(pax,[]).append(i)
    if filtered[0] or filtered[1]:
        for side,info in enumerate(infos):
            entry={'path':path+'keys.commission_info','present':isinstance(info,dict),'excerpt':'only unmatched consolidators','original_fare_indices':indices[side]}
            if isinstance(info,dict):
                entry['object']={k:copy.deepcopy(v) for k,v in info.items() if k!='fareCalculation'}
                entry['object']['fareCalculation']=filtered[side]
            sides[side].append(entry)
    tickets=[prod.get('tickets') or [],preprod.get('tickets') or []]
    for i in range(max(map(len,tickets))):
        nested=unmatched_commission_objects(tickets[0][i] if i<len(tickets[0]) else {},tickets[1][i] if i<len(tickets[1]) else {},path+f'tickets[{i}].')
        for side in range(2):sides[side].extend(nested[side])
    return sides
def filtered_snapshots(prod,preprod):
    copies=[copy.deepcopy(prod),copy.deepcopy(preprod)]
    clipped=unmatched_commission_objects(prod,preprod)
    def strip(snapshot):
        snapshot.pop('commission_info',None)
        for ticket in snapshot.get('tickets') or []:strip(ticket)
    for side,snapshot in enumerate(copies):
        strip(snapshot)
        for entry in clipped[side]:
            if not entry.get('present'):continue
            target=snapshot
            for index in re.findall(r'tickets\[(\d+)\]',entry['path']):target=target['tickets'][int(index)]
            target['commission_info']=entry['object']
    return copies
def percentile(xs,p):
    xs=sorted(xs); return xs[max(0,math.ceil(len(xs)*p)-1)] if xs else None
def stats(xs): return {'n':len(xs),'median':statistics.median(xs) if xs else None,'p95':percentile(xs,.95)}

def chart(rows,field,title,unit,name):
    width,height=900,290; left,right,top,bottom=75,20,40,55
    groups={env:[r for r in rows if r['environment']==env] for env in ['prod','preprod']}
    maxx=max([len(v) for v in groups.values()]+[1]); maxy=max([r[field] for v in groups.values() for r in v if r.get(field) is not None and r['status']==200]+[.001])*1.1
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}"><rect width="900" height="290" fill="#f7fafb"/><g font-family="sans-serif" fill="#15202b"><text x="75" y="22" font-size="16">{esc(title)}</text>']
    for i in range(5):
        y=top+(height-top-bottom)*i/4; val=maxy*(4-i)/4
        parts.append(f'<path d="M{left},{y}H{width-right}" stroke="#cad7dc"/><text x="65" y="{y+4}" text-anchor="end" font-size="11">{val:.2f}</text>')
    for env,color in [('prod','#08788e'),('preprod','#b42832')]:
        points=[]
        for i,r in enumerate(groups[env]):
            if r.get(field) is None or r['status']!=200: continue
            x=left+(width-left-right)*i/max(1,maxx-1); y=top+(height-top-bottom)*(1-r[field]/maxy); points.append(f'{x:.2f},{y:.2f}')
        if points: parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="1.5"/>')
        offset=0 if env=='prod' else 115
        parts.append(f'<text x="{width-240+offset}" y="22" fill="{color}" font-size="12">{env.upper()}</text>')
    parts.append(f'<text x="75" y="{height-12}" font-size="12">{esc(unit)}  |  paired request index (scenario, repetition); each line has one point per request</text></g></svg>')
    svg=''.join(parts); (RUN/name).write_text(svg,encoding='utf-8'); return svg

def main():
    data=json.loads((RUN/'comparison.json').read_text(encoding='utf-8')); pairs=data['pairs']; timings=data['timings']
    context=json.loads((RUN/'run-context.json').read_text(encoding='utf-8')) if (RUN/'run-context.json').exists() else {}
    cases=[]
    for p in pairs:
        route=' / '.join(p['query'][f'fl.{i}.o']+'-'+p['query'][f'fl.{i}.d'] for i in range(2))
        detail=f"{route}; {p['query']['fl.0.dt']} / {p['query']['fl.1.dt']}; {p['query']['cabin']}; ADT=1"+('; CHD=1 INF=1' if 'chd' in p['query'] else '')
        filters={k:p['query'][k] for k in ['gds','pcc','fare','val_cr'] if k in p['query']}
        if filters:detail+='; filters='+dump(filters)
        sid=p['scenario_id']+f"-R{p['repeat']}"
        cases.extend([
            {'id':sid+'-OUTPUT','data':detail,'expected':'Equivalent commission/price output on identical exposed fare inputs under accepted exclusions; USD total price/tax, passenger breakdown and Commission.ValuePerPax.amount tolerance $1; PROD trip-1/2 duplicates omitted; PREPROD segment fees may be lower; additional PREPROD breakdowns accepted.','actual':f"{p['equal']}/{p['matched']} matched results equivalent; {len(p['differences'])} differing input groups; unmatched PROD/PREPROD {p['prod_only']}/{p['preprod_only']}.",'status':p['amount_status'],'pair':p,'kind':'OUTPUT'},
            {'id':sid+'-RULE','data':detail,'expected':'Equivalent selections under approved duplicate 6189/6082 and equal-amount 4989/4926 choices; other rule metadata remains checked.','actual':f"{p['rule_equal']}/{p['rule_evaluated']} exposed matched results equivalent; {len(p['rule_differences'])} differing groups; unexposed matched results {p['matched']-p['rule_evaluated']}.",'status':p['rule_status'],'pair':p,'kind':'RULE'}])
    if context.get('public_report'):
        for c in cases:
            c['expected']='Commission output matches expected behavior.' if c['kind']=='OUTPUT' else 'Commission rule selection matches expected behavior.'
            c['actual']=c['actual'].replace('matched results equivalent','matched results meet expectations').replace('exposed matched results equivalent','exposed matched results meet expectations')
    counts=collections.Counter(c['status'] for c in cases); signal='FAIL' if counts['FAIL'] else ('WARN' if counts['WARN'] else 'PASS')
    fields={'response_seconds':'End-to-end Search response (s)','server_search_seconds':'API excutionTime (s)','commission_seconds':'Commission service executionTime (s)','commission_us_per_processed':'Commission service microseconds / processed result'}
    valid_pairs={(p['scenario_id'],str(p['repeat'])) for p in pairs if p['statuses']==[200,200]}
    summary={env:{f:stats([t[f] for t in timings if t['environment']==env and (t['scenario_id'],str(t['repeat'])) in valid_pairs and t.get(f) is not None]) for f in fields} for env in ['prod','preprod']}
    (RUN/'timing-summary.json').write_text(json.dumps(summary,indent=2))
    grouped=collections.defaultdict(list)
    def changes(a,b,path='',usd_prices=False):
        out=[]
        if pair_equal(a,b,path):return out
        if path.endswith('.segments'):a=prod_segments(a)
        if usd_breakdown_equal(a,b):return out
        if type(a)!=type(b): return [(path,a,b)]
        if isinstance(a,dict):
            for k in sorted(a.keys()|b.keys()):
                if k=='oComm':continue
                if k not in a and ((k=='commBreakdown' and isinstance(b[k],dict)) or (path.endswith('.commBreakdown') and isinstance(b[k],list))):continue
                if '.segmentFees' in path and k in ['amount','fullAmount'] and isinstance(a.get(k),(int,float)) and isinstance(b.get(k),(int,float)) and b[k]<=a[k]+1e-9:continue
                if k=='amount' and re.search(r'\.priceElement\.Assets\.Commission\.ValuePerPax\.[^.]+$',path) and a.get('currency')==b.get('currency')=='USD' and isinstance(a.get(k),(int,float)) and isinstance(b.get(k),(int,float)) and abs(a[k]-b[k])<=1+1e-9:continue
                if k in ['rule','subRule','combKey'] and a.get('rule') in (4989,4926) and b.get('rule') in (4989,4926) and a.get('amount')==b.get('amount') and a.get('fullAmount')==b.get('fullAmount'):continue
                if usd_prices and k in ['totalPrice','totalTax'] and isinstance(a.get(k),(int,float)) and not isinstance(a.get(k),bool) and isinstance(b.get(k),(int,float)) and not isinstance(b.get(k),bool) and abs(a[k]-b[k])<=1+1e-9:continue
                if k in ['rule','subRule'] and a.get('rule') in (6189,6082) and b.get('rule') in (6189,6082):continue
                if k=='subRule' and same_lowest_choice(a,b):continue
                q=path+'.'+k
                if k not in a or k not in b: out.append((q,a.get(k,'[MISSING]'),b.get(k,'[MISSING]')))
                else: out.extend(changes(a[k],b[k],q,k=='prices' and a.get('currency')==b.get('currency')=='USD'))
        elif isinstance(a,list):
            if len(a)!=len(b): out.append((path+'.length',len(a),len(b)))
            for i,(x,y) in enumerate(zip(a,b)): out.extend(changes(x,y,path+f'[{i}]'))
        elif a!=b: out.append((path,a,b))
        return out
    for p in pairs:
        for d in p['differences']:
            delta=changes(d['prod'],d['preprod'])
            signature=dump([(re.sub(r'\[\d+\]','[]',path),a,b) for path,a,b in delta])
            grouped[signature].append({'scenario_id':p['scenario_id'],'repeat':p['repeat'],'requests':p['requests'],'difference':d,'changes':delta})
    findings=[]
    finding_prefix=context.get('finding_prefix','F')
    finding_id=lambda i:context.get('finding_ids',{}).get(str(i),f'{finding_prefix}-{i:02}')
    for i,(sig,items) in enumerate(sorted(grouped.items(),key=lambda kv:-len(kv[1])),1):
        findings.append({'finding_id':finding_id(i),'occurrences':len(items),'scenario_repetitions':sorted(set(x['scenario_id']+f"-R{x['repeat']}" for x in items)),'representative':items[0]})
    (RUN/'debug-findings.json').write_text(json.dumps(findings,indent=2))
    commission_mismatches=[{'finding_id':finding_id(i),'scenario_id':item['scenario_id'],'repeat':item['repeat'],'requests':item['requests'],'prod_key':item['difference']['prod_key'],'preprod_key':item['difference']['preprod_key'],'changes':item['changes'],'prod_commission_info':commission_objects(item['difference']['prod']),'preprod_commission_info':commission_objects(item['difference']['preprod'])} for i,(_,items) in enumerate(sorted(grouped.items(),key=lambda kv:-len(kv[1])),1) for item in items]
    originals={(item['scenario_id'],str(item['repeat']),item['difference']['prod_key'],item['difference']['preprod_key']):item['difference'] for items in grouped.values() for item in items}
    for item in commission_mismatches:
        d=originals[(item['scenario_id'],str(item['repeat']),item['prod_key'],item['preprod_key'])]
        item['prod_commission_info'],item['preprod_commission_info']=unmatched_commission_objects(d['prod'],d['preprod'])
        item['prod_affected_passengers']={};item['preprod_affected_passengers']={}
        def affected_passengers(a,b,path=''):
            ap=a.get('passengers') or {};bp=b.get('passengers') or {}
            for pax in ap.keys()|bp.keys():
                if not pair_equal(ap.get(pax),bp.get(pax)):
                    key=path+'passengers.'+pax
                    item['prod_affected_passengers'][key]={'present':pax in ap,'object':ap.get(pax)}
                    item['preprod_affected_passengers'][key]={'present':pax in bp,'object':bp.get(pax)}
            ats=a.get('tickets') or [];bts=b.get('tickets') or []
            for i in range(max(len(ats),len(bts))):affected_passengers(ats[i] if i<len(ats) else {},bts[i] if i<len(bts) else {},path+f'tickets[{i}].')
        affected_passengers(display_snapshot(d['prod']),display_snapshot(d['preprod']))
        if item['prod_affected_passengers'] or item['preprod_affected_passengers']:
            item['prod_price_context']={k:d['prod'].get(k) for k in ['prices','priceElement']}
            item['preprod_price_context']={k:d['preprod'].get(k) for k in ['prices','priceElement']}
        if not item['prod_commission_info'] and not item['preprod_commission_info']:item['commission_info_note']='No unmatched consolidator: differences are outside consolidator commission objects.'
    (RUN/'commission-info-mismatches.json').write_text(json.dumps(commission_mismatches,indent=2),encoding='utf-8')
    categories=collections.defaultdict(list)
    for f in findings:
        paths=[p for p,a,b in f['representative']['changes']]
        for label,active in [
            ('Rule/sub-rule selection',any(p.endswith('.rule') or p.endswith('.subRule') for p in paths)),
            ('Passenger oComm amount',any('.oComm.amount' in p for p in paths)),
            ('Commission breakdown',any('.commBreakdown.' in p for p in paths)),
            ('Segment fee amounts',any('.segmentFees.amount' in p or '.segmentFees.fullAmount' in p for p in paths)),
            ('Fare segment references',any('.segments.' in p for p in paths)),
            ('Total price/tax rounding/output',any(p.endswith('.totalPrice') or p.endswith('.totalTax') for p in paths))]:
            if active: categories[label].append(f)
    (RUN/'finding-categories.json').write_text(json.dumps({label:{'matched_group_observations':sum(f['occurrences'] for f in fs),'finding_ids':[f['finding_id'] for f in fs]} for label,fs in categories.items()},indent=2))
    investigation=['# SS-6401 debug handoff','', 'Remaining cross-environment differences are retained after the reviewed PROD exceptions and approved USD 1 tolerances. Duplicate trip-1/2 references, lower/equal PREPROD segment fees, additional PREPROD breakdowns and equal-amount 4989/4926 choices are accepted. Other monetary/output differences remain checked. Attribution to a particular optimization is not established by black-box evidence. Same rule source is user-confirmed. Counts below include repeated observations and categories can overlap.','']
    investigation+=['All Lowest sub-rule IDs are also accepted when all other commission fields match. Full affected passenger objects and prices/priceElement context are available for each retained mismatch in qa-report.html and commission-info-mismatches.json.','']
    investigation+=['The user-classified PROD oComm bug is excluded from comparison and displayed objects. Current grouped evidence: debug-findings.json and commission-info-mismatches.json. All Lowest sub-rule ranges are accepted at the user request, provided other commission fields match.','']
    for label,fs in categories.items():
        f=max(fs,key=lambda x:x['occurrences']); rep=f['representative']; d=rep['difference']
        clipped=unmatched_commission_objects(d['prod'],d['preprod'])
        investigation += [f'## {label}',f"{sum(x['occurrences'] for x in fs)} differing matched-group observations; signatures: "+', '.join(x['finding_id'] for x in fs), '',f"Representative: {rep['scenario_id']} repetition {rep['repeat']}.", '','```json',json.dumps({'requests':rep['requests'],'prod_key':d['prod_key'],'preprod_key':d['preprod_key'],'changes':rep['changes']},indent=2),'```','','PROD commission_info (unmatched consolidators only):','```json',json.dumps(clipped[0],indent=2),'```','','PREPROD commission_info (unmatched consolidators only):','```json',json.dumps(clipped[1],indent=2),'```','']
    stability_path=RUN/'stability.json'
    stability=json.loads(stability_path.read_text(encoding='utf-8')) if stability_path.exists() else None
    if stability: investigation+=['## Within-environment stability (raw metadata)','```json',json.dumps(stability['summary'],indent=2),'```','This raw metadata audit includes accepted duplicate-rule choices; it is not a failure count. PROD also varies on some identical exposed inputs. Review repeated raw responses before treating remaining cross-environment sub-rule differences as newly introduced regressions.','']
    investigation+=['## Focused investigation sequence','1. Use each representative exact Search pair and compare the same opaque-key entries against the saved matched_input. Do not decode keys or substitute different inventory.','2. For rule IDs: inspect the listed fare owner, fare code/designator, passenger, booking class, dates and every consolidator entry. Verify whether baseline rule selection is stable across repetitions.','3. For segment fees: compare the displayed trip segments and commission_info fare segment references, including duplicate references; compare fullAmount/amount and deduct flags.','4. For refreshed price output: compare priceElement.Assets.Commission, passenger comm/oComm, commBreakdown and totalPrice independently. An unchanged top-level total does not establish field parity.','5. Reproduce any fixes against the saved paired inputs, then rerun the same broad matrix. This handoff performs no configuration mutation or application-source inspection.','', 'Full differences and original snapshots: comparison.json; grouped representative snapshots: debug-findings.json; request/response excerpts for every FAIL/WARN: qa-report.html; raw evidence: evidence/.']
    if not findings:
        investigation=['# SS-6401 verification outcome','', 'Intended behavior: preserve expected commission application and selection behavior.','', f"{counts['PASS']} PASS, {counts['FAIL']} FAIL, {counts['WARN']} WARN checks. No remaining mismatch signatures.",'', 'F-90 is passed following the user confirmation recorded on 2026-10-16. Complete saved results remain available in commission-info-evidence.json where present. See qa-report.md for the test-case results table.']
    (RUN/'investigation.md').write_text('\n'.join(investigation),encoding='utf-8')
    cols=['scenario_id','expected_result','provider_filter','search_url','cid','cabin','adt','chd','inf','departure_date','return_date','prod_url','preprod_url','repetitions','commission_info_path','commission_timing_prefix']
    with (RUN/'expected-outcomes.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
        for s in json.loads((RUN/'scenarios.json').read_text(encoding='utf-8')):
            from urllib.parse import urlencode
            q=s['query']; suffix='/v1/search?'+urlencode(q)
            w.writerow(dict(scenario_id=s['scenario_id'],expected_result='Reviewed PROD parity: ignore duplicate PROD tripId=1/2 references; PREPROD segmentFees amounts <= PROD; missing-PROD/additional-PREPROD commBreakdown accepted; duplicate 6189/6082 and equal-amount 4989/4926 metadata accepted; Lowest sub-rule choices accepted with other fields equal; USD totalPrice/totalTax, passenger breakdown and Assets.Commission.ValuePerPax.amount tolerance $1; all other values remain checked; WARN if comparable inventory or required paths unavailable',provider_filter=dump({k:q[k] for k in ['gds','pcc','fare','val_cr'] if k in q}) if any(k in q for k in ['gds','pcc','fare','val_cr']) else '',search_url='{{base_url}}'+suffix,cid=q['cid'],cabin=q['cabin'],adt=q['adt'],chd=q.get('chd','0'),inf=q.get('inf','0'),departure_date=q['fl.0.dt'],return_date=q['fl.1.dt'],prod_url='https://airsearch.api.travelinsides.com'+suffix,preprod_url='http://airapi51.kivops.info'+suffix,repetitions=3,commission_info_path='keys.commission_info',commission_timing_prefix='Commission service processed '))
    if context.get('public_report'):
        with (RUN/'expected-outcomes.csv').open(encoding='utf-8',newline='') as f: public_rows=list(csv.DictReader(f))
        for row in public_rows:row['expected_result']='Commission outputs and rule selections meet expected behavior; WARN if comparable inventory or required response fields are unavailable.'
        with (RUN/'expected-outcomes.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader();writer.writerows(public_rows)
    tests=[
        "const body=pm.response.json();",
        "pm.test('Search results are exposed',()=>pm.expect(body.results).to.be.an('array'));",
        "pm.test('Opaque Search keys are strings',()=>body.results.forEach(r=>pm.expect(r.key).to.be.a('string')));",
        "const path=pm.iterationData.get('commission_info_path')||'keys.commission_info'; const get=(o)=>path.split('.').reduce((a,k)=>a==null?undefined:a[k],o);",
        "const observed=body.results.filter(r=>get(r)!==undefined);",
        "if(!observed.length) pm.test.skip('WARN: commission_info unavailable for rule selection',()=>{}); else pm.test('Commission fare components are exposed',()=>observed.forEach(r=>pm.expect(get(r).fareCalculation).to.be.an('object')));",
        "const prefix=pm.iterationData.get('commission_timing_prefix')||'Commission service processed '; const timings=(body.timing||[]).filter(t=>t.process.startsWith(prefix));",
        "if(!timings.length) pm.test.skip('WARN: commission-service timing unavailable',()=>{}); else pm.test('Commission-service timing includes explicit unit',()=>timings.forEach(t=>pm.expect(t.executionTime).to.match(/[0-9](ns|us|µs|μs|ms|s)$/)));",
        "console.log(JSON.stringify({scenario_id:pm.iterationData.get('scenario_id'),environment:pm.variables.get('environment'),response_ms:pm.response.responseTime,commission_timings:timings,results:body.results.length}));",
        "// Paired cross-environment assertions follow; analyze.py evaluates the saved live response bodies independently."
    ]
    parity_js=(ROOT/'postman-parity.js').read_text(encoding='utf-8').splitlines()
    items=[]
    for env in ['prod','preprod']:
        setup=[f"pm.variables.set('environment','{env}');",f"pm.variables.set('active_search_url',pm.iterationData.get('{env}_url')||'');","if(!pm.variables.get('basic_token')) throw new Error('Provide local basic_token before execution');"]
        items.append({'name':env.upper()+' Search','event':[{'listen':'prerequest','script':{'type':'text/javascript','exec':setup}},{'listen':'test','script':{'type':'text/javascript','exec':tests+parity_js}}],'request':{'auth':{'type':'noauth'},'method':'GET','header':[{'key':'Authorization','value':'Basic {{basic_token}}'}],'url':'{{active_search_url}}'}})
    collection={'info':{'name':'SS-6401 TSTCOM Search commission comparison','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json','description':'Search-only paired PROD then PREPROD requests; no provider-level tracks. Run with expected-outcomes.csv. Supply basic_token locally. Each iteration overwrites the baseline, compares matched original fare inputs and all exposed commission output, and reports unavailable inventory as WARN/skipped. run.py/analyze.py provide the saved live evidence and interleaved repetitions.'},'auth':{'type':'noauth'},'variable':[{'key':'basic_token','value':''}],'item':items}
    (RUN/'SS-6401.postman_collection.json').write_text(json.dumps(collection,indent=2),encoding='utf-8')
    timing_table='<table><thead><tr><th>Metric</th><th>PROD median / p95</th><th>PREPROD median / p95</th><th>Median change</th></tr></thead><tbody>'
    for field,label in fields.items():
        a,b=summary['prod'][field],summary['preprod'][field]
        def fmt(s): return f"{s['median']:.4f} / {s['p95']:.4f} (n={s['n']})" if s['n'] else 'Unavailable'
        delta=f"{(b['median']/a['median']-1)*100:+.1f}%" if a['median'] and b['median'] is not None else 'Unavailable'
        timing_table+=f'<tr><td>{esc(label)}</td><td>{fmt(a)}</td><td>{fmt(b)}</td><td>{delta}</td></tr>'
    timing_table+='</tbody></table>'
    graphs=''.join(chart(timings,field,label,'seconds' if field!='commission_us_per_processed' else 'microseconds / result',field+'.svg') for field,label in fields.items())
    matched=sum(p['matched'] for p in pairs); equal=sum(p['equal'] for p in pairs)
    finding_text=f"SS-6401 must preserve matching rules and applied commissions. {len(pairs)} paired Search runs evaluated {matched:,} matched returned results; {equal:,} have equivalent commission/financial output. {sum(len(p['differences']) for p in pairs):,} input groups differ, grouped into {len(findings)} debug signatures. Accepted PROD exceptions: duplicate tripId=1/2 fare references; PREPROD segment fee amounts equal to or lower than PROD; additional PREPROD commBreakdown fields missing on PROD. Accepted duplicate choices: 6189/6082 and equal-amount 4989/4926 (including their sub-rule/combKey metadata); Lowest sub-rule IDs when other fields match. The known PROD oComm bug remains excluded. USD totalPrice/totalTax, backend/upfront passenger breakdowns and Assets.Commission.ValuePerPax.amount have a $1 tolerance. Other financial differences remain checked. Both environments use the same rule source."
    strip=f"{context.get('run_date','2026-10-13')}  |  GET /v1/search  |  TSTCOM  |  {len(timings)} captured request attempts ({context.get('planned_requests',180)} planned + retries)  |  {context.get('scenario_count',30)} scenarios x {context.get('repetitions',3)} repetitions  |  {context.get('filter_scope','gds/pcc/fare/val_cr filters omitted')}"
    if context.get('scope'):strip+='  |  '+context['scope']
    if (RUN/'target-summary.json').exists():
        target=json.loads((RUN/'target-summary.json').read_text(encoding='utf-8'))
        finding_text=target['summary']+' '+finding_text
    if context.get('public_report'):
        finding_text=context['public_summary']
        strip=f"{context.get('run_date','2026-10-15')}  |  GET /v1/search  |  TSTCOM  |  {len(timings)} requests  |  {context.get('scenario_count',30)} scenarios x {context.get('repetitions',3)} repetitions"
    rows=''.join(f"<tr><td>{c['id']}</td><td class=\"test\">{esc(c['data'])}</td><td>{esc(c['expected'])}<br>-> {esc(c['actual'])}</td><td class=\"status {c['status'].lower()}\">{c['status']}</td></tr>" for c in cases)
    evidence=[]
    for c in cases:
        if c['status']=='PASS': continue
        p=c['pair']; ds=p['differences'] if c['kind']=='OUTPUT' else p['rule_differences']
        response={'prod':ds[0]['prod'],'preprod':ds[0]['preprod'],'prod_key':ds[0]['prod_key'],'preprod_key':ds[0]['preprod_key'],'matched_input':ds[0]['input']} if ds else {'http_statuses':p['statuses'],'matched':p['matched'],'rule_evaluated':p['rule_evaluated'],'prod_only':p['prod_only'],'preprod_only':p['preprod_only'],'responses':{}}
        if ds:
            original=originals[(p['scenario_id'],str(p['repeat']),ds[0]['prod_key'],ds[0]['preprod_key'])]
            response['prod'],response['preprod']=filtered_snapshots(original['prod'],original['preprod'])
            response['commission_info_scope']='Unmatched consolidators only; matching consolidator objects omitted.'
        if not ds:
            for env in ['prod','preprod']:
                folder=RUN/'evidence'/p['scenario_id']/str(p['repeat'])/env
                meta=json.loads((folder/'meta.json').read_text(encoding='utf-8')); raw=(folder/'response.json').read_text(encoding='utf-8',errors='replace')
                try:
                    body=json.loads(raw)
                    relevant={k:body[k] for k in ['count','messages','error','errors','status'] if k in body}
                    relevant['results']=[] if not body.get('results') else [{'key':r.get('key'),'input':__import__('analyze').identity(r),'output':__import__('analyze').output(r)} for r in body['results'][:1]]
                except ValueError: relevant={'body':raw[:2000]}
                response['responses'][env]={'http_status':meta['status'],'transport_error':meta['error'],'payload':relevant}
        response=display_snapshot(response)
        evidence.append(f'<details class="failure-sample"><summary>{esc(c["id"])}  |  {c["status"]} payload evidence</summary><h2>Request pair</h2><pre>{esc(json.dumps(p["requests"],indent=2))}</pre><h2>Response pair</h2><pre>{esc(json.dumps(response,indent=2))}</pre></details>')
    fhtml=[]
    for f in findings:
        rep=f['representative']; lines='; '.join(f"{p}: {dump(a)} -> {dump(b)}" for p,a,b in rep['changes'])
        occurrences=[]
        for item in commission_mismatches:
            if item['finding_id']!=f['finding_id']:continue
            identity={k:item[k] for k in ['scenario_id','repeat','requests','prod_key','preprod_key']}
            note=esc(item.get('commission_info_note','Commission_info excerpts include only consolidators whose objects differ; matching consolidators are omitted.'))
            passenger_html=''
            if item['prod_affected_passengers'] or item['preprod_affected_passengers']:
                passenger_html='<h2>PROD affected passenger objects</h2><pre>'+esc(json.dumps(item['prod_affected_passengers'],indent=2))+'</pre><h2>PREPROD affected passenger objects</h2><pre>'+esc(json.dumps(item['preprod_affected_passengers'],indent=2))+'</pre>'
                passenger_html+='<h2>PROD prices / priceElement</h2><pre>'+esc(json.dumps(item['prod_price_context'],indent=2))+'</pre><h2>PREPROD prices / priceElement</h2><pre>'+esc(json.dumps(item['preprod_price_context'],indent=2))+'</pre>'
            occurrences.append(f'<details><summary>{esc(item["scenario_id"])}  |  repetition {esc(item["repeat"])}  |  unmatched consolidators / affected passengers</summary><p>{note}</p><h2>Exact Search URLs and opaque keys</h2><pre>{esc(json.dumps(identity,indent=2))}</pre><h2>PROD commission_info</h2><pre>{esc(json.dumps(item["prod_commission_info"],indent=2))}</pre><h2>PREPROD commission_info</h2><pre>{esc(json.dumps(item["preprod_commission_info"],indent=2))}</pre>{passenger_html}</details>')
        fhtml.append(f'<details class="failure-sample"><summary>{f["finding_id"]}  |  {f["occurrences"]} differing matched groups  |  commission_info objects</summary><p>{esc(lines)}</p>'+''.join(occurrences)+'</details>')
    template=(ROOT.parent.parent/'templates'/'airapi-qa-dispatch-template.html').read_text(encoding='utf-8')
    template=template.replace('&lt;Ticket title&gt;','SS-6401  |  Commission parity').replace('Run &lt;YYYY-MM-DD&gt;<br>&lt;Endpoint / route / scope&gt;',esc(strip))
    template=template.replace('class="value fail">&lt;PASS / FAIL / WARN&gt;',f'class="value {signal.lower()}">{signal}')
    for label,status in [('Passed','PASS'),('Failed','FAIL'),('Warn','WARN')]:
        template=re.sub(r'(<span class="label">'+label+r'</span><span class="value \w+">)&lt;0&gt;',lambda m:m[1]+str(counts[status]),template)
    template=re.sub(r'<p class="finding">.*?</p>',f'<p class="finding">{esc(finding_text)}</p>',template,count=1,flags=re.S)
    template=re.sub(r'<tbody>.*?</tbody>','<tbody>'+rows+'</tbody>',template,count=1,flags=re.S)
    cat_table='<table><thead><tr><th>Difference category</th><th>Matched-group observations</th></tr></thead><tbody>'+''.join(f'<tr><td>{esc(label)}</td><td>{sum(f["occurrences"] for f in fs)}</td></tr>' for label,fs in categories.items())+'</tbody></table>'
    stability_note=('Within-environment repetition audit: '+dump(stability['summary'])+'. Some baseline output varies; cross-environment mismatches are observed failures of exact parity, not proof of a particular source-code cause.') if stability else 'Within-environment repetition audit is retained separately after the run.'
    if context.get('public_report'):stability_note=''
    extra='<h2>Timing comparison</h2>'+timing_table+graphs+f'<p class="run">Summary statistics use the {len(valid_pairs)} pairs where both responses completed with HTTP 200. Charts preserve the same pair index across environments and omit unavailable/error measurements. Service executionTime is elapsed wall time, not CPU. Recorded commission-service durations and processed counts are summed if multiple entries exist. Different hosts, provider latency, cache effects and returned workloads remain confounders; endpoint timings cannot establish CPU/allocation savings.</p><h2>Debug findings</h2>'+cat_table+'<p class="run">'+esc(stability_note)+'</p>'+''.join(fhtml)+''.join(evidence)
    if context.get('reproduction_run'):
        reproduction=RUN.parent/context['reproduction_run']
        reproduced=(reproduction/'qa-report.html').read_text(encoding='utf-8')
        table=re.search(r'<table>.*?</table>',reproduced,re.S).group(0)
        fresh=json.loads((reproduction/'comparison.json').read_text(encoding='utf-8'))['pairs']
        fresh_counts=collections.Counter(status for pair in fresh for status in [pair['amount_status'],pair['rule_status']])
        result=f"{fresh_counts['PASS']} PASS, {fresh_counts['FAIL']} FAIL and {fresh_counts['WARN']} WARN checks"
        note='F-90 is passed: the confirmed rule choices apply the same amounts for the tested origin/destination.' if context.get('f90_passed') else 'Rule-choice differences remain under review.'
        extra+='<h2>F-90 - fresh verification</h2><p>12 additional Search requests, all HTTP 200: six paired runs, with '+result+'. These results are separate from the matrix totals above. '+note+'</p><div class="table-wrap">'+table+'</div>'
    full_info_path=RUN/'commission-info-evidence.json'
    if full_info_path.exists():
        extra+='<h2>F-90 verification: full commission info for both trips</h2><p>Full selected Search results are shown below, including all consolidators and both trips. No commission_info entries are clipped. The exact original itinerary was absent from broad Search; focused Search reproduced the rule-choice pattern on fresh itineraries.</p>'
        summary_path=RUN/'f90-reproduction-summary.json'
        if summary_path.exists():
            selected=json.loads(summary_path.read_text(encoding='utf-8')).get('trip_comparison',[])
            extra+='<table><thead><tr><th>Observation</th><th>Trip</th><th>PROD VZC upfront</th><th>PREPROD VZC upfront</th></tr></thead><tbody>'
            for row in selected:
                compact=lambda env:'<br>'.join(esc(k+': '+str(v)) for item in row[env] for k,v in item.items() if k in ['fareCode','rule','subRule','combKey','tourCode','amount','currency','percent'])
                extra+='<tr><td>'+esc(row['observation'])+'</td><td>'+str(row['tripId'])+'</td><td>'+compact('prod')+'</td><td>'+compact('preprod')+'</td></tr>'
            extra+='</tbody></table>'
        for entry in json.loads(full_info_path.read_text(encoding='utf-8')):
            if context.get('f90_passed'):
                extra+='<details><summary class="pass">PASS - '+esc(entry['label'])+'</summary><pre style="overflow:auto">'+esc(json.dumps(entry,indent=2))+'</pre></details>'
            else:
                extra+='<details class="failure-sample"><summary>'+esc(entry['label'])+'</summary><pre>'+esc(json.dumps(entry,indent=2))+'</pre></details>'
        summary_path=RUN/'f90-reproduction-summary.json'
        if summary_path.exists():extra+='<p>'+esc(json.loads(summary_path.read_text(encoding='utf-8'))['summary'])+'</p>'
    preliminary_path=ROOT/'comparison.json'
    if RUN!=ROOT and preliminary_path.exists() and not context:
        preliminary=json.loads(preliminary_path.read_text(encoding='utf-8'))['pairs']; pr=[]; pe=[]
        for p in preliminary:
            for kind,status in [('OUTPUT',p['amount_status']),('RULE',p['rule_status'])]:
                cid=f"SAL103-{p['scenario_id']}-R{p['repeat']}-{kind}"
                expected='Identical exposed financial output on matched fares' if kind=='OUTPUT' else 'Selected commission rule details available for parity comparison'
                actual=f"{p['equal']}/{p['matched']} matched output snapshots identical" if kind=='OUTPUT' else f"{p['rule_evaluated']} matched results expose rule details; CID replaced with TSTCOM"
                pr.append(f'<tr><td>{cid}</td><td>SAL103; {esc(dump(p["query"]))}</td><td>{expected} -> {actual}</td><td class="status {status.lower()}">{status}</td></tr>')
                if status!='PASS':
                    sample=display_snapshot(p['samples'][0]) if p['samples'] else {'matched':p['matched'],'commission_info_available':False}
                    pe.append(f'<details class="failure-sample"><summary>{cid}  |  {status} payload evidence</summary><h2>Request pair</h2><pre>{esc(json.dumps(p["requests"],indent=2))}</pre><h2>Response excerpts</h2><pre>{esc(json.dumps(sample,indent=2))}</pre></details>')
        for f in (ROOT/'evidence').glob('TC-*/*/*/request.json'):
            if (f.parent/'meta.json').exists():continue
            request=json.loads(f.read_text(encoding='utf-8')); cid='SAL103-INTERRUPTED'
            pr.append(f'<tr><td>{cid}</td><td>{esc(request["url"])}</td><td>Capture Search response for comparison -> Interrupted during CID change; no response captured</td><td class="status warn">WARN</td></tr>')
            pe.append(f'<details class="failure-sample"><summary>{cid}  |  WARN capture evidence</summary><h2>Request</h2><pre>{esc(json.dumps(request,indent=2))}</pre><h2>Response capture</h2><pre>No response body was captured before interruption. This is capture evidence, not a server response.</pre></details>')
        extra+='<h2>Superseded SAL103 discovery</h2><p class="run">14 completed preliminary requests and one interrupted capture; these diagnostics are excluded from active TSTCOM release counts and timing graphs. Rule-details coverage was unavailable for matched SAL103 entries.</p><table><thead><tr><th>ID</th><th>Test data</th><th>Expected -> actual</th><th>Status</th></tr></thead><tbody>'+''.join(pr)+'</tbody></table>'+''.join(pe)
    template=re.sub(r'<section class="failure-sample">.*?</section>',lambda m:extra,template,count=1,flags=re.S)
    coverage_text='; '.join(e.upper()+': '+', '.join(k+'='+('/'.join(v) if k not in ['fareCode','rule','subRule','ticketCode'] else str(len(v))+' distinct') for k,v in data['coverage'][e].items()) for e in ['prod','preprod'])
    template=template.replace('&lt;Response count, exact field paths, and other confirmed API facts.&gt;',esc(coverage_text+' Matching requires identical itinerary, exposed original fare inputs and source metadata. Unmatched inventory is excluded from commission equivalence. All exposed fareCalculation passenger/consolidator entries are compared, not just selected cons. No booking/config mutations. Raw timing labels and full sanitized bodies are retained. No CPU profiles or allocation instrumentation performed.'))
    if context.get('public_report'):
        old=esc(coverage_text+' Matching requires identical itinerary, exposed original fare inputs and source metadata. Unmatched inventory is excluded from commission equivalence. All exposed fareCalculation passenger/consolidator entries are compared, not just selected cons. No booking/config mutations. Raw timing labels and full sanitized bodies are retained. No CPU profiles or allocation instrumentation performed.')
        template=template.replace(old,esc(f'{len(timings)} Search responses captured. Exact request URLs, opaque Search keys and saved paired response evidence are provided below.'))
    for name,tag in [('SS-6401.postman_collection.json','collection'),('expected-outcomes.csv','csv')]:
        template=template.replace('&lt;'+tag+'-file-name&gt;',name).replace("'<"+tag+"-file-name>'", "'"+name+"'")
        template=template.replace('<'+tag+'-base64>',base64.b64encode((RUN/name).read_bytes()).decode())
    if context.get('end_at_last_graph'):
        downloads=re.search(r'<section class="evidence">.*?</section>',template,re.S).group(0)
        template=template.replace(downloads,'')
        template=template.replace('<h2>Timing comparison</h2>',downloads+'<h2>Timing comparison</h2>',1)
        scripts=template[template.index('  <script>'):]
        template=template[:template.rindex('</svg>')+len('</svg>')]+'\n    </article>\n  </main>\n'+scripts
    (RUN/'qa-report.html').write_text(template,encoding='utf-8')
    md=[f'Release signal: **{signal}** - '+', '.join(f'{counts[s]} {s}' for s in ['PASS','FAIL','WARN']),strip,'',finding_text,'','Intended behavior: Cut commission CPU/allocations without changing rule matching, selected rules, or applied commissions.','', '| ID | Test data | Expected | Actual | Status |','|---|---|---|---|---|']
    md += ['| '+' | '.join(esc(c[k]).replace('|','/') for k in ['id','data','expected','actual','status'])+' |' for c in cases]
    md+=['','Timing summary: `timing-summary.json`; per-request measurements: `timing.csv`. Server commission timing: `timing[].executionTime` where `process` starts with `Commission service processed `. Units are explicit Go-style durations.','', 'Workload-normalized service timings are elapsed time per processed result, not CPU per fare. Different environments and provider inventory confound direct performance attribution.','', 'All FAIL/WARN request/response excerpts are embedded in qa-report.html. Full opaque keys, exact URLs and consolidated changes: debug-findings.json. Comparison inputs/outputs: comparison.json. Full bodies and sanitized requests: evidence/.','', 'Supporting evidence: SAL103 preliminary runs are retained separately at the task root. They do not establish rule parity because those bodies omitted commission_info. TSTCOM is the active user-corrected CID.','', 'Importable collection: SS-6401.postman_collection.json; expected inputs/outcomes: expected-outcomes.csv. These are embedded Blob downloads in the HTML report. Postman/Newman execution is not claimed; live calls were executed by run.py. No ledger update.']
    if context.get('public_report'):
        cutoff=md.index('Timing summary: `timing-summary.json`; per-request measurements: `timing.csv`. Server commission timing: `timing[].executionTime` where `process` starts with `Commission service processed `. Units are explicit Go-style durations.')
        md=md[:cutoff]+['Timing data: timing.csv and timing-summary.json.','', 'Paired request/response evidence and complete commission_info objects for both trips are embedded in qa-report.html. The collection and expected-outcome CSV are available through its embedded downloads.']
        if context.get('reproduction_run'):
            reproduction_md=(RUN.parent/context['reproduction_run']/'qa-report.md').read_text(encoding='utf-8')
            md+=['','F-90 fresh verification (additional checks, separate from the main matrix):','',reproduction_md]
    if context.get('end_at_last_graph'):
        md=[line.replace('Paired request/response evidence and complete commission_info objects for both trips are embedded in qa-report.html. The collection and expected-outcome CSV are available through its embedded downloads.','Supporting evidence is retained separately. The collection and expected-outcome CSV are available through the HTML report downloads.') for line in md]
    (RUN/'qa-report.md').write_text('\n'.join(md),encoding='utf-8')
    print(dump({'pairs':len(pairs),'test_counts':dict(counts),'release_signal':signal,'findings':len(findings),'timing_summary':summary}))

if __name__=='__main__':main()
