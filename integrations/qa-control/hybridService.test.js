import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import {hybridScope,plannerPrompt,runHybridService} from './hybridService.js';

test('planner scope is pinned to selected environment and contains no runtime secrets',t=>{
 const root=mkdtempSync(path.join(os.tmpdir(),'hybrid-'));t.after(()=>rmSync(root,{recursive:true,force:true}));
 const folder=path.join(root,'tasks','SS-6412-currency-ranking');mkdirSync(folder,{recursive:true});
 const scope={ticket:'SS-6412',workflow:'currency_points_diff',environment:'STAGE1',base_url:'https://fixture.invalid',scope_sha256:'fixture',examples:[]};
 writeFileSync(path.join(folder,'service-scope.json'),JSON.stringify(scope));
 const settings={project_path:root,output_report:path.join(root,'run','results.json'),runtime_environment:{name:'STAGE1',base_url:scope.base_url,search_authorization:'private-fixture'}};
 const task={key:'SS-6412',title:'Currency comparison'};
 assert.deepEqual(hybridScope(task,settings),scope);
 assert.equal(hybridScope({key:'SS-9999'},settings),null);
 assert.ok(!plannerPrompt(task,settings,scope).includes('private-fixture'));
 assert.throws(()=>hybridScope(task,{...settings,runtime_environment:{name:'PROD',base_url:scope.base_url}}),/environment/);
});

test('backend submits once, downloads service artifacts and never forwards model credentials',async t=>{
 const root=mkdtempSync(path.join(os.tmpdir(),'hybrid-'));t.after(()=>rmSync(root,{recursive:true,force:true}));
 mkdirSync(path.join(root,'.qa-service'));mkdirSync(path.join(root,'run'));
 const scope={ticket:'SS-6412',workflow:'currency_points_diff',environment:'STAGE1',base_url:'https://fixture.invalid',scope_sha256:'fixture',examples:[]};
 const plan=Object.fromEntries(['ticket','workflow','environment','scope_sha256','examples'].map(k=>[k,scope[k]]));
 writeFileSync(path.join(root,'run','service-plan.json'),JSON.stringify(plan));
 let submissions=0,cancellations=0,failPoll=false;
 const id='a'.repeat(32),report={environment:scope.environment,base_url:scope.base_url,cases:[{status:'WARN'}]};
 const server=http.createServer(async(req,res)=>{
  assert.equal(req.headers.authorization,'Bearer '+'fixture-service-key');
  let result;
  if(req.url==='/health')result={workflows:['SS-6412']};
  else if(req.url==='/jobs'){
   submissions++;let body='';for await(const chunk of req)body+=chunk;
   const data=JSON.parse(body);assert.deepEqual(data.plan,plan);assert.equal(data.runtime.search_authorization,'private-fixture');assert.ok(!body.includes('model-private'));result={id};
  }else if(req.url.endsWith('/cancel')){cancellations++;result={state:'cancellation_requested'};}
  else if(req.url.endsWith('/artifacts/results.json'))result=report;
  else if(failPoll){res.statusCode=503;result={error:'fixture polling failure'};}
  else result={state:'completed',report,artifacts:['results.json']};
  res.setHeader('Content-Type','application/json');res.end(JSON.stringify(result));
 });
 server.listen(0,'127.0.0.1');await new Promise(resolve=>server.once('listening',resolve));t.after(()=>new Promise(resolve=>server.close(resolve)));
 writeFileSync(path.join(root,'.qa-service','runtime.json'),JSON.stringify({url:`http://127.0.0.1:${server.address().port}`,access_key:'fixture-service-key'}));
 const settings={project_path:root,output_report:path.join(root,'run','results.json'),runtime_environment:{search_authorization:'private-fixture'}};
 await runHybridService({task:{key:'SS-6412'},settings,scope,onEvent:async()=>{}});
 assert.equal(submissions,1);assert.deepEqual(JSON.parse(readFileSync(settings.output_report)),report);
 failPoll=true;
 await assert.rejects(runHybridService({task:{key:'SS-6412'},settings,scope,onEvent:async()=>{}}),/503/);
 assert.equal(cancellations,1,'failed polling must cancel the submitted worker job');
});
