"""Analyze saved AirAPI evidence only; makes no network calls."""
import csv
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from templates.render_dispatch import render

FOLDER = Path(__file__).parent / 'runs/2026-10-23'


def load(name):
    return json.loads((FOLDER / name).read_text(encoding='utf-8'))


def signature(result):
    return [(z['departureAirportCode'], z['arrivalAirportCode'], z['departureTime'],
             str(z['flightNumber']), z['bookingClass'], z['fareCode'])
            for trip in result['trips'] for z in trip['segments']]


def analyze():
    soap = load('soap-network-approved-response.json')
    rest = load('rest-recheck-response.json')
    body = rest['body']
    # Transport redacts names inside JSON strings into bare placeholders; omit only those fields.
    source = json.loads(body['req_resp'][0]['response'].replace(',[REDACTED]', ''))
    flights = {x['id']: x for x in source['flights']}
    journeys = {x['id']: x for x in source['journeys']}
    bags = {x['id']: x for x in source['offerAttributes']['checkedBaggageItems']}
    errors = {k: [] for k in ('matching', 'itinerary', 'cabin_meal', 'pricing', 'allowance', 'weight')}
    pairs = []
    segments = 0
    allowance_checks = 0
    weight_checks = 0
    for offer in source['offers']:
        assert len(offer['items']) == 1 and len(offer['items'][0]['fares']) == 1
        fare = offer['items'][0]['fares'][0]
        details = {d['flightRef']: (d, c) for c in fare['fareComponents'] for d in c['segmentDetails']}
        refs = [f for j in offer['journeyRefs'] for f in journeys[j]['flightRefs']]
        expected = [(flights[f]['departureAirportCode'], flights[f]['arrivalAirportCode'],
                     flights[f]['departureDate'] + ' ' + flights[f]['departureTime'],
                     str(flights[f]['marketingFlightNumber']), details[f][0]['bookingClassCode'],
                     details[f][1]['fareBasisCode']) for f in refs]
        matches = [r for r in body['results'] if signature(r) == expected]
        if len(matches) != 1:
            errors['matching'].append({'offer': offer['id'], 'matches': len(matches)})
            continue
        result = matches[0]
        pairs.append((offer, result))
        actual_segments = [z for t in result['trips'] for z in t['segments']]
        segments += len(refs)
        for ref, segment in zip(refs, actual_segments):
            flight = flights[ref]
            detail, component = details[ref]
            expected_fields = {
                'arrivalTime': flight['arrivalDate'] + ' ' + flight['arrivalTime'],
                'marketingAirline': flight['marketingAirlineCode'],
                'operatingAirline': flight['operatingAirlineCode'],
                'airEquipType': flight['aircraftTypeCode'], 'duration': flight['durationInMinutes']}
            for key, value in expected_fields.items():
                if segment.get(key) != value:
                    errors['itinerary'].append({'offer': offer['id'], 'field': key, 'source': value, 'actual': segment.get(key)})
            for key, value in [('cabin', {'Economy': 'Y', 'Business': 'C'}[detail['cabinName']])]:
                if segment.get(key) != value:
                    errors['cabin_meal'].append({'offer': offer['id'], 'field': key})
            if 'mealCode' in detail and segment.get('meal') != detail['mealCode']:
                errors['cabin_meal'].append({'offer': offer['id'], 'field': 'meal'})
            allowance = bags[detail['checkedBaggageRef']]['allowances']
            assert len(allowance) == 1
            supplied = allowance[0]
            actual = segment['baggage']['ADT']
            if 'numberOfPieces' in supplied:
                allowance_checks += 1
                if supplied['numberOfPieces'] != actual.get('allowPieces'):
                    errors['allowance'].append({'offer': offer['id'], 'source': supplied, 'actual': actual})
            descriptions = supplied.get('bagDefinition', {}).get('description', [])
            for description in descriptions:
                if description not in (actual.get('allowMaxWeight'), actual.get('allowMaxSize')):
                    errors['allowance'].append({'offer': offer['id'], 'description': description, 'actual': actual})
                kg = re.search(r'(\d+) KILOGRAMS', description)
                if kg:
                    weight_checks += 1
                    if actual.get('kg') != int(kg.group(1)):
                        errors['weight'].append({'offer': offer['id'], 'description': description, 'actual': actual})
            if 'maximumWeightInKilograms' in supplied:
                weight_checks += 1
                if actual.get('kg') != supplied['maximumWeightInKilograms']:
                    errors['weight'].append({'offer': offer['id'], 'flight': flight,
                                             'segmentDetails': detail, 'source_bag': bags[detail['checkedBaggageRef']],
                                             'actual_segment_baggage': actual})
        for jid, trip in zip(offer['journeyRefs'], result['trips']):
            if trip['duration'] != journeys[jid]['durationInMinutes']:
                errors['itinerary'].append({'offer': offer['id'], 'field': 'trip duration'})
        pd = fare['priceDifference']
        pax = result['passengers']['ADT']
        for src, dst in [('baseFare', 'oExchangeFareDiff'), ('totalTax', 'oExchangeTaxDiff')]:
            if pax[dst]['amount'] != float(pd[src]) or pax[dst]['currency'] != pd['currencyCode']:
                errors['pricing'].append({'offer': offer['id'], 'field': dst})
        if result['prices']['totalPrice'] != float(offer['totalPriceDifference']['grandTotal']):
            errors['pricing'].append({'offer': offer['id'], 'field': 'grandTotal'})
    assert len(pairs) == len(body['results']) == len(source['offers']) == 13
    assert segments == 24
    assert all(not errors[k] for k in ('matching', 'itinerary', 'cabin_meal', 'pricing', 'allowance'))
    assert len(errors['weight']) == 2
    assert all(x['source_bag']['allowances'][0]['maximumWeightInKilograms'] == 20
               and x['actual_segment_baggage']['kg'] == 23 for x in errors['weight'])
    assert all(x['actual_segment_baggage']['allowPieces'] == 1 for x in errors['weight'])
    errors['weight_only_observations'] = errors.pop('weight')
    analysis = {'offers': len(pairs), 'segments': segments, 'piece_checks': allowance_checks,
                'weight_checks': weight_checks, 'errors': errors}
    (FOLDER / 'analysis.json').write_text(json.dumps(analysis, indent=2), encoding='utf-8')
    return soap, rest, source, analysis


def deliver():
    soap, rest, source, analysis = analyze()
    rows = []
    def row(id, data, expected, actual, status='PASS'):
        rows.append(dict(id=id, data=data, expected=expected, actual=actual, status=status))
    row('TC-01', 'SOAP baseline; TST101 / 6NVG; JFKâ€“DOH, 18 Dec; 1 ADT',
        'Disabled REST selection uses SOAP and returns exchange offers.',
        'HTTP 200; 14 offers; Sabre_Exchange with ExchangeShoppingRQ/RS.')
    row('TC-02', 'Same request; user switched configuration',
        'Enabled REST selection executes Flight Reshop and returns offers.',
        'HTTP 200; 13 offers; Sabre_Exchange_Rest JSON. Discovery exposes sabre_rest.enable_exchange=true.')
    row('TC-03', '13 source offers / 13 AirAPI results',
        'Each returned offer maps to its source itinerary and fare.',
        '13 unique matches by airports, departure, flight, booking class and fare basis; 24 segments.')
    row('TC-04', '24 REST segments / 13 journeys',
        'Preserve airlines, flight identity, airports/dates, equipment, segment duration and journey grouping/duration.',
        'All checked fields match linked source flights and journeys across 24 segments / 13 trips.')
    row('TC-05', 'Economy and Business; supplied meal codes',
        'Retain cabin meaning and supplied meal values.',
        'Economy â†’ Y; Business â†’ C; all supplied meal codes match. Booking class/fare basis matched in TC-03.')
    row('TC-06', '13 ADT priceDifference blocks; USD',
        'Retain fare difference, aggregate tax difference, currency and grand total.',
        '13/13 match oExchangeFareDiff, oExchangeTaxDiff and prices.totalPrice; ADT retained.')
    row('TC-07', '22 segment-linked checked allowances with pieces; supplied descriptions',
        'Preserve source piece counts and supplied weight/size descriptions.',
        '22/22 supplied piece counts match; supplied checked weight/size descriptions retained. Numeric-weight check separate.')
    row('TC-08', 'EI108 JFKâ€“DUB + QR18 DUBâ€“DOH; source allowance 20 kg',
        'User-confirmed rule: positive weight sets allowPieces=1 without setting kg in the parser; post-processing supplies missing details.',
        'Both linked segments return allowPieces=1. Final kg=23 is post-processing output, not a required direct mapping of source 20 kg. PASS under clarified rule; intermediate parser state not observed.')
    row('TC-09', 'Captured REST flights: no hiddenStops supplied',
        'Map supplied hidden stops without losing their association.',
        'No positive hidden-stop inventory in this approved request; mapping cannot be evaluated.', 'WARN')
    row('TC-10', '13 offers: Add collect; no totalFee; totalTaxOnFee=0',
        'Exercise fee amount, fee tax and Refund mappings when supplied.',
        'No nonzero fee, fee-tax or Refund example. Those paths remain unverified.', 'WARN')
    row('TC-11', 'Per-PTC taxes[], subtotalBeforeFee, type and identity fields',
        'Establish public-output parity for the remaining ticket-listed pricing/identity fields.',
        'REST source contains taxes/subtotal/type; AirAPI result has no evidenced dedicated output paths. Legacy baseline also lacks these fields. Identity is redacted. Public parity not certified.', 'WARN')
    request = load('rest-recheck-request.json')
    evidence = []
    for rid in ('TC-08', 'TC-09', 'TC-10', 'TC-11'):
        if rid == 'TC-08':
            response = {'http_status': 200, 'req_resp_name': 'Sabre_Exchange_Rest', 'mismatches': analysis['errors']['weight_only_observations']}
        elif rid == 'TC-09':
            response = {'http_status': 200, 'source_flight_count': len(source['flights']),
                        'source_hiddenStops_field_count': sum('hiddenStops' in f for f in source['flights']),
                        'source_flight_example': source['flights'][0],
                        'airapi_segment_example': rest['body']['results'][0]['trips'][0]['segments'][0]}
        elif rid == 'TC-10':
            response = {'http_status': 200, 'all_offer_price_blocks': [o['totalPriceDifference'] for o in source['offers']],
                        'airapi_passenger_example': rest['body']['results'][0]['passengers']['ADT']}
        else:
            fare = source['offers'][0]['items'][0]['fares'][0]
            response = {'http_status': 200, 'source_priceDifference': fare['priceDifference'],
                        'source_travelers_redacted': fare['travelers'],
                        'airapi_passenger': rest['body']['results'][0]['passengers']['ADT'],
                        'airapi_prices': rest['body']['results'][0]['prices']}
        evidence.append({'id': rid, 'request': request, 'response': response})
    collection_name = 'SS-6414.postman_collection.json'
    variables = {'search_url': request['url'], 'provider_filter': 'S', 'request_body': '',
                 'expected_result': 'source_parity', 'scenario_id': 'REST', 'expected_track': 'Sabre_Exchange_Rest',
                 'authorization': '', 'pnr_code': '', 'ticket_number': '', 'first_name': '', 'last_name': ''}
    request_body = json.loads(json.dumps(request['body']))
    request_body['book_info']['pnrCode'] = '{{pnr_code}}'
    request_body['book_info']['passengers']['1.1'].update(firstName='{{first_name}}', lastName='{{last_name}}', ticketNumber='{{ticket_number}}')
    variables['request_body'] = json.dumps(request_body)
    setup = ["['search_url','provider_filter','expected_track','scenario_id','expected_result'].forEach(k=>{if(pm.iterationData.has(k))pm.variables.set(k,pm.iterationData.get(k));});",
             "['authorization','pnr_code','ticket_number','first_name','last_name'].forEach(k=>{if(!pm.variables.get(k))throw new Error('Set runtime variable: '+k);});",
             "const rb=JSON.parse(pm.variables.replaceIn(pm.variables.get('request_body')));if(pm.iterationData.has('pcc'))rb.itinerary.pcc=pm.iterationData.get('pcc');if(pm.iterationData.has('departure'))rb.search_params.flights[0].departure=pm.iterationData.get('departure');if(pm.iterationData.has('issue_date'))rb.itinerary.issueDate=pm.iterationData.get('issue_date');pm.variables.set('rendered_body',JSON.stringify(rb));"]
    tests = ["const b=pm.response.json();",
             "pm.test('Exchange inventory available',()=>pm.expect(b.results).to.be.an('array').that.is.not.empty);",
             "pm.test('Count matches results',()=>pm.expect(b.count).to.eql(b.results.length));",
             "pm.test('Expected protocol executed',()=>pm.expect(b.req_resp.map(x=>x.name)).to.include(pm.variables.get('expected_track')));",
             "pm.test('Requested provider returned',()=>b.results.forEach(r=>pm.expect(r.gds).to.eql(pm.variables.get('provider_filter'))));",
             "if(pm.variables.get('expected_track')==='Sabre_Exchange_Rest'){",
             " const raw=b.req_resp.find(x=>x.name==='Sabre_Exchange_Rest').response; const s=typeof raw==='string'?JSON.parse(raw):raw;",
             " const fs=Object.fromEntries(s.flights.map(f=>[f.id,f])), js=Object.fromEntries(s.journeys.map(j=>[j.id,j])), bags=Object.fromEntries(s.offerAttributes.checkedBaggageItems.map(x=>[x.id,x]));",
             " s.offers.forEach(o=>{const fare=o.items[0].fares[0], ds={};fare.fareComponents.forEach(c=>c.segmentDetails.forEach(d=>ds[d.flightRef]={d,c})); const refs=o.journeyRefs.flatMap(j=>js[j].flightRefs);",
             " const matches=b.results.filter(r=>JSON.stringify(r.trips.flatMap(t=>t.segments).map(z=>[z.departureAirportCode,z.arrivalAirportCode,z.departureTime,String(z.flightNumber),z.bookingClass,z.fareCode]))===JSON.stringify(refs.map(f=>[fs[f].departureAirportCode,fs[f].arrivalAirportCode,fs[f].departureDate+' '+fs[f].departureTime,String(fs[f].marketingFlightNumber),ds[f].d.bookingClassCode,ds[f].c.fareBasisCode])));",
             " pm.test('Unique source match '+o.id,()=>pm.expect(matches.length).to.eql(1));if(matches.length!==1)return; const r=matches[0], zs=r.trips.flatMap(t=>t.segments), pd=fare.priceDifference;",
             " pm.test('Fare/tax/total parity '+o.id,()=>{pm.expect(r.passengers.ADT.oExchangeFareDiff.amount).to.eql(Number(pd.baseFare));pm.expect(r.passengers.ADT.oExchangeTaxDiff.amount).to.eql(Number(pd.totalTax));pm.expect(r.currency).to.eql(pd.currencyCode);pm.expect(r.prices.totalPrice).to.eql(Number(o.totalPriceDifference.grandTotal));});",
             " pm.test('Journey durations '+o.id,()=>o.journeyRefs.forEach((j,i)=>pm.expect(r.trips[i].duration).to.eql(js[j].durationInMinutes)));",
             " refs.forEach((f,i)=>pm.test('Segment mapping '+o.id+' '+i,()=>{const z=zs[i],fl=fs[f],d=ds[f].d;pm.expect(z.arrivalTime).to.eql(fl.arrivalDate+' '+fl.arrivalTime);pm.expect(z.marketingAirline).to.eql(fl.marketingAirlineCode);pm.expect(z.operatingAirline).to.eql(fl.operatingAirlineCode);pm.expect(z.airEquipType).to.eql(fl.aircraftTypeCode);pm.expect(z.duration).to.eql(fl.durationInMinutes);pm.expect(z.cabin).to.eql({Economy:'Y',Business:'C'}[d.cabinName]);if(Object.hasOwn(d,'mealCode'))pm.expect(z.meal).to.eql(d.mealCode);}));",
             " refs.forEach((f,i)=>{const a=bags[ds[f].d.checkedBaggageRef].allowances[0], z=zs[i].baggage.ADT; if(Object.hasOwn(a,'maximumWeightInKilograms')&&a.maximumWeightInKilograms>=1)pm.test('Weight-only allowance maps to one piece '+o.id+' segment '+i,()=>pm.expect(z.allowPieces).to.eql(1));if(Object.hasOwn(a,'numberOfPieces'))pm.test('Checked pieces '+o.id+' segment '+i,()=>pm.expect(z.allowPieces).to.eql(a.numberOfPieces));});});}"]
    collection = {'info': {'name': 'SS-6414 /v1/exchange Sabre REST integration',
                          'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
                          'description': 'AirAPI only. User must set the desired server mode before each row. No configuration mutation or provider calls. Runtime credentials and booking identities required. Do not run both mode rows without manually switching. No count parity assertion across live runs. Captured coverage limits remain in the report.'},
                  'variable': [{'key': k, 'value': v} for k, v in variables.items()],
                  'item': [{'name': 'Read-only AirAPI exchange', 'event': [
                      {'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': setup}},
                      {'listen': 'test', 'script': {'type': 'text/javascript', 'exec': tests}}],
                      'request': {'method': 'POST', 'header': [{'key': 'Authorization', 'value': '{{authorization}}'},
                                                                            {'key': 'Content-Type', 'value': 'application/json'}],
                                  'url': '{{search_url}}', 'body': {'mode': 'raw', 'raw': '{{rendered_body}}',
                                                                               'options': {'raw': {'language': 'json'}}}}}]}
    (FOLDER / collection_name).write_text(json.dumps(collection, indent=2), encoding='utf-8')
    with (FOLDER / 'expected-outcomes.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['scenario_id', 'expected_result', 'provider_filter', 'search_url', 'expected_track', 'pcc', 'departure', 'issue_date', 'required_mode'])
        writer.writeheader()
        for mode, track in [('SOAP', 'Sabre_Exchange'), ('REST', 'Sabre_Exchange_Rest')]:
            writer.writerow(dict(scenario_id=mode, expected_result='source_parity', provider_filter='S', search_url=request['url'], expected_track=track,
                                 pcc='6NVG', departure='2026-12-18', issue_date='2026-10-20', required_mode=mode))
    limits = ('Fresh captures: SOAP 14 offers, then two SOAP observations with 19 and 13 offers while awaiting the switch, '
              'then confirmed REST 13 offers. Counts are live inventory, not equality expectations. Source-to-output REST analysis: '
              '13 offers / 24 segments. sabre_rest.enable_exchange is the observed flag; the ticket spelling exchange_enabled is not exposed. '
              'No application source inspected, no configuration writes, no booking changes, no further API calls. '
              'Single ADT / USD / approved itinerary only; hidden stops, Refund, nonzero fees and fee tax unverified. '
              'REST terminals and marriageGroup are empty as anticipated by the ticket. Carry-on numeric allowance parity and baggage charges '
              'are not certified. Historical request names rest-response/rest-retest-response contain SOAP, not REST. '
              'Initial sandbox connection refusal is transport-only evidence. Identity fields are redacted; SOAP headers removed. '
              'Embedded source JSON required removal of redaction-only bare placeholders for offline analysis. '
              'Full paired sanitized payloads, config discovery and analysis.json are in this run directory. '
              'Collection/CSV are rerun artifacts, not additional executed test cases. Set runtime identities and authentication; '
              'run each mode separately after the user changes the flag; apply the authorized TLS bypass in the runner. '
              'No operational lessons applied; lesson search returned none. Ledger unchanged. TC-08 was reclassified from FAIL to PASS using the user-confirmed pieces-only mapping; this is saved-evidence reassessment, not a fresh API run. Intermediate parsing and post-processing were not independently observed.')
    data = {'title': 'SS-6414 /v1/exchange Sabre REST integration',
            'scope': 'STAGE | POST /v1/exchange | TST101 / 6NVG | SOAP â†’ REST | 1 ADT / USD',
            'summary': 'FAIL: REST execution works, but the supplied 20 kg checked allowance becomes 23 kg on both linked JFKâ€“DUBâ€“DOH segments. '
                       'Flight mapping and fare/tax differences/grand totals match the 13 REST offers. Missing positive inventory and unevidenced public pricing mappings remain WARN.',
            'intended': 'Integrate Sabre REST Flight Reshop with SOAP/REST selection and preserve the ticket-listed itinerary, allowance and per-PTC pricing information when supplied. '
                        'User clarification: when a weight-only allowance is at least 1 kg, set only allowPieces=1 in the parser; do not set kg, and allow post-processing to fill missing details. Terminals, marriage group and fee-type gaps are identified in the ticket.',
            'rows': rows, 'evidence': evidence, 'limits': limits, 'collection': collection_name}
    (FOLDER / 'report-data.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    result = render(FOLDER)
    # Shared renderer has a historical fixed date; correct only these ticket outputs.
    for name in ('qa-report.md', 'qa-report.html'):
        path = FOLDER / name
        path.write_text(path.read_text(encoding='utf-8').replace('2026-10-21', '2026-10-23'), encoding='utf-8')
    assert result == {'signal': 'WARN', 'PASS': 8, 'FAIL': 0, 'WARN': 3}
    assert all(any(e['id'] == r['id'] for e in evidence) for r in rows if r['status'] != 'PASS')
    print(json.dumps(result))


if __name__ == '__main__':
    deliver()
