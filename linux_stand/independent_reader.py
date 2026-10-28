"""Separate ASCII DXF pair reader; no ezdxf and no production parser reuse.
Only verifies the controlled stand fixture, not a general-purpose DXF parser.
"""
from pathlib import Path

def inspect(path: Path) -> dict:
    lines = path.read_text(encoding='utf-8').splitlines()
    if len(lines) % 2:
        raise ValueError('Odd group-code line count')
    groups = [(int(lines[i]), lines[i + 1]) for i in range(0, len(lines), 2)]
    records = []
    for code, value in groups:
        if code == 0:
            records.append((value, []))
        elif records:
            records[-1][1].append((code, value))
    entities = []; in_entities = False; attrs = {}
    for kind, pairs in records:
        if kind == 'SECTION':
            in_entities = (2, 'ENTITIES') in pairs
        elif kind == 'ENDSEC':
            in_entities = False
        elif in_entities:
            entities.append((kind, pairs))
            if kind == 'ATTRIB':
                data = dict(pairs)
                if data[2] in attrs: raise ValueError('Duplicate attribute')
                attrs[data[2]] = data[1]
    counts = {}
    for kind, _ in entities: counts[kind] = counts.get(kind, 0) + 1
    poly = next(p for kind, p in entities if kind == 'LWPOLYLINE')
    xs = [float(v) for c, v in poly if c == 10]
    ys = [float(v) for c, v in poly if c == 20]
    return {'counts': counts, 'attributes': attrs,
            'layers': sorted({dict(p).get(8, '0') for _, p in entities if p}),
            'frameBounds': [min(xs), min(ys), max(xs), max(ys)]}
