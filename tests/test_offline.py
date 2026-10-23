"""Missing ignored evidence skips; malformed evidence still fails."""
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_evidence_skips():
    for relative in ('tasks/SS-6401-commission-optimization/check-postman.cjs',
                     'tasks/ss-6340/verify-and-report.cjs'):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            script = folder / Path(relative).name
            shutil.copy2(ROOT / relative, script)
            if script.name == 'check-postman.cjs':
                shutil.copy2(ROOT / Path(relative).parent / 'postman-parity.js', folder)
            def run():
                return subprocess.run(['node', str(script)], cwd=folder, capture_output=True)
            result = run()
            assert result.returncode == 77 and b'evidence not in repo' in result.stdout
            if script.name == 'check-postman.cjs':
                capture = folder / 'runs/TSTCOM/evidence/TC-01/1/prod/response.json'
                capture.parent.mkdir(parents=True)
                capture.write_text('invalid JSON')
            else:
                (folder / 'latest-run.txt').write_text(str(folder))
                assert run().returncode == 77, 'partial captures must skip before writing reports'
                for name in ('search-response', 'selected-solution', 'result-request', 'result-response',
                             'result-additional-info', 'search-meta', 'result-meta'):
                    (folder / (name + '.json')).write_text('invalid JSON')
                assert run().returncode == 77, 'missing Search request must skip before parsing or writes'
                (folder / 'search-request.json').write_text('invalid JSON')
            assert run().returncode not in (0, 77), 'malformed evidence must fail'


if __name__ == '__main__':
    test_evidence_skips()
    print('test_evidence_skips: PASS')
