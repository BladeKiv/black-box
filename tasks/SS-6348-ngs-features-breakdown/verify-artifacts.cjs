const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const read = name => JSON.parse(fs.readFileSync(path.join(__dirname, name), 'utf8').replace(/^\uFEFF/, ''));
const collection = read('SS-6348.postman_collection.json');
const source = collection.item[0].event.find(e => e.listen === 'test').script.exec.join('\n');
const setup = collection.item[0].event.find(e => e.listen === 'prerequest').script.exec.join('\n');
new vm.Script(setup);
function run(results, variables = {}) {
  const outcomes = [];
  const test = (name, fn) => { try { fn(); outcomes.push('PASS'); } catch { outcomes.push('FAIL'); } };
  test.skip = () => outcomes.push('WARN');
  vm.runInNewContext(source, {
    pm: {response: {json: () => ({results})}, iterationData: {get: key => variables[key]},
      collectionVariables: {get: key => collection.variable.find(v => v.key === key)?.value},
      test, expect: actual => ({to: {eql: expected => assert.equal(JSON.stringify(actual), JSON.stringify(expected))}})},
    console: {log: () => {}}
  });
  return outcomes;
}
const evidence = read('search-evidence.json');
assert.deepEqual(run(evidence), read('test-results.json').cases.slice(0, 2).map(c => c.status));
for (const regression of read('regression-results.json')) {
  const saved = read('regression/' + regression.scenario_id + '.json');
  assert.ok(!saved.request.url.includes('val_cr='));
  assert.deepEqual(run(saved.response.body_excerpt.results, {check_fixture:'false', reference_case_id:regression.scenario_id}), [regression.case.status]);
}
const broken = structuredClone(evidence);
broken.forEach(r => r.ngsFeatures.list.forEach(f => { f.breakdown = ['2:2', '3:1']; }));
assert.deepEqual(run(broken), ['FAIL', 'FAIL']);
// Synthetic checker self-test only; never counted as a live API pass.
const corrected = structuredClone(evidence);
corrected.forEach(r => r.ngsFeatures.list.forEach(f => { f.breakdown = ['1:2', '2:1']; }));
assert.deepEqual(run(corrected), ['PASS', 'PASS']);
assert.deepEqual(run([]), ['WARN', 'WARN']);
const html = fs.readFileSync(path.join(__dirname, 'report.html'), 'utf8');
const template = fs.readFileSync(path.join(__dirname, '../../templates/airapi-qa-dispatch-template.html'), 'utf8');
assert.equal(html.match(/<style>[\s\S]*?<\/style>/)[0].replace(/\r\n/g, '\n'), template.match(/<style>[\s\S]*?<\/style>/)[0].replace(/\r\n/g, '\n'));
for (const filename of ['SS-6348.postman_collection.json', 'SS-6348.expected-outcomes.csv']) {
  const encoded = fs.readFileSync(path.join(__dirname, filename)).toString('base64');
  assert.ok(html.includes(encoded));
}
for (const name of fs.readdirSync(__dirname)) {
  if (!fs.statSync(path.join(__dirname, name)).isFile()) continue;
  const text = fs.readFileSync(path.join(__dirname, name), 'utf8');
  assert.ok(!/Basic\s+[A-Za-z0-9+/]{20,}={0,2}/.test(text), 'Credential-like value in ' + name);
}
console.log('Verified: live evidence matches reported statuses; synthetic bad/good references FAIL/FAIL and PASS/PASS; absent inventory WARN/WARN; template CSS unchanged; embedded downloads match artifacts; no Basic credential values.');
