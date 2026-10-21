import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import vm from 'node:vm';

const dir = new URL('./', import.meta.url);
const read = name => fs.readFile(new URL(name, dir), 'utf8');
const files = (await fs.readdir(dir)).sort();
const results = [];
for (const file of files.filter(f => /^results-round-.*\.json$/.test(f))) {
  results.push(...JSON.parse(await read(file)).cases);
}
assert(results.length > 0);
assert(results.every(r => ['PASS', 'FAIL', 'WARN'].includes(r.status)));
const counts = Object.fromEntries(['PASS', 'FAIL', 'WARN'].map(status => [status, results.filter(r => r.status === status).length]));
const signal = counts.FAIL ? 'FAIL' : 'IN PROGRESS';
const escape = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const artifacts = {};
const artifactFiles = ['SS-6332.postman_collection.json', ...files.filter(f => /^expected-outcomes-round-.*\.csv$/.test(f))];
for (const file of artifactFiles) artifacts[file] = {type: file.endsWith('.json') ? 'application/json;charset=utf-8' : 'text/csv;charset=utf-8', content: Buffer.from(await read(file)).toString('base64')};
const evidenceFiles = files.filter(f => /^evidence-round-.*\.json$/.test(f));
const intent = 'Intended behavior: eligible UA options map to G / DEF / GTT. Mapping requires enabled=true and CID OR project eligibility; operating carrier differences do not block it. Ineligible options continue through existing mapping rules.';
const observation = `${counts.PASS} PASS, ${counts.FAIL} FAIL, ${counts.WARN} WARN across ${evidenceFiles.length} Search calls. All 200 UA itineraries matched uniquely between the enabled and disabled runs; 14 WS itineraries kept the same final triple. ${results.filter(r => r.status !== 'PASS').map(r => r.id + ': ' + r.actual).join(' ')} Testing remains in progress; remaining configuration rounds and exact pricing calculations are not certified.`;
const evidence = 'Fields: results[].gds, pcc, cons, validatingCarrier and trips[].segments[].marketingAirline / operatingAirline. NDC markers/assets provide supporting evidence. Baselines match explicit itinerary, fare and passenger attributes; Search keys remain opaque. Configuration snapshots are user-confirmed. Use each CSV only with its corresponding configuration; set authorization locally in Postman. A03 reuses the A01 response.';
let failureHtml = '';
let failureMarkdown = '';
for (const result of results.filter(r => r.status !== 'PASS')) {
  assert(result.evidenceFiles?.length, 'Non-PASS cases require paired evidence');
  for (const file of result.evidenceFiles) {
    const capture = JSON.parse(await read(file));
    assert(capture.request && capture.response);
    const sample = capture.response.results[0];
    const response = {httpStatus: capture.httpStatus, returnedOptions: capture.response.results.length, sample: {validatingCarrier:sample.validatingCarrier,gds:sample.gds,pcc:sample.pcc,cons:sample.cons,fareType:sample.fareType,cabin:sample.cabin,original_info:sample.original_info,trips:sample.trips}};
    const requestText = JSON.stringify(capture.request, null, 2);
    const responseText = JSON.stringify(response, null, 2);
    failureHtml += `<section class="failure-sample"><h2>${escape(result.id)} · ${escape(file)}</h2><p>${escape(result.actual)} · ${escape(capture.started)}</p><h2>Request</h2><pre>${escape(requestText)}</pre><h2>Response · relevant fields, first option</h2><pre>${escape(responseText)}</pre></section>`;
    failureMarkdown += '\n\n### ' + result.id + ' — ' + file + '\n\nRequest\n```json\n' + requestText + '\n```\n\nResponse (relevant fields, first option)\n```json\n' + responseText + '\n```\n';
  }
}
let html = await fs.readFile(new URL('../../templates/airapi-qa-dispatch-template.html', dir), 'utf8');
html = html.replace('<title>AirAPI QA Dispatch</title>', '<title>SS-6332 · QA dispatch</title>')
  .replace('&lt;Ticket title&gt;', 'SS-6332 · UA NDC mapping')
  .replace('&lt;YYYY-MM-DD&gt;', '2026-09-18 · cumulative checks')
  .replace('&lt;Endpoint / route / scope&gt;', 'DEV · GET /v1/search · TST101 · LHR–LAS')
  .replace('value fail">&lt;PASS / FAIL / WARN&gt;', `value ${counts.FAIL ? 'fail' : 'warn'}">${signal}`)
  .replace('value pass">&lt;0&gt;', `value pass">${counts.PASS}`)
  .replace('value fail">&lt;0&gt;', `value fail">${counts.FAIL}`)
  .replace('value warn">&lt;0&gt;', `value warn">${counts.WARN}`)
  .replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;', escape(intent + ' ' + observation))
  .replace(/<tbody>[\s\S]*?<\/tbody>/, '<tbody>' + results.map(r => `<tr><td>${escape(r.id)}</td><td class="test">${escape(r.data)}</td><td>${escape(r.expected)} → ${escape(r.actual)}</td><td class="status ${r.status.toLowerCase()}">${r.status}</td></tr>`).join('') + '</tbody>')
  .replace(/      <section class="failure-sample">[\s\S]*?<\/section>\r?\n/, failureHtml)
  .replace('&lt;Response count, exact field paths, and other confirmed API facts.&gt;', escape(evidence))
  .replace(/<p><button class="download-artifact"[\s\S]*?<\/p>/, '<p>' + artifactFiles.map(file => `<button class="download-artifact" type="button" data-file="${escape(file)}">${escape(file)}</button>`).join('<br>') + '</p>')
  .replace(/const artifacts = \{[\s\S]*?\n    \};/, 'const artifacts = ' + JSON.stringify(artifacts, null, 2) + ';');
assert(!html.includes('&lt;'));
for (const script of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) new vm.Script(script[1]);
for (const artifact of Object.values(artifacts)) assert(html.includes(artifact.content));
await fs.writeFile(new URL('qa-report.html', dir), html);
const markdown = '# SS-6332 — QA dispatch\n\nRelease signal: ' + signal + ' — ' + counts.PASS + ' PASS, ' + counts.FAIL + ' FAIL, ' + counts.WARN + ' WARN across executed checks.\n\nDEV | GET /v1/search | TST101 | LHR–LAS 2026-10-14 | Y / 1 ADT / PUB\n\n' + intent + '\n\n' + observation + '\n\n| ID | Test data | Expected result | Actual result | Status |\n|---|---|---|---|---|\n' + results.map(r => '| ' + [r.id,r.data,r.expected,r.actual,r.status].join(' | ') + ' |').join('\n') + '\n\n' + evidence + '\n\nEvidence files: ' + evidenceFiles.join(', ') + '.\n' + failureMarkdown;
await fs.writeFile(new URL('qa-report.md', dir), markdown);
console.log(JSON.stringify({checks: results.length, calls: evidenceFiles.length, report: 'verified', embeddedArtifacts: artifactFiles.length}));
