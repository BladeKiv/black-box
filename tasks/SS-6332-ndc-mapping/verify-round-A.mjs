import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import vm from 'node:vm';
const read = name => fs.readFile(new URL(name, import.meta.url), 'utf8');
const ua=JSON.parse(await read('evidence-round-A-UA.json')).response.results;
const ws=JSON.parse(await read('evidence-round-A-WS.json')).response.results;
const triple=r=>({gds:r.gds,pcc:r.pcc,cons:r.cons});
const target={gds:'G',pcc:'DEF',cons:'GTT'};
assert(ua.length>0 && ws.length>0);
for(const r of ua){assert.equal(r.validatingCarrier,'UA');assert.deepEqual(triple(r),target);assert.equal(r.ndcMapped,true);assert(r.trips.flatMap(t=>t.segments).every(s=>s.marketingAirline==='UA'));}
for(const r of ws){assert.equal(r.validatingCarrier,'WS');assert.notDeepEqual(triple(r),target);assert.notEqual(r.ndcMapped,true);}
const codeshares=ua.filter(r=>r.trips.some(t=>t.segments.some(s=>s.operatingAirline!=='UA')));assert(codeshares.length>0);
const collectionText=await read('SS-6332.postman_collection.json');
const collection=JSON.parse(collectionText);
assert.equal(collection.info.schema,'https://schema.getpostman.com/json/collection/v2.1.0/collection.json');
for(const item of collection.item) for(const event of item.event) new vm.Script(event.script.exec.join('\n'));
const html=await read('qa-report.html');assert(!html.includes('&lt;'));assert(!html.includes('<collection-base64>'));
for(const script of html.matchAll(/<script>([\s\S]*?)<\/script>/g))new vm.Script(script[1]);
assert(html.includes(Buffer.from(collectionText).toString('base64')));
assert(html.includes(Buffer.from(await read('expected-outcomes.csv')).toString('base64')));
console.log(JSON.stringify({UA:ua.length,WS:ws.length,codeshares:codeshares.length,mappingChecks:'PASS',artifactStructure:'PASS'}));
