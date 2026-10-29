#!/usr/bin/env python3
"""Reproducible DXF -> render -> independent read -> tests -> evidence."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['MPLBACKEND'] = 'Agg'
from linux_stand.core.vedmist import Stamp, draw_demo, parse_stamps
from linux_stand.core.normcontrol import check_stamp
from linux_stand.dxf_backend import DxfBackend
from linux_stand.independent_reader import inspect


def main():
    out = ROOT / 'delivery/linux-stand'; out.mkdir(parents=True, exist_ok=True)
    logs = [f'Linux stand: {platform.platform()}', f'Python: {sys.version}',
            f'dotnet: {shutil.which("dotnet") or "NOT AVAILABLE"}']
    stamp = Stamp('NK-001-AR', '1', 'General data', 'A4')
    path = out / 'hello_stamp.dxf'
    backend = DxfBackend(); draw_demo(backend, stamp); backend.save_document(path)
    assert parse_stamps(DxfBackend(), path) == [stamp]
    assert check_stamp(stamp) == []
    assert check_stamp(Stamp('', '0', 'General data', 'A4')) == ['EMPTY_DESIGNATION', 'INVALID_SHEET']
    evidence = inspect(path)
    assert evidence['counts'] == {'LWPOLYLINE': 1, 'LINE': 1, 'TEXT': 1, 'INSERT': 1, 'ATTRIB': 4, 'SEQEND': 1}
    assert evidence['frameBounds'] == [0, 0, 297, 210]
    assert evidence['attributes'] == {'DESIGNATION': 'NK-001-AR', 'SHEET': '1', 'TITLE': 'General data', 'FORMAT': 'A4'}
    assert {'FRAME', 'STAMP', 'NOTES'} <= set(evidence['layers'])
    logs.append('PASS: stamp roundtrip, 2 seeded defects, independent counts/layers/bounds/text')
    import ezdxf
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    doc = ezdxf.readfile(path)
    assert not doc.audit().has_errors
    fig = plt.figure(figsize=(12, 9), dpi=120)
    ax = fig.add_axes((.03, .08, .94, .86))
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace(), finalize=True)
    fig.text(.5, .025, 'nanoCAD НЕ запускался / не скриншот CAD', ha='center', fontsize=12, color='#b22222')
    fig.savefig(out / 'hello_stamp.png'); plt.close(fig)
    logs.append('PASS: ezdxf audit + render actual saved DXF to PNG')
    run = subprocess.run([sys.executable, '-m', 'pytest', 'tests/test_linux_stand.py', '-v'],
                         cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    logs.append(run.stdout)
    (out / 'run.log').write_text('\n'.join(logs), encoding='utf-8')
    print('\n'.join(logs))
    if run.returncode: raise SystemExit(run.returncode)
    evidence.update(status='PASS', nanoCADExecuted=False, renderer=f'ezdxf {ezdxf.__version__} / matplotlib',
                    limitations=['ГИПОТЕЗА/ПРОВЕРИТЬ: form geometry, SDK binding, DWG, transactions, layouts, printing'],
                    hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (path, out / 'hello_stamp.png')})
    (out / 'verification.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__': main()
