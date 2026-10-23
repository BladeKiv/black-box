"""Exercise the offline runner's exit codes and table using real subprocesses."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys


def test_runner_statuses():
    from bb.selftest import run_tests
    cases = [(name, [sys.executable, '-c', f'raise SystemExit({code})'])
             for name, code in [('success', 0), ('missing evidence', 77), ('failure', 1)]]
    output = io.StringIO()
    with redirect_stdout(output):
        assert run_tests(cases, Path.cwd()) == 1
    table = output.getvalue()
    for name, status in [('success', 'PASS'), ('missing evidence', 'SKIP'), ('failure', 'FAIL')]:
        assert f'| {name} | {status} |' in table
    assert '1 PASS / 1 SKIP / 1 FAIL' in table
    with redirect_stdout(io.StringIO()):
        assert run_tests(cases[:2], Path.cwd()) == 0


if __name__ == '__main__':
    test_runner_statuses()
    print('test_runner_statuses: PASS')
