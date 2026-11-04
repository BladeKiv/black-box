const row = pm.iterationData;
function value(name) { return row.get(name) ?? pm.variables.get(name); }
function at(obj, path) { return String(path).split('.').reduce((a, k) => a == null ? undefined : a[k], obj); }
const body = pm.response.json();
pm.test('Search exposes results[]', () => pm.expect(body.results).to.be.an('array'));
const childPath = value('children_path');
const markerPath = value('upgrade_path');
const upg = o => at(o, markerPath) !== undefined;
const groups = body.results.filter(r => upg(r) || (at(r, childPath) || []).some(upg));
if (!groups.length) {
  console.warn('WARN/NO_DATA: no qualifying UPG groups; merge checks cannot be evaluated.');
  pm.test.skip('Qualifying merge inventory is available', () => {});
} else {
  const keepBoth = String(value('keepBothBagOptions')) === 'true';
  const vectors = o => [at(o,value('bags_path')), at(o,value('exchange_path')), at(o,value('refund_path'))];
  const price = o => at(o,value('price_path'));
  const signature = o => JSON.stringify((o.trips || []).map(t => (t.segments || []).map(s => [s.departureAirportCode,s.arrivalAirportCode,s.departureTime,s.arrivalTime,s.marketingAirline,s.flightNumber])));
  pm.test('Retained groups follow the scoped merge rules', () => {
    for (const main of groups) {
      const children = at(main,childPath) || [];
      pm.expect(children).to.be.an('array');
      const options = [main,...children];
      for (let i=0;i<options.length;i++) {
        const o=options[i], f=vectors(o);
        pm.expect(f[0]).to.be.a('number');
        pm.expect(f[1]).to.be.a('boolean');
        pm.expect(f[2]).to.be.a('boolean');
        pm.expect(price(o)).to.be.a('number');
        pm.expect(o.currency).to.equal(main.currency);
        if (children.length) pm.expect(o.gdsOfferId.endsWith(':NGS#'+(i+1))).to.equal(true);
        if (i) {
          const previous=options[i-1], pf=vectors(previous);
          pm.expect(price(o)).to.be.at.least(price(previous));
          pm.expect(f.every((x,j)=>x>=pf[j]) && f.some((x,j)=>x>pf[j])).to.equal(true);
          pm.expect(signature(o)).to.equal(signature(main));
          if (!keepBoth) pm.expect(upg(o)).to.equal(false);
        }
      }
    }
  });
  const regularMainCount=groups.filter(g=>!upg(g)).length;
  if (!regularMainCount) {
    console.warn('WARN/NO_DATA: regular-cheapest branch unavailable.');
    pm.test.skip('Regular-cheapest branch has qualifying inventory',()=>{});
  }
  console.warn('Coverage limit: returned groups do not expose the complete pre-filter candidate set.');
}
