#!/usr/bin/env python3
"""Stdlib-only smoke check: not a replacement for pytest or 59 delivery checks."""
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from linux_stand.independent_reader import inspect

def main():
    out = ROOT / 'delivery/linux-stand'
    expected = json.loads((out / 'parsed_stamps.json').read_text(encoding='utf-8'))
    assert len(expected) == 12
    for name, data in expected.items():
        assert inspect(out / 'samples' / name) == data, name
    renders = json.loads((out / 'renders_manifest.json').read_text(encoding='utf-8'))
    assert len(renders) == 12
    for entry in renders:
        assert hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest() == entry['sha256']
    print('PASS: stdlib independent read of 12 DXF + SHA-256 of 12 PNG (not full pytest)')

if __name__ == '__main__': main()
