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
        calls = []
        private_value = 'dummy-' + 'sensitive-value'
        def transport(url, **kwargs):
            calls.append((url, kwargs))
            return {'http_status': 200, 'body': {'results': [
                {'key': 'opaque+/=', 'meta': {'rank_v2': {'points_diff': 7}}, 'unrelated': private_value}
            ]}, 'transport_error': None, 'reason_code': 'UNEVALUATED'}
        report, folder = execute_job(root, plan, private_value, 'a' * 32, transport=transport)
        assert len(calls) == 3
        assert all(c[1]['verify_tls'] is False and c[1]['tls_bypass_authorized'] for c in calls)
        assert all(c['status'] == 'PASS' for c in report['cases'])
        assert report['base_url'] == scope['base_url']
        for file in folder.iterdir():
            assert private_value not in file.read_text(encoding='utf-8'), file.name
        assert '<' not in report['cases'][0]['id']
        assert (folder / 'qa-report.html').exists()
        assert '2026-10-21' not in (folder / 'qa-report.md').read_text()
        check = r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const collection=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));
const source=collection.item[0].event.find(e=>e.listen==='test').script.exec.join('\n');
const store=new Map();
function run(currency,rows,code=200){
 const outcomes=[];const test=(name,fn)=>{try{fn();outcomes.push('PASS');}catch{outcomes.push('FAIL');}};test.skip=()=>outcomes.push('WARN');
 vm.runInNewContext(source,{pm:{response:{code,json:()=>({results:rows})},iterationData:{get:k=>k==='currency'?currency:0.5},collectionVariables:{set:(k,v)=>store.set(k,v),get:k=>store.get(k)},test,expect:x=>({to:{eql:y=>assert.deepEqual(x,y)}})}});
 return outcomes;
}
const row=n=>[{key:'opaque+/=',meta:{rank_v2:{points_diff:n}}}];
run('USD',row(7));assert.deepEqual(run('GBP',row(7.5)),['PASS']);
assert.deepEqual(run('GBP',row(8)),['FAIL']);
assert.deepEqual(run('GBP',row(7),500),['WARN']);
run('USD',row(7),500);assert.deepEqual(run('INR',row(7)),['WARN']);
'''
        replay = subprocess.run(['node', '-e', check, str(folder / 'collection.json')], capture_output=True)
        assert replay.returncode == 0, 'Postman parity replay failed; output suppressed'
        calls.clear()
        missing, missing_folder = execute_job(root, plan, '', 'b' * 32, transport=transport)
        assert not calls and all(c['status'] == 'WARN' for c in missing['cases'])
        assert all(c['reason_code'] == 'AUTH_MISSING' for c in missing['cases'])
        assert 'Request' in (missing_folder / 'qa-report.html').read_text()
        try:
            execute_job(root, plan, private_value, 'a' * 32, transport=transport)
        except FileExistsError:
            pass
        else:
            assert False, 'historical run overwritten'


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
            job = call('/jobs', {'plan': plan, 'runtime': {'search_authorization': ''}})
            server.worker.shutdown(wait=True)
            result = call('/jobs/' + job['id'])
            assert result['state'] == 'completed'
            assert all(c['status'] == 'WARN' for c in result['report']['cases'])
            assert runtime['access_key'] not in json.dumps(result)
            assert (root / '.qa-service/jobs' / (job['id'] + '.json')).exists()
            assert call('/jobs/' + job['id'] + '/artifacts/results.json')['environment'] == 'STAGE1'
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
            execute_job(root, plan, 'private-fixture', 'c' * 32, transport=transport, cancelled=lambda: bool(calls))
        except JobCancelled:
            pass
        else:
            assert False, 'cancelled job continued'
        assert len(calls) == 1
        captures = json.loads((root / 'tasks/SS-6412-currency-ranking/runs' / ('service-' + 'c' * 32) / 'paired-evidence.json').read_text())
        assert len(captures) == 1, 'partial evidence must survive cancellation'
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
        (output / 'service-plan.json').write_text(json.dumps(plan))
        module = (Path(__file__).resolve().parents[1] / 'integrations/qa-control/hybridService.js').as_uri()
        code = '''
import {readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const {runHybridService}=await import(process.argv[1]);
const root=process.argv[2],scope=JSON.parse(readFileSync(path.join(root,'tasks/SS-6412-currency-ranking/service-scope.json')));
const settings={project_path:root,output_report:path.join(root,'dashboard-output/results.json'),runtime_environment:{search_authorization:''}};
await runHybridService({task:{key:'SS-6412'},settings,scope,onEvent:async()=>{}});
const report=JSON.parse(readFileSync(settings.output_report));
assert.equal(report.cases.length,2);assert.ok(report.cases.every(c=>c.status==='WARN'&&c.reason_code==='AUTH_MISSING'));
const html=readFileSync(path.join(root,'dashboard-output/qa-report.html'),'utf8');
const collection=readFileSync(path.join(root,'dashboard-output/collection.json'));
assert.ok(html.includes(collection.toString('base64')));
'''
        try:
            result = subprocess.run(['node', '--input-type=module', '-e', code, module, str(root)], capture_output=True, timeout=30)
            assert result.returncode == 0, 'Real dashboard-to-Python bridge failed; output suppressed'
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    for test in (test_scope, test_compare, test_job, test_http, test_cancel_restart, test_dashboard_bridge):
        test()
        print(test.__name__ + ': PASS')
