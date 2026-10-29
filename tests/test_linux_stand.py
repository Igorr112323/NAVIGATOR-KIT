"""Project-contract tests. ПРОВЕРИТЬ ПО ТЕКСТУ ГОСТ: no clause claims."""
import ast
import tempfile
import unittest
from pathlib import Path
from linux_stand.core.vedmist import Stamp, draw_demo, parse_stamps
from linux_stand.core.normcontrol import check_stamp
from linux_stand.dxf_backend import DxfBackend
from linux_stand.independent_reader import inspect
from linux_stand.multicad_backend import MulticadBackend

EXPECTED = {'DESIGNATION': 'NK-001-AR', 'SHEET': '1', 'TITLE': 'General data', 'FORMAT': 'A4'}

class LinuxStandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'hello.dxf'
        self.stamp = Stamp('NK-001-AR', '1', 'General data', 'A4')
        backend = DxfBackend(); draw_demo(backend, self.stamp); backend.save_document(self.path)

    def test_stamp_roundtrip(self):
        self.assertEqual(parse_stamps(DxfBackend(), self.path), [self.stamp])

    def test_required_field(self):
        self.assertEqual(check_stamp(Stamp('', '1', 'Title', 'A4')), ['EMPTY_DESIGNATION'])

    def test_numbering(self):
        for value in ('0', '-1', 'x', '１'):
            self.assertEqual(check_stamp(Stamp('NK', value, 'Title', 'A4')), ['INVALID_SHEET'])
        self.assertEqual(check_stamp(self.stamp), [])

    def test_independent_entities(self):
        self.assertEqual(inspect(self.path)['counts'],
                         {'LWPOLYLINE': 1, 'LINE': 1, 'TEXT': 1, 'INSERT': 1, 'ATTRIB': 4, 'SEQEND': 1})

    def test_independent_geometry_and_text(self):
        data = inspect(self.path)
        self.assertEqual(data['frameBounds'], [0, 0, 297, 210])
        self.assertEqual(data['attributes'], EXPECTED)
        self.assertTrue({'FRAME', 'STAMP', 'NOTES'} <= set(data['layers']))

    def test_duplicate_attribute_rejected(self):
        import ezdxf
        doc = ezdxf.readfile(self.path)
        doc.modelspace().query('INSERT')[0].add_attrib('SHEET', '2')
        doc.saveas(self.path)
        with self.assertRaises(ValueError): parse_stamps(DxfBackend(), self.path)
        with self.assertRaises(ValueError): inspect(self.path)

    def test_core_has_no_cad_import(self):
        for path in (Path(__file__).resolve().parents[1] / 'linux_stand/core').glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Import):
                    self.assertTrue(all(not a.name.startswith(('ezdxf', 'linux_stand.dxf_backend')) for a in node.names))
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn('ezdxf', node.module or '')

    def test_multicad_fails_explicitly(self):
        with self.assertRaises(NotImplementedError): MulticadBackend()

    def test_independent_odd_lines_rejected(self):
        self.path.write_text('0\nSECTION\n2\n')
        with self.assertRaises(ValueError): inspect(self.path)

    def test_batch_reader_two_files(self):
        from tools.independent_dxf_parser import parse_folder
        import shutil
        shutil.copyfile(self.path, self.path.with_name('second.dxf'))
        parsed = parse_folder(self.path.parent)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed['second.dxf']['attributes'], EXPECTED)

    def test_actual_render_dimensions(self):
        from linux_stand.render import render
        from PIL import Image
        png = self.path.with_suffix('.png')
        render(self.path, png)
        with Image.open(png) as image:
            self.assertEqual(image.size, (1600, 1200))
            self.assertGreater(len(set(image.getdata())), 5)
