#!/usr/bin/env python3
"""Verify delivery, then build non-recursive <=3 MB Linux bundle."""
import json
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'delivery/linux-stand'

def main():
    result = subprocess.run([sys.executable, 'tools/verify_delivery.py', '--check-only'], cwd=ROOT, text=True, capture_output=True)
    print(result.stdout, end='')
    if result.returncode: raise SystemExit(result.stderr or result.returncode)
    checks = json.loads(result.stdout)
    report = json.loads((OUT / 'test_report.json').read_text())
    report.update(total_checks=checks['requiredChecks'], failed_checks=checks['failedRequiredChecks'])
    (OUT / 'test_report.json').write_text(json.dumps(report, indent=2) + '\n')
    with (OUT / 'pytest.log').open('a') as log:
        log.write(f"\n{checks['requiredChecks']} checks — {checks['failedRequiredChecks']} failures (separate delivery verifier)\n")
    # Refresh manifests after changing report. Verifier checks hashes, so run again.
    subprocess.run([sys.executable, 'tools/finalize_delivery.py'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, 'tools/verify_delivery.py', '--check-only'], cwd=ROOT, check=True)
    bundle = ROOT / 'delivery/navigator-kit-linux-stand.zip'
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for folder in ('delivery/linux-stand', 'delivery/screenshots', 'delivery/data', 'delivery/xml', 'linux_stand', 'tests', 'tools'):
            for p in sorted((ROOT / folder).rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.zip'):
                    z.write(p, p.relative_to(ROOT))
        for name in ('delivery/manifest.json', 'delivery/MANIFEST.json', 'requirements.txt'):
            z.write(ROOT / name, name)
    assert bundle.stat().st_size <= 3_000_000, bundle.stat().st_size
    with zipfile.ZipFile(bundle) as z: assert z.testzip() is None
    print(f'Linux bundle PASS: {bundle.stat().st_size} bytes')

if __name__ == '__main__': main()
