#!/usr/bin/env python3
"""Self-contained source+data bundle, with isolated extracted pytest smoke test."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'delivery/navigator-kit-test-runner.zip'


def main():
    folders = ('delivery', 'docs', 'src', 'tools', 'tests', 'samples', 'linux_stand', 'logs', '.github/workflows')
    extras = ('README.md', 'README_test_runner.md', 'requirements.txt', 'requirements-test-runner.txt',
              'requirements-analysis.txt', 'briefing.md', 'night-log.md', '.gitignore')
    with zipfile.ZipFile(BUNDLE, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in extras:
            z.write(ROOT / name, name)
        for folder in folders:
            for p in sorted((ROOT / folder).rglob('*')):
                if p.is_file() and p.suffix not in ('.zip', '.pyc') and '__pycache__' not in p.parts:
                    z.write(p, p.relative_to(ROOT))
    if BUNDLE.stat().st_size > 3_000_000:
        raise RuntimeError(f'Bundle exceeds 3 MB: {BUNDLE.stat().st_size}')
    with tempfile.TemporaryDirectory(prefix='navigator-runner-') as temp:
        with zipfile.ZipFile(BUNDLE) as z:
            if z.testzip() is not None: raise RuntimeError('ZIP CRC failure')
            z.extractall(temp)
        run = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
                             cwd=temp, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # Logs kept in repo, not in the extracted archive that will disappear.
        logdir = ROOT / 'logs'
        logdir.mkdir(exist_ok=True)
        (logdir / 'test-runner-extracted.log').write_text(run.stdout, encoding='utf-8')
        print(run.stdout)
        if run.returncode: raise SystemExit(run.returncode)
        report = json.loads((Path(temp) / 'delivery/linux-stand/test_report.json').read_text(encoding='utf-8'))
        assert report['tests_passed'] == 28 and report['tests_failed'] == 0, report
        subprocess.run([sys.executable, '-S', 'tools/check_test_runner_data.py'], cwd=temp, check=True)
    print(f'Test-runner ZIP PASS: {BUNDLE.stat().st_size} bytes; extracted suite 28 PASS')

if __name__ == '__main__': main()
