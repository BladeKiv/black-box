"""Local authenticated QA worker. Run: python -B -m bb.service."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets
import threading
import uuid

from .search_job import ARTIFACTS, ROOT, JobCancelled, execute_job, validate_plan, ticket_folder


class LocalServer(ThreadingHTTPServer):
    worker = None
    instance_lock = None

    def server_close(self):
        super().server_close()
        if self.worker:
            self.worker.shutdown(wait=True)
        if self.instance_lock:
            self.instance_lock.close()
            self.instance_lock = None


def instance_lock(state):
    """OS-released lock: one hosting writer even when a different port is chosen."""
    handle = (state / 'worker.lock').open('a+b')
    handle.seek(0, 2)
    if handle.tell() == 0:
        handle.write(b'0')
        handle.flush()
    handle.seek(0)
    try:
        import os
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise ValueError('A QA service already owns this project') from None
    return handle


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def create_server(root=ROOT, port=8766):
    root = Path(root).resolve()
    state = root / '.qa-service'
    state.mkdir(exist_ok=True)
    state.chmod(0o700)
    singleton = instance_lock(state)
    jobs_dir = state / 'jobs'
    jobs_dir.mkdir(exist_ok=True)
    jobs, scopes, cancellations = {}, {}, {}
    # Startup snapshots prevent the planner from widening execution scope mid-session.
    for path in (root / 'tasks').glob('*/service-scope.json'):
        scope = json.loads(path.read_text(encoding='utf-8'))
        plan = {k: scope[k] for k in ('ticket', 'workflow', 'environment', 'scope_sha256', 'examples')}
        scopes[scope['ticket']] = validate_plan(root, plan)
    # Claim the port before touching persisted jobs: a second instance must not
    # mark the active instance's jobs interrupted.
    try:
        server = LocalServer(('127.0.0.1', port), BaseHTTPRequestHandler)
    except OSError:
        singleton.close()
        raise
    server.instance_lock = singleton
    for path in jobs_dir.glob('*.json'):
        record = json.loads(path.read_text(encoding='utf-8'))
        if record['state'] in ('queued', 'running'):
            record.update(state='interrupted', error='Service restarted; job was not retried. Review any partial evidence before submitting a new run.')
            write_json(path, record)
        jobs[record['id']] = record
    access_key = secrets.token_urlsafe(32)
    lock = threading.Lock()
    slots = threading.BoundedSemaphore(8)
    worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix='qa-job')

    def save(record):
        jobs[record['id']] = record
        write_json(jobs_dir / (record['id'] + '.json'), record)

    def run(job_id, plan, credential, base_url):
        try:
            with lock:
                save({**jobs[job_id], 'state': 'running'})
            if validate_plan(root, plan) != scopes[plan['ticket']]:
                raise ValueError('Service scope changed since startup; review and restart the service')
            report, folder = execute_job(root, plan, credential, job_id, cancelled=cancellations[job_id].is_set, base_url=base_url)
            with lock:
                save({**jobs[job_id], 'state': 'completed', 'report': report,
                      'artifacts': list(ARTIFACTS), 'folder': str(folder.relative_to(root))})
        except JobCancelled:
            with lock:
                save({**jobs[job_id], 'state': 'cancelled', 'error': 'Cancelled between requests; partial evidence retained; no automatic retry.'})
        except Exception:
            # Never return exception text which may contain response/credential data.
            with lock:
                save({**jobs[job_id], 'state': 'failed', 'error': 'Job could not complete. Inspect local scope and any partial artifacts; no automatic retry.'})
        finally:
            credential = None
            slots.release()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def send(self, status, body, mime='application/json'):
            data = body if isinstance(body, bytes) else json.dumps(body, allow_nan=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(data)

        def authorized(self):
            if self.headers.get('Origin') or self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
                self.send(403, {'error': 'Only local backend clients are allowed'})
                return False
            if not hmac.compare_digest(self.headers.get('Authorization', '').encode('utf-8'), ('Bearer ' + access_key).encode('ascii')):
                self.send(401, {'error': 'Service authentication required'})
                return False
            return True

        def do_GET(self):
            if not self.authorized():
                return
            if self.path == '/health':
                self.send(200, {'status': 'ready', 'version': 1, 'workflows': list(scopes), 'workers': 1})
                return
            match = re.fullmatch(r'/jobs/([a-f0-9]{32})(?:/artifacts/([A-Za-z0-9_.-]+))?', self.path)
            if not match:
                self.send(404, {'error': 'Unknown resource'})
                return
            with lock:
                record = jobs.get(match[1])
            if not record:
                self.send(404, {'error': 'Unknown job'})
                return
            filename = match[2]
            if filename:
                if filename not in ARTIFACTS:
                    self.send(404, {'error': 'Artifact unavailable'})
                    return
                folder = record.get('folder') or str((ticket_folder(root, record['ticket']) / 'runs' / ('service-' + record['id'])).relative_to(root))
                path = (root / folder / filename).resolve()
                if not path.is_relative_to(root) or not path.is_file():
                    self.send(404, {'error': 'Artifact unavailable'})
                    return
                mime = 'application/json' if filename.endswith('.json') else 'text/html; charset=utf-8' if filename.endswith('.html') else 'text/plain; charset=utf-8'
                self.send(200, path.read_bytes(), mime)
            else:
                folder = root / record.get('folder', str((ticket_folder(root, record['ticket']) / 'runs' / ('service-' + record['id'])).relative_to(root)))
                available = [name for name in ARTIFACTS if (folder / name).is_file()]
                self.send(200, {**record, 'available_artifacts': available})

        def do_POST(self):
            if not self.authorized():
                return
            cancel = re.fullmatch(r'/jobs/([a-f0-9]{32})/cancel', self.path)
            if cancel:
                with lock:
                    record = jobs.get(cancel[1])
                    if record and record['state'] in ('queued', 'running'):
                        cancellations[cancel[1]].set()
                self.send(202 if record else 404, {'state': 'cancellation_requested' if record else 'unknown'})
                return
            if self.path != '/jobs':
                self.send(404, {'error': 'Unknown resource'})
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 128 * 1024 or self.headers.get_content_type() != 'application/json':
                    raise ValueError('JSON request must be between 1 byte and 128 KiB')
                data = json.loads(self.rfile.read(size), parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
                if not isinstance(data, dict) or set(data) - {'plan', 'runtime'}:
                    raise ValueError('Only plan and runtime are accepted')
                plan = data.get('plan')
                scope = validate_plan(root, plan)
                if scopes.get(scope['ticket']) != scope:
                    raise ValueError('Scope was not registered at service startup')
                runtime = data.get('runtime', {})
                if not isinstance(runtime, dict) or set(runtime) - {'search_authorization', 'base_url'}:
                    raise ValueError('Only runtime Search authentication is accepted')
                base_url = runtime.get('base_url', '')
                if not isinstance(base_url, str) or base_url.rstrip('/') != scope['base_url'].rstrip('/'):
                    raise ValueError('Selected runtime base URL must match scope')
                credential = runtime.get('search_authorization', '')
                if not isinstance(credential, str) or len(credential) > 8192 or '\r' in credential or '\n' in credential:
                    raise ValueError('Invalid runtime authentication format')
            except (ValueError, TypeError, KeyError, OSError):
                self.send(400, {'error': 'Plan/runtime rejected. Match the registered service-scope.json and requested environment; credentials belong only in runtime.'})
                return
            if not slots.acquire(blocking=False):
                self.send(429, {'error': 'Queue full; no requests executed'})
                return
            record = {'id': uuid.uuid4().hex, 'state': 'queued', 'ticket': plan['ticket'], 'environment': plan['environment']}
            with lock:
                cancellations[record['id']] = threading.Event()
                save(record)
            worker.submit(run, record['id'], plan, credential, base_url)
            self.send(202, record)

    server.RequestHandlerClass = Handler
    server.worker = worker
    runtime_path = state / 'runtime.json'
    write_json(runtime_path, {'url': f'http://127.0.0.1:{server.server_port}', 'access_key': access_key, 'version': 1})
    runtime_path.chmod(0o600)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    server = create_server(port=args.port)
    print(f'QA service listening on 127.0.0.1:{server.server_port}; one worker; no job submitted.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.worker.shutdown(wait=True)


if __name__ == '__main__':
    main()
