const fs=require('fs'),assert=require('assert');
const script=fs.readFileSync(__dirname+'/postman-parity.js','utf8');
const evidence=__dirname+'/runs/TSTCOM/evidence/TC-01/1/prod/response.json';
if(!fs.existsSync(evidence)){
 console.log('SKIP: evidence not in repo (SS-6401 Postman response fixture)');
 process.exit(77);
}
const fixture=JSON.parse(fs.readFileSync(evidence,'utf8')).results[0];
function check(mutate){
 const vars=new Map(), results=[]; let env='prod';
 const pm={iterationData:{get:()=> 'test'},variables:{get:()=>env},collectionVariables:{set:(k,v)=>vars.set(k,v),get:k=>vars.get(k)},expect:x=>({to:{eql:y=>assert.deepStrictEqual(x,y),have:{length:n=>assert.strictEqual(x.length,n)}}}),test:(name,fn)=>{try{fn();results.push({name,pass:true});}catch(e){results.push({name,pass:false});}}};
 pm.test.skip=name=>results.push({name,skip:true});
 const run=new Function('pm','body','console',script);
 run(pm,{results:[fixture]},{log:()=>{}}); env='preprod';const other=structuredClone(fixture);mutate(other);
 run(pm,{results:[other]},{log:()=>{}});return results;
}
assert(check(r=>r.key='another-opaque').every(r=>r.pass));
assert(check(r=>r.prices.comm=999).some(r=>r.pass===false));
assert(check(r=>r.priceElement.oBaseFare={ADT:999}).some(r=>r.skip));
console.log('Postman comparator: opaque-key, changed-amount, unmatched-input checks passed');

for(const field of ['totalPrice','totalTax']){
 assert(check(r=>r.prices[field]+=1).every(r=>r.pass));
 assert(check(r=>r.prices[field]+=1.01).some(r=>r.pass===false));
 assert(check(r=>r.tickets[0].prices[field]+=1).every(r=>r.pass));
}
console.log('Postman USD total price/tax: inclusive $1, rejected $1.01, nested-ticket checks passed');

const reviewedSame=new Function(script.split('const sid=')[0]+';return same;')();
const segment=(tripId,segmentId)=>({tripId,segmentId});
for(const trip of [1,2]){
 assert(reviewedSame({segments:[segment(trip,1),segment(trip,1)]},{segments:[segment(trip,1)]}));
 assert(!reviewedSame({segments:[segment(trip,1)]},{segments:[segment(trip,1),segment(trip,1)]}));
}
const fee=n=>({segmentFees:{amount:n,fullAmount:n,currency:'USD',rule:4933}});
assert(reviewedSame(fee(35),fee(15)));assert(!reviewedSame(fee(15),fee(35)));
assert(reviewedSame({}, {commBreakdown:{upfront:[{amount:15,currency:'USD'}]}}));
assert(!reviewedSame({commBreakdown:{upfront:[{amount:15,currency:'USD'}]}}, {}));
const amA={rule:4989,subRule:34186,combKey:'AMOTHER',amount:41.65},amB={rule:4926,subRule:33655,combKey:'AMNONJV',amount:41.65};
assert(reviewedSame(amA,amB));assert(!reviewedSame(amA,{...amB,amount:42}));
const asset=n=>({priceElement:{Assets:{Commission:{ValuePerPax:{ADT:{amount:n,currency:'USD'}}}}}});
assert(reviewedSame(asset(167.56),asset(168.56)));assert(!reviewedSame(asset(167.56),asset(168.57)));
console.log('Postman reviewed PROD exceptions and reverse-direction guards passed');

const f90Fare=(rule,subRule,combKey,tourCode,amount=100,departure='SFO',arrival='MUC')=>({departure,arrival,commissions:{VZC:{upfront:{rule,subRule,combKey,tourCode,amount,fullAmount:amount,currency:'CAD',percent:[10]}}}});
assert(reviewedSame(f90Fare(5561,37750,'TC7AIB','TC7A'),f90Fare(4065,28486,'AJBUPY','AJBUPY')));
assert(!reviewedSame(f90Fare(5561,37750,'TC7AIB','TC7A'),f90Fare(4065,28486,'AJBUPY','AJBUPY',101)));
assert(!reviewedSame(f90Fare(5561,37750,'TC7AIB','TC7A',100,'JFK','MUC'),f90Fare(4065,28486,'AJBUPY','AJBUPY',100,'JFK','MUC')));
assert(reviewedSame(f90Fare(5556,37713,'TC7AOB','TC7A',100,'MUC','SFO'),f90Fare(4065,28486,'AJBUPY','AJBUPY',100,'MUC','SFO')));
console.log('Postman F-90 OD-scoped equal-amount choice checks passed');
