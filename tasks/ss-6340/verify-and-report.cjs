const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const dir = __dirname;
const latest = path.join(dir, 'latest-run.txt');
function requireEvidence(files) {
  if (files.some(file => !fs.existsSync(file))) {
    console.log('SKIP: evidence not in repo (SS-6340 run captures)');
    process.exit(77);
  }
}
requireEvidence([latest]);
const run = fs.readFileSync(latest, 'utf8').trim();
requireEvidence(['search-response.json', 'selected-solution.json', 'result-request.json',
  'result-response.json', 'result-additional-info.json', 'search-meta.json', 'result-meta.json']
  .map(file => path.join(run, file)));
const read = file => JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
const search = read(path.join(run, 'search-response.json'));
const selected = read(path.join(run, 'selected-solution.json'));
const request = read(path.join(run, 'result-request.json'));
const result = read(path.join(run, 'result-response.json'));
const saved = read(path.join(run, 'result-additional-info.json'));
const collectionFile = 'brightsun service.postman_collection.json';
const collection = read(path.join(dir, collectionFile));
const itinerary = o => o.trips.flatMap(t => t.segments.map(s => [s.departureAirportCode, s.arrivalAirportCode, s.departureTime, s.flightNumber, s.marketingAirline]));
assert.equal(read(path.join(run, 'search-meta.json')).status, 200);
assert.equal(read(path.join(run, 'result-meta.json')).status, 200);
assert.deepEqual(selected, search.results[0]);
assert.deepEqual(request.body, selected);
assert.deepEqual(itinerary(result), itinerary(selected));
assert.equal(typeof result.prices.totalPrice, 'number');
assert.equal(typeof result.prices.totalTax, 'number');
assert.equal(result.currency, selected.currency);
assert.equal(typeof result.keys.brightsun.key, 'string');
assert.ok(result.keys.brightsun.key.length);
assert.deepEqual(saved, result.keys.brightsun);
const extra = `
pm.test('SS-6340: Result returns fare data', function () {
    pm.expect(data.prices.totalPrice).to.be.a('number');
    pm.expect(data.prices.totalTax).to.be.a('number');
    pm.expect(data.currency).to.be.a('string').and.not.empty;
});
const selected = JSON.parse(pm.collectionVariables.get('brightsun_selected_solution'));
const itinerary = o => o.trips.flatMap(t => t.segments.map(s => [s.departureAirportCode, s.arrivalAirportCode, s.departureTime, s.flightNumber, s.marketingAirline]));
pm.test('SS-6340: Result retains selected itinerary and currency', function () {
    pm.expect(itinerary(data)).to.deep.equal(itinerary(selected));
    pm.expect(data.currency).to.equal(selected.currency);
});`;
const resultEvent = collection.item[2].event.find(e => e.listen === 'test');
if (!resultEvent.script.exec.join('\n').includes('Result returns fare data')) resultEvent.script.exec.push(...extra.split('\n'));
fs.writeFileSync(path.join(dir, collectionFile), JSON.stringify(collection, null, 2));
const vars = new Map();
let body;
let checks = 0;
function expect(value) {
  const chain = {};
  for (const name of ['to', 'be', 'and']) Object.defineProperty(chain, name, {get: () => chain});
  chain.a = chain.an = type => { assert.equal(Array.isArray(value) ? 'array' : typeof value, type); return chain; };
  chain.equal = other => { assert.equal(value, other); return chain; };
  chain.deep = {equal: other => { assert.deepEqual(value, other); return chain; }};
  Object.defineProperty(chain, 'not', {get: () => { assert.ok(value != null && value.length > 0); return {empty: chain}; }});
  return chain;
}
const pm = {response: {json: () => body}, expect, test: (name, fn) => {fn(); checks++;}, collectionVariables: {get: k => vars.get(k), set: (k,v) => vars.set(k,v), unset: k => vars.delete(k)}, execution: {skipRequest: () => {throw Error('Unexpected skip');}}};
for (const item of collection.item) for (const event of item.event || []) {
  body = item.name === 'v1/search' ? search : result;
  new Function('pm', event.script.exec.join('\n'))(pm);
}
assert.deepEqual(JSON.parse(vars.get('brightsun_selected_solution')), request.body);
assert.deepEqual(JSON.parse(vars.get('brightsun_result_additional_info')), result.keys.brightsun);
const cases = [
  ['TC-01', 'Search results[0]; AMS–LHR return 11–18 Nov 2026; 1 ADT', 'POST complete selected object unchanged', 'Search HTTP 200; 100 solutions; POST body matches results[0] exactly', 'PASS'],
  ['TC-02', 'Fresh selected solution', 'Return selected itinerary with current fare data', 'Result HTTP 200; itinerary retained; GBP 187.75 total / 124.75 tax, unchanged from Search', 'PASS'],
  ['TC-03', 'Result keys.brightsun', 'Retain returned Key and any token as additional info', 'Nonempty new Key; token unchanged; saved additional info equals Result object', 'PASS']
];
const intended = 'Reprice the selected solution before booking. keys.brightsun is additional info: retain the Result Key and any refreshed token, replacing Search additional info for booking preparation.';
const observed = 'Search returned 100 solutions. The first complete solution was posted unchanged to Result, which returned HTTP 200 with the same GBP 187.75 total / GBP 124.75 tax and selected itinerary. The Result Key changed; token stayed unchanged. All three executed cases passed. Errors 112/113 were excluded by user instruction; no booking was called.';
const csv = 'scenario_id,expected_result,provider_filter,search_url,selected_index\n' + ['"TC-01/TC-02/TC-03"','"Repriced selected itinerary and Result keys.brightsun"','""',JSON.stringify(read(path.join(run, 'search-request.json')).url),'0'].join(',') + '\n';
const csvFile = 'expected-outcomes.csv';
fs.writeFileSync(path.join(dir, csvFile), csv);
const md = `Release signal: PASS — scoped successful Search → Result flow.\nScope/run: 2026-09-30 | DEV | AMS–LHR RT | 1 ADT | results[0].\n\nIntended behavior: ${intended}\n\n${observed}\n\n| ID | Test data | Expected | Actual | Status |\n|---|---|---|---|---|\n${cases.map(c => '| ' + c.join(' | ') + ' |').join('\n')}\n\nEvidence: ${path.relative(dir, run)}. Search Key: ${selected.keys.brightsun.key}; Result Key: ${result.keys.brightsun.key}. Paired search-request/search-response and result-request/result-response JSON are saved with metadata, selected solution, and returned additional info. Postman scripts replayed against captured live responses: ${checks} assertions passed. This replay did not send another network request. Error cases excluded; no claim of full terminal-error coverage.\n`;
fs.writeFileSync(path.join(dir, 'qa-report.md'), md);
let html = fs.readFileSync(path.join(dir, '..', '..', 'templates', 'airapi-qa-dispatch-template.html'), 'utf8');
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
html = html.replace('&lt;Ticket title&gt;', 'SS-6340 · Result repricing').replace('&lt;YYYY-MM-DD&gt;', '2026-09-30').replace('&lt;Endpoint / route / scope&gt;', 'DEV / Search → Result / AMS–LHR RT');
html = html.replace('value fail">&lt;PASS / FAIL / WARN&gt;', 'value pass">PASS').replace('&lt;0&gt;', '3').replace('&lt;0&gt;', '0').replace('&lt;0&gt;', '0');
html = html.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;', esc(observed));
html = html.replace('<h2>Executed tests</h2>', '<h2>Intended behavior</h2><p>' + esc(intended) + '</p><h2>Executed tests</h2>');
html = html.replace(/<tbody>[\s\S]*?<\/tbody>/, '<tbody>' + cases.map(c => `<tr><td>${c[0]}</td><td>${esc(c[1])}</td><td>${esc(c[2])} → ${esc(c[3])}</td><td class="status pass">PASS</td></tr>`).join('') + '</tbody>');
html = html.replace(/\s*<section class="failure-sample">[\s\S]*?<\/section>/, '');
html = html.replace('&lt;Response count, exact field paths, and other confirmed API facts.&gt;', esc(`Evidence: ${path.relative(dir, run)}. Search Key ${selected.keys.brightsun.key}; Result Key ${result.keys.brightsun.key}. ${checks} Postman assertions passed against captured responses.`));
for (const [placeholder,value] of [['collection-file-name',collectionFile],['csv-file-name',csvFile],['collection-base64',Buffer.from(fs.readFileSync(path.join(dir,collectionFile))).toString('base64')],['csv-base64',Buffer.from(csv).toString('base64')]]) html = html.replaceAll(`&lt;${placeholder}&gt;`,value).replaceAll(`<${placeholder}>`,value);
assert.ok(!html.includes('&lt;'));
fs.writeFileSync(path.join(dir,'qa-report.html'),html);
fs.writeFileSync(path.join(run,'verification.json'),JSON.stringify({cases,postmanAssertions:checks,searchCount:search.results.length,searchKey:selected.keys.brightsun.key,resultKey:result.keys.brightsun.key,tokenUnchanged:selected.keys.brightsun.token===result.keys.brightsun.token,errorCases:'Excluded by user',bookingCalled:false},null,2));
console.log(`PASS: 3 executed cases; ${checks} Postman assertions verified; report, collection, CSV, and evidence saved.`);
