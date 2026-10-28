#!/usr/bin/env python3
"""Independent batch reader for controlled ASCII stand fixtures, no ezdxf."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from linux_stand.independent_reader import inspect

def parse_folder(folder: Path) -> dict:
    return {p.name: inspect(p) for p in sorted(folder.glob('*.dxf'))}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(parse_folder(args.folder), indent=2, ensure_ascii=False) + '\n')
