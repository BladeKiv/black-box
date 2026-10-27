"""Render ticket-scoped result data with the established dispatch template."""
import base64
import collections
import html
import json
from pathlib import Path


def render(folder):
    folder = Path(folder)
    data = json.loads((folder / 'report-data.json').read_text(encoding='utf-8'))
    rows = data['rows']
    assert rows and all(r['status'] in ('PASS', 'FAIL', 'WARN') for r in rows)
    counts = collections.Counter(r['status'] for r in rows)
    signal = 'FAIL' if counts['FAIL'] else 'WARN' if counts['WARN'] else 'PASS'
    esc = lambda value: html.escape(str(value))
    template = (Path(__file__).parent / 'airapi-qa-dispatch-template.html').read_text(encoding='utf-8')
    template = template.replace('&lt;Ticket title&gt;', esc(data['title']))
    date = data.get('date', '2026-10-21')
    template = template.replace('&lt;YYYY-MM-DD&gt;', esc(date)).replace('&lt;Endpoint / route / scope&gt;', esc(data['scope']))
    template = template.replace('value fail">&lt;PASS / FAIL / WARN&gt;', f'value {signal.lower()}">{signal}')
    for status in ('PASS', 'FAIL', 'WARN'):
        template = template.replace(f'value {status.lower()}">&lt;0&gt;', f'value {status.lower()}">{counts[status]}')
    template = template.replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;', esc(data['summary']) + '<br><br><strong>Intended behavior:</strong> ' + esc(data['intended']))
    start = template.index('        <tr><td>TC-01')
    end = template.index('</tbody>', start)
    template = template[:start] + ''.join(f'<tr><td>{esc(r["id"])}</td><td class="test">{esc(r["data"])}</td><td>{esc(r["expected"])} → {esc(r["actual"])}</td><td class="status {r["status"].lower()}">{r["status"]}</td></tr>' for r in rows) + template[end:]
    start = template.index('      <section class="failure-sample">')
    end = template.index('      <section class="evidence">', start)
    payloads = []
    md_evidence = []
    for evidence in data.get('evidence', []):
        request = json.dumps(evidence['request'], ensure_ascii=False, indent=2)
        response = json.dumps(evidence['response'], ensure_ascii=False, indent=2)
        payloads.append(f'<section class="failure-sample"><h2>{esc(evidence["id"])} · Payload evidence</h2><h2>Request</h2><pre>{esc(request)}</pre><h2>Response</h2><pre>{esc(response)}</pre></section>')
        md_evidence.append(f'### {evidence["id"]}\n\nRequest:\n```json\n{request}\n```\n\nResponse:\n```json\n{response}\n```')
    template = template[:start] + '\n'.join(payloads) + template[end:]
    template = template.replace('&lt;Response count, exact field paths, and other confirmed API facts.&gt;', esc(data['limits']))
    for label, filename in [('collection', data['collection']), ('csv', 'expected-outcomes.csv')]:
        template = template.replace(f'&lt;{label}-file-name&gt;', filename).replace(f'<{label}-file-name>', filename)
        template = template.replace(f'<{label}-base64>', base64.b64encode((folder / filename).read_bytes()).decode())
    assert '&lt;0&gt;' not in template and '<collection-' not in template and '<csv-' not in template
    (folder / 'qa-report.html').write_text(template, encoding='utf-8')
    md = [data['title'], f'\n**{signal} — {counts["PASS"]} PASS / {counts["FAIL"]} FAIL / {counts["WARN"]} WARN**', '\n' + date + ' | ' + data['scope'], '\n' + data['summary'], '\nIntended behavior: ' + data['intended'], '\n| ID | Test data | Expected result | Actual result | Status |', '|---|---|---|---|---|']
    for row in rows:
        md.append('| ' + ' | '.join(str(row[k]).replace('|', '\\|') for k in ('id', 'data', 'expected', 'actual', 'status')) + ' |')
    md.extend(['\nSupporting evidence and rerun artifacts', '\n' + data['limits'], f'\nCollection: {data["collection"]}; CSV: expected-outcomes.csv.'] + md_evidence)
    (folder / 'qa-report.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    return {'signal': signal, **{s: counts[s] for s in ('PASS', 'FAIL', 'WARN')}}
