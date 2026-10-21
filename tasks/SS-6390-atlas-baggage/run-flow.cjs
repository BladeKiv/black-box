if (!process.env.AIRAPI_POSTMAN_COLLECTION) throw new Error('Missing required environment variable: AIRAPI_POSTMAN_COLLECTION');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = process.env.QA_RUN_DIR || __dirname;
const host = 'https://api.search.dev.travel-dev.com';
const source = JSON.parse(fs.readFileSync(process.env.AIRAPI_POSTMAN_COLLECTION,'utf8').replace(/^\uFEFF/,''));
const folder = source.item.find(x=>x.name==='SERVICE APIs TEST ENV');
assert(folder);
const item = name => {const i=folder.item.find(x=>x.name===name);assert(i, name);return i;};
const stateFile = path.join(root,'flow-state.json');
const state = fs.existsSync(stateFile)?JSON.parse(fs.readFileSync(stateFile,'utf8')):{};
const save = (name,value) => fs.writeFileSync(path.join(root,name+'.json'),JSON.stringify(value,null,2));
const step=process.argv[2];
function headers(i){
  const h={};
  for(const x of i.request.header||[])if(!x.disabled)h[x.key]=x.value;
  const basic=i.request.auth?.basic;
  if (basic) {
    assert(process.env.BOOKING_USERNAME && process.env.BOOKING_PASSWORD, 'Missing BOOKING_USERNAME or BOOKING_PASSWORD environment variable');
    h['Authorization'] = 'Basic ' + Buffer.from(process.env.BOOKING_USERNAME + ':' + process.env.BOOKING_PASSWORD).toString('base64');
  }
  h['Content-Type']='application/json';
  assert(!Object.values(h).some(v=>v.includes('{{')), 'Unresolved headers');
  return h;
}
async function request(name,template,body,url){
  url=url||host+'/'+template.request.url.path.join('/');
  assert.equal(new URL(url).origin,host);
  save(name+'-request',{method:template.request.method,url,headerNames:Object.keys(headers(template)),...(body?{body}:{})});
  const r=await fetch(url,{method:template.request.method,headers:headers(template),body:body?JSON.stringify(body):undefined,redirect:'error',signal:AbortSignal.timeout(60000)});
  const text=await r.text();let data;try{data=JSON.parse(text);}catch{data={raw:text};}
  save(name+'-response',data);save(name+'-meta',{status:r.status,receivedAt:new Date().toISOString()});
  console.log(JSON.stringify({step:name,http:r.status,keys:Object.keys(data),status:data.status,code:data.code,name:data.name,resultCount:data.results?.length}));
  assert(r.ok || (r.status===408 && data.name==='Retry' && ['05-ticket-create','06-book-info'].includes(name)), 'HTTP '+r.status);return data;
}
function bookBody(r){
  assert(r.keys?.atlas && r.trips?.length && Number.isFinite(r.prices?.totalPrice));
  const cabin=c=>{assert(['Y','W','C','F'].includes(c));return {Y:1,W:2,C:3,F:4}[c];};
  const b=JSON.parse(item('/atlas/v1/book/create').request.body.raw);
  b.additionalInfo=structuredClone(r.keys.atlas);
  b.payments={pay_type:1};b.trip.total_price=r.prices.totalPrice;b.trip.cabin=cabin(r.trips[0].segments[0].cabin);
  b.trip.passengers=[{pas_first_name:'Alex',pas_middle_name:'QA',pas_last_name:'Bennett',pas_dob:'1995-01-15',pas_type_id:1,pas_nationality:'US',pas_gender_id:1,pas_country:'US',pas_doc_number:'AA111222A0',pas_doc_expiration_date:'2030-05-16'}];
  b.trip.contact_email='atlas-qa@example.com';b.trip.contact_phone='+1 2025550100';
  b.trip.flights=r.trips.map(t=>({segments:t.segments.map(s=>({seg_departure_airport_code:s.departureAirportCode,seg_arrival_airport_code:s.arrivalAirportCode,seg_airline_code:s.marketingAirline,seg_air_equip_type:s.airEquipType,seg_departure_dt:s.departureTime,seg_arrival_dt:s.arrivalTime,seg_flight_number:s.flightNumber,seg_cabin_type_id:cabin(s.cabin),seg_booking_class:s.bookingClass,seg_marriage_grp:s.marriageGroup||'',seg_fare_basis:s.fareCode})),fl_origin_location_code:t.segments[0].departureAirportCode,fl_destination_location_code:t.segments.at(-1).arrivalAirportCode}));
  return b;
}
async function main(){
  if(step==='search'){
    assert(!state.book,'Existing booking: do not restart this flow');
    const url=item('/atlas/v1/search').request.url.raw.replace('{{searchhost}}',host).replace('2026-07-29','2026-11-11');
    const r=await request('01-search',item('/atlas/v1/search'),null,url);assert(r.results?.length,'No selectable inventory');
    state.searchUrl=url;state.selected=r.results[0];save('selected-search',state.selected);
    console.log(JSON.stringify({selectedCarrier:state.selected.validatingCarrier,segments:state.selected.trips?.flatMap(t=>t.segments).map(s=>({from:s.departureAirportCode,to:s.arrivalAirportCode,baggage:s.baggage}))}));
  }else if(step==='result'){
    assert(state.selected&&!state.book);state.result=await request('02-result',item('/atlas/v1/result'),state.selected);
    state.bookingBody=bookBody(state.result);console.log(JSON.stringify({atlasKeyFields:Object.keys(state.result.keys.atlas),segments:state.result.trips.flatMap(t=>t.segments).map(s=>({from:s.departureAirportCode,to:s.arrivalAirportCode,baggage:s.baggage,carryOn:s.carryOn}))}));
  }else if(step==='book'){
    assert(state.bookingBody&&!state.book);state.book=await request('03-book-create',item('/atlas/v1/book/create'),state.bookingBody);
    console.log(JSON.stringify({dataKeys:Object.keys(state.book.data||{}),responseKeys:Object.keys(state.book.data?.response||{}),additionalInfoKeys:Object.keys(state.book.data?.additionalInfo||{}),segments:state.book.data?.response?.pnrInfo?.segments}));
  }else if(step==='info-before'||step==='info-after'){
    assert(state.book?.data?.additionalInfo);if(step==='info-after')assert(state.ticket);
    const r=await request(step==='info-before'?'04-book-info':'06-book-info',item('/atlas/v1/book/info'),{additionalInfo:state.book.data.additionalInfo});
    state[step]=r;console.log(JSON.stringify({dataKeys:Object.keys(r.data||{}),responseKeys:Object.keys(r.data?.response||{}),segments:r.data?.response?.pnrInfo?.segments}));
  }else if(step==='ticket'){
    assert(state['info-before']&&!state.ticket);
    const b=structuredClone(state.bookingBody);delete b.payments;b.additionalInfo=structuredClone(state.book.data.additionalInfo);b.data={payments:[{pay_type:1}]};
    state.ticket=await request('05-ticket-create',item('/atlas/v1/ticket/create pay=1'),b);
    console.log(JSON.stringify({dataKeys:Object.keys(state.ticket.data||{}),responseKeys:Object.keys(state.ticket.data?.response||{})}));
  }else throw new Error('Unknown step');
  fs.writeFileSync(stateFile,JSON.stringify(state,null,2));
}
main().catch(e=>{console.error(e.message);process.exitCode=1;});
