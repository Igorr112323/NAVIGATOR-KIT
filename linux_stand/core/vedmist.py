from dataclasses import dataclass
from pathlib import Path
from .backend import ICadBackend
from .geometry import Point

@dataclass(frozen=True)
class Stamp:
    designation: str
    sheet: str
    title: str
    format: str

    def attributes(self) -> dict[str, str]:
        return dict(zip(('DESIGNATION', 'SHEET', 'TITLE', 'FORMAT'),
                        (self.designation, self.sheet, self.title, self.format)))

def parse_stamps(backend: ICadBackend, path: Path) -> list[Stamp]:
    result = []
    for values in backend.read_blocks(path):
        if values.get('__block__') == 'NK_STAMP':
            result.append(Stamp(*(values.get(k, '') for k in
                                  ('DESIGNATION', 'SHEET', 'TITLE', 'FORMAT'))))
    return result

def draw_demo(backend: ICadBackend, stamp: Stamp) -> None:
    # Test geometry only. ПРОВЕРИТЬ ПО ТЕКСТУ ГОСТ: not official form dimensions.
    backend.add_layer('FRAME', 7)
    backend.add_layer('STAMP', 3)
    backend.add_layer('NOTES', 1)
    backend.add_polyline([Point(0, 0), Point(297, 0), Point(297, 210),
                          Point(0, 210), Point(0, 0)], 'FRAME')
    backend.add_line(Point(10, 45), Point(287, 45), 'FRAME')
    backend.add_text('LINUX TEST BENCH / NOT A STANDARD FORM', Point(10, 180), 5, 'NOTES')
    backend.add_block('NK_STAMP', Point(15, 15), stamp.attributes(), 'STAMP')
