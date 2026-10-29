from pathlib import Path
from collections.abc import Mapping, Sequence
import ezdxf
from .core.geometry import Point

class DxfBackend:
    def __init__(self):
        self.doc = ezdxf.new('R2010')
        self.doc.units = 4  # millimeters

    def add_layer(self, name: str, color: int) -> None:
        self.doc.layers.new(name, dxfattribs={'color': color})

    def add_line(self, start: Point, end: Point, layer: str) -> None:
        self.doc.modelspace().add_line((start.x, start.y), (end.x, end.y), dxfattribs={'layer': layer})

    def add_polyline(self, points: Sequence[Point], layer: str) -> None:
        self.doc.modelspace().add_lwpolyline([(p.x, p.y) for p in points], dxfattribs={'layer': layer})

    def add_text(self, text: str, position: Point, height: float, layer: str) -> None:
        self.doc.modelspace().add_text(text, dxfattribs={'insert': (position.x, position.y), 'height': height, 'layer': layer})

    def add_block(self, name: str, position: Point, attributes: Mapping[str, str], layer: str) -> None:
        block = self.doc.blocks.new(name)
        for i, tag in enumerate(attributes):
            block.add_attdef(tag, insert=(0, i * 6), height=3, dxfattribs={'layer': layer})
        insert = self.doc.modelspace().add_blockref(name, (position.x, position.y), dxfattribs={'layer': layer})
        insert.add_auto_attribs(dict(attributes))

    def read_blocks(self, path: Path) -> list[dict[str, str]]:
        doc = ezdxf.readfile(path)
        result = []
        for insert in doc.modelspace().query('INSERT'):
            values = {}
            for attr in insert.attribs:
                if attr.dxf.tag in values:
                    raise ValueError(f'Duplicate attribute: {attr.dxf.tag}')
                values[attr.dxf.tag] = attr.dxf.text
            values['__block__'] = insert.dxf.name
            result.append(values)
        return result

    def save_document(self, path: Path) -> None:
        self.doc.saveas(path)
