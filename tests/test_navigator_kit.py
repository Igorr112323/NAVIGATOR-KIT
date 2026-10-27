#!/usr/bin/env python3
"""Regression tests for the locally executed reference pipeline."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "navigator_kit.py"
spec = importlib.util.spec_from_file_location("navigator_kit", TOOL)
nk = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(nk)


class NavigatorKitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = nk.load_mapping(ROOT / "delivery/xml/stamp_mapping.xml")
        cls.sheets = nk.scan_sheets(ROOT / "samples/synthetic_sets", cls.profiles)

    def test_mapping_has_two_profiles(self):
        self.assertEqual(len(self.profiles), 2)
        self.assertEqual({p["id"] for p in self.profiles},
                         {"SPDS_FORM3_CLASSIC", "SPDS_FORM3_ALT"})

    def test_xml_examples_parse(self):
        for p in (ROOT / "delivery/xml").glob("*.xml"):
            ET.parse(p)

    def test_scan_120_sheets(self):
        self.assertEqual(len(self.sheets), 120)
        self.assertEqual({s["mark"] for s in self.sheets}, {"АР", "КР", "ОВ"})
        self.assertEqual(sum(1 for s in self.sheets if s["source_sha256"]), 120)

    def test_dxf_attribute_reader(self):
        attrs = nk.parse_dxf_attributes(ROOT / "samples/synthetic_sets/АР/АР_001.dxf")
        self.assertEqual(attrs["MARK"], "АР")
        self.assertEqual(attrs["SHEET"], "1")
        self.assertEqual(attrs["FORMAT"], "A1")

    def test_format_validator(self):
        self.assertTrue(nk.is_allowed_format("A0"))
        self.assertTrue(nk.is_allowed_format("A5"))
        self.assertTrue(nk.is_allowed_format("A2x3"))
        self.assertFalse(nk.is_allowed_format("B4"))
        self.assertFalse(nk.is_allowed_format("A6"))
        self.assertFalse(nk.is_allowed_format("A1x2"))

    def test_pipeline_reports_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            issues = nk.validate(self.sheets, ROOT / "samples", out)
            form1 = nk.build_form1(self.sheets, issues, out)
            form2 = nk.build_form2(ROOT / "samples", out)
            numbering = nk.build_numbering(self.sheets, out)
            stamp = nk.build_stamp_transaction(ROOT / "samples", out)
            changes = nk.build_changes(ROOT / "samples", out)
            print_data = nk.build_print_order(self.sheets, form1, ROOT / "samples", out)
            self.assertGreaterEqual(len(issues), 16)
            self.assertEqual(len(form1), 120)
            self.assertGreaterEqual(len(form2), 6)
            self.assertGreaterEqual(len(numbering["duplicates"]), 2)
            self.assertEqual(len(numbering["plan"]), 120)
            self.assertTrue(stamp["rollbackVerified"])
            self.assertTrue(stamp["applyVerified"])
            self.assertEqual(changes["template_rows"], 10)
            self.assertEqual(len(print_data["order"]), 120)
            self.assertTrue(print_data["consistency"]["consistent"])

    def test_xml_key_attributes_for_sheet_and_format(self):
        for path in (ROOT / "delivery/xml").glob("*.xml"):
            root = ET.parse(path).getroot()
            fields = {a.attrib.get("field", "") for a in root.findall("./keyAttributes/attributeBinding")}
            self.assertIn("sheet_no", fields, path.name)
            self.assertIn("format", fields, path.name)

    def test_numbering_patch_script_compiles(self):
        path = ROOT / "delivery/numbering_patch.py"
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
        self.assertIn("minimal_patch", source)
        self.assertIn("full_shift", source)

    def test_wo1_docx_is_valid_package(self):
        path = ROOT / "delivery/data/wo1_template.docx"
        self.assertTrue(path.is_file())
        with zipfile.ZipFile(path) as zf:
            self.assertIn("[Content_Types].xml", zf.namelist())
            self.assertIsNone(zf.testzip())

    def test_changes_table_keeps_normative_and_operational_apart(self):
        text = (ROOT / "delivery/changes_table.md").read_text(encoding="utf-8")
        self.assertIn("Изм.", text)
        self.assertIn("№ докум.", text)
        self.assertIn("Номер листа", text)
        self.assertIn("не заменяет", text)

    def test_session2_summary_and_labels(self):
        import json
        summary = json.loads((ROOT / "delivery/data/session2_summary.json").read_text(encoding="utf-8"))
        labels = json.loads((ROOT / "delivery/data/pr_labels.json").read_text(encoding="utf-8"))
        self.assertEqual(len(summary["tasks"]), 11)
        self.assertFalse(summary["nanoCADExecuted"])
        self.assertEqual(labels["requestedLabels"], ["good first issue", "night-session"])

    def test_replace_attribute_value_roundtrip(self):
        source = ROOT / "samples/synthetic_sets/АР/АР_002.dxf"
        text = source.read_text(encoding="utf-8")
        new_text, old_value, changed = nk.replace_dxf_attribute(text, "SHEET", "99")
        self.assertTrue(changed)
        self.assertEqual(old_value, "2")
        self.assertIn("99", new_text)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "patched.dxf"
            p.write_text(new_text, encoding="utf-8")
            self.assertEqual(nk.parse_dxf_attributes(p)["SHEET"], "99")


if __name__ == "__main__":
    unittest.main(verbosity=2)
