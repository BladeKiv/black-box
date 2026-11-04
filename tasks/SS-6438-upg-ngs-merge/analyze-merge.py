"""Offline evaluation of captured AirAPI groups; Search keys remain opaque."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def features(option):
    bags = option['keys']['baggage']['allowPieces']
    exchange = option['penalties']['exchange']
    refund = option['penalties']['refund']
    if type(bags) not in (int, float) or type(exchange) is not bool or type(refund) is not bool:
        raise ValueError('Required feature type missing or ambiguous')
    return bags, exchange, refund

def improves(current, previous):
    return all(a >= b for a, b in zip(current, previous)) and any(a > b for a, b in zip(current, previous))

def retain(options):
    kept = []
    for option in sorted(options, key=lambda x:x[0]):
        if not kept or improves(option[1], kept[-1][1]):
            kept.append(option)
    return kept

def signature(option):
    return [[{k:s.get(k) for k in ('departureAirportCode','arrivalAirportCode','departureTime','arrivalTime','marketingAirline','flightNumber')} for s in trip.get('segments', [])] for trip in option.get('trips', [])]

def excerpt(option):
    bags, exchange, refund = features(option)
    keys={'baggage':{'allowPieces':bags}}
    if 'upgrade_info' in option['keys']:
        keys['upgrade_info']={k:v for k,v in option['keys']['upgrade_info'].items() if k=='upgrade_program'}
    return {'key':option['key'], 'gdsOfferId':option.get('gdsOfferId'), 'currency':option.get('currency'), 'prices':{'totalPrice':option['prices']['totalPrice']}, 'keys':keys, 'penalties':{'exchange':exchange,'refund':refund}}

def analyze():
    runs = []
    for name in ('M01','M02','M03','M04','M05'):
        capture = json.loads((ROOT / (name+'.json')).read_text())
        assert capture['response']['http_status'] == 200
        results = capture['response']['body']['results']
        groups = []
        for index, main in enumerate(results):
            children = main.get('ngsItineraries', [])
            assert isinstance(children, list)
            if not ('upgrade_info' in main.get('keys', {}) or any('upgrade_info' in child.get('keys', {}) for child in children)):
                continue
            options = [main]+children
            assert all(o.get('currency')=='USD' for o in options)
            prices = [o['prices']['totalPrice'] for o in options]
            vectors = [features(o) for o in options]
            groups.append({'result_index':index, 'main_source':'UPG' if 'upgrade_info' in main.get('keys', {}) else 'regular', 'options':[excerpt(o) for o in options], 'children_count':len(children), 'regular_children':sum('upgrade_info' not in o.get('keys', {}) for o in children), 'upg_children':sum('upgrade_info' in o.get('keys', {}) for o in children), 'price_order_ok':prices==sorted(prices), 'main_minimum_retained':prices[0]==min(prices), 'features_ok':all(improves(a,b) for a,b in zip(vectors[1:],vectors)), 'flight_identity_ok':all(signature(main)==signature(o) for o in children), 'numbering_ok':all(o.get('gdsOfferId','').endswith(':NGS#'+str(i+1)) for i,o in enumerate(options)) if children else None})
        runs.append({'scenario_id':name, 'request':capture['request'], 'http_status':capture['response']['http_status'], 'started_at':capture['started_at'], 'result_count':len(results), 'keepBothBagOptions':name in ('M02','M04','M05'), 'groups':groups})
    return runs

if __name__=='__main__':
    # The four ticket examples verify the offline oracle before it evaluates evidence.
    assert [x[0] for x in retain([(3000,(1,0,0)),(4500,(1,1,0)),(6000,(2,1,1))])]==[3000,4500,6000]
    assert [x[0] for x in retain([(3000,(1,0,0)),(3500,(2,0,0)),(4500,(1,1,0)),(6000,(2,1,1))])]==[3000,3500,6000]
    assert [x[0] for x in retain([(2800,(0,0,0)),(3000,(1,0,0)),(4500,(1,1,0)),(6000,(2,1,1))])]==[2800,3000,4500,6000]
    assert [x[0] for x in retain([(2800,(0,0,0)),(3000,(1,0,0)),(3500,(2,0,0)),(4500,(1,1,0)),(6000,(2,1,1))])]==[2800,3000,3500,6000]
    runs=analyze()
    (ROOT/'merge-analysis.json').write_text(json.dumps(runs,indent=2),encoding='utf-8')
    groups=[g for r in runs for g in r['groups']]
    print(json.dumps({'searches':len(runs),'results':sum(r['result_count'] for r in runs),'groups':len(groups),'options':sum(len(g['options']) for g in groups),'regular_mains':sum(g['main_source']=='regular' for g in groups),'regular_children':sum(g['regular_children'] for g in groups),'upg_children':sum(g['upg_children'] for g in groups),'singletons':sum(g['children_count']==0 for g in groups),'violations':{k:sum(not g[k] for g in groups) for k in ('price_order_ok','main_minimum_retained','features_ok','flight_identity_ok')},'multi_option_numbering_violations':sum(g['numbering_ok'] is False for g in groups),'oracle_examples':4}))
