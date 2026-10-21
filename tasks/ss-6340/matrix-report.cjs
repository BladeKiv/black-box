const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const dir = __dirname, read = f => JSON.parse(fs.readFileSync(f,'utf8').replace(/^\uFEFF/,''));
const run = fs.readFileSync(path.join(dir,'latest-matrix.txt'),'utf8').trim();
const matrix = read(path.join(run,'matrix.json'));
const itinerary = o => o.trips.flatMap(t => t.segments.map(s => [s.departureAirportCode,s.arrivalAirportCode,s.departureTime,s.flightNumber,s.marketingAirline]));
const rows = [];
for (const c of matrix) {
  const file = name => path.join(c.evidence,name+'.json');
  const expected = 'POST selected Search object unchanged; preserve itinerary and requested passengers; return fare data and Result keys.brightsun for reuse';
  const row = {...c, expected, status:'WARN', actual:'Result not evaluated', issues:[], count:0};
  try {
    const s = read(file('search-response')), sm = read(file('search-meta'));
    row.count = s.results?.length || 0;
    row.searchStatus = sm.status;
    if (!row.count) {row.actual=`Search HTTP ${sm.status}; no selectable solution`; rows.push(row); continue;}
    const selected = read(file('selected-solution')), req = read(file('result-request'));
    const r = read(file('result-response')), rm = read(file('result-meta'));
    row.resultStatus=rm.status;
    if (!r.keys?.brightsun || !r.prices || !r.trips) {row.actual=`Result HTTP ${rm.status}; no repriced solution returned: ${JSON.stringify(r)}`; rows.push(row); continue;}
    assert.deepEqual(selected,s.results[0]);
    assert.deepEqual(req.body,selected);
    assert.deepEqual(itinerary(r),itinerary(selected));
    assert.equal(r.tripType,c.tripType);
    assert.equal(selected.tripType,c.tripType);
    for (const [code,n] of [['ADT',c.adt],['CHD',c.chd],['INF',c.inf]]) {
      if (n>0) { assert.equal(selected.passengers?.[code]?.cnt,n,`Search ${code} count`); assert.equal(r.passengers?.[code]?.cnt,n,`Result ${code} count`); }
      else {if (selected.passengers?.[code]) assert.equal(selected.passengers[code].cnt,0,`Unexpected Search ${code}`); if (r.passengers?.[code]) assert.equal(r.passengers[code].cnt,0,`Unexpected Result ${code}`);}
    }
    assert.equal(typeof r.prices.totalPrice,'number'); assert.ok(Number.isFinite(r.prices.totalPrice));
    assert.equal(typeof r.prices.totalTax,'number'); assert.ok(Number.isFinite(r.prices.totalTax));
    assert.equal(r.currency,selected.currency);
    assert.equal(typeof r.keys.brightsun.key,'string'); assert.ok(r.keys.brightsun.key.length);
    if (Object.hasOwn(r.keys.brightsun,'token')) {assert.equal(typeof r.keys.brightsun.token,'string');assert.ok(r.keys.brightsun.token.length);}
    fs.writeFileSync(file('result-additional-info'),JSON.stringify(r.keys.brightsun,null,2));
    assert.deepEqual(read(file('result-additional-info')),r.keys.brightsun);
    row.status='PASS'; row.searchPrices=selected.prices; row.resultPrices=r.prices; row.currency=r.currency;
    row.searchKey=selected.keys.brightsun.key; row.resultKey=r.keys.brightsun.key;
    row.keyChanged=row.searchKey!==row.resultKey; row.tokenChanged=selected.keys.brightsun.token!==r.keys.brightsun.token;
    row.actual=`Search HTTP ${sm.status} (${row.count} solutions) → Result HTTP ${rm.status}; ${r.currency} ${selected.prices.totalPrice} → ${r.prices.totalPrice}; tax ${r.prices.totalTax}; requested passengers and itinerary retained; Result additional info saved`;
  } catch(e) {
    row.status=e.code==='ERR_ASSERTION'?'FAIL':'WARN'; row.actual=e.message; row.issues.push(e.message);
  }
  rows.push(row);
}
const collectionFile='brightsun service.postman_collection.json', cf=path.join(dir,collectionFile), collection=read(cf);
const defaultUrl=collection.item[1].request.url.raw || collection.item[1].request.url;
const fallback=typeof defaultUrl==='string' && defaultUrl!=='{{search_url}}'? defaultUrl.replace('{{brightsun_host}}','https://api.search.dev.travel-dev.com'):read(path.join(dir,'runs',path.basename(fs.readFileSync(path.join(dir,'latest-run.txt'),'utf8').trim()),'search-request.json')).url;
const pre=`const url = pm.iterationData.get('search_url') || ${JSON.stringify(fallback)};
pm.variables.set('search_url', url);
pm.collectionVariables.unset('brightsun_selected_solution');
pm.collectionVariables.unset('brightsun_result_additional_info');`;
collection.item[1].request.url='{{search_url}}';
collection.item[1].event=collection.item[1].event.filter(e=>e.listen!=='prerequest');
collection.item[1].event.unshift({listen:'prerequest',script:{type:'text/javascript',exec:pre.split('\n')}});
const event=collection.item[2].event.find(e=>e.listen==='test');
const extra=`
pm.test('SS-6340: Result preserves selected passenger counts and trip type', function () {
    pm.expect(data.tripType).to.equal(selected.tripType);
    const counts = o => Object.fromEntries(Object.entries(o.passengers).map(([k,v]) => [k,v.cnt]));
    pm.expect(counts(data)).to.deep.equal(counts(selected));
});
const url = new URL(pm.variables.get('search_url'));
pm.test('SS-6340: Selected passengers match Search parameters', function () {
    for (const code of ['ADT','CHD','INF']) {
        const count = Number(url.searchParams.get(code.toLowerCase()) || (code === 'ADT' ? 1 : 0));
        if (count > 0) pm.expect(selected.passengers[code].cnt).to.equal(count);
        else if (selected.passengers[code]) pm.expect(selected.passengers[code].cnt).to.equal(0);
    }
    pm.expect(selected.tripType).to.equal(url.searchParams.get('tripType'));
});`;
if (!event.script.exec.join('\n').includes('Selected passengers match Search parameters')) event.script.exec.push(...extra.split('\n'));
collection.info.description='SS-6340: Run v1/search then v1/result with expected-outcomes.csv in Collection Runner. Each row selects results[0] and POSTs that complete object unchanged. keys.brightsun returned by Result is saved as brightsun_result_additional_info. Error 112/113 scenarios excluded by user instruction. No booking calls.';
fs.writeFileSync(cf,JSON.stringify(collection,null,2));
const quote=s=>'"'+String(s).replaceAll('"','""')+'"';
const csv='scenario_id,expected_result,provider_filter,search_url,trip_type,adt,chd,inf,selected_index\n'+matrix.map(c=>[c.scenario_id,'Repriced selected itinerary, requested passenger counts, and Result additional info','',''+(c.reused?read(path.join(c.evidence,'search-request.json')).url:c.search_url),c.tripType,c.adt,c.chd,c.inf,0].map(quote).join(',')).join('\n')+'\n';
fs.writeFileSync(path.join(dir,'expected-outcomes.csv'),csv);
let checks=0;
function expect(value) {
  const chain={}; for(const k of ['to','be','and'])Object.defineProperty(chain,k,{get:()=>chain});
  chain.a=chain.an=t=>{assert.equal(Array.isArray(value)?'array':typeof value,t);return chain;};
  chain.equal=v=>{assert.equal(value,v);return chain;}; chain.deep={equal:v=>{assert.deepEqual(value,v);return chain;}};
  Object.defineProperty(chain,'not',{get:()=>{assert.ok(value!=null&&value.length>0);return {empty:chain};}}); return chain;
}
for(const row of rows.filter(r=>r.status==='PASS')) {
  const vars=new Map(), local=new Map(); let body;
  const pm={expect,test:(name,fn)=>{fn();checks++;},response:{json:()=>body},iterationData:{get:k=>k==='search_url'?read(path.join(row.evidence,'search-request.json')).url:undefined},variables:{get:k=>local.get(k),set:(k,v)=>local.set(k,v)},collectionVariables:{get:k=>vars.get(k),set:(k,v)=>vars.set(k,v),unset:k=>vars.delete(k)},execution:{skipRequest:()=>{throw Error('Unexpected skip');}}};
  for(const item of collection.item)for(const e of item.event||[]) {body=read(path.join(row.evidence,item.name==='v1/search'?'search-response.json':'result-response.json'));new Function('pm',e.script.exec.join('\n'))(pm);}
  assert.deepEqual(JSON.parse(vars.get('brightsun_selected_solution')),read(path.join(row.evidence,'result-request.json')).body);
  assert.deepEqual(JSON.parse(vars.get('brightsun_result_additional_info')),read(path.join(row.evidence,'result-response.json')).keys.brightsun);
}
const totals={PASS:0,FAIL:0,WARN:0};for(const r of rows)totals[r.status]++;
const signal=totals.FAIL?'FAIL':totals.WARN?'WARN':'PASS';
const intended='Reprice each selected solution before booking. Preserve the selected itinerary and passenger counts. Retain Result keys.brightsun, including its returned Key and any token, for subsequent booking preparation. Fare, Key, or token changes are permitted but not mandatory.';
const finding=`${matrix.length} Search → Result scenarios cover OW, RT, and MC crossed with five passenger mixes. ${totals.PASS} PASS / ${totals.FAIL} FAIL / ${totals.WARN} WARN. RT adult-only rows reuse the two earlier live runs; other rows use fresh Search responses. Errors 112/113 excluded by user instruction; no booking endpoint called.`;
const tableHeader='| ID | Test data | Expected | Actual | Status |\n|---|---|---|---|---|\n';
const data=r=>`${r.tripType}; ADT ${r.adt}, CHD ${r.chd}, INF ${r.inf}; ${r.tripType==='MC'?'LAX→FRA / MUC→LAX':r.tripType==='OW'?'AMS→LHR':'AMS→LHR→AMS'}; 11 Nov${r.tripType==='OW'?'':' / 18 Nov'} 2026`;
const evidence=[];
for(const row of rows.filter(r=>r.status!=='PASS')) {
  for(const endpoint of ['search','result']) {
    const q=path.join(row.evidence,endpoint+'-request.json'),a=path.join(row.evidence,endpoint+'-response.json');
    if(fs.existsSync(q))evidence.push({id:row.scenario_id,endpoint,request:read(q),response:fs.existsSync(a)?read(a):{transport:fs.existsSync(path.join(row.evidence,'transport-error.json'))?read(path.join(row.evidence,'transport-error.json')):'No response captured'}});
  }
}
const md=`Release signal: ${signal}\nScope/run: 2026-09-30 | DEV | OW / RT / MC | 15 trip/passenger combinations.\n\nIntended behavior: ${intended}\n\n${finding}\n\n${tableHeader}${rows.map(r=>'| '+[r.scenario_id,data(r),r.expected,r.actual.replaceAll('|','/'),r.status].join(' | ')+' |').join('\n')}\n\nEvidence and rerun: ${path.relative(dir,run)}; matrix-results.json records exact evidence locations, Search URLs, Keys, fare comparisons, and provenance. Run the collection with expected-outcomes.csv. ${checks} Postman assertions replayed against captured responses; this replay made no network calls.\n\n${evidence.map(e=>`${e.id} ${e.endpoint}:\nRequest:\n\`\`\`json\n${JSON.stringify(e.request,null,2)}\n\`\`\`\nResponse:\n\`\`\`json\n${JSON.stringify(e.response,null,2)}\n\`\`\``).join('\n')}`;
fs.writeFileSync(path.join(dir,'qa-report.md'),md);
let html=fs.readFileSync(path.join(dir,'../../templates/airapi-qa-dispatch-template.html'),'utf8');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
html=html.replace('&lt;Ticket title&gt;','SS-6340 · Result matrix').replace('&lt;YYYY-MM-DD&gt;','2026-09-30').replace('&lt;Endpoint / route / scope&gt;','DEV / OW · RT · MC / 5 passenger mixes');
html=html.replace('value fail">&lt;PASS / FAIL / WARN&gt;',`value ${signal.toLowerCase()}">${signal}`).replace('&lt;0&gt;',totals.PASS).replace('&lt;0&gt;',totals.FAIL).replace('&lt;0&gt;',totals.WARN);
html=html.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;',esc(finding)).replace('<h2>Executed tests</h2>','<h2>Intended behavior</h2><p>'+esc(intended)+'</p><h2>Executed tests</h2>');
html=html.replace(/<tbody>[\s\S]*?<\/tbody>/,'<tbody>'+rows.map(r=>`<tr><td>${r.scenario_id}</td><td>${esc(data(r))}</td><td>${esc(r.expected)} → ${esc(r.actual)}</td><td class="status ${r.status.toLowerCase()}">${r.status}</td></tr>`).join('')+'</tbody>');
html=html.replace(/<section class="failure-sample">[\s\S]*?<\/section>/,evidence.map(e=>`<section class="failure-sample"><h2>${e.id} · ${e.endpoint} evidence</h2><h2>Request</h2><pre>${esc(JSON.stringify(e.request,null,2))}</pre><h2>Response</h2><pre>${esc(JSON.stringify(e.response,null,2))}</pre></section>`).join(''));
html=html.replace('&lt;Response count, exact field paths, and other confirmed API facts.&gt;',esc(`${checks} Postman assertions verified against captured responses. Evidence directory: ${path.relative(dir,run)}. Exact request URLs and opaque Search/Result Keys recorded in matrix-results.json.`));
for(const [name,value] of [['collection-file-name',collectionFile],['csv-file-name','expected-outcomes.csv'],['collection-base64',Buffer.from(fs.readFileSync(cf)).toString('base64')],['csv-base64',Buffer.from(csv).toString('base64')]])html=html.replaceAll('&lt;'+name+'&gt;',value).replaceAll('<'+name+'>',value);
assert.ok(!html.includes('&lt;'));
fs.writeFileSync(path.join(dir,'qa-report.html'),html);
fs.writeFileSync(path.join(run,'matrix-results.json'),JSON.stringify({signal,totals,postmanAssertions:checks,rows},null,2));
fs.writeFileSync(path.join(dir,'test-plan-matrix.md'),`# SS-6340 expanded Search → Result matrix\n\n${intended}\n\nFor each CSV row: Search with its exact URL; select results[0]; POST the entire object unchanged; compare itinerary, trip type, passenger counts, fare fields, and returned additional info. Store returned keys.brightsun. Key/token/price equality with Search is allowed. Terminal-error cases are excluded by user instruction.\n\n${tableHeader}${rows.map(r=>'| '+[r.scenario_id,data(r),r.expected,r.actual,r.status].join(' | ')+' |').join('\n')}\n`);
console.log(JSON.stringify({signal,totals,postmanAssertions:checks},null,2));
for(const row of rows) console.log(`${row.scenario_id}: ${row.status} ${row.actual}`);
