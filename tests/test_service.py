"""Offline service boundaries and currency comparisons; no AirAPI calls."""
import copy
import hashlib
import json
import tempfile
import threading
import subprocess
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def fixture(root):
    folder = root / 'tasks/SS-6412-currency-ranking'
    folder.mkdir(parents=True)
    (folder / 'ticket-scope.md').write_text('Approved fixture scope', encoding='utf-8')
    scope = {'ticket': 'SS-6412', 'workflow': 'currency_points_diff',
             'title': 'Different rankings on currency switch - investigate.',
             'environment': 'STAGE1', 'base_url': 'https://fixture.example.invalid',
             'scope_sha256': hashlib.sha256((folder / 'ticket-scope.md').read_bytes()).hexdigest(),
             'intended_behavior': 'Exact-key points_diff within 0.5 of USD.',
             'tolerance': 0.5, 'currencies': ['USD', 'GBP', 'INR'],
             'examples': [{'id': 'route-1', 'query': {'cid': 'TST103', 'adt': '1'}}],
             'preparation_exception': 'One fixture route explicitly approved.', 'max_requests': 3}
    (folder / 'service-scope.json').write_text(json.dumps(scope), encoding='utf-8')
    plan = {k: copy.deepcopy(scope[k]) for k in ('ticket', 'workflow', 'environment', 'scope_sha256', 'examples')}
    return scope, plan


def test_scope():
    from bb.search_job import validate_plan
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        scope, plan = fixture(root)
        assert validate_plan(root, plan)['base_url'] == scope['base_url']
        for change in ({'environment': 'PROD'}, {'ticket': '../outside'}, {'scope_sha256': 'stale'},
                       {'examples': [{'id': 'route-2', 'query': {}}]}, {'base_url': 'https://other.invalid'}):
            try:
                validate_plan(root, {**plan, **change})
            except ValueError:
                pass
            else:
                assert False, 'unapproved plan accepted'
        (root / 'tasks/SS-6412-currency-ranking/ticket-scope.md').write_text('Changed scope')
        try:
            validate_plan(root, plan)
        except ValueError:
            pass
        else:
            assert False, 'changed ticket scope accepted'


def test_compare():
    from bb.search_job import compare_points
    def result(key, score):
        return {'key': key, 'meta': {'rank_v2': {'points_diff': score}}}
    base = [result('opaque+/= A', 10), result('other', 2)]
    assert compare_points(base, [result('opaque+/= A', 10.5)], 0.5)['status'] == 'PASS'
    assert compare_points(base, [result('opaque+/= A', 10.51)], 0.5)['status'] == 'FAIL'
    for target in ([], [result('different', 10)], [result('opaque+/= A', None)],
                   [result('opaque+/= A', True)], [result('opaque+/= A', float('nan'))],
                   [result('opaque+/= A', 10), result('opaque+/= A', 10)]):
        assert compare_points(base, target, 0.5)['status'] == 'WARN'
    assert compare_points(base, [result('opaque+/= A', 10)], 0.5)['matched'] == 1


def test_job():
    from bb.search_job import execute_job
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        scope, plan = fixture(root)
        folder = root / 'tasks/SS-6412-currency-ranking/runs' / ('service-' + 'a' * 32)
        calls = []
        private_value = 'dummy-sensitive-value'
        def transport(url, **kwargs):
            planned = json.loads((folder / 'cases.json').read_text())
            assert [c['case_id'] for c in planned['cases']] == ['TC-1', 'TC-2']
            if len(calls) == 2:
                lines = (folder / 'results.jsonl').read_text().splitlines()
                assert len(lines) == 1, 'GBP comparison must be appended before INR request'
            calls.append((url, kwargs))
            return {'http_status': 200, 'body': {'results': [
                {'key': 'opaque+/=', 'meta': {'rank_v2': {'points_diff': 7}}, 'unrelated': private_value}
            ]}, 'reason_code': 'UNEVALUATED'}
        report, folder = execute_job(root, plan, private_value, 'a' * 32, transport=transport, base_url=scope['base_url'])
        assert len(calls) == 3
        assert all(c[1]['verify_tls'] is False and c[1]['tls_bypass_authorized'] for c in calls)
        assert report['status'] == 'passed'
        assert set(p.name for p in folder.iterdir()) == {'cases.json', 'results.jsonl'}
        rows = [json.loads(line) for line in (folder / 'results.jsonl').read_text().splitlines()]
        assert all(set(c) == {'case_id', 'status', 'duration_ms', 'actual'} for c in rows)
        assert all(c['status'] == 'passed' and c['duration_ms'] >= 0 for c in rows)
        assert private_value not in ''.join(p.read_text() for p in folder.iterdir())
        missing, _ = execute_job(root, plan, '', 'b' * 32, transport=transport, base_url=scope['base_url'])
        assert len(calls) == 3 and missing['status'] == 'need_action'
        assert all(c['action_needed'] for c in missing['cases'])
        try:
            execute_job(root, plan, private_value, 'a' * 32, transport=transport, base_url=scope['base_url'])
        except FileExistsError:
            pass
        else:
            assert False, 'historical run overwritten'


def test_failure_stream():
    from bb.search_job import execute_job
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        scope, plan = fixture(root)
        scope['examples'][0]['query']['cid'] = 'x' * 6000
        plan['examples'] = copy.deepcopy(scope['examples'])
        (root / 'tasks/SS-6412-currency-ranking/service-scope.json').write_text(json.dumps(scope))
        def transport(url, **kwargs):
            score = 9 if 'currency=GBP' in url else 7
            return {'http_status': 200, 'reason_code': 'OK', 'body': {'results': [
                {'key': 'opaque-' + str(i) + chr(233) * 100, 'meta': {'rank_v2': {'points_diff': score}}}
                for i in range(100)]}}
        report, folder = execute_job(root, plan, 'private-fixture', 'e' * 32, transport=transport, base_url=scope['base_url'])
        assert report['status'] == 'failed'
        failed, passed = report['cases']
        assert failed['status'] == 'failed' and passed['status'] == 'passed'
        failure = failed['failure']
        assert len(json.dumps(failure, ensure_ascii=False).encode()) <= 8192
        for side in ('request', 'response'):
            excerpt = failure[side]['body_excerpt']
            assert len(excerpt.encode()) <= 2048
        assert '[truncated ' in failure['response']['body_excerpt']
        assert 'failure' not in passed


def test_http():
    from bb.service import create_server
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _, plan = fixture(root)
        server = create_server(root, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        runtime = json.loads((root / '.qa-service/runtime.json').read_text())
        def call(path, data=None, authenticated=True, origin=None):
            headers = {'Content-Type': 'application/json'}
            if authenticated:
                headers['Authorization'] = 'Bearer ' + runtime['access_key']
            if origin:
                headers['Origin'] = origin
            req = Request(runtime['url'] + path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
            return json.loads(urlopen(req, timeout=5).read())
        try:
            assert call('/health')['status'] == 'ready'
            try:
                create_server(root, port=0)
            except ValueError:
                pass
            else:
                assert False, 'second service writer accepted'
            for path, origin in (('/health', None), ('/health', 'https://other.invalid')):
                try:
                    call(path, authenticated=bool(origin), origin=origin)
                except HTTPError as error:
                    assert error.code in (401, 403)
                else:
                    assert False, 'unauthenticated/cross-origin request accepted'
            job = call('/jobs', {'plan': plan, 'runtime': {'search_authorization': '', 'base_url': 'https://fixture.example.invalid'}})
            server.worker.shutdown(wait=True)
            result = call('/jobs/' + job['id'])
            assert result['state'] == 'completed'
            assert all(c['status'] == 'need_action' for c in result['report']['cases'])
            assert runtime['access_key'] not in json.dumps(result)
            assert (root / '.qa-service/jobs' / (job['id'] + '.json')).exists()
            assert call('/jobs/' + job['id'] + '/artifacts/cases.json')['environment'] == 'STAGE1'
            try:
                call('/jobs', {'plan': {**plan, 'environment': 'PROD'}})
            except HTTPError as error:
                assert error.code == 400
            else:
                assert False, 'wrong environment accepted'
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


def test_cancel_restart():
    from bb.search_job import execute_job, JobCancelled
    from bb.service import create_server
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _, plan = fixture(root)
        calls = []
        def transport(url, **kwargs):
            calls.append(url)
            return {'http_status': 200, 'body': {'results': []}, 'reason_code': 'NO_DATA'}
        try:
            execute_job(root, plan, 'private-fixture', 'c' * 32, transport=transport, cancelled=lambda: bool(calls), base_url='https://fixture.example.invalid')
        except JobCancelled:
            pass
        else:
            assert False, 'cancelled job continued'
        assert len(calls) == 1
        rows = (root / 'tasks/SS-6412-currency-ranking/runs' / ('service-' + 'c' * 32) / 'results.jsonl').read_text().splitlines()
        assert len(rows) == 2 and all(json.loads(row)['status'] == 'need_action' for row in rows)
        jobs = root / '.qa-service/jobs'
        jobs.mkdir(parents=True)
        job_file = jobs / ('d' * 32 + '.json')
        job_file.write_text(json.dumps({'id': 'd' * 32, 'state': 'running', 'ticket': 'SS-6412'}))
        server = create_server(root, port=0)
        try:
            assert json.loads(job_file.read_text())['state'] == 'interrupted'
        finally:
            server.server_close()


def test_dashboard_bridge():
    from bb.service import create_server
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        scope, plan = fixture(root)
        server = create_server(root, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        output = root / 'dashboard-output'
        output.mkdir()
        plans = root / '.qa-service/plans'
        plans.mkdir()
        (plans / (hashlib.sha256(str(output / 'results.json').encode()).hexdigest() + '.json')).write_text(json.dumps(plan))
        module = (Path(__file__).resolve().parents[1] / 'integrations/qa-control/hybridService.js').as_uri()
        code = '''
import {readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const {runHybridService}=await import(process.argv[1]);
const root=process.argv[2],scope=JSON.parse(readFileSync(path.join(root,'tasks/SS-6412-currency-ranking/service-scope.json')));
const settings={project_path:root,output_report:path.join(root,'dashboard-output/results.json'),runtime_environment:{search_authorization:'',base_url:scope.base_url}};
await runHybridService({task:{key:'SS-6412'},settings,scope,onEvent:async()=>{}});
const planned=JSON.parse(readFileSync(path.join(root,'dashboard-output/cases.json')));
const rows=readFileSync(path.join(root,'dashboard-output/results.jsonl'),'utf8').trim().split('\\n').map(JSON.parse);
assert.equal(planned.cases.length,2);assert.ok(rows.every(c=>c.status==='need_action'&&c.action_needed));
'''
        try:
            result = subprocess.run(['node', '--input-type=module', '-e', code, module, str(root)], capture_output=True, timeout=30)
            assert result.returncode == 0, 'Real dashboard-to-Python bridge failed; output suppressed'
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    for test in (test_scope, test_compare, test_job, test_failure_stream, test_http, test_cancel_restart, test_dashboard_bridge):
        test()
        print(test.__name__ + ': PASS')
