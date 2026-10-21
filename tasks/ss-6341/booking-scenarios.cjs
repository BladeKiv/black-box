const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {run}=require('./booking-flow.cjs');
const dir=__dirname;
const scenarios=[['ow-1adt','OW',1,0,0],['rt-2adt','RT',2,0,0],['ow-adt-chd','OW',1,1,0],['rt-adt-inf','RT',1,0,1],['mc-2adt','MC',2,0,0]].map(([id,type,adt,chd,inf])=>{
  let url='https://api.search.dev.travel-dev.com/brightsun/v1/search?tripType='+type+'&fl[0][o]='+ (type==='MC'?'LAX':'AMS')+'&fl[0][d]='+ (type==='MC'?'FRA':'LHR')+'&fl[0][dt]=2026-11-11&cabin=Y&adt='+adt+'&chd='+chd+'&inf='+inf;
  if(type!=='OW')url+='&fl[1][o]='+ (type==='MC'?'MUC':'LHR')+'&fl[1][d]='+ (type==='MC'?'LAX':'AMS')+'&fl[1][dt]=2026-11-18';
  return {id,type,adt,chd,inf,url:url+'&limit=100'};
});
const read=(p)=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const indexPath=path.join(dir,'booking-scenarios.json');
async function execute(){
  const original=fs.readFileSync(path.join(dir,'latest-run.txt'),'utf8').trim();
  const index=fs.existsSync(indexPath)?read(indexPath):[{id:'rt-adt-chd-inf',type:'RT',adt:1,chd:1,inf:1,evidence:original,provenance:'earlier captured booking, not rerun'}];
  fs.writeFileSync(indexPath,JSON.stringify(index,null,2));
  for(const scenario of scenarios){
    if(index.some(s=>s.id===scenario.id))continue;
    console.log(scenario.id);
    await run({searchUrl:scenario.url});
    index.push({...scenario,evidence:fs.readFileSync(path.join(dir,'latest-run.txt'),'utf8').trim(),provenance:'new live booking'});
    fs.writeFileSync(indexPath,JSON.stringify(index,null,2));
  }
}
function report(){
  const index=read(indexPath),rows=[];
  const payloads=[];
  function redact(value){if(Array.isArray(value))return value.map(redact);if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,/token|authorization|password/i.test(k)?'[REDACTED]':redact(v)]));return value;}
  for(const s of index){
    const load=n=>{const p=path.join(s.evidence,n+'.json');return fs.existsSync(p)?read(p):null;};
    const initial=load('booking-meta'),retry=load('booking-retry-meta'),meta=retry||initial,response=load(retry?'booking-retry-response':'booking-response');
    const info=response?.data?.additionalInfo;
    const refs=typeof info?.recLoc==='string'&&info.recLoc.length>0&&typeof info?.brightsunReference==='string'&&info.brightsunReference.length>0;
    const status=!meta?'WARN':meta.status===200&&refs?'PASS':'FAIL';
    rows.push({id:s.id,data:s.type+'; ADT '+s.adt+' / CHD '+s.chd+' / INF '+s.inf,expected:'Booking HTTP 200; PNR and Brightsun reference returned; on 422 Price change update price and resend once',actual:meta?('HTTP '+initial.status+(retry?' → '+retry.status:'')+'; '+(info?.recLoc||'no PNR')+'; '+(info?.brightsunReference||'no reference')+'; '+(response?.data?.response?.total_price??'price unavailable')+' '+(response?.data?.response?.currency||'')):('No booking response; '+(load('error')?.message||'setup unavailable')),status,provenance:s.provenance,evidence:s.evidence});
    payloads.push({scenario_id:s.id,provenance:s.provenance,initial:{request:redact(load('booking-request')||load('result-request')||load('search-request')),response:redact(load('booking-response')||load('result-response')||load('search-response')),meta:initial},retry:retry?{request:redact(load('booking-retry-request')),response:redact(load('booking-retry-response')),meta:retry}:null,error:load('error')});
  }
  fs.writeFileSync(path.join(dir,'booking-payloads.json'),JSON.stringify(payloads,null,2));
  fs.writeFileSync(path.join(dir,'test-results.json'),JSON.stringify(rows,null,2));
  const cpath=path.join(dir,'brightsun-book-create.postman_collection.json'),c=read(cpath);
  c.info.description+=' Search and Result are setup only, with no pm.test assertions. TC-07 vendor mapping is excluded by user instruction.';
  fs.writeFileSync(cpath,JSON.stringify(c,null,2));
  const original=read(path.join(index[0].evidence,'search-request.json')).url;
  const csv='scenario_id,expected_result,provider_filter,search_url,expected_status,adt,chd,inf,booking_date_basis\n'+[{...index[0],url:original},...scenarios].map(s=>[s.id,'HTTP 200 and booking references','brightsun','"'+s.url+'"',200,s.adt,s.chd,s.inf,'Europe/Bucharest booking day'].join(',')).join('\n')+'\n';
  fs.writeFileSync(path.join(dir,'expected-outcomes.csv'),csv);
  const signal=rows.some(r=>r.status==='FAIL')?'FAIL':rows.some(r=>r.status==='WARN')?'WARN':'PASS';
  const scope='2026-10-01 | DEV | booking only | '+(index.length-1)+' new scenarios + 1 earlier captured booking | OW / RT / MC | economy';
  const intended='POST /brightsun/v1/book/create returns HTTP 200 and booking references data.additionalInfo.recLoc and brightsunReference. On HTTP 422 Price change, update only trip.total_price from data.response.total_price and resubmit once. Search and Result supply fresh booking data only. TC-07 vendor mapping is excluded pending user clarification.';
  const summary=rows.filter(r=>r.status==='PASS').length+' PASS / '+rows.filter(r=>r.status==='FAIL').length+' FAIL / '+rows.filter(r=>r.status==='WARN').length+' WARN. One row retains earlier executed booking evidence; five rows are additional live scenarios. Each row represents a booking scenario, including any price retry.';
  const pairs=rows.filter(r=>r.status!=='PASS').map(r=>({id:r.id,payload:payloads.find(p=>p.scenario_id===r.id)}));
  fs.writeFileSync(path.join(dir,'qa-report.md'),'Release signal: '+signal+'\nScope/run: '+scope+'\n\nIntended behavior: '+intended+'\n\n'+summary+'\n\n| ID | Test data | Expected result | Actual result | Status |\n|---|---|---|---|---|\n'+rows.map(r=>'| '+[r.id,r.data,r.expected,r.actual,r.status].join(' | ')+' |').join('\n')+'\n\nEvidence and rerun: booking-scenarios.json records evidence paths and provenance; booking-payloads.json contains full request/response pairs with session tokens redacted. Set local Postman Basic Auth environment variables booking_username and booking_password; run with expected-outcomes.csv. No Search/Result assertions; TC-07 excluded.\n\n'+(pairs.length?'WARN/FAIL payload pairs:\n```json\n'+JSON.stringify(pairs,null,2)+'\n```':'All booking scenarios conclusively evaluated.')+'\n');
  const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
  let html=fs.readFileSync(path.join(dir,'../../templates/airapi-qa-dispatch-template.html'),'utf8');
  html=html.replace('&lt;Ticket title&gt;','SS-6341 · Brightsun booking scenarios').replace('&lt;YYYY-MM-DD&gt;','2026-10-01').replace('&lt;Endpoint / route / scope&gt;',esc(scope)).replace('&lt;PASS / FAIL / WARN&gt;',signal).replace('value fail','value '+signal.toLowerCase());
  for(const status of ['PASS','FAIL','WARN'])html=html.replace('&lt;0&gt;',String(rows.filter(r=>r.status===status).length));
  html=html.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;',esc(intended+' '+summary));
  html=html.replace(/<tbody>[\s\S]*?<\/tbody>/,'<tbody>'+rows.map(r=>'<tr><td>'+r.id+'</td><td class="test">'+esc(r.data)+'</td><td>'+esc(r.expected)+' → '+esc(r.actual)+'</td><td class="status '+r.status.toLowerCase()+'">'+r.status+'</td></tr>').join('')+'</tbody>');
  html=html.replace(/<section class="failure-sample">[\s\S]*?<\/section>/,pairs.map(p=>'<section class="failure-sample"><h2>'+esc(p.id)+' · Payload evidence</h2><pre>'+esc(JSON.stringify(p.payload,null,2))+'</pre></section>').join(''));
  html=html.replace('&lt;Response count, exact field paths, and other confirmed API facts.&gt;',esc('Booking-only evaluation. Full request/response pairs: booking-payloads.json. Evidence paths and provenance: booking-scenarios.json. '+summary));
  for(const [placeholder,name]of [['collection','brightsun-book-create.postman_collection.json'],['csv','expected-outcomes.csv']])html=html.replaceAll('&lt;'+placeholder+'-file-name&gt;',name).replaceAll('<'+placeholder+'-file-name>',name).replace('<'+placeholder+'-base64>',fs.readFileSync(path.join(dir,name)).toString('base64'));
  fs.writeFileSync(path.join(dir,'qa-report.html'),html);
  assert(!/&lt;[^&]+&gt;|<[^>]*-base64>/.test(html));
  for(const item of c.item){for(const e of item.event)new Function('pm',e.script.exec.join('\n'));if(item.name!=='v1/book/create')assert(!item.event.some(e=>e.script.exec.join('\n').includes('pm.test(')));}
  assert.equal(index.length,6);
  console.log(summary);for(const row of rows)console.log(row.id+': '+row.status+' '+row.actual);
}
if(process.argv.includes('--run'))execute().catch(e=>{console.error(e.message);process.exitCode=1;});
else report();
