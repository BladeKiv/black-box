"""Scanner checks use constructed dummy strings, never real credentials."""
import subprocess
import json
import base64
import tempfile
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


if __name__ == '__main__':
    test_scanner()
    print('test_scanner: PASS')
