#!/usr/bin/env python3
"""Batch fixtures -> DXF reread -> actual render -> full pytest evidence.
Run after reference pipeline; finalize delivery afterwards.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from linux_stand.core.vedmist import Stamp, draw_demo, parse_stamps
from linux_stand.dxf_backend import DxfBackend
from linux_stand.render import render
from tools.independent_dxf_parser import parse_folder

OUT = ROOT / 'delivery/linux-stand'

def main():
    folder = OUT / 'samples'; folder.mkdir(exist_ok=True)
    expected = {}
    for n in range(1, 13):
        name = f'stamp_{n:02d}.dxf'
        stamp = Stamp(f'NK-{n:03d}-AR', str(n), f'Sheet {n:02d}', 'A4')
        backend = DxfBackend(); draw_demo(backend, stamp); backend.save_document(folder / name)
        assert parse_stamps(DxfBackend(), folder / name) == [stamp]
        expected[name] = stamp.attributes()
        render(folder / name, ROOT / 'delivery/screenshots' / f'linux_stamp_{n:02d}.png')
    from PIL import Image
    images = []
    for image_path in sorted((ROOT / 'delivery/screenshots').glob('linux_stamp_*.png')):
        with Image.open(image_path) as image:
            assert image.size == (1600, 1200)
        images.append({'path': image_path.relative_to(ROOT).as_posix(),
                       'bytes': image_path.stat().st_size,
                       'sha256': hashlib.sha256(image_path.read_bytes()).hexdigest(),
                       'size': [1600, 1200], 'nanoCADScreenshot': False,
                       'warningBanner': True, 'bottomRightWatermark': True})
    assert len(images) == 12
    (OUT / 'renders_manifest.json').write_text(json.dumps(images, indent=2) + '\n')
    parsed = parse_folder(folder)
    differences = []
    for name, data in parsed.items():
        if data['attributes'] != expected[name]: differences.append(f'{name}: attributes')
        if data['frameBounds'] != [0, 0, 297, 210]: differences.append(f'{name}: frameBounds')
        if data['counts'] != {'LWPOLYLINE': 1, 'LINE': 1, 'TEXT': 1, 'INSERT': 1, 'ATTRIB': 4, 'SEQEND': 1}: differences.append(f'{name}: counts')
        if not {'FRAME', 'STAMP', 'NOTES'} <= set(data['layers']): differences.append(f'{name}: layers')
    # Compare original hello-DXF against the previous stand verification as well.
    from linux_stand.independent_reader import inspect
    original = json.loads((OUT / 'verification.json').read_text())
    reread = inspect(OUT / 'hello_stamp.dxf')
    for key in ('attributes', 'counts', 'frameBounds', 'layers'):
        if original[key] != reread[key]: differences.append(f'hello: {key}')
    (OUT / 'parser_diff.log').write_text('\n'.join(differences) + ('\n' if differences else 'PASS: 12 fixtures + original verification; no differences\n'))
    if differences: raise ValueError(differences)
    (OUT / 'parsed_stamps.json').write_text(json.dumps(parsed, indent=2) + '\n')
    # Persist full output and pytest machine report; never manufacture a passing count.
    result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short',
                             f'--junitxml={OUT / "pytest.xml"}'], cwd=ROOT,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT / 'pytest.log').write_text(result.stdout)
    print(result.stdout)
    if result.returncode: raise SystemExit(result.returncode)
    import xml.etree.ElementTree as ET
    suites = ET.parse(OUT / 'pytest.xml').getroot().findall('testsuite')
    totals = {key: sum(int(s.get(key, 0)) for s in suites) for key in ('tests', 'failures', 'errors', 'skipped')}
    report = {'passed': totals['tests'] - totals['failures'] - totals['errors'] - totals['skipped'],
              'failed': totals['failures'] + totals['errors'], 'skipped': totals['skipped'],
              'total_tests': totals['tests'], 'delivery_checks': 'Run tools/finalize_linux_stand.py after finalize_delivery.py'}
    (OUT / 'test_report.json').write_text(json.dumps(report, indent=2) + '\n')
    (OUT / 'log.txt').write_text('stand_status: ready\nScope: Linux DXF only; nanoCAD not executed\n12 generated fixtures, independent reread and renders PASS\n')
    shutil.copyfile(ROOT / 'logs/night-session.log', OUT / 'night-session.log')
    print('stand_status: ready (Linux DXF scope only)')

if __name__ == '__main__': main()
