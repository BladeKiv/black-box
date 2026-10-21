import json,collections
from analyze import RUN,identity,output,rules,dump

def main():
    result={}; examples=[]
    for env in ['prod','preprod']:
        groups=collections.defaultdict(list)
        for path in sorted((RUN/'evidence').glob('TC-*/*/'+env+'/response.json')):
            try: d=json.loads(path.read_bytes())
            except ValueError: continue
            for r in d.get('results',[]):
                groups[(path.parents[2].name,dump(identity(r)))].append({'repeat':path.parents[1].name,'key':r.get('key'),'rules':dump(rules(r)),'output':dump(output(r))})
        repeated={k:v for k,v in groups.items() if len(set(x['repeat'] for x in v))>=2}
        rule_changed=[]; output_changed=[]
        for (scenario,inp),rows in repeated.items():
            rv={x['rules'] for x in rows}; ov={x['output'] for x in rows}
            if len(rv)>1: rule_changed.append((scenario,inp,rows))
            if len(ov)>1: output_changed.append((scenario,inp,rows))
        result[env]={'repeated_input_groups':len(repeated),'groups_with_rule_variants':len(rule_changed),'groups_with_output_variants':len(output_changed)}
        # Retain a bounded diagnostic sample; complete raw repetitions remain in evidence/.
        for scenario,inp,rows in rule_changed[:5]: examples.append({'environment':env,'scenario_id':scenario,'matched_input':json.loads(inp),'observations':[{'repeat':r['repeat'],'key':r['key'],'rules':json.loads(r['rules'])} for r in rows]})
    (RUN/'stability.json').write_text(json.dumps({'summary':result,'examples':examples},indent=2))
    print(dump(result))

if __name__=='__main__':main()
