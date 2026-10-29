#!/usr/bin/env python3
"""Generate 3 x 40 synthetic but valid DXF R2010 sheets for a reproducible POC.

The files are intentionally NOT production DWG drawings. They contain a block
reference with ATTRIB entities that emulate two different SPDS title-block
profiles. Run with ezdxf installed (see requirements.txt).
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"
SETS = SAMPLES / "synthetic_sets"
REFDOCS = SAMPLES / "reference_docs"
MARKS = ["АР", "КР", "ОВ"]
PROFILE_A = "SPDS_FORM3_CLASSIC"
PROFILE_B = "SPDS_FORM3_ALT"

TAGS = {
    PROFILE_A: ["PROFILE", "MARK", "DESIGNATION", "SHEET", "TITLE", "FORMAT", "REV", "LAYOUT"],
    PROFILE_B: ["PROFIL", "MARKA", "OBOZN", "LIST", "NAIM", "FORM", "IZM", "LSTLAYOUT"],
}
BLOCK_NAMES = {PROFILE_A: "SPDS_FORM3", PROFILE_B: "FORMAT_A3_SPDS"}

TITLES = {
    "АР": [
        "Общие данные по рабочим чертежам", "План на отм. 0,000", "План на отм. 3,300",
        "План кровли", "Фасад 1-4", "Фасад А-Д", "Разрез 1-1", "Разрез 2-2",
        "План полов", "Ведомость отделки", "Узлы наружных стен", "Спецификация окон",
    ],
    "КР": [
        "Общие данные по рабочим чертежам", "Схема расположения свай", "План фундаментов",
        "Сечение 1-1 фундамента", "План колонн", "План перекрытия", "Схема армирования плиты",
        "Схема балок покрытия", "Узел опирания", "Спецификация элементов", "Разрез по лестнице",
        "Ведомость расхода стали",
    ],
    "ОВ": [
        "Общие данные по рабочим чертежам", "План отопления подвала", "План отопления 1 этажа",
        "План вентиляции", "Схема воздуховодов", "План дымоудаления", "Разрез венткамеры",
        "Схема трубопроводов", "Узел присоединения", "Спецификация оборудования",
        "Аксонометрическая схема", "Ведомость воздуховодов",
    ],
}
FORMATS = ["A1", "A2", "A3", "A4", "A0"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def values_for(profile: str, mark: str, n: int) -> dict[str, str]:
    sheet_no = str(n)
    title = TITLES[mark][(n - 1) % len(TITLES[mark])]
    fmt = FORMATS[(n - 1) % len(FORMATS)]
    designation = f"2345-12-{mark}"

    # Deliberately seeded defects for the validators.
    if mark == "АР" and n == 16:
        sheet_no = "15"  # duplicate of sheet 15
    if mark == "АР" and n == 28:
        sheet_no = "27"  # duplicate of sheet 27
    if mark == "КР" and n == 8:
        sheet_no = "7"  # duplicate of sheet 7
    if mark == "ОВ" and n == 22:
        sheet_no = "21"  # duplicate of sheet 21
    if mark == "КР" and n == 12:
        title = ""  # empty required stamp field
    if mark == "ОВ" and n == 33:
        sheet_no = ""  # empty required stamp field
    if mark == "КР" and n == 20:
        fmt = "B4"  # not a GOST 2.301-68 basic format
    if mark == "ОВ" and n == 18:
        fmt = "A6"  # not in the standard's main/derived designations
    if mark == "АР" and n == 35:
        fmt = "A2x3"  # valid derived format designation, must not be flagged

    fields = {
        "PROFILE": profile, "MARK": mark, "DESIGNATION": designation,
        "SHEET": sheet_no, "TITLE": title, "FORMAT": fmt,
        "REV": "0", "LAYOUT": f"Лист {n}",
    }
    if profile == PROFILE_B:
        return {
            "PROFIL": fields["PROFILE"], "MARKA": fields["MARK"], "OBOZN": fields["DESIGNATION"],
            "LIST": fields["SHEET"], "NAIM": fields["TITLE"], "FORM": fields["FORMAT"],
            "IZM": fields["REV"], "LSTLAYOUT": fields["LAYOUT"],
        }
    return fields


def make_dxf(path: Path, profile: str, mark: str, n: int) -> None:
    import ezdxf

    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4  # millimeters
    doc.header["$MEASUREMENT"] = 1
    if "FRAME" not in doc.layers:
        doc.layers.add("FRAME", color=7)
    if "STAMP" not in doc.layers:
        doc.layers.add("STAMP", color=2)

    block = doc.blocks.new(name=BLOCK_NAMES[profile])
    for idx, tag in enumerate(TAGS[profile]):
        block.add_attdef(tag, dxfattribs={
            "height": 2.5,
            "insert": (0, -idx * 4.0),
            "layer": "STAMP",
        })

    vals = values_for(profile, mark, n)
    model = doc.modelspace()
    ref = model.add_blockref(BLOCK_NAMES[profile], (10, 10), dxfattribs={"layer": "STAMP"})
    ref.add_auto_attribs(vals)

    # One paper-space layout per file, with a simple frame. No duplicate ATTRIB in layout.
    layout = doc.layouts.new(f"Лист {n}")
    layout.add_lwpolyline([(0, 0), (420, 0), (420, 297), (0, 297)], close=True,
                          dxfattribs={"layer": "FRAME"})
    layout.add_text(f"СИНТЕТИЧЕСКИЙ ЛИСТ {mark}-{n:03d} / НЕ РЕАЛЬНЫЙ DWG ЗАКАЗЧИКА",
                    dxfattribs={"height": 4, "insert": (20, 270), "layer": "FRAME"})
    doc.saveas(path)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_reference_docs() -> list[dict]:
    REFDOCS.mkdir(parents=True, exist_ok=True)
    files = {
        "GOST_note.txt": "Заглушка: действующая редакция ГОСТ Р 21.101-2026. Не является текстом ГОСТ.\n",
        "Template_A.txt": "Заглушка описания эталонного шаблона СПДС A.\n",
        "Template_B.txt": "Заглушка описания эталонного шаблона СПДС B.\n",
        "Plot_profile.txt": "Заглушка профиля печати. Файл зарегистрирован в ведомости.\n",
        "EXTRA_not_registered.txt": "Физический файл, который намеренно отсутствует в ведомости.\n",
    }
    for name, text in files.items():
        (REFDOCS / name).write_text(text, encoding="utf-8")
    return [
        {"section": "Ссылочные документы", "designation": "ГОСТ Р 21.101-2026",
         "name": "Основные требования к проектной и рабочей документации",
         "file": "samples/reference_docs/GOST_note.txt", "version": "2026-04-01", "note": ""},
        {"section": "Ссылочные документы", "designation": "ГОСТ 2.301-68",
         "name": "ЕСКД. Форматы", "file": "samples/reference_docs/EXTRA_not_registered.txt",
         "version": "", "note": "Проверка: файл есть, но отсутствует в ведомости"},
        {"section": "Прилагаемые документы", "designation": "2345-12-ТП-А",
         "name": "Описание эталонного шаблона СПДС A",
         "file": "samples/reference_docs/Template_A.txt", "version": "1", "note": ""},
        {"section": "Прилагаемые документы", "designation": "2345-12-ТП-Б",
         "name": "Описание эталонного шаблона СПДС B",
         "file": "samples/reference_docs/Template_B.txt", "version": "1", "note": ""},
        {"section": "Прилагаемые документы", "designation": "2345-12-ПРОФИЛЬ",
         "name": "Профиль печати", "file": "samples/reference_docs/Plot_profile.txt",
         "version": "1", "note": ""},
        {"section": "Прилагаемые документы", "designation": "2345-12-СЕРТ",
         "name": "Сертификат (тестовая отсутствующая заглушка)",
         "file": "samples/reference_docs/MISSING_certificate.txt", "version": "1",
         "note": "Проверка: запись есть, файл отсутствует"},
    ]


def main() -> int:
    import csv

    if SETS.exists():
        for child in SETS.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
    SETS.mkdir(parents=True, exist_ok=True)

    inventory: list[dict] = []
    expected_rows: list[dict] = []
    for mark_idx, mark in enumerate(MARKS):
        folder = SETS / mark
        folder.mkdir(parents=True, exist_ok=True)
        for n in range(1, 41):
            if mark == "АР":
                profile = PROFILE_A
            elif mark == "КР":
                profile = PROFILE_B
            else:
                profile = PROFILE_A if n % 2 else PROFILE_B
            path = folder / f"{mark}_{n:03d}.dxf"
            make_dxf(path, profile, mark, n)
            vals = values_for(profile, mark, n)
            sheet_no = vals.get("SHEET", vals.get("LIST", ""))
            rel = path.relative_to(ROOT).as_posix()
            inventory.append({
                "file": rel, "mark": mark, "sequence": n, "profile": profile,
                "sheet_no": sheet_no, "sha256": sha256_file(path),
            })
            expected_rows.append({"file": rel, "mark": mark, "sheet_no": sheet_no})

    # Deliberately omit one real file and add one nonexistent file.
    expected_rows = [r for r in expected_rows if not r["file"].endswith("АР_040.dxf")]
    expected_rows.append({"file": "samples/synthetic_sets/АР/АР_041.dxf", "mark": "АР", "sheet_no": "41"})
    expected_path = SAMPLES / "expected_registry.csv"
    with expected_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "mark", "sheet_no"], delimiter=";")
        writer.writeheader()
        writer.writerows(expected_rows)

    docs = make_reference_docs()
    # Remove the intentionally extra file from the registry view: keep physical file for detection.
    registry_docs = [d for d in docs if "EXTRA_not_registered" not in d["file"]]
    # Add a second missing-file case in form 2.
    registry_docs.append({
        "section": "Ссылочные документы", "designation": "СП 000.00000-00",
        "name": "Отсутствующий ссылочный документ", "file": "samples/reference_docs/MISSING_reference.txt",
        "version": "1", "note": "Проверка: запись есть, файл отсутствует",
    })
    write_json(SAMPLES / "reference_documents.json", {
        "format": "navigator-kit.reference-documents/v1",
        "documents": registry_docs,
        "physical_extra_files": ["samples/reference_docs/EXTRA_not_registered.txt"],
    })

    write_json(SAMPLES / "stamp_patch_request.json", {
        "format": "navigator-kit.stamp-patch/v1",
        "dry_run": True,
        "note": "Правка применяется только к копиям DXF и откатывается; исходные файлы не меняются.",
        "patches": [
            {"file": "samples/synthetic_sets/АР/АР_016.dxf", "tag": "SHEET", "old_value": "15", "new_value": "16"},
            {"file": "samples/synthetic_sets/КР/КР_008.dxf", "tag": "LIST", "old_value": "7", "new_value": "8"},
        ],
    })

    write_json(SAMPLES / "change_events.json", [
        {"change_id": "1", "operation": "changed", "list_marker": "-", "document": "ИИ-2026-001", "signature": "", "date": "", "note": "Изменение без замены листа"},
        {"change_id": "2", "operation": "replaced", "list_marker": "Зам.", "document": "ИИ-2026-002", "signature": "", "date": "", "note": "Лист выпущен взамен заменённого"},
        {"change_id": "3", "operation": "added", "list_marker": "Нов.", "document": "ИИ-2026-003", "signature": "", "date": "", "note": "Лист введён вновь"},
        {"change_id": "4", "operation": "annulled", "list_marker": "-", "document": "ИИ-2026-004", "signature": "", "date": "", "note": "Аннулирование оформляется отдельно; не писать «Аннулир.» в графу «Лист»"},
        {"change_id": "5", "operation": "all_replaced", "list_marker": "Все", "document": "ИИ-2026-005", "signature": "", "date": "", "note": "Рукописный способ, только первый лист"},
        {"change_id": "6", "operation": "added", "list_marker": "Нов.", "document": "ИИ-2026-006", "signature": "", "date": "", "note": "Ещё один новый лист"},
    ])

    write_json(SAMPLES / "print_profile.json", {
        "format": "navigator-kit.print-profile/v1",
        "target": "manual-sheetsethandoff",
        "dst_export": False,
        "status": "HYPOTHESIS-VERIFY-WITH-NANOCAD-26",
        "copies": 1,
        "notes": "Не является файлом задания nanoCAD. Порядок нужно сверить с вкладками layouts и SHEETSET.",
    })
    write_json(SAMPLES / "project_info.json", {
        "project": "2345-12", "object": "Демонстрационный объект",
        "mark_order": MARKS, "profiles": [PROFILE_A, PROFILE_B],
        "normative_profile": "GOST-R-21.101-2026-Appendix-B",
    })
    write_json(SETS / "manifest.json", {
        "format": "navigator-kit.fixture-manifest/v1",
        "count": len(inventory), "files": inventory,
        "warning": "Synthetic DXF, not customer DWG.",
    })
    print(f"Generated {len(inventory)} DXF files in {SETS}")
    print(f"Expected registry rows: {len(expected_rows)}; reference docs: {len(registry_docs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
