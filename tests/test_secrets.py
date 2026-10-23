"""Scanner checks use constructed dummy strings, never real credentials."""
import subprocess
import json
import base64
import tempfile
import shutil
from pathlib import Path


def test_scanner():
    from scripts.check_secrets import scan_text, scan_bytes, scan_staged, scan_history
    value = 'dummy' + '-sensitive-value'
    assert any(f['type'] == 'authorization' for f in scan_text('Author' + 'ization: ' + 'Bearer ' + value))
    assert scan_text('"bookpass": "' + value + '"')
    assert scan_text('"firstName": "' + 'Example' + '"')
    assert scan_text(json.dumps({'type': 'session_' + 'meta', 'payload': {}}))
    assert any(f['type'] == 'local_path' for f in scan_text('C:/' + 'Users/example/local'))
    assert not scan_text('"bookpass": "{{bookpass}}"')
    assert scan_text(json.dumps([{'key': 'book' + 'pass', 'value': value}]))
    assert not scan_text('Fare label: Basic Economy')
    encoded = base64.b64encode(('example:' + value).encode()).decode()
    assert scan_text('Basic ' + encoded)
    header = 'Author' + 'ization'
    assert not scan_text("headers." + header + "='Basic '+Buffer.from(process.env.BOOKING_USERNAME)")
    assert not scan_text("headers={'" + header + "': vals['search_authorization']}")
    assert not scan_text(json.dumps({'token': 'INVALID_TEST_TOKEN'}))
    embedded = base64.b64encode(json.dumps({'token': value}).encode()).decode()
    assert any(f['type'] == 'embedded_credential' for f in scan_bytes(('<script>const data="' + embedded + '";</script>').encode()))
    with tempfile.TemporaryDirectory() as tmp:
        def git(*args):
            return subprocess.run(['git', '-C', tmp, *args], check=True, capture_output=True)
        git('init')
        path = Path(tmp) / 'sample.txt'
        path.write_text('password = "' + value + '"', encoding='utf-8')
        git('add', 'sample.txt')
        assert scan_staged(Path(tmp))
        path.write_text('clean worktree', encoding='utf-8')
        assert scan_staged(Path(tmp)), 'must inspect index, not working copy'
        git('-c', 'user.name=Scanner Test', '-c', 'user.email=scanner@example.invalid', 'commit', '-m', 'test fixture')
        path.write_text('clean history tip', encoding='utf-8')
        git('add', 'sample.txt')
        git('-c', 'user.name=Scanner Test', '-c', 'user.email=scanner@example.invalid', 'commit', '-m', 'clean tip')
        assert scan_history(Path(tmp)), 'must scan old blobs too'


def test_assignment_formats():
    from scripts.check_secrets import scan_bytes
    value = 'dummy' + '-sensitive-value'
    encoded = base64.b64encode(('example:' + value).encode()).decode()
    field = 'to' + 'ken'
    positives = [
        field + ' = "' + value + '"', field + ': ' + value, field.upper() + '=' + value,
        "apiKey: '" + value + "'", '$token = "' + value + '"',
        'Authorization: Bearer ' + value, 'Basic ' + encoded,
        '"token": "' + value + '"', 'token\t=\t"' + value + '"',
    ]
    negatives = [
        'token = {{token}}', 'token: "{{token}}"', 'TOKEN=process.env.X',
        "apiKey: 'INVALID_TEST_TOKEN'", 'token = os.environ["TOKEN"]',
        'Authorization: Bearer {{token}}', 'Authorization: Bearer INVALID_TEST_TOKEN',
        'Authorization: Basic {{token}}', 'Bearer process.env.X',
        'Fare label: Basic Economy', 'token == other',
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for suffix in ('.py', '.cjs', '.mjs', '.json', '.md', '.csv', '.ps1'):
            path = Path(tmp) / ('fixture' + suffix)
            for i, text in enumerate(positives):
                path.write_text(text, encoding='utf-8')
                assert scan_bytes(path.read_bytes()), f'missed positive {suffix} #{i}'
            for i, text in enumerate(negatives):
                path.write_text(text, encoding='utf-8')
                assert not scan_bytes(path.read_bytes()), f'flagged placeholder {suffix} #{i}'


def test_precommit_hook():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name in ('bb/__init__.py', 'bb/security.py', 'scripts/check_secrets.py', '.githooks/pre-commit'):
            target = folder / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / name, target)
        def git(*args):
            return subprocess.run(['git', '-C', tmp, *args], capture_output=True)
        assert git('init').returncode == 0
        assert git('config', 'core.hooksPath', '.githooks').returncode == 0
        (folder / 'dummy.py').write_text('to' + 'ken = "dummy-sensitive-value"\n')
        assert git('add', 'dummy.py').returncode == 0
        result = git('-c', 'user.name=Scanner Test', '-c', 'user.email=scanner@example.invalid',
                     'commit', '-m', 'must be blocked')
        assert result.returncode == 1 and b'credential' in result.stderr, 'hook did not reject assignment'
        assert git('rev-parse', '--verify', 'HEAD').returncode != 0


if __name__ == '__main__':
    test_scanner()
    print('test_scanner: PASS')
    test_assignment_formats()
    print('test_assignment_formats: PASS')
    test_precommit_hook()
    print('test_precommit_hook: PASS')
