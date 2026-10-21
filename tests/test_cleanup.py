"""Offline regressions for environment-only credential loading."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_environment_wrapper():
    code = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('tasks/SS-6390-atlas-baggage/with-prior-auth.cjs', 'utf8');
for (const supplied of [[], ['BOOKING_USERNAME'], ['BOOKING_PASSWORD']]) {
  const env = Object.fromEntries(supplied.map(k => [k, 'offline-fixture']));
  let invoked = false;
  const load = name => {
    if (name === 'node:assert/strict') return assert;
    if (name === './run-flow.cjs') { invoked = true; return {}; }
    throw new Error('Unexpected dependency');
  };
  assert.throws(() => vm.runInNewContext(source, {process: {env}, require: load}), /BOOKING_(USERNAME|PASSWORD)/);
  assert.equal(invoked, false);
}
let invoked = false;
vm.runInNewContext(source, {
  process: {env: Object.fromEntries(['BOOKING_USERNAME', 'BOOKING_PASSWORD'].map(k => [k, 'offline-fixture']))},
  require: name => {
    if (name === 'node:assert/strict') return assert;
    assert.equal(name, './run-flow.cjs'); invoked = true;
  }
});
assert.equal(invoked, true);
'''
    result = subprocess.run(['node', '-e', code], cwd=ROOT, capture_output=True)
    assert result.returncode == 0, 'Environment-only wrapper regression failed; output suppressed'


def test_fake_token_fixture():
    text = (ROOT / 'tasks/ss-6344/qa.cjs').read_text(encoding='utf-8')
    assert 'INVALID_TEST_TOKEN' in text
    data = json.loads((ROOT / 'tasks/ss-6344/recovery.postman_collection.json').read_text())
    assert 'INVALID_TEST_TOKEN' in json.dumps(data)


if __name__ == '__main__':
    for test in (test_environment_wrapper, test_fake_token_fixture):
        test()
        print(test.__name__ + ': PASS')
