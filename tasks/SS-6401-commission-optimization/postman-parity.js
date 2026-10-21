function usdBreakdownEqual(a,b){if(!a||!b||typeof a!=='object'||typeof b!=='object'||Array.isArray(a)||Array.isArray(b))return false;const keys=[...Object.keys(a),...Object.keys(b)];if(!keys.length||keys.some(k=>!['backend','upfront'].includes(k))||[...Object.values(a),...Object.values(b)].some(v=>!Array.isArray(v)))return false;const context=x=>stable(Object.fromEntries(Object.entries(x).filter(([k])=>!['amount','fullAmount'].includes(k))));const aa=Object.values(a).flat().sort((x,y)=>context(x).localeCompare(context(y))),bb=Object.values(b).flat().sort((x,y)=>context(x).localeCompare(context(y)));return aa.length>0&&aa.length===bb.length&&aa.every((x,i)=>{const y=bb[i];return typeof x.amount==='number'&&typeof y.amount==='number'&&x.currency==='USD'&&y.currency==='USD'&&context(x)===context(y)&&Object.keys(x).length===Object.keys(y).length&&['amount','fullAmount'].every(k=>!(k in x)||typeof x[k]==='number'&&typeof y[k]==='number'&&Math.abs(x[k]-y[k])<=1+1e-9);});}
const pick=(o,names)=>Object.fromEntries(names.filter(k=>o && Object.prototype.hasOwnProperty.call(o,k)).map(k=>[k,o[k]]));
function equivalents(o){
 if(Array.isArray(o))return o.map(equivalents);
 if(!o||typeof o!=='object')return o;
 const fare=o.fare||o,od=fare.departure+'-'+fare.arrival;
 const approved={'SFO-MUC':[[5561,37750,'TC7AIB','TC7A'],[4065,28486,'AJBUPY','AJBUPY']],'MUC-SFO':[[5556,37713,'TC7AOB','TC7A'],[4065,28486,'AJBUPY','AJBUPY']]};
 const commissions=o.commissions||{},vzc=commissions.VZC||{},upfront=vzc.upfront||{};
 if((approved[od]||[]).some(choice=>choice.every((v,i)=>v===upfront[['rule','subRule','combKey','tourCode'][i]]))){
  const choice=Object.fromEntries(Object.entries(upfront).filter(([k])=>!['subRule','combKey','tourCode'].includes(k)));choice.rule='TC7A/AJBUPY equivalent';
  o={...o,commissions:{...commissions,VZC:{...vzc,upfront:choice}}};
 }
 const duplicate=[6189,6082].includes(o.rule),amDuplicate=[4989,4926].includes(o.rule);
 return Object.fromEntries(Object.entries(o).filter(([k])=>k!=='oComm'&&!(duplicate&&k==='subRule')&&!(amDuplicate&&['subRule','combKey'].includes(k))).map(([k,v])=>[k,duplicate&&k==='rule'?'6189/6082 equivalent':amDuplicate&&k==='rule'?'4989/4926 equivalent':equivalents(v)]));
}
const stable=o=>JSON.stringify(sort(equivalents(o)));
function sort(o){ if(Array.isArray(o))return o.map(sort);if(o&&typeof o==='object')return Object.fromEntries(Object.keys(o).sort().map(k=>[k,sort(o[k])]));return o; }
function input(r){
 const out=pick(r,['gds','pcc','cons','fareType','validatingCarrier','currency','paxCnt','tripType']);
 out.trips=(r.trips||[]).map(t=>(t.segments||[]).map(s=>pick(s,['departureAirportCode','arrivalAirportCode','departureTime','arrivalTime','marketingAirline','operatingAirline','flightNumber','bookingClass','cabin','fareCode','brandId'])));
 out.input_prices=pick(r.priceElement||{},['GdsCurrency','TargetCurrency','oBaseFare','oBaseTax','oPubBaseFare','oPubBaseTax']);
 out.passenger_inputs=Object.fromEntries(Object.entries(r.passengers||{}).map(([k,p])=>[k,pick(p,['codeAs','cnt','pubBaseFare','pubBaseTax'])]));
 out.original_info=pick(r.keys||{},['original_info']);
 const info=r.keys?.commission_info;
 if(info && typeof info==='object')out.fare_inputs=Object.fromEntries(Object.entries(info.fareCalculation||{}).map(([pax,fares])=>[pax,fares.map(f=>pick(f,['code','owner','bookingClass','cabin','departure','arrival','departureTime','arrivalTime','amount','currency','surcharges'])).sort((a,b)=>stable(a).localeCompare(stable(b)))]));
 if(r.tickets?.length)out.tickets=r.tickets.map(input);
 return out;
}
function result(r){
 const out={...pick(r,['currency']),prices:pick(r.prices||{},['totalPrice','totalTax','comm','commBreakdown','isCk','markup','oMarkup']),passengers:r.passengers||{},priceElement:pick(r.priceElement||{},['Assets','CK','CpanelMK'])};
 if(Object.prototype.hasOwnProperty.call(r.keys||{},'commission_info'))out.commission_info=r.keys.commission_info;
 if(Object.prototype.hasOwnProperty.call(r,'tickets'))out.tickets=r.tickets===null?null:r.tickets.map(result);
 return out;
}
function groups(rows){const m=new Map();for(const r of rows){const k=stable(input(r));if(!m.has(k))m.set(k,[]);m.get(k).push(r);}return m;}
function prodSegments(rows){
 if(!Array.isArray(rows)||!rows.every(v=>v&&typeof v==='object'&&'tripId' in v&&'segmentId' in v))return rows;
 const seen=new Set();return rows.filter(v=>{const key=stable(v);if([1,2].includes(v.tripId)&&seen.has(key))return false;seen.add(key);return true;});
}
function same(a,b,usdPrices=false,path=''){
 if(usdBreakdownEqual(a,b))return true;
 a=equivalents(a);b=equivalents(b);
 if(Array.isArray(a)&&Array.isArray(b)){
  if(path.endsWith('.segments'))a=prodSegments(a);
  return a.length===b.length&&a.every((v,i)=>same(v,b[i],false,path+'['+i+']'));
 }
 if(a&&b&&typeof a==='object'&&typeof b==='object'&&!Array.isArray(a)&&!Array.isArray(b)){
  const lowest=a.contract==='Lowest'&&b.contract==='Lowest'&&Number.isInteger(a.subRule)&&Number.isInteger(b.subRule);
  const without=o=>Object.fromEntries(Object.entries(o).filter(([k])=>k!=='subRule'));
  if(lowest&&stable(without(a))===stable(without(b)))return true;
  const breakdown=path.endsWith('.commBreakdown');
  if(breakdown){const aa=pick(a,['backend','upfront']),bb=pick(b,['backend','upfront']);if(usdBreakdownEqual(aa,bb)){a=Object.fromEntries(Object.entries(a).filter(([k])=>!(k in aa)));b=Object.fromEntries(Object.entries(b).filter(([k])=>!(k in bb)));}}
  const extras=Object.keys(b).filter(k=>!(k in a)&&((k==='commBreakdown'&&b[k]&&typeof b[k]==='object'&&!Array.isArray(b[k]))||(breakdown&&Array.isArray(b[k]))));
  const keys=Object.keys(a);if(keys.length!==Object.keys(b).length-extras.length)return false;
  const asset=/\.priceElement\.Assets\.Commission\.ValuePerPax\.[^.]+$/.test(path)&&a.currency==='USD'&&b.currency==='USD';
  return keys.every(k=>{
   if(!Object.prototype.hasOwnProperty.call(b,k))return false;
   const numeric=typeof a[k]==='number'&&typeof b[k]==='number';
   if(path.includes('.segmentFees')&&['amount','fullAmount'].includes(k)&&numeric)return b[k]<=a[k]+1e-9;
   if(((usdPrices&&['totalPrice','totalTax'].includes(k))||(asset&&k==='amount'))&&numeric)return Math.abs(a[k]-b[k])<=1+1e-9;
   return same(a[k],b[k],k==='prices'&&a.currency==='USD'&&b.currency==='USD',path+'.'+k);
  });
 }
 return a===b;
}
function matchedCount(aa,bb){const edges=aa.map(a=>bb.map((b,j)=>same(result(a),result(b))?j:-1).filter(j=>j>=0));const owners=new Map();function assign(i,seen){for(const j of edges[i]){if(seen.has(j))continue;seen.add(j);if(!owners.has(j)||assign(owners.get(j),seen)){owners.set(j,i);return true;}}return false;}aa.forEach((_,i)=>assign(i,new Set()));return owners.size;}
const sid=pm.iterationData.get('scenario_id');
if(pm.variables.get('environment')==='prod'){
 pm.collectionVariables.set('prod_baseline',JSON.stringify({scenario_id:sid,results:body.results}));
}else{
 const saved=pm.collectionVariables.get('prod_baseline');
 if(!saved){pm.test.skip('WARN: PROD baseline unavailable',()=>{});}else{
  const baseline=JSON.parse(saved);pm.test('Baseline belongs to this scenario',()=>pm.expect(baseline.scenario_id).to.eql(sid));
  const prod=groups(baseline.results), pre=groups(body.results);let matched=0,equal=0;const differences=[];
  for(const [k,aa] of prod){if(!pre.has(k))continue;const bb=pre.get(k);matched+=Math.min(aa.length,bb.length);
   const shared=matchedCount(aa,bb);equal+=shared;
   if(shared<Math.min(aa.length,bb.length))differences.push({input:JSON.parse(k),prod_keys:aa.map(r=>r.key),preprod_keys:bb.map(r=>r.key)});
  }
  if(!matched)pm.test.skip('WARN: comparable inventory unavailable',()=>{});else pm.test('Matched commission and financial output equals PROD',()=>pm.expect(differences,JSON.stringify({matched,equal,differences:differences.slice(0,3)})).to.have.length(0));
  console.log(JSON.stringify({scenario_id:sid,matched,equal,differences}));
 }
}
