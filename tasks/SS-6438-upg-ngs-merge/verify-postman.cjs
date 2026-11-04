// Replay the collection assertions against saved responses; no HTTP requests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = process.argv[2] || __dirname;
const collection = JSON.parse(fs.readFileSync(path.join(root,'collection.json'),'utf8'));
const analysisFile = fs.existsSync(path.join(root,'analysis.json')) ? 'analysis.json' : 'all-cases-analysis.json';
const analysis = JSON.parse(fs.readFileSync(path.join(root,analysisFile),'utf8'));
const failures=[];
let passed=0, skipped=0;
function expect(actual) {
  const api={equal:expected=>assert.equal(actual,expected),least:minimum=>assert.ok(actual>=minimum),a:type=>assert.equal(typeof actual,type),an:type=>assert.ok(type==='array' && Array.isArray(actual))};
  api.to=api;api.be=api;api.at=api;
  return api;
}
for(const run of analysis.runs) {
  const capture=JSON.parse(fs.readFileSync(path.join(root,run.scenario_id+'.json'),'utf8'));
  const row={scenario_id:run.scenario_id,search_url:capture.request.url,expected_result:'retained merge rules',keepBothBagOptions:String(run.keepBothBagOptions),bags_path:'keys.baggage.allowPieces',exchange_path:'penalties.exchange',refund_path:'penalties.refund',price_path:'prices.totalPrice',children_path:'ngsItineraries',upgrade_path:'keys.upgrade_info'};
  const local={};
  const test=(name,fn)=>{try{fn();passed++;}catch(error){failures.push({scenario:run.scenario_id,test:name,error:error.message});}};
  test.skip=()=>skipped++;
  const pm={iterationData:{get:key=>row[key]},variables:{get:key=>local[key],set:(key,value)=>local[key]=value},response:{json:()=>capture.response.body},expect,test};
  for(const event of collection.item[0].event)vm.runInNewContext(event.script.exec.join('\n'),{pm,console:{warn(){}}});
}
const expectedScenarios=[...new Set(analysis.failing_groups.map(x=>x.scenario_id))].sort();
assert.deepEqual(failures.map(x=>x.scenario).sort(),expectedScenarios);
console.log(JSON.stringify({saved_responses:analysis.runs.length,assertions_passed:passed,assertions_failed:failures.length,inventory_checks_skipped:skipped,failed_scenarios:failures.map(x=>x.scenario)}));
