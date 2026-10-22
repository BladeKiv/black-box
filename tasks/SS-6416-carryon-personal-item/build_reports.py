"""Build the two ticket dispatch sheets from the saved fresh Book/Info captures."""
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from templates.render_dispatch import render
from bb.classify import classify_outcome
from bb.lessons import Store
from bb.escalations import Escalations, handle_outcome

URL = 'https://airapi51.kivops.info:8089/ndc/v1/book/info'
RUN = '2026-10-21-preprod-live'
HERE = Path(__file__).parent
SQ = ROOT / 'tasks/SS-6425-baggage-description/runs' / RUN
NDC = HERE / 'runs' / RUN


def read(folder, filename):
    return json.loads((folder / filename).read_text(encoding='utf-8'))


def segments(result):
    return result['body']['data']['response']['pnrInfo']['segments']


def build(folder, ticket, title, intended, summary, rows, cases, limits, source):
    folder.mkdir(parents=True, exist_ok=True)
    collection_name = ticket + '.postman_collection.json'
    setup = [
        "['book_info_url','request_body','checks_json','scenario_id'].forEach(k => { const v=pm.iterationData.get(k); if(v===undefined || v==='') throw new Error('Supply CSV '+k); pm.variables.set(k,v); });",
        "const u=pm.variables.get('book_info_url'); if(u !== 'https://airapi51.kivops.info:8089/ndc/v1/book/info') throw new Error('Unexpected endpoint');",
        "if(!pm.environment.get('booklogin') || !pm.environment.get('bookpass')) throw new Error('Supply local credentials');",
        "JSON.parse(pm.variables.get('request_body')); JSON.parse(pm.variables.get('checks_json'));"
    ]
    checks = [
        "const b=pm.response.json();",
        "const get=(o,p)=>p.split('.').reduce((v,k)=>v==null?undefined:v[k],o);",
        "const checks=JSON.parse(pm.variables.get('checks_json'));",
        "pm.test('Ticket baggage response available',()=>pm.expect(pm.response.code).to.equal(200));",
        "checks.forEach(c=>pm.test(c.path,()=>pm.expect(get(b,c.path)).to.eql(c.value)));",
        "console.log('Actual baggage snapshot',get(b,'data.response.pnrInfo.segments'));"
    ]
    collection = {'info': {'name': title, 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
        'description': 'AirAPI Book/Info only. Use Collection Runner with CSV and local booklogin/bookpass. HTTPS; disable TLS verification under standing user authorization. Refresh trace-correlated source on rerun. QF SYD-PER and null return segments are observation-only; no numerical correctness assertion is supplied.'},
        'item': [{'name': '{{scenario_id}} Book/Info', 'event': [
            {'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': setup}},
            {'listen': 'test', 'script': {'type': 'text/javascript', 'exec': checks}}],
            'request': {'method': 'POST', 'url': '{{book_info_url}}',
                'auth': {'type': 'basic', 'basic': [{'key': 'username', 'value': '{{booklogin}}', 'type': 'string'}, {'key': 'password', 'value': '{{bookpass}}', 'type': 'string'}]},
                'header': [{'key': 'Content-Type', 'value': 'application/json'}],
                'body': {'mode': 'raw', 'raw': '{{request_body}}', 'options': {'raw': {'language': 'json'}}}}}]}
    (folder / collection_name).write_text(json.dumps(collection, indent=2), encoding='utf-8')
    fields = ['scenario_id','expected_result','provider_filter','search_url','book_info_url','request_body','checks_json']
    with (folder / 'expected-outcomes.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for name, case_folder, expectation, assertions in cases:
            writer.writerow(dict(scenario_id=name, expected_result=expectation, provider_filter=ticket + ':' + name,
                search_url='', book_info_url=URL, request_body=json.dumps(read(case_folder,'request.json'), separators=(',',':')),
                checks_json=json.dumps(assertions, separators=(',',':'))))
    evidence = [{'id': row['id'], 'request': read(case_folder,'request.json'), 'response': read(case_folder,'response.json')}
                for row, case_folder in rows if row['status'] in ('WARN','FAIL')]
    if ticket == 'SS-6416':
        evidence.append({'id': 'QF actual fields - observation only',
                         'request': read(folder/'QF', 'request.json'),
                         'response': read(folder/'QF', 'response.json')})
    data = dict(title=title, scope='PREPROD | POST /ndc/v1/book/info | 2026-10-21 | HTTPS / TLS verification bypassed',
                intended=intended, summary=summary, rows=[r for r,_ in rows], collection=collection_name,
                limits=limits, evidence=evidence)
    (folder/'report-data.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    (folder/'provider-source-evidence.json').write_text(json.dumps(source,indent=2),encoding='utf-8')
    (folder/'test-results.json').write_text(json.dumps(data['rows'],indent=2),encoding='utf-8')
    result=render(folder)
    assert all(r['status']=='PASS' or any(e['id']==r['id'] for e in evidence) for r in data['rows'])
    print(ticket, result)


def check(path, value):
    return {'path':'data.response.pnrInfo.segments.'+path, 'value':value}


def main():
    sq=read(SQ,'response.json'); lx=read(NDC/'LX','response.json'); aa=read(NDC/'AA','response.json'); qf=read(NDC/'QF','response.json')
    ss=segments(sq); ls=segments(lx); qs=segments(qf)
    assert len(ss)==6 and len(ls)==1 and len(qs)==7
    assert all(s['baggage']['ADT']['weightKg']==23 and s['baggage']['ADT']['numberOfPcs']=='02P' and s['baggage']['ADT']['baggageFullTextD']=='FBD UP TO 2  UPTO50LB 23KG' for s in ss)
    assert all(s['carryOn']['ADT']['numberOfPcs']=='1P' and s['carryOn']['ADT']['weightKg']==7 and s['carryOn']['ADT']['lengthCm']==115 for s in ss)
    assert ls[0]['carryOnAllowance']=='3P' and ls[0]['carryOn']['ADT']['numberOfPcs']=='3P'
    assert aa['http_status']==409 and aa['body']['message']=='Booking already flown'
    assert all(s['carryOnAllowance']=='1P' and s['carryOn']['JCB']['lengthCm']==115 for s in qs[:2])
    assert qs[2]['carryOn']['JCB']['weightKg']==7 and qs[2]['carryOn']['JCB']['lengthCm']==115
    assert all(s['baggage']['JCB']['numberOfPcs']=='01P' and s['baggage']['JCB']['weightKg']==32 and s['baggage']['JCB']['lengthCm']==158 for s in qs[:4])
    sq_checks=[check(f'{i}.baggage.ADT.{k}',v) for i in range(6) for k,v in [('numberOfPcs','02P'),('weightKg',23),('baggageFullTextD','FBD UP TO 2  UPTO50LB 23KG')]]
    sq_checks += [check(f'{i}.carryOn.ADT.{k}',v) for i in range(6) for k,v in [('numberOfPcs','1P'),('weightKg',7),('lengthCm',115)]]
    sq_source={'traceID':sq['traceID'],'operation':'/Travel_OrderRetrieve_1.1','timestamp_local':'2026-10-21 14:39:52.371 Europe/Bucharest',
        'checked_allowance':{'BaggageAllowanceID':'FBA1','TypeCode':'Checked','TotalQty':2},
        'associations':'BAGALLOW_1 -> FBA1; PAX2 and PAX3 linked to SEG1 through SEG6',
        'priceClasses':{'FF31CORDPL':{'segments':['SEG1','SEG2','SEG3'],'DescText':'Check-in baggage - 30kg (or 2 pieces up to 23kg each for flights to/from the USA or Canada only)'},
        'FF51CORDPL':{'segments':['SEG4','SEG5','SEG6'],'DescText':'Check-in baggage - 25kg (or 2 pieces up to 23kg each for flights to/from the USA or Canada only)'}},
        'carryOn_DescText':'Cabin baggage - 1 piece Up to 7kg each. Sum of length, width and height of each piece should not exceed 115cm.'}
    build(SQ,'SS-6425','SS-6425 - checked-baggage description parsing',
        'For FBA with allowPieces >= 1, parse the up to #kg trigger and create the baggage template. Retain carry-on parsing.',
        'Checked-baggage extension verified on all six SQ segments: 2 pieces, 23 kg and FBD text. Carry-on remains 1 piece, 7 kg, 115 cm. Fresh provider source matches response trace.',
        [(dict(id='TC-01',data='SQ CPS9CG; 2 ADT; 6 segments; linked PriceClasses',expected='2 checked pieces at 23 kg; weight-bearing FBD template on six segments',actual='HTTP 200; all six: numberOfPcs=02P, weightKg=23, weightLb=50, FBD UP TO 2  UPTO50LB 23KG',status='PASS'),SQ),
         (dict(id='TC-02',data='Same fresh SQ response; six segments',expected='Carry-on 1 piece, 7 kg, 115 cm retained',actual='All six: carryOnAllowance=1P, numberOfPcs=1P, weightKg=7, lengthCm=115',status='PASS'),SQ)],
        [('SQ',SQ,'Checked: 2 pieces / 23 kg plus FBD template. Carry-on: 1 piece / 7 kg / 115 cm.',sq_checks)],
        'Fresh trace '+sq['traceID']+'. Both PriceClasses and twelve passenger/segment FBA links checked. No booking changes. Original sandbox transport attempts are retained separately and do not establish a service outage. Other fixtures/endpoints are not certified. Ledger unchanged.',sq_source)
    qf_checks=[check(f'{i}.carryOn.JCB.numberOfPcs','1P') for i in range(3)]
    qf_checks += [check(f'{i}.carryOn.JCB.lengthCm',115) for i in range(3)]
    qf_checks += [check('2.carryOn.JCB.weightKg',7)]
    qf_checks += [check(f'{i}.baggage.JCB.{k}',v) for i in range(4) for k,v in [('numberOfPcs','01P'),('weightKg',32),('lengthCm',158)]]
    rows=[(dict(id='TC-01',data='LX 2L2FGK; 2 ADT; VCE-ZRH',expected='2 carry-on pieces; exclude the 1-piece handbag',actual='HTTP 200; carryOnAllowance=3P and carryOn.ADT.numberOfPcs=3P; 8 kg / 118 cm. Handbag is still included.',status='FAIL'),NDC/'LX'),
          (dict(id='TC-02',data='AA BRGQ35; 1 ADT; ORD-MCO',expected='1 carry-on piece; exclude personal item',actual='HTTP/body 409; Booking already flown. No current baggage data returned.',status='WARN'),NDC/'AA'),
          (dict(id='TC-03',data='QF C6426L; 5 JCB; TPA-DFW and DFW-AKL',expected='1 carry-on piece / 115 cm per segment; exclude PERSONAL ITEM UP TO 40 LI',actual='Both segments: carryOnAllowance=1P; carryOn.JCB.numberOfPcs=1P, lengthCm=115. Fresh source includes separate personal-item entry for all five passengers.',status='PASS'),NDC/'QF'),
          (dict(id='TC-04',data='QF C6426L; AKL-SYD carry-on and first four checked-baggage segments',expected='AKL-SYD carry-on: 1 piece / 7 kg / 115 cm. Checked: 1 piece / 32 kg / 158 cm on first four segments, matching linked source.',actual='Fresh response matches these quantities, weights, dimensions and source segment associations.',status='PASS'),NDC/'QF')]
    source={'LX':{'traceID':lx['traceID'],'timestamp_local':'2026-10-21 14:40:07.372 Europe/Bucharest','source_segment':'S3 VCE-ZRH','carryOn':[{'TotalQty':2,'ApplicableBagText':'CARRY8KG 18LB UPTO46LI 118LCM','kg':8,'cm':118},{'TotalQty':1,'ApplicableBagText':'HANDBAG UPTO 40 X 30 X 15CM'}],'links':{'T1':'BABF434102-CO','T2':'BA57365A23-CO'}},
        'AA':{'traceID':aa['traceID'],'http_status':409,'message':'Booking already flown','baggage_data_available':False},
        'QF':{'traceID':qf['traceID'],'timestamp_local':'2026-10-21 14:40:33.375 Europe/Bucharest','operation':'/Travel_OrderRetrieve_1.1',
        'checked':'All T1-T5 -> S6,S7,S8,S9: 1 piece / 32 kg / 158 cm',
        'carryOn':{'S6,S7':'All T1-T5: 1 CARRY ON UP TO 45 LI 115 LCM plus 1 PERSONAL ITEM UP TO 40 LI','S8':'All T1-T5: 1 CARRY7KG 15LB UPTO45LI 115LCM','S9':'All T1-T5: quantities 2,1,1; text dimensions 105,105,115 cm; structured dimensions 105,105,105 cm; each 7 kg','S10,S11,S12':'No linked baggage services observed'},
        'actual_segments':qs,'SYD_PER_verdict':'Observation only, per user request to see actual output; no numerical correctness claim'}}
    build(NDC,'SS-6416','SS-6416 - carry-on versus personal item',
        'Exclude personal items from carry-on: LX expects 2, AA expects 1. Check QF baggage differences per linked segment. User requested actual SYD-PER fields without choosing an expected numeric interpretation.',
        'LX still returns 3P instead of 2P. AA is unavailable: 409 Booking already flown. QF excludes the explicit personal item on its first two segments; SYD-PER actually returns 4P / 7 kg / 105 cm. Its final three segments return explicit null baggage and carry-on.',rows,
        [('LX',NDC/'LX','2 carry-on pieces; exclude handbag',[check('0.carryOnAllowance','2P'),check('0.carryOn.ADT.numberOfPcs','2P')]),
         ('AA',NDC/'AA','1 carry-on piece; exclude personal item',[check('0.carryOnAllowance','1P')]),
         ('QF',NDC/'QF','Check approved first-segment mappings; log all actual fields. SYD-PER and final null segments remain observation-only.',qf_checks)],
        'Fresh traces: LX '+lx['traceID']+'; AA '+aa['traceID']+'; QF '+qf['traceID']+'. Full sanitized QF segment snapshot is in QF/response.json and provider-source-evidence.json. SYD-PER is actual-only: no correctness verdict for the 4-piece aggregation or conflicting source dimensions. Final three null segments are recorded as returned, with no missing/null equivalence claim. No state-changing endpoints or ledger updates. AA requires an available existing booking for a conclusive retest.',source)
    store=Store(); escalations=Escalations(store=store)
    for case,status in [('LX','FAIL'),('AA','WARN')]:
        r=read(NDC/case,'response.json')
        outcome=classify_outcome(r['http_status'],json.dumps(r['body']),r['transport_error'],
            {'inventory_field':'data.response.pnrInfo.segments','expectation_observed':False} if case=='LX' else {'inventory_field':'data.response.pnrInfo.segments','comparable_count':0})
        assert outcome['status']==status
        scope={'ticket':'SS-6416','environment':'PREPROD','endpoint':'/ndc/v1/book/info','allow_retry':False,'allow_poll':False,'allow_retest':True,'approved_inputs':[case]}
        decision=handle_outcome(store,escalations,outcome,'SS-6416-'+RUN+'-'+case,['SS-6416','PREPROD'],
            'handbag included in carry-on' if case=='LX' else 'existing booking already flown',scope,retries=0,steps=1)
        (NDC/case/'triage.json').write_text(json.dumps(decision,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
