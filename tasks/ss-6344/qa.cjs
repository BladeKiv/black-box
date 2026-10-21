const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {buildBooking,updatedPriceBody}=require('../ss-6341/booking-flow.cjs');
const dir=__dirname,host='https://api.search.dev.travel-dev.com';
const url=host+'/brightsun/v1/search?tripType=RT&fl[0][o]=AMS&fl[0][d]=LHR&fl[0][dt]=2026-11-11&fl[1][o]=LHR&fl[1][d]=AMS&fl[1][dt]=2026-11-18&cabin=Y&adt=1&limit=100';
const cases=[['result-token','result','token'],['result-offers','result','offers'],['booking-token','booking','token'],['booking-offers','booking','offers']].map(([id,endpoint,mutation])=>({id,endpoint,mutation}));
function corrupt(info,mutation){const copy=JSON.parse(JSON.stringify(info));if(mutation==='token')copy.token='INVALID_TEST_TOKEN';else{for(const k of ['optionKeys','outboundKey','inboundKey']){if(!Object.hasOwn(copy,k))throw new Error('Required mutation field unavailable: '+k);copy[k]=Array.isArray(copy[k])?copy[k].map((_,i)=>'SS6344-MALFORMED-OFFER-'+i):'SS6344-MALFORMED-OFFER';}}return copy;}
function matching(r){
  const segments=r.trips.flatMap(t=>t.segments.map(s=>[s.departureAirportCode,s.arrivalAirportCode,s.departureTime.slice(0,10),s.arrivalTime.slice(0,10),s.marketingAirline,String(s.flightNumber)]));
  const before=r.penalties.list.filter(p=>p.applicability==='before').map(p=>[p.type,p.permitted]).sort((a,b)=>a[0].localeCompare(b[0]));
  if(!before.length)throw new Error('Before penalties unavailable');
  const fare=r.keys.brightsun.fare;
  for(const k of ['checkedBaggage','exchange','refund'])if(typeof fare[k]!=='boolean')throw new Error('Matching flag missing: '+k);
  return {segments,before,fare:{checkedBaggage:fare.checkedBaggage,exchange:fare.exchange,refund:fare.refund}};
}
function redact(x){if(Array.isArray(x))return x.map(redact);if(x&&typeof x==='object')return Object.fromEntries(Object.entries(x).map(([k,v])=>[k,/token|authorization|password/i.test(k)&&!(k==='token'&&v==='INVALID_TEST_TOKEN')?'[REDACTED]':redact(v)]));return x;}
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
async function run(){
  if(!process.env.BOOKING_USERNAME||!process.env.BOOKING_PASSWORD)throw new Error('Set local booking Basic Auth');
  const runDir=path.join(dir,'runs',new Date().toISOString().replace(/[:.]/g,'-'));fs.mkdirSync(runDir,{recursive:true});fs.writeFileSync(path.join(dir,'latest-run.txt'),runDir);
  const rows=[];
  for(const c of cases){
    const d=path.join(runDir,c.id);fs.mkdirSync(d);const save=(n,x)=>fs.writeFileSync(path.join(d,n+'.json'),JSON.stringify(x,null,2));
    let stage='search',actual,selected;
    async function request(n,u,body,auth=false){stage=n;save(n+'-request',{method:body?'POST':'GET',url:u,...(body?{body}:{})});const headers=body?{'Content-Type':'application/json'}:{};if(auth)headers.Authorization='Basic '+Buffer.from(process.env.BOOKING_USERNAME+':'+process.env.BOOKING_PASSWORD).toString('base64');const response=await fetch(u,{method:body?'POST':'GET',headers,body:body?JSON.stringify(body):undefined,redirect:'error',signal:AbortSignal.timeout(60000)});const text=await response.text();fs.writeFileSync(path.join(d,n+'-response.json'),text);save(n+'-meta',{status:response.status,receivedAt:new Date().toISOString()});console.log(c.id+' '+n+': '+response.status);return {status:response.status,data:JSON.parse(text)};}
    const row={id:c.id,data:'RT AMS–LHR, 1 ADT; malformed '+c.mutation,expected:'Automatic recovery; same segments, checkedBaggage and before exchange/refund penalties',status:'WARN',actual:'Not evaluated',evidence:d};
    try{
      const s=await request('search',url);selected=s.data.results?.[0];if(!selected)throw new Error('No selectable inventory');const expected=matching(selected);save('matching-baseline',expected);
      let body=structuredClone(selected);if(c.endpoint==='result')body.keys.brightsun=corrupt(body.keys.brightsun,c.mutation);
      const r=await request('result',host+'/brightsun/v1/result',body);
      if(c.endpoint==='result'){
        actual=r;if(r.status!==200){row.status='FAIL';row.actual='Result HTTP '+r.status+'; '+(r.data.message||r.data.type||'recovery failed');}
        else {assert.deepEqual(matching(r.data),expected);row.status='PASS';row.actual='Result HTTP 200; segments, baggage flag and before penalties retained';}
      }else{
        if(r.status!==200)throw new Error('Result setup HTTP '+r.status);
        const baseline=matching(r.data);save('matching-baseline',baseline);
        const date=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Bucharest',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
        const booking=buildBooking(r.data,date);booking.additionalInfo=corrupt(booking.additionalInfo,c.mutation);
        actual=await request('booking',host+'/brightsun/v1/book/create',booking,true);
        const firstStatus=actual.status;
        if(actual.status===422&&actual.data.type==='Price change'){const updated=updatedPriceBody(booking,actual.data,actual.status);actual=await request('booking-retry',host+'/brightsun/v1/book/create',updated,true);}
        if(actual.status!==200){row.status='FAIL';row.actual='Booking HTTP '+firstStatus+(stage==='booking-retry'?' → '+actual.status:'')+'; '+(actual.data.type||actual.data.message||'recovery failed');}
        else{
          const response=actual.data.data.response,info=actual.data.data.additionalInfo;
          const segments=response.pnrInfo.segments.map(s=>[s.departureAirportCode,s.arrivalAirportCode,s.departureDate.slice(0,10),s.arrivalDate.slice(0,10),s.marketingAirlineCode,String(s.marketingFlightNumber)]);
          assert.deepEqual(segments,baseline.segments);
          assert.deepEqual({checkedBaggage:info.fare.checkedBaggage,exchange:info.fare.exchange,refund:info.fare.refund},baseline.fare);
          for(const [type,permitted]of baseline.before)assert.equal(info.fare[type==='ex'?'exchange':'refund'],permitted);
          assert(info.recLoc&&info.brightsunReference);
          row.status='PASS';row.actual='Booking HTTP '+firstStatus+(stage==='booking-retry'?' → '+actual.status:'')+'; '+info.recLoc+' / '+info.brightsunReference+'; segments and matching flags retained';
        }
      }
    }catch(e){row.status=actual?.status===200?'FAIL':'WARN';row.actual=stage+': '+e.message;save('evaluation-error',{message:e.message,stage});}
    rows.push(row);fs.writeFileSync(path.join(runDir,'results.json'),JSON.stringify(rows,null,2));console.log(c.id+': '+row.status+' '+row.actual);
  }
  report();
}
function evaluate(){
  const runDir=fs.readFileSync(path.join(dir,'latest-run.txt'),'utf8').trim(),rows=read(path.join(runDir,'results.json'));
  for(const row of rows){
    const load=n=>read(path.join(row.evidence,n+'.json'));
    if(row.id.startsWith('result-')){
      const response=load('result-response'),meta=load('result-meta');
      if(meta.status!==200){row.status='FAIL';row.actual='Result HTTP '+meta.status+'; '+(response.Status||response.name||'error')+'; '+(response.Message||response.message||'')+'; unmodified same-offer control HTTP '+load('control-meta').status;continue;}
      try{assert.deepEqual(matching(response),matching(load('search-response').results[0]));row.status='PASS';row.actual='Result HTTP 200; same airports, flight dates, airlines and flight numbers; baggage flag and before penalties retained';}catch(e){row.status='FAIL';row.actual='Recovered Result matching criteria differ';}
    }else{
      const retry=fs.existsSync(path.join(row.evidence,'booking-retry-meta.json')),response=load(retry?'booking-retry-response':'booking-response'),meta=load(retry?'booking-retry-meta':'booking-meta');
      try{
        assert.equal(meta.status,200);const baseline=matching(load('result-response')),data=response.data,info=data.additionalInfo;
        const segments=data.response.pnrInfo.segments.map(s=>[s.departureAirportCode,s.arrivalAirportCode,s.departureDate.slice(0,10),s.arrivalDate.slice(0,10),s.marketingAirlineCode,String(s.marketingFlightNumber)]);
        assert.deepEqual(segments,baseline.segments);assert.deepEqual({checkedBaggage:info.fare.checkedBaggage,exchange:info.fare.exchange,refund:info.fare.refund},baseline.fare);for(const [t,p]of baseline.before)assert.equal(info.fare[t==='ex'?'exchange':'refund'],p);assert(info.recLoc&&info.brightsunReference);
        row.status='PASS';row.actual='Booking HTTP 200; '+info.recLoc+' / '+info.brightsunReference+'; same flights, baggage flag and before penalties retained; 5-minute schedule changes accepted by user';
      }catch(e){row.status='FAIL';row.actual='Booking HTTP '+meta.status+'; '+e.message.split('\n')[0];}
    }
  }
  fs.writeFileSync(path.join(runDir,'results.json'),JSON.stringify(rows,null,2));report();
}
function prepare(){
  const c=read(path.join(dir,'../ss-6341/brightsun-book-create.postman_collection.json'));c.info.name='SS-6344 Brightsun automatic Search and Match';c.info.description='Malformed token and offer IDs on Result/book/create. Search is setup only. Match segments, checkedBaggage and before exchange/refund permissions. Service performs recovery; collection does not manually re-search. Booking price retry retained.';
  c.item[0].event.find(e=>e.listen==='prerequest').script.exec[0]="const url = pm.iterationData.get('search_url') || "+JSON.stringify(url)+';';
  c.item[1].event.find(e=>e.listen==='prerequest').script.exec.push(corrupt.toString(),"if (pm.iterationData.get('endpoint') === 'result') { const body = JSON.parse(pm.collectionVariables.get('brightsun_selected_solution')); body.keys.brightsun = corrupt(body.keys.brightsun, pm.iterationData.get('mutation')); pm.collectionVariables.set('brightsun_selected_solution', JSON.stringify(body)); }");
  c.item[0].event.find(e=>e.listen==='test').script.exec.push(matching.toString(),"pm.collectionVariables.set('matching_baseline', JSON.stringify(matching(data.results[0])));");
  c.item[1].event.find(e=>e.listen==='test').script.exec=[matching.toString(),corrupt.toString(),buildBooking.toString(),
    "const data=pm.response.json();",
    "if (pm.iterationData.get('endpoint') === 'result') {",
    " pm.execution.setNextRequest(null);",
    " pm.test('SS-6344: Result recovery HTTP 200', () => pm.expect(pm.response.code).to.equal(200));",
    " if(pm.response.code===200) pm.test('SS-6344: Segments and matching fare flags retained', () => pm.expect(matching(data)).to.deep.equal(JSON.parse(pm.collectionVariables.get('matching_baseline'))));",
    "} else {",
    " try {",
    "  pm.collectionVariables.set('matching_baseline',JSON.stringify(matching(data)));",
    "  const date=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Bucharest',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());",
    "  const body=buildBooking(data,date);body.additionalInfo=corrupt(body.additionalInfo,pm.iterationData.get('mutation'));pm.collectionVariables.set('booking_body',JSON.stringify(body));",
    " } catch(e){pm.execution.setNextRequest(null);throw e;}","}"];
  c.item[2].event.find(e=>e.listen==='test').script.exec.push(
    "if(pm.response.code===200){",
    " const data=pm.response.json().data, baseline=JSON.parse(pm.collectionVariables.get('matching_baseline'));",
    " const segments=data.response.pnrInfo.segments.map(s=>[s.departureAirportCode,s.arrivalAirportCode,s.departureDate.slice(0,10),s.arrivalDate.slice(0,10),s.marketingAirlineCode,String(s.marketingFlightNumber)]);",
    " pm.test('SS-6344: Recovered booking segments match',()=>pm.expect(segments).to.deep.equal(baseline.segments));",
    " pm.test('SS-6344: Baggage and before penalties match',()=>{const f=data.additionalInfo.fare;pm.expect({checkedBaggage:f.checkedBaggage,exchange:f.exchange,refund:f.refund}).to.deep.equal(baseline.fare);for(const [t,p]of baseline.before)pm.expect(f[t==='ex'?'exchange':'refund']).to.equal(p);});",
    "}");
  fs.mkdirSync(dir,{recursive:true});fs.writeFileSync(path.join(dir,'recovery.postman_collection.json'),JSON.stringify(c,null,2));
  fs.writeFileSync(path.join(dir,'expected-outcomes.csv'),'scenario_id,expected_result,provider_filter,search_url,endpoint,mutation,expected_status\n'+cases.map(c=>[c.id,'Automatic recovery preserving segments baggage and before penalties','brightsun','"'+url+'"',c.endpoint,c.mutation,200].join(',')).join('\n')+'\n');
  const fixture=read(path.join(dir,'../ss-6341/runs/2026-10-01T10-00-04-677Z/result-response.json'));const copy=corrupt(fixture.keys.brightsun,'offers');assert.equal(copy.optionKeys.length,fixture.keys.brightsun.optionKeys.length);assert.deepEqual(copy.fare,fixture.keys.brightsun.fare);assert.notEqual(copy.inboundKey,fixture.keys.brightsun.inboundKey);assert.equal(corrupt(fixture.keys.brightsun,'token').token,'INVALID_TEST_TOKEN');assert(matching(fixture).before.length);for(const i of c.item)for(const e of i.event)new Function('pm',e.script.exec.join('\n'));console.log('Collection prepared; mutation and script checks passed.');
}
function report(){
  const runDir=fs.readFileSync(path.join(dir,'latest-run.txt'),'utf8').trim(),rows=read(path.join(runDir,'results.json'));
  const signal=rows.some(r=>r.status==='FAIL')?'FAIL':rows.some(r=>r.status==='WARN')?'WARN':'PASS';
  const scope='2026-10-01 | DEV | RT AMS–LHR | 1 ADT | Result and book/create | token / optionKeys+outboundKey+inboundKey';
  const intended='Malformed token or offer IDs trigger service-owned Search and Match recovery. Retain airports, flight dates, airlines and flight numbers; timing changes on the same flights are accepted by the user. Match fare.checkedBaggage and exchange/refund permissions with applicability before. Booking may accept a price update from a 422 Price change response and retry once. No expired-token timing, missing-match cases or vendor payload mapping tested.';
  const summary=rows.filter(r=>r.status==='PASS').length+' PASS / '+rows.filter(r=>r.status==='FAIL').length+' FAIL / '+rows.filter(r=>r.status==='WARN').length+' WARN. Endpoint responses establish observable recovery and match retention; internal Search execution is not directly visible.';
  const pairs=rows.map(r=>({id:r.id,evidence:fs.readdirSync(r.evidence).filter(n=>/request|response|meta|baseline|error/.test(n)).map(n=>({file:n,payload:redact(read(path.join(r.evidence,n)))}))}));
  fs.writeFileSync(path.join(dir,'payload-evidence.json'),JSON.stringify(pairs,null,2));
  fs.writeFileSync(path.join(dir,'qa-report.md'),'Release signal: '+signal+'\nScope/run: '+scope+'\n\nIntended behavior: '+intended+'\n\n'+summary+'\n\n| ID | Test data | Expected result | Actual result | Status |\n|---|---|---|---|---|\n'+rows.map(r=>'| '+[r.id,r.data,r.expected,r.actual,r.status].join(' | ')+' |').join('\n')+'\n\nEvidence: '+runDir+'; payload-evidence.json contains request/response pairs with tokens redacted. Rerun via recovery.postman_collection.json and expected-outcomes.csv, with local booking_username/booking_password environment variables.\n\n'+rows.filter(r=>r.status!=='PASS').map(r=>'```json\n'+JSON.stringify(pairs.find(p=>p.id===r.id),null,2)+'\n```').join('\n'));
  const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');let html=fs.readFileSync(path.join(dir,'../../templates/airapi-qa-dispatch-template.html'),'utf8');
  html=html.replace('&lt;Ticket title&gt;','SS-6344 · Search and Match').replace('&lt;YYYY-MM-DD&gt;','2026-10-01').replace('&lt;Endpoint / route / scope&gt;',esc(scope)).replace('&lt;PASS / FAIL / WARN&gt;',signal).replace('value fail','value '+signal.toLowerCase());for(const s of ['PASS','FAIL','WARN'])html=html.replace('&lt;0&gt;',String(rows.filter(r=>r.status===s).length));html=html.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;',esc(intended+' '+summary));html=html.replace(/<tbody>[\s\S]*?<\/tbody>/,'<tbody>'+rows.map(r=>'<tr><td>'+r.id+'</td><td class="test">'+esc(r.data)+'</td><td>'+esc(r.expected)+' → '+esc(r.actual)+'</td><td class="status '+r.status.toLowerCase()+'">'+r.status+'</td></tr>').join('')+'</tbody>');html=html.replace(/<section class="failure-sample">[\s\S]*?<\/section>/,rows.filter(r=>r.status!=='PASS').map(r=>'<section class="failure-sample"><h2>'+r.id+' · Paired evidence</h2><pre>'+esc(JSON.stringify(pairs.find(p=>p.id===r.id),null,2))+'</pre></section>').join(''));html=html.replace('&lt;Response count, exact field paths, and other confirmed API facts.&gt;',esc(summary+' Evidence: '+runDir+'; payload-evidence.json.'));for(const [placeholder,name]of [['collection','recovery.postman_collection.json'],['csv','expected-outcomes.csv']])html=html.replaceAll('&lt;'+placeholder+'-file-name&gt;',name).replaceAll('<'+placeholder+'-file-name>',name).replace('<'+placeholder+'-base64>',fs.readFileSync(path.join(dir,name)).toString('base64'));fs.writeFileSync(path.join(dir,'qa-report.html'),html);assert(!/&lt;[^&]+&gt;|<[^>]*-base64>/.test(html));console.log(summary);
}
if(process.argv.includes('--run'))run().catch(e=>{console.error(e.message);process.exitCode=1;});else if(process.argv.includes('--evaluate'))evaluate();else if(process.argv.includes('--report'))report();else prepare();

