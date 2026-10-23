"""Run every offline check in a disposable copy of tracked working files."""
from collections import Counter
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run_tests(cases, root):
    counts = Counter()
    print('| Test | Result | Detail |')
    print('|---|---|---|')
    for name, command in cases:
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, timeout=120)
            status = 'PASS' if result.returncode == 0 else 'SKIP' if result.returncode == 77 else 'FAIL'
            detail = 'evidence not in repo' if status == 'SKIP' else '' if status == 'PASS' else f'exit {result.returncode}; output suppressed'
        except (OSError, subprocess.TimeoutExpired) as error:
            status, detail = 'FAIL', type(error).__name__
        counts[status] += 1
        print(f'| {name} | {status} | {detail} |')
    print(f"{counts['PASS']} PASS / {counts['SKIP']} SKIP / {counts['FAIL']} FAIL")
    return int(bool(counts['FAIL']))


def main():
    names = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, check=True, capture_output=True).stdout
    # Some ticket verifiers regenerate reports; keep all their writes out of the checkout.
    with tempfile.TemporaryDirectory(prefix='bb-selftest-') as tmp:
        root = Path(tmp)
        for name in names.decode('utf-8').split('\0'):
            if name:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
        cases = [(path.stem, [sys.executable, '-B', '-m', 'tests.' + path.stem])
                 for path in sorted((root / 'tests').glob('test_*.py'))]
        cases += [
            ('SS-6401 comparator', [sys.executable, '-B', 'tasks/SS-6401-commission-optimization/self_check.py']),
            ('SS-6401 Postman', ['node', 'tasks/SS-6401-commission-optimization/check-postman.cjs']),
            ('SS-6332 artifacts', ['node', 'tasks/SS-6332-ndc-mapping/verify-round-A.mjs']),
            ('SS-6348 artifacts', ['node', 'tasks/SS-6348-ngs-features-breakdown/verify-artifacts.cjs']),
            ('SS-6340 evidence', ['node', 'tasks/ss-6340/verify-and-report.cjs']),
        ]
        return run_tests(cases, root)


if __name__ == '__main__':
    raise SystemExit(main())
