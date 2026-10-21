const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const dir = __dirname;
const host = 'https://api.search.dev.travel-dev.com';
const searchUrl = process.env.SCENARIO_SEARCH_URL || host + '/brightsun/v1/search?tripType=RT&fl[0][o]=AMS&fl[0][d]=LHR&fl[0][dt]=2026-11-11&fl[1][o]=LHR&fl[1][d]=AMS&fl[1][dt]=2026-11-18&cabin=Y&adt=1&chd=1&inf=1&limit=100';
function buildBooking(r, bookingDate) {
  const cabins = {Y:1,S:2,C:3,F:4};
  const cabinId = code => {
    if (!Object.hasOwn(cabins, code)) throw new Error('Unsupported cabin: ' + code);
    return cabins[code];
  };
  if (!r.keys?.brightsun?.key || !r.keys.brightsun.token || !Object.hasOwn(r.keys.brightsun,'supp') || !r.trips?.length || !Number.isFinite(r.prices?.totalPrice) || !r.validatingCarrier) throw new Error('Result missing booking inputs');
  const stamp = dt => {
    if (!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$/.test(dt)) throw new Error('Unsupported segment timestamp');
    return dt.length === 16 ? dt + ':00' : dt;
  };
  const first = ['Alex','Taylor','Morgan','Jamie','Casey','Jordan'];
  const last = ['Bennett','Parker','Hayes','Reed','Carter','Brooks'];
  const pick = a => a[Math.floor(Math.random()*a.length)];
  const passengers = [];
  for (const [ptc, p] of Object.entries(r.passengers)) {
    if (!['ADT','CHD','INF'].includes(ptc) || !Number.isInteger(p.cnt) || p.cnt < 0) throw new Error('Unsupported passenger count/type');
    const years = {ADT:25,CHD:7,INF:1}[ptc];
    const dob = new Date(bookingDate + 'T12:00:00Z');
    dob.setUTCFullYear(dob.getUTCFullYear()-years);
    for (let i=0;i<p.cnt;i++) passengers.push({pas_first_name:pick(first),pas_middle_name:'KIVO',pas_last_name:pick(last),pas_dob:dob.toISOString().slice(0,10),pas_type_id:1,pas_nationality:'US',pas_country:'US',pas_gender_id:2,pas_doc_expiration_date:'2030-04-01',pas_doc_number:'AA111222A0'});
  }
  return {
    gds:{gds_id:9,gds_pcc:'DFWG32100',backoffice_id:11111,hybrid_id:'A6F17DE'},
    additionalInfo:JSON.parse(JSON.stringify(r.keys.brightsun)),
    contact_info:{address:'701 BENNETT ST',country:'US',city:'BOTTINEAU',state:'ND',zip:'58318'},
    data:{payments:[{pay_airline:'BA',pay_amount:474,pay_cc_cvv:'***',pay_cc_expire_month:9,pay_cc_expire_year:2025,pay_cc_first_name:'Kathleen',pay_cc_holder:'Kathleen Pankanin',pay_cc_last_name:'Pankanin',pay_cc_name:'Kathleen Pankanin',pay_cc_number:'****8299',pay_cc_type:'VI',pay_type:1}]},
    payments:{pay_type:1},
    trip:{booking_type:2,cabin:cabinId(r.cabin),validating_carrier:r.validatingCarrier,total_price:r.prices.totalPrice,passengers,
      flights:r.trips.map(t=>({segments:t.segments.map(s=>({seg_departure_airport_code:s.departureAirportCode,seg_arrival_airport_code:s.arrivalAirportCode,seg_airline_code:s.marketingAirline,seg_air_equip_type:s.airEquipType,seg_departure_dt:stamp(s.departureTime),seg_arrival_dt:stamp(s.arrivalTime),seg_flight_number:s.flightNumber,seg_cabin_type_id:cabinId(s.cabin),seg_booking_class:s.bookingClass,seg_marriage_grp:'',seg_fare_basis:s.fareCode})),fl_origin_location_code:t.segments[0].departureAirportCode,fl_destination_location_code:t.segments.at(-1).arrivalAirportCode})),
      contact_phone:'+1 7075642084',country_code:'+1',contact_email:'zahid.bernell@kiv.dev',selling_price:{amount:1,currency_code:'USD'},agency_selling_price:{amount:1,currency_code:'USD'},account_code:'EURKIV',agency_phone:'18888633910'},account_info:null
  };
}
function updatedPriceBody(body, response, status) {
  const price=response.data?.response?.total_price;
  if(status!==422 || response.type!=='Price change' || !Number.isFinite(price) || price<=0) throw new Error('No usable 422 price-change response');
  const updated=JSON.parse(JSON.stringify(body));
  updated.trip.total_price=price;
  return updated;
}
function prepare() {
  const c = JSON.parse(fs.readFileSync(path.join(dir,'../ss-6340/brightsun service.postman_collection.json'),'utf8'));
  c.info.name = 'SS-6341 Brightsun Search → Result → book/create';
  delete c.info._collection_link;
  c.info.description = 'DEV booking workflow. Basic Auth uses local environment variables booking_username and booking_password. On HTTP 422 Price change, update trip.total_price from data.response.total_price and resubmit once. HTTP 200 confirms booking success.';
  c.item = c.item.filter(i=>['v1/search','v1/result'].includes(i.name));
  const search = c.item[0];
  search.event[0].script.exec[0] = `const url = pm.iterationData.get('search_url') || ${JSON.stringify(searchUrl)};`;
  search.event[0].script.exec.push("pm.collectionVariables.unset('booking_body');");
  search.event[0].script.exec.push("pm.collectionVariables.set('booking_price_retry', '0');");
  search.event[1].script.exec=[
    "pm.collectionVariables.unset('brightsun_selected_solution');",
    "const data = pm.response.json();",
    "if (!Array.isArray(data.results) || !data.results.length) { pm.execution.setNextRequest(null); throw new Error('No selectable Search setup inventory'); }",
    "pm.collectionVariables.set('brightsun_selected_solution', JSON.stringify(data.results[0]));"];
  const result = c.item[1];
  result.request.description = 'POST selected Search solution unchanged; prepare booking from the fresh Result response.';
  result.event[0].script.exec.push("pm.collectionVariables.unset('booking_body');");
  result.event[1].script.exec=["const data = pm.response.json();",buildBooking.toString(),
    "try {",
    " const bookingDate = new Intl.DateTimeFormat('en-CA', {timeZone:'Europe/Bucharest',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());",
    " const booking = buildBooking(data, bookingDate);",
    " pm.collectionVariables.set('booking_body', JSON.stringify(booking));",
    "} catch (e) { pm.execution.setNextRequest(null); throw e; }"];
  c.item.push({name:'v1/book/create',request:{method:'POST',auth:{type:'basic',basic:[{key:'username',value:'{{booking_username}}',type:'string'},{key:'password',value:'{{booking_password}}',type:'string'}]},header:[{key:'Content-Type',value:'application/json'}],url:host+'/brightsun/v1/book/create',body:{mode:'raw',raw:'{{booking_body}}',options:{raw:{language:'json'}}}},event:[{listen:'prerequest',script:{type:'text/javascript',exec:["if (!pm.collectionVariables.get('booking_body')) { pm.execution.skipRequest(); throw new Error('No fresh booking body: run Search and Result first'); }","if (!pm.variables.get('booking_username') || !pm.variables.get('booking_password')) { pm.execution.skipRequest(); throw new Error('Set local Basic Auth environment variables'); }"]}},{listen:'test',script:{type:'text/javascript',exec:["pm.test('SS-6341: Booking returns HTTP 200', () => pm.expect(pm.response.code).to.equal(Number(pm.iterationData.get('expected_status') || 200)));","pm.collectionVariables.unset('booking_body');"]}}]});
  c.item.at(-1).event.find(e=>e.listen==='test').script.exec=[updatedPriceBody.toString(),
    "const data = pm.response.json();",
    "const retry = pm.response.code === 422 && data.type === 'Price change' && pm.collectionVariables.get('booking_price_retry') !== '1';",
    "if (retry) {",
    " try {",
    "  const original = JSON.parse(pm.collectionVariables.get('booking_body'));",
    "  const updated = updatedPriceBody(original, data, pm.response.code);",
    "  pm.test('SS-6341: Updated price equals 422 response price', () => pm.expect(updated.trip.total_price).to.equal(data.data.response.total_price));",
    "  pm.collectionVariables.set('booking_body', JSON.stringify(updated));",
    "  pm.collectionVariables.set('booking_price_retry', '1');",
    "  pm.execution.setNextRequest('v1/book/create');",
    " } catch (e) { pm.execution.setNextRequest(null); pm.collectionVariables.unset('booking_body'); throw e; }",
    "} else {",
    " pm.test('SS-6341: Booking returns HTTP 200', () => pm.expect(pm.response.code).to.equal(Number(pm.iterationData.get('expected_status') || 200)));",
    " if (pm.response.code === 200) {",
    "  pm.test('SS-6341: Booking references returned', () => {",
    "   pm.expect(data.data.additionalInfo.brightsunReference).to.be.a('string').and.not.empty;",
    "   pm.expect(data.data.additionalInfo.recLoc).to.be.a('string').and.not.empty;",
    "  });",
    " }",
    " pm.collectionVariables.unset('booking_body');",
    "}"];
  fs.writeFileSync(path.join(dir,'brightsun-book-create.postman_collection.json'),JSON.stringify(c,null,2));
  fs.writeFileSync(path.join(dir,'expected-outcomes.csv'),'scenario_id,expected_result,provider_filter,search_url,expected_status,adt,chd,inf,booking_date_basis\nrt-adt-chd-inf,HTTP 200,brightsun,"'+searchUrl+'",200,1,1,1,Europe/Bucharest booking day\n');
  const fixture = JSON.parse(fs.readFileSync(path.join(dir,'../ss-6340/runs/20260930-125236-matrix/rt-adt-chd-inf/result-response.json'),'utf8').replace(/^\uFEFF/,''));
  for (const code of ['Y','S','C','F']) {
    const r = structuredClone(fixture);r.cabin=code;for(const t of r.trips) for(const s of t.segments)s.cabin=code;
    const b=buildBooking(r,'2026-10-01');
    assert.deepEqual(b.additionalInfo,r.keys.brightsun);assert.equal(b.trip.passengers.length,3);
    assert.deepEqual(b.trip.passengers.map(p=>p.pas_dob),['2001-10-01','2019-10-01','2025-10-01']);
    assert.equal(b.trip.cabin,{Y:1,S:2,C:3,F:4}[code]);assert.equal(b.trip.flights.length,r.trips.length);
    assert.equal(b.trip.total_price,r.prices.totalPrice);assert.equal(b.trip.validating_carrier,r.validatingCarrier);
  }
  for(const i of c.item) for(const e of i.event) new Function('pm',e.script.exec.join('\n'));
  const original=buildBooking(fixture,'2026-10-01');
  const updated=updatedPriceBody(original,{type:'Price change',data:{response:{total_price:569.55}}},422);
  assert.equal(updated.trip.total_price,569.55);
  assert.deepEqual({...updated,trip:{...updated.trip,total_price:original.trip.total_price}},original);
  assert.throws(()=>updatedPriceBody(original,{type:'Price change',data:{response:{}}},422));
  console.log('Prepared collection/CSV; mapping self-check passed (offline, no API calls).');
}
async function run(options={}) {
  const prepareOnly = process.argv.includes('--prepare-only');
  if (!prepareOnly && (!process.env.BOOKING_USERNAME || !process.env.BOOKING_PASSWORD)) throw new Error('Missing Basic Auth environment variables');
  const bookPrepared = process.argv.includes('--book-prepared');
  const retryPrice = process.argv.includes('--retry-price');
  const runDir = bookPrepared || retryPrice ? fs.readFileSync(path.join(dir,'latest-run.txt'),'utf8').trim() : path.join(dir,'runs',new Date().toISOString().replace(/[:.]/g,'-'));
  fs.mkdirSync(runDir,{recursive:true});
  fs.writeFileSync(path.join(dir,'latest-run.txt'),runDir);
  const save=(name,value)=>fs.writeFileSync(path.join(runDir,name+'.json'),JSON.stringify(value,null,2));
  async function request(name,url,body,auth=false) {
    save(name+'-request',{method:body?'POST':'GET',url,...(body?{body}: {})});
    const headers = body ? {'Content-Type':'application/json'} : {};
    if(auth) headers.Authorization='Basic '+Buffer.from(process.env.BOOKING_USERNAME+':'+process.env.BOOKING_PASSWORD).toString('base64');
    const response=await fetch(url,{method:body?'POST':'GET',headers,body:body?JSON.stringify(body):undefined,redirect:'error',signal:AbortSignal.timeout(60000)});
    const text=await response.text();fs.writeFileSync(path.join(runDir,name+'-response.json'),text);
    save(name+'-meta',{status:response.status,receivedAt:new Date().toISOString()});
    console.log(name+': HTTP '+response.status);
    return {status:response.status,data:JSON.parse(text)};
  }
  try {
    if(retryPrice) {
      if(fs.existsSync(path.join(runDir,'booking-retry-request.json'))) throw new Error('Price retry already attempted; refusing duplicate');
      const read=n=>JSON.parse(fs.readFileSync(path.join(runDir,n+'.json'),'utf8').replace(/^\uFEFF/,''));
      const updated=updatedPriceBody(read('booking-body'),read('booking-response'),read('booking-meta').status);
      const retry=await request('booking-retry',host+'/brightsun/v1/book/create',updated,true);
      console.log('Retry response fields: '+Object.keys(retry.data).join(', '));
      return;
    }
    if (bookPrepared) {
      if(fs.existsSync(path.join(runDir,'booking-meta.json'))) throw new Error('Booking response already captured; refusing duplicate booking');
      const body=JSON.parse(fs.readFileSync(path.join(runDir,'booking-body.json'),'utf8'));
      const b=await request('booking',host+'/brightsun/v1/book/create',body,true);
      if(b.status===422 && b.data.type==='Price change') await request('booking-retry',host+'/brightsun/v1/book/create',updatedPriceBody(body,b.data,b.status),true);
      console.log('Booking response fields: '+Object.keys(b.data).join(', '));
      return;
    }
    const s=await request('search',options.searchUrl || searchUrl);
    if(!s.data.results?.length) throw new Error('Search returned no selectable solution');
    const r=await request('result',host+'/brightsun/v1/result',s.data.results[0]);
    const bookingDate = new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Bucharest',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
    const body=buildBooking(r.data,bookingDate);save('booking-body',body);save('booking-context',{bookingDate,counts:Object.fromEntries(Object.entries(r.data.passengers).map(([k,p])=>[k,p.cnt]))});
    if (prepareOnly) { console.log('Fresh booking body prepared; booking endpoint not called.'); return; }
    const b=await request('booking',host+'/brightsun/v1/book/create',body,true);
    if(b.status===422 && b.data.type==='Price change') await request('booking-retry',host+'/brightsun/v1/book/create',updatedPriceBody(body,b.data,b.status),true);
    console.log('Booking response fields: '+Object.keys(b.data).join(', '));
  } catch(e) {save('error',{message:e.message});console.log('Flow stopped: '+e.message);}
  console.log('Evidence: '+runDir);
}
if(require.main===module) { if(process.argv.includes('--run')) run().catch(e=>{console.error(e.message);process.exitCode=1;});else prepare(); }
module.exports={buildBooking,updatedPriceBody,run};
