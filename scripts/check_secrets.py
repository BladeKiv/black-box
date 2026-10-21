"""Metadata-only security scan. Exit 1 for findings, 2 for scan errors."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bb.security import findings

EXTRA_PATTERNS = {
    'local_path': re.compile(r'(?i)\b[A-Z]:[\\/]+Users[\\/]+[^\s"<>]+'),
    'session_content': re.compile(r'"(?:type|event)"\s*:\s*"(?:session_meta|response_item|turn_context|event_msg)"'),
}
EXTRA_HINTS = {'local_path': ('users',),
               'session_content': ('session_meta', 'response_item', 'turn_context', 'event_msg')}


def scan_text(text):
    matches = findings(text)
    lowered = text.lower()
    for kind, pattern in EXTRA_PATTERNS.items():
        if not any(h in lowered for h in EXTRA_HINTS[kind]):
            continue
        matches.extend({'line': text.count('\n', 0, m.start()) + 1, 'type': kind} for m in pattern.finditer(text))
    return [{'line': line, 'type': kind} for line, kind in sorted({(m['line'], m['type']) for m in matches})]


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True).stdout


def scan_bytes(data):
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        return scan_text(data.decode('utf-16'))
    # Binary blobs still get an ASCII-compatible scan for embedded tokens/paths.
    text = data.decode('utf-8', errors='replace')
    output = scan_text(text)
    # Dispatch sheets embed importable collections as base64 JSON for Blob downloads.
    for match in re.finditer(r'''(?<=["'])[A-Za-z0-9+/]{24,}={0,2}(?=["'])''', text):
        try:
            decoded = base64.b64decode(match.group(), validate=True).decode('utf-8')
            json.loads(decoded)
        except (ValueError, UnicodeError):
            continue
        for finding in scan_text(decoded):
            output.append({'line': text.count('\n', 0, match.start()) + 1,
                           'type': 'embedded_' + finding['type'], 'embedded_line': finding['line']})
    return output


def scan_staged(root):
    output = []
    names = git(root, 'diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z').split(b'\0')
    for raw in names:
        if not raw:
            continue
        name = raw.decode('utf-8')
        data = git(root, 'show', ':' + name)
        output.extend({'file': name, **m} for m in scan_bytes(data))
    # Lessons can change after staging; inspect their working copies as well.
    folder = root / 'knowledge/lessons'
    for path in folder.glob('*.jsonl'):
        output.extend({'file': path.relative_to(root).as_posix(), **m} for m in scan_bytes(path.read_bytes()))
    return output


def scan_history(root):
    output = []
    # Includes reachable branch/tag history and local reflogs; each blob once.
    objects = git(root, 'rev-list', '--objects', '--all', '--reflog').decode('utf-8').splitlines()
    with subprocess.Popen(['git', '-C', str(root), 'cat-file', '--batch'],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as process:
        try:
            for line in objects:
                oid, _, name = line.partition(' ')
                process.stdin.write((oid + '\n').encode('ascii'))
                process.stdin.flush()
                header = process.stdout.readline().split()
                if len(header) != 3:
                    raise ValueError('Unreadable git object')
                kind, size = header[1], int(header[2])
                data = process.stdout.read(size)
                if len(data) != size or process.stdout.read(1) != b'\n':
                    raise ValueError('Incomplete git object')
                if kind in (b'blob', b'commit', b'tag'):
                    label = name or '(unnamed blob)' if kind == b'blob' else '(' + kind.decode() + ' message)'
                    output.extend({'file': label, 'object': oid, **m} for m in scan_bytes(data))
        finally:
            process.stdin.close()
        if process.wait() != 0:
            raise ValueError('Git object scan failed')
    return output


def scan_tree(root):
    output, large = [], []
    total = 0
    checked = 0
    for folder, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d != '.git' and not (Path(folder) / d).is_symlink()]
        for name in files:
            path = Path(folder) / name
            if path.is_symlink():
                output.append({'file': path.relative_to(root).as_posix(), 'line': 0, 'type': 'unscanned_symlink'})
                continue
            data = path.read_bytes()
            total += len(data)
            rel = path.relative_to(root).as_posix()
            if len(data) > 5 * 1024 * 1024:
                large.append({'file': rel, 'bytes': len(data)})
            output.extend({'file': rel, **m} for m in scan_bytes(data))
            checked += 1
            if checked % 200 == 0:
                print(f'Scanned {checked} files, {total} bytes; {len(output)} finding locations', file=sys.stderr, flush=True)
    git_bytes = sum(p.stat().st_size for p in (root / '.git').rglob('*') if p.is_file())
    return {'findings': output, 'working_tree_bytes': total, 'git_bytes': git_bytes,
            'total_bytes': total + git_bytes, 'files_over_5mb': sorted(large, key=lambda x: -x['bytes'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--staged', action='store_true')
    group.add_argument('--audit', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.audit:
            history = scan_history(ROOT)
            print(f'History scan: {len(history)} finding locations', file=sys.stderr, flush=True)
            report = {**scan_tree(ROOT), 'history_findings': history}
            report['history_needs_review'] = bool(report['history_findings'])
            dirty = bool(report['findings'] or report['history_findings'])
        else:
            report = {'findings': scan_staged(ROOT)}
            dirty = bool(report['findings'])
        serialized = json.dumps(report, indent=2)
        if args.output:
            args.output.write_text(serialized + '\n', encoding='utf-8')
            print(json.dumps({'output': args.output.as_posix(), 'findings': len(report['findings']),
                              'history_findings': len(report.get('history_findings', [])),
                              'total_bytes': report.get('total_bytes')}))
        else:
            print(serialized)
        return 1 if dirty else 0
    except (OSError, subprocess.CalledProcessError, UnicodeError, ValueError):
        print('Security scan failed; no contents printed. Commit blocked.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
