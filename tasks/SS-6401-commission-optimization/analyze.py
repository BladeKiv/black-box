import json, re, collections, statistics, math, csv, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
requested=sys.argv[1] if len(sys.argv)>1 else 'TSTCOM'
RUN=ROOT if requested=='SAL103' else ROOT/'runs'/requested

def equivalent_rules(x):
    if isinstance(x,list):return [equivalent_rules(v) for v in x]
    if not isinstance(x,dict):return x
    fare=x.get('fare',x)
    od=(fare.get('departure'),fare.get('arrival')) if isinstance(fare,dict) else (None,None)
    approved={('SFO','MUC'):{(5561,37750,'TC7AIB','TC7A'),(4065,28486,'AJBUPY','AJBUPY')},('MUC','SFO'):{(5556,37713,'TC7AOB','TC7A'),(4065,28486,'AJBUPY','AJBUPY')}}
    commissions=x.get('commissions',{});vzc=commissions.get('VZC',{});upfront=vzc.get('upfront',{})
    if tuple(upfront.get(k) for k in ['rule','subRule','combKey','tourCode']) in approved.get(od,set()):
        choice={k:v for k,v in upfront.items() if k not in ['subRule','combKey','tourCode']}
        choice['rule']='TC7A/AJBUPY equivalent'
        x={**x,'commissions':{**commissions,'VZC':{**vzc,'upfront':choice}}}
    duplicate=x.get('rule') in (6189,6082)
    am_duplicate=x.get('rule') in (4989,4926)
    return {k:('6189/6082 equivalent' if duplicate and k=='rule' else '4989/4926 equivalent' if am_duplicate and k=='rule' else equivalent_rules(v)) for k,v in x.items() if k!='oComm' and not (duplicate and k=='subRule') and not (am_duplicate and k in ['subRule','combKey'])}
def dump(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)
def comparison_dump(x):return dump(equivalent_rules(x))
def same_lowest_choice(a,b):
    return (isinstance(a,dict) and isinstance(b,dict) and a.get('contract')==b.get('contract')=='Lowest' and isinstance(a.get('subRule'),int) and isinstance(b.get('subRule'),int) and {k:v for k,v in a.items() if k!='subRule'}=={k:v for k,v in b.items() if k!='subRule'})
def usd_breakdown_equal(a,b):
    if not isinstance(a,dict) or not isinstance(b,dict) or not a or not b or not (a.keys()|b.keys())<={'backend','upfront'}:return False
    rows=[]
    for value in [a,b]:
        if not all(isinstance(v,list) for v in value.values()):return False
        rows.append(sorted([v for entries in value.values() for v in entries],key=lambda v:dump({k:n for k,n in v.items() if k not in ['amount','fullAmount']})))
    if not rows[0] or len(rows[0])!=len(rows[1]):return False
    for x,y in zip(*rows):
        if 'amount' not in x or 'amount' not in y:return False
        if x.get('currency')!='USD' or y.get('currency')!='USD':return False
        if x.keys()!=y.keys() or {k:v for k,v in x.items() if k not in ['amount','fullAmount']}!={k:v for k,v in y.items() if k not in ['amount','fullAmount']}:return False
        for k in ['amount','fullAmount']:
            if k in x and (not isinstance(x[k],(int,float)) or not isinstance(y[k],(int,float)) or abs(x[k]-y[k])>1+1e-9):return False
    return True
def prod_segments(value):
    if not isinstance(value,list) or not all(isinstance(v,dict) and 'tripId' in v and 'segmentId' in v for v in value):return value
    seen=set();out=[]
    for v in value:
        key=dump(v)
        if v['tripId'] in (1,2) and key in seen:continue
        seen.add(key);out.append(v)
    return out

def pair_equal(a,b,path=''):
    # Direction matters: a is PROD, b is PREPROD.
    a=equivalent_rules(a);b=equivalent_rules(b)
    def same(x,y,path,usd_prices=False):
        if isinstance(x,dict) and isinstance(y,dict):
            if usd_breakdown_equal(x,y):return True
            if same_lowest_choice(x,y):return True
            breakdown=path.endswith('.commBreakdown')
            if breakdown:
                aa={k:v for k,v in x.items() if k in ['backend','upfront']}
                bb={k:v for k,v in y.items() if k in ['backend','upfront']}
                if usd_breakdown_equal(aa,bb):
                    x={k:v for k,v in x.items() if k not in aa};y={k:v for k,v in y.items() if k not in bb}
            allowed_extra={k for k in y.keys()-x.keys() if (k=='commBreakdown' and isinstance(y[k],dict)) or (breakdown and isinstance(y[k],list))}
            if x.keys()!=y.keys()-allowed_extra:return False
            asset=bool(re.search(r'\.priceElement\.Assets\.Commission\.ValuePerPax\.[^.]+$',path)) and x.get('currency')==y.get('currency')=='USD'
            for k in x:
                numeric=isinstance(x[k],(int,float)) and not isinstance(x[k],bool) and isinstance(y[k],(int,float)) and not isinstance(y[k],bool)
                if '.segmentFees' in path and k in ['amount','fullAmount'] and numeric:
                    if y[k]>x[k]+1e-9:return False
                elif ((usd_prices and k in ['totalPrice','totalTax']) or (asset and k=='amount')) and numeric:
                    if abs(x[k]-y[k])>1+1e-9:return False
                elif not same(x[k],y[k],path+'.'+k,k=='prices' and x.get('currency')==y.get('currency')=='USD'):return False
            return True
        if isinstance(x,list) and isinstance(y,list):
            if path.endswith('.segments'):x=prod_segments(x)
            return len(x)==len(y) and all(same(v,w,path+f'[{i}]') for i,(v,w) in enumerate(zip(x,y)))
        if isinstance(x,bool)!=isinstance(y,bool):return False
        return x==y
    return same(a,b,path)

def match_records(aa,bb,project):
    left=[project(r) for r in aa];right=[project(r) for r in bb]
    edges=[[j for j,value in enumerate(right) if pair_equal(other,value)] for other in left];owners={}
    def assign(i,seen):
        for j in edges[i]:
            if j in seen:continue
            seen.add(j)
            if j not in owners or assign(owners[j],seen):owners[j]=i;return True
        return False
    for i in range(len(aa)):assign(i,set())
    used=set(owners.values())
    return [(aa[i],bb[j]) for j,i in owners.items()],[r for i,r in enumerate(aa) if i not in used],[r for j,r in enumerate(bb) if j not in owners]
def pick(x,names): return {k:x[k] for k in names if isinstance(x,dict) and k in x}
def identity(r):
    # Only original fare inputs belong here; applied amounts must not hide a regression.
    out=pick(r,['gds','pcc','cons','fareType','validatingCarrier','currency','paxCnt','tripType'])
    out['trips']=[[pick(s,['departureAirportCode','arrivalAirportCode','departureTime','arrivalTime','marketingAirline','operatingAirline','flightNumber','bookingClass','cabin','fareCode','brandId']) for s in t.get('segments',[])] for t in r.get('trips',[])]
    out['input_prices']=pick(r.get('priceElement',{}),['GdsCurrency','TargetCurrency','oBaseFare','oBaseTax','oPubBaseFare','oPubBaseTax'])
    out['passenger_inputs']={k:pick(p,['codeAs','cnt','pubBaseFare','pubBaseTax']) for k,p in r.get('passengers',{}).items()}
    out['original_info']=pick(r.get('keys',{}),['original_info'])
    info=r.get('keys',{}).get('commission_info')
    if isinstance(info,dict):
        out['fare_inputs']={pax:sorted([pick(f,['code','owner','bookingClass','cabin','departure','arrival','departureTime','arrivalTime','amount','currency','surcharges']) for f in fares],key=dump) for pax,fares in info.get('fareCalculation',{}).items()}
    if r.get('tickets'): out['tickets']=[identity(t) for t in r['tickets']]
    return out

def output(r):
    pe=r.get('priceElement',{})
    out={'prices':pick(r.get('prices',{}),['totalPrice','totalTax','comm','commBreakdown','isCk','markup','oMarkup']), 'passengers':r.get('passengers',{}), 'priceElement':pick(pe,['Assets','CK','CpanelMK'])}
    if 'commission_info' in r.get('keys',{}): out['commission_info']=r['keys']['commission_info']
    out.update(pick(r,['currency']))
    if 'tickets' in r: out['tickets']=None if r['tickets'] is None else [output(t) for t in r['tickets']]
    return out

def rules(r):
    info=r.get('keys',{}).get('commission_info')
    out={}
    if isinstance(info,dict):
        out['fareCalculation']={pax:sorted([{'fare':pick(f,['code','owner','bookingClass','cabin','departure','arrival','amount','currency','surcharges']), 'commissions':{cons:{kind:pick(c,['rule','subRule','type','percent','contract','contractClass','mapping','ticketCode','tourCode','combKey','consolidator','currency','deduct','withSurcharges','dropnet']+(['amount','fullAmount'] if c.get('rule') in (4989,4926) or (cons=='VZC' and kind=='upfront' and (f.get('departure'),f.get('arrival')) in [('SFO','MUC'),('MUC','SFO')]) else [])) for kind,c in kinds.items()} for cons,kinds in f.get('commissions',{}).items()}} for f in fares],key=dump) for pax,fares in info.get('fareCalculation',{}).items()}
        out['processed']=info.get('processed','[MISSING]')
    if r.get('tickets'):
        children=[rules(t) for t in r['tickets']]
        if any(children): out['tickets']=children
    return out

def duration(v):
    if not isinstance(v,str): return None
    unit={'h':3600,'m':60,'s':1,'ms':.001,'us':.000001,'\u00b5s':.000001,'\u03bcs':.000001,'ns':1e-9}
    matches=re.findall(r'([\d.]+)(ms|us|\u00b5s|\u03bcs|ns|h|m|s)',v)
    return sum(float(n)*unit[u] for n,u in matches) if matches else None

def timing(d,m):
    t=[x for x in d.get('timing',[]) if x.get('process','').startswith('Commission service processed ')]
    row={k:m.get(k) for k in ['scenario_id','repeat','environment','status','response_seconds','started_utc']}
    row.update(returned_results=len(d.get('results',[])),server_search_seconds=duration(d.get('excutionTime')))
    row['commission_seconds']=sum(duration(x.get('executionTime')) or 0 for x in t) if t else None
    parsed=[re.search(r'processed (\d+) and returned (\d+) results',x.get('process','')) for x in t]
    row['commission_processed']=sum(int(x[1]) for x in parsed if x) if parsed and all(parsed) else None
    row['commission_returned']=sum(int(x[2]) for x in parsed if x) if parsed and all(parsed) else None
    row['commission_us_per_processed']=(row['commission_seconds']*1e6/row['commission_processed']) if row['commission_processed'] else None
    row['commission_info_results']=sum('commission_info' in r.get('keys',{}) for r in d.get('results',[]))
    return row

def compare(a,b):
    groups=[]
    for d in [a,b]:
        g=collections.defaultdict(list)
        for r in d.get('results',[]): g[dump(identity(r))].append(r)
        groups.append(g)
    ga,gb=groups; matched=equal=0; differences=[]; samples=[]; positive=0; info_matched=0; rule_evaluated=rule_equal=0; rule_differences=[]
    for key in ga.keys() & gb.keys():
        aa,bb=ga[key],gb[key]; matched+=min(len(aa),len(bb))
        rule_a=[r for r in aa if rules(r)]; rule_b=[r for r in bb if rules(r)]
        rule_evaluated+=min(len(rule_a),len(rule_b))
        rule_matches,rule_left,rule_right=match_records(rule_a,rule_b,rules)
        rule_equal+=len(rule_matches)
        if rule_left and rule_right:
            x,y=rule_left[0],rule_right[0]
            rule_differences.append({'input':identity(x),'prod_key':x.get('key'),'preprod_key':y.get('key'),'prod':rules(x),'preprod':rules(y)})
        matches,ra,rb=match_records(aa,bb,output);equal+=len(matches)
        for r,p in matches:
            if r.get('prices',{}).get('comm',0): positive+=1
            if 'commission_info' in r.get('keys',{}): info_matched+=1
            if len(samples)<3:
                samples.append({'input':identity(r),'prod_key':r.get('key'),'preprod_key':p.get('key'),'output':output(r)})
        # Unequal availability alone is not a financial contradiction.
        if ra and rb:
            x,y=ra[0],rb[0]
            differences.append({'input':identity(x),'prod_key':x.get('key'),'preprod_key':y.get('key'),'prod':output(x),'preprod':output(y),'prod_variants':len(ra),'preprod_variants':len(rb)})
    return {'matched':matched,'equal':equal,'positive_commission_equal':positive,'commission_info_equal':info_matched,'rule_evaluated':rule_evaluated,'rule_equal':rule_equal,'rule_differences':rule_differences,'differences':differences,'samples':samples,'prod_only':sum(len(v) for k,v in ga.items() if k not in gb),'preprod_only':sum(len(v) for k,v in gb.items() if k not in ga)}

def main():
    pairs=[]; timings=[]; coverage={env:{k:set() for k in ['validatingCarrier','gds','pcc','cons','fareType','bookingClass','fareCode','pax','fare_owner','commission_consolidator','rule','subRule','contract','ticketCode']} for env in ['prod','preprod']}
    def commission_coverage(r,env):
        info=r.get('keys',{}).get('commission_info') or {}
        for fares in info.get('fareCalculation',{}).values():
            for fare in fares:
                if 'owner' in fare: coverage[env]['fare_owner'].add(str(fare['owner']))
                for cons,kinds in fare.get('commissions',{}).items():
                    coverage[env]['commission_consolidator'].add(cons)
                    for commission in kinds.values():
                        for k in ['rule','subRule','contract','ticketCode']:
                            if k in commission: coverage[env][k].add(str(commission[k]))
        for t in r.get('tickets') or []: commission_coverage(t,env)
    for scenario in json.loads((RUN/'scenarios.json').read_text()):
        sid=scenario['scenario_id']
        repeats=sorted([p.name for p in (RUN/'evidence'/sid).glob('*') if p.is_dir()],key=lambda s:(int(s.split('-')[0]),s))
        for repeat in repeats:
            folders=[RUN/'evidence'/sid/str(repeat)/env for env in ['prod','preprod']]
            if not all((p/'meta.json').exists() for p in folders): continue
            ds=[]; ms=[]
            for env,p in zip(['prod','preprod'],folders):
                m=json.loads((p/'meta.json').read_text()); ms.append(m)
                try: d=json.loads((p/'response.json').read_bytes())
                except (ValueError,OSError): d={}
                ds.append(d); timings.append(timing(d,m))
                for r in d.get('results',[]):
                    commission_coverage(r,env)
                    for k in ['validatingCarrier','gds','pcc','cons','fareType']:
                        if k in r: coverage[env][k].add(str(r[k]))
                    coverage[env]['pax'].update(r.get('passengers',{}))
                    for t in r.get('trips',[]):
                        for s in t.get('segments',[]):
                            for k in ['bookingClass','fareCode']:
                                if k in s: coverage[env][k].add(str(s[k]))
            c=compare(*ds)
            c.update(scenario_id=sid,repeat=repeat,query=scenario['query'],requests=[json.loads((p/'request.json').read_text()) for p in folders],statuses=[m.get('status') for m in ms])
            c['amount_status']='FAIL' if c['differences'] else ('PASS' if c['matched'] and c['equal']==c['matched'] else 'WARN')
            c['rule_status']='FAIL' if c['rule_differences'] else ('PASS' if c['rule_evaluated'] and c['rule_equal']==c['rule_evaluated'] else 'WARN')
            pairs.append(c)
    out={'pairs':pairs,'timings':timings,'coverage':{e:{k:sorted(v) for k,v in c.items()} for e,c in coverage.items()}}
    (RUN/'comparison.json').write_text(json.dumps(out,indent=2))
    if timings:
        with (RUN/'timing.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(timings[0])); w.writeheader(); w.writerows(timings)
    print(dump({'pairs':len(pairs),'matched':sum(p['matched'] for p in pairs),'equal':sum(p['equal'] for p in pairs),'differences':sum(len(p['differences']) for p in pairs),'amount_statuses':dict(collections.Counter(p['amount_status'] for p in pairs)),'commission_info_results':sum(t['commission_info_results'] for t in timings)}))

if __name__=='__main__': main()
