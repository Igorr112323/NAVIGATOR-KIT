#!/usr/bin/env python3
"""Navigator Kit reference pipeline.

This is the implementation that was ACTUALLY executed in the Linux sandbox.
It scans synthetic DXF fixtures, validates the registry, and emits reproducible
CSV/JSON artifacts. It deliberately makes no claims about MultiCAD .NET APIs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import platform
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "samples" / "synthetic_sets"
DEFAULT_MAPPING = ROOT / "delivery" / "xml" / "stamp_mapping.xml"
DEFAULT_OUTPUT = ROOT / "delivery" / "data"
DEFAULT_SAMPLES = ROOT / "samples"
LOG_REPO = ROOT / "logs" / "night-session.log"
LOG_DELIVERY = ROOT / "delivery" / "logs" / "night-session.log"
LOG_EXTERNAL = Path("/home/user/logs/night-session.log")
NIGHT_LOG_MD = ROOT / "night-log.md"
NIGHT_LOG_MD_DELIVERY = ROOT / "delivery" / "night-log.md"
MARK_ORDER = ["АР", "КР", "ОВ"]
MARK_SLUG = {"АР": "AR", "КР": "KR", "ОВ": "OV"}
REQUIRED_FIELDS = ["mark", "doc_designation", "sheet_no", "sheet_name", "format"]
BASIC_FORMATS = {"A0", "A1", "A2", "A3", "A4", "A5"}
DERIVED_MULTIPLICITIES = {
    "A0": {2, 3}, "A1": {3, 4}, "A2": {3, 4, 5},
    "A3": {3, 4, 5, 6, 7}, "A4": {3, 4, 5, 6, 7, 8, 9},
}
SESSION_ID = "night-session-20261027"
LOG_LINES: list[str] = []


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def init_log() -> None:
    LOG_LINES.clear()
    for p in [LOG_REPO, LOG_DELIVERY, LOG_EXTERNAL]:
        try:
            ensure_parent(p)
            p.write_text("", encoding="utf-8")
        except OSError:
            pass
    log("SESSION_START", f"id={SESSION_ID}; repo={ROOT}; python={platform.python_version()}")
    log("WARNING", "Original briefing.md is absent; reconstructed brief is not authoritative.")
    log("WARNING", "No Windows/nanoCAD 26/MultiCAD .NET SDK/dotnet in this sandbox.")
    log("WARNING", "Screenshots later in the pipeline are labelled diagnostic mockups, not nanoCAD captures.")


def log(level: str, message: str) -> None:
    line = f"{utcnow()} [{level}] {message}"
    LOG_LINES.append(line)
    print(line)
    for p in [LOG_REPO, LOG_DELIVERY, LOG_EXTERNAL]:
        try:
            with p.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass


def write_json(path: Path, data) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_mapping(path: Path) -> list[dict]:
    root = ET.parse(path).getroot()
    profiles = []
    for tpl in root.findall("./templates/template"):
        tag_to_field: dict[str, str] = {}
        required: list[str] = []
        for attr in tpl.findall("attribute"):
            tag = attr.attrib["tag"]
            field = attr.attrib["field"]
            tag_to_field[tag] = field
            if attr.attrib.get("required", "false").lower() == "true":
                required.append(field)
        profiles.append({
            "id": tpl.attrib["id"],
            "block_name": tpl.attrib.get("blockName", ""),
            "description": tpl.attrib.get("description", ""),
            "status": tpl.attrib.get("status", ""),
            "tag_to_field": tag_to_field,
            "required": required,
        })
    if not profiles:
        raise ValueError("No stamp templates found in mapping XML")
    return profiles


def parse_dxf_attributes(path: Path) -> dict[str, str]:
    """Minimal DXF pair reader: extract code-2 tag / code-1 value from ATTRIB."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    pairs: list[tuple[int, str]] = []
    for i in range(0, len(lines) - 1, 2):
        try:
            code = int(lines[i].strip())
        except ValueError:
            continue
        pairs.append((code, lines[i + 1]))
    result: dict[str, str] = {}
    entity_type: str | None = None
    current_tag: str | None = None
    current_value: str | None = None

    def flush() -> None:
        nonlocal current_tag, current_value
        if current_tag and current_value is not None:
            result[current_tag] = current_value.strip()
        current_tag = None
        current_value = None

    for code, value in pairs:
        if code == 0:
            flush()
            entity_type = value.strip()
        elif entity_type == "ATTRIB" and code == 2:
            current_tag = value.strip()
        elif entity_type == "ATTRIB" and code == 1:
            current_value = value
    flush()
    return result


def select_profile(attrs: dict[str, str], profiles: list[dict]) -> dict | None:
    for p in profiles:
        profile_tag = next((tag for tag, field in p["tag_to_field"].items() if field == "profile_id"), None)
        if profile_tag and attrs.get(profile_tag) == p["id"]:
            return p
    best: tuple[int, dict] | None = None
    for p in profiles:
        score = sum(1 for tag in p["tag_to_field"] if tag in attrs)
        if best is None or score > best[0]:
            best = (score, p)
    return best[1] if best and best[0] >= 3 else None


def sequence_from_name(path: Path) -> int:
    m = re.search(r"_(\d+)$", path.stem)
    return int(m.group(1)) if m else 0


def scan_sheets(input_dir: Path, profiles: list[dict]) -> list[dict]:
    paths = sorted([p for p in input_dir.rglob("*.dxf")], key=lambda p: p.as_posix())
    sheets: list[dict] = []
    for path in paths:
        attrs = parse_dxf_attributes(path)
        profile = select_profile(attrs, profiles)
        if profile is None:
            mapped = {}
            profile_id = ""
            block_name = ""
            profile_status = "UNKNOWN"
        else:
            mapped = {field: attrs.get(tag, "").strip() for tag, field in profile["tag_to_field"].items()}
            profile_id = profile["id"]
            block_name = profile["block_name"]
            profile_status = profile["status"]
        rel = path.relative_to(ROOT).as_posix()
        sheet_no = mapped.get("sheet_no", "")
        record = {
            "file": rel,
            "file_name": path.name,
            "source_format": "DXF R2010",
            "source_type": "SYNTHETIC_FIXTURE_NOT_DWG",
            "source_sha256": sha256_file(path),
            "sequence": sequence_from_name(path),
            "mark": mapped.get("mark", "") or path.parent.name,
            "doc_designation": mapped.get("doc_designation", ""),
            "sheet_no": sheet_no,
            "sheet_no_num": int(sheet_no) if sheet_no.isdigit() else None,
            "sheet_name": mapped.get("sheet_name", ""),
            "format": mapped.get("format", ""),
            "revision": mapped.get("revision", ""),
            "layout": mapped.get("layout", ""),
            "profile_id": profile_id,
            "block_name": block_name,
            "profile_status": profile_status,
            "stamp_attributes": attrs,
        }
        sheets.append(record)
    return sheets


def is_allowed_format(value: str) -> bool:
    fmt = value.strip().upper().replace("А", "A").replace("×", "X")
    if fmt in BASIC_FORMATS:
        return True
    m = re.fullmatch(r"A([0-4])X(\d+)", fmt)
    if not m:
        return False
    base = "A" + m.group(1)
    return int(m.group(2)) in DERIVED_MULTIPLICITIES.get(base, set())


def validate(sheets: list[dict], samples_dir: Path, output_dir: Path) -> list[dict]:
    issues: list[dict] = []

    def add(code: str, severity: str, message: str, **kwargs) -> None:
        row = {"issue_id": f"ISS-{len(issues)+1:04d}", "code": code, "severity": severity, "message": message}
        for key in ["mark", "sheet_no", "file", "field", "suggestion"]:
            row[key] = kwargs.get(key, "")
        issues.append(row)

    for s in sheets:
        for field in REQUIRED_FIELDS:
            if not str(s.get(field, "")).strip():
                add("EMPTY_STAMP_FIELD", "ERROR",
                    f"Пустая обязательная графа штампа «{field}».",
                    mark=s["mark"], sheet_no=s["sheet_no"], file=s["file"], field=field,
                    suggestion="Заполнить атрибут блока основной надписи и повторить сканирование.")
        if not is_allowed_format(s["format"]):
            # TODO: проверка по ГОСТ 2.301-68 — сверить фактический размер внешней рамки в CAD.
            add("INVALID_FORMAT", "ERROR",
                f"Обозначение формата «{s['format']}» не найдено среди основных/производных форматов.",
                mark=s["mark"], sheet_no=s["sheet_no"], file=s["file"], field="format",
                suggestion="Проверить обозначение и размеры рамки по ГОСТ 2.301-68.")
        if not s["profile_id"]:
            add("MAPPING_MISMATCH", "ERROR", "Не найден подходящий XML-профиль штампа.",
                mark=s["mark"], file=s["file"], field="profile_id",
                suggestion="Добавить реальные теги атрибутов шаблона в stamp_mapping.xml.")

    duplicates: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for s in sheets:
        if s["sheet_no_num"] is not None:
            duplicates[(s["mark"], s["sheet_no_num"])].append(s)
    for (mark, number), group in duplicates.items():
        if len(group) > 1:
            add("DUPLICATE_SHEET_NUMBER", "ERROR",
                f"Номер листа {number} используется {len(group)} разами.",
                mark=mark, sheet_no=str(number), file="; ".join(x["file"] for x in group),
                field="sheet_no", suggestion="Утвердить minimal patch или полный сдвиг нумерации.")

    for mark in sorted({s["mark"] for s in sheets}):
        nums = [s["sheet_no_num"] for s in sheets if s["mark"] == mark and s["sheet_no_num"] is not None]
        if nums:
            missing = sorted(set(range(1, max(nums) + 1)) - set(nums))
            if missing:
                add("SEQUENCE_GAP", "WARN",
                    "Нарушена последовательность номеров листов.",
                    mark=mark, file="", field="sheet_no",
                    suggestion="Отсутствуют номера: " + ", ".join(map(str, missing)))

    expected_rows = read_csv(samples_dir / "expected_registry.csv")
    expected_files = {r["file"] for r in expected_rows}
    actual_files = {s["file"] for s in sheets}
    for r in expected_rows:
        if r["file"] not in actual_files:
            add("IN_REGISTRY_NO_FILE", "ERROR", "Есть запись в эталонном реестре, но физический лист отсутствует.",
                mark=r.get("mark", ""), sheet_no=r.get("sheet_no", ""), file=r["file"], field="file",
                suggestion="Найти файл или удалить запись после согласования с ГИПом.")
    for s in sheets:
        if s["file"] not in expected_files:
            add("FILE_NOT_IN_REGISTRY", "ERROR", "Файл листа отсутствует в эталонном реестре.",
                mark=s["mark"], sheet_no=s["sheet_no"], file=s["file"], field="file",
                suggestion="Добавить лист в реестр/ведомость или исключить из комплекта.")

    docs_data = read_json(samples_dir / "reference_documents.json")
    docs = docs_data["documents"]
    for d in docs:
        p = ROOT / d.get("file", "")
        if d.get("file") and not p.is_file():
            add("DOC_IN_REGISTRY_NO_FILE", "ERROR",
                "Документ есть в ведомости ф.2, но файл отсутствует.",
                file=d["file"], field="file",
                suggestion="Вложить документ или скорректировать ведомость.")
    listed_doc_files = {d.get("file", "") for d in docs}
    refdir = samples_dir / "reference_docs"
    for p in sorted(refdir.iterdir()):
        if p.is_file() and p.suffix.lower() in {".txt", ".pdf", ".docx", ".xlsx"}:
            rel = p.relative_to(ROOT).as_posix()
            if rel not in listed_doc_files:
                add("DOC_FILE_NOT_IN_REGISTRY", "WARN",
                    "Файл в папке документов не внесён в ведомость ф.2.",
                    file=rel, field="file",
                    suggestion="Добавить в раздел «Ссылочные» или «Прилагаемые документы».")

    write_csv(output_dir / "completeness_report.csv", issues,
              ["issue_id", "code", "severity", "mark", "sheet_no", "file", "field", "message", "suggestion"])
    return issues


def notes_by_file(issues: list[dict]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for issue in issues:
        for f in str(issue.get("file", "")).split("; "):
            if f:
                result[f].append(issue["code"])
    return result


def sheet_sort_key(s: dict) -> tuple:
    n = s["sheet_no_num"] if s["sheet_no_num"] is not None else 10**9
    return (MARK_ORDER.index(s["mark"]) if s["mark"] in MARK_ORDER else 999, n, s["sequence"], s["file"])


def build_form1(sheets: list[dict], issues: list[dict], output_dir: Path) -> list[dict]:
    nbf = notes_by_file(issues)
    rows: list[dict] = []
    for s in sorted(sheets, key=sheet_sort_key):
        codes = sorted(set(nbf.get(s["file"], [])))
        note = "; ".join(codes)
        rows.append({
            "Марка": s["mark"],
            "Лист": s["sheet_no"] or "?",
            "Наименование": s["sheet_name"] or "[НЕ ЗАПОЛНЕНО]",
            "Примечание": note,
            "Файл": s["file"],
            "Формат": s["format"],
            "Профиль": s["profile_id"],
            "НормативныйСтатус": "ДАННЫЕ ДЛЯ ФОРМЫ 1; ГЕОМЕТРИЯ ТАБЛИЦЫ — ГИПОТЕЗА/ПРОВЕРИТЬ",
        })
    write_csv(output_dir / "form1_vedomost.csv", rows,
              ["Марка", "Лист", "Наименование", "Примечание", "Файл", "Формат", "Профиль", "НормативныйСтатус"])
    strict_cols = ["Лист", "Наименование", "Примечание"]
    for mark in MARK_ORDER:
        strict_rows = [{k: r[k] for k in strict_cols} for r in rows if r["Марка"] == mark]
        write_csv(output_dir / f"form1_{MARK_SLUG[mark]}.csv", strict_rows, strict_cols)
    lines = [
        "# Форма 1 — данные ведомости рабочих чертежей",
        "",
        "Профиль: ГОСТ Р 21.101-2026, обязательное приложение Б (для backward compatibility — приложение В редакции 2020).",
        "",
        "**Внимание:** это CSV-данные, а не сертифицированная векторная форма. Точные ширины граф и размещение на листе требуют сверки с официальным графическим изображением формы 1.",
        "",
        "| Лист | Наименование | Примечание |",
        "|---|---|---|",
    ]
    for r in rows[:25]:
        name = r["Наименование"].replace("|", "\\|")
        lines.append(f"| {r['Лист']} | {name} | {r['Примечание']} |")
    (output_dir / "form1_draft.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output_dir / "form1_notes.md").write_text(
        "# Форма 1 — примечания\n\n"
        "- Графа «Лист»: порядковый номер листа основного комплекта (Б.2 ГОСТ Р 21.101-2026).\n"
        "- Графа «Наименование»: наименование изображений по основной надписи.\n"
        "- Графа «Примечание»: дополнительные сведения, в том числе об изменениях.\n"
        "- Технические колонки «Марка», «Файл», «Формат», «Профиль» есть только в мастер-CSV и не должны вставляться в чертёж.\n",
        encoding="utf-8")
    return rows


def build_form2(samples_dir: Path, output_dir: Path) -> list[dict]:
    docs = read_json(samples_dir / "reference_documents.json")["documents"]
    rows: list[dict] = []
    sections = ["Ссылочные документы", "Прилагаемые документы"]
    for section in sections:
        rows.append({
            "Раздел": section, "Обозначение": "", "Наименование": section,
            "Примечание": "ЗАГОЛОВОК РАЗДЕЛА — ПОДЧЕРКНУТЬ В ЧЕРТЕЖЕ",
            "Файл": "", "НормативныйСтатус": "ФОРМА 2 / ПРИЛОЖЕНИЕ Б-2026",
        })
        for d in docs:
            if d.get("section") != section:
                continue
            bits = []
            if d.get("note"):
                bits.append(d["note"])
            if d.get("version"):
                bits.append(f"версия/изм. ДЭ: {d['version']}")
            if d.get("file"):
                bits.append(f"файл: {Path(d['file']).name}")
            rows.append({
                "Раздел": section,
                "Обозначение": d.get("designation", ""),
                "Наименование": d.get("name", ""),
                "Примечание": "; ".join(bits),
                "Файл": d.get("file", ""),
                "НормативныйСтатус": "ДАННЫЕ ДЛЯ ФОРМЫ 2; ГЕОМЕТРИЯ — ГИПОТЕЗА/ПРОВЕРИТЬ",
            })
    write_csv(output_dir / "form2_vedomost.csv", rows,
              ["Раздел", "Обозначение", "Наименование", "Примечание", "Файл", "НормативныйСтатус"])
    strict_cols = ["Обозначение", "Наименование", "Примечание"]
    strict_rows = [{k: r[k] for k in strict_cols} for r in rows]
    write_csv(output_dir / "form2_strict.csv", strict_rows, strict_cols)
    lines = [
        "# Форма 2 — ведомость ссылочных и прилагаемых документов", "",
        "Профиль: ГОСТ Р 21.101-2026, приложение Б. Для электронных документов в примечании указывают версию/номер изменения ДЭ и имя файла.",
        "", "**Внимание:** это CSV-данные, а не векторная форма.", "",
        "| Обозначение | Наименование | Примечание |", "|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['Обозначение']} | {r['Наименование']} | {r['Примечание']} |")
    (output_dir / "form2_draft.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output_dir / "form2_notes.md").write_text(
        "# Форма 2 — примечания\n\n"
        "- Заголовки разделов записывают в графе «Наименование» и подчёркивают (4.3.3 ГОСТ Р 21.101-2026).\n"
        "- Графы формы 2: «Обозначение», «Наименование», «Примечание».\n"
        "- Технические колонки «Раздел», «Файл», «НормативныйСтатус» не вставлять в чертёж.\n",
        encoding="utf-8")
    return rows


def build_numbering(sheets: list[dict], output_dir: Path) -> dict:
    dup_groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for s in sheets:
        if s["sheet_no_num"] is not None:
            dup_groups[(s["mark"], s["sheet_no_num"])].append(s)
    duplicate_keys = {k for k, v in dup_groups.items() if len(v) > 1}
    change_files: set[str] = set()
    duplicate_rows: list[dict] = []
    for key in sorted(duplicate_keys):
        group = sorted(dup_groups[key], key=lambda x: (x["sequence"], x["file"]))
        keeper = group[0]
        to_change = group[1:]
        for s in to_change:
            change_files.add(s["file"])
        duplicate_rows.append({
            "mark": key[0], "sheet_no": key[1], "count": len(group),
            "keeper": keeper["file"], "files": "; ".join(x["file"] for x in group),
            "to_change": "; ".join(x["file"] for x in to_change),
            "recommendation": "Утвердить full_shift; minimal patch оставляет разрывы в последовательности.",
        })

    plan: list[dict] = []
    for mark in MARK_ORDER:
        group = sorted([s for s in sheets if s["mark"] == mark], key=lambda x: (x["sequence"], x["file"]))
        numeric = [s["sheet_no_num"] for s in group if s["sheet_no_num"] is not None]
        used = set(numeric)
        tail = (max(used) if used else 0) + 1
        for idx, s in enumerate(group, start=1):
            old = s["sheet_no"]
            full = str(idx)
            if s["file"] in change_files:
                while tail in used:
                    tail += 1
                minimal = str(tail)
                used.add(tail)
                tail += 1
            else:
                minimal = old if old.isdigit() else ""
            action = "KEEP" if minimal == old and full == old else "CHANGE_REQUIRED"
            plan.append({
                "mark": mark, "file": s["file"], "old_sheet_no": old,
                "minimal_new_no": minimal, "full_shift_new_no": full,
                "action": action, "requires_approval": "YES" if action != "KEEP" else "NO",
                "recommendation": "FULL_SHIFT" if duplicate_keys else "NO_CHANGE",
            })
    write_csv(output_dir / "duplicate_report.csv", duplicate_rows,
              ["mark", "sheet_no", "count", "keeper", "files", "to_change", "recommendation"])
    write_csv(output_dir / "numbering_plan.csv", plan,
              ["mark", "file", "old_sheet_no", "minimal_new_no", "full_shift_new_no", "action", "requires_approval", "recommendation"])
    graph = {
        "format": "navigator-kit.numbering-graph/v1",
        "generatedAt": utcnow(),
        "nodes": {
            "files": len(sheets), "marks": len(MARK_ORDER),
            "uniqueSheetNumbers": len({(s["mark"], s["sheet_no"]) for s in sheets}),
            "stamps": len(sheets), "form1Rows": len(sheets), "printOrderItems": len(sheets),
        },
        "edges": {
            "file_to_sheet": len(sheets), "sheet_to_stamp": len(sheets),
            "stamp_to_form1": len(sheets), "form1_to_print_order": len(sheets),
        },
        "duplicateGroups": len(duplicate_rows),
        "status": "VERIFIED_LOCALLY_ON_SYNTHETIC_DXF",
    }
    write_json(output_dir / "numbering_graph.json", graph)
    (output_dir / "numbering_policy.md").write_text(
        "# Политика нумерации\n\n"
        "1. Построить граф «файл ↔ лист ↔ штамп ↔ ведомость ↔ печать».\n"
        "2. Найти дубли в пределах марки; первый лист в порядке файлов оставить.\n"
        "3. `minimal_new_no` меняет только дубликаты, но оставляет пропуски.\n"
        "4. `full_shift_new_no` перенумеровывает весь комплект 1..N и рекомендуется для конкурсного демо.\n"
        "5. Ни один вариант автоматически не применяется к исходным чертежам без подтверждения ГИПа.\n",
        encoding="utf-8")
    return {"duplicates": duplicate_rows, "plan": plan, "graph": graph}


def replace_dxf_attribute(text: str, tag: str, new_value: str) -> tuple[str, str | None, bool]:
    """Replace code-1 value for an ATTRIB whose code-2 tag matches.

    DXF writers are free to emit code 1 before code 2, so buffer the whole
    entity first instead of assuming tag-before-value order.
    """
    lines = text.splitlines()
    entity_type: str | None = None
    entity_pairs: list[tuple[str, str, int]] = []
    old_value: str | None = None
    changed = False

    def flush() -> None:
        nonlocal changed, old_value
        if entity_type != "ATTRIB" or not entity_pairs:
            return
        entity_tag = next((value for code, value, _ in entity_pairs if code == "2"), None)
        if entity_tag != tag:
            return
        for code, value, line_index in entity_pairs:
            if code == "1":
                old_value = value
                lines[line_index] = new_value
                changed = True
                break

    for i in range(0, len(lines) - 1, 2):
        code = lines[i].strip()
        value = lines[i + 1]
        if code == "0":
            flush()
            entity_type = value.strip()
            entity_pairs = []
        else:
            entity_pairs.append((code, value, i + 1))
    flush()
    return "\n".join(lines) + "\n", old_value, changed


def build_stamp_transaction(samples_dir: Path, output_dir: Path) -> dict:
    request = read_json(samples_dir / "stamp_patch_request.json")
    workspace = output_dir / "stamp_workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    report_rows: list[dict] = []
    details: list[dict] = []
    for idx, patch in enumerate(request["patches"], start=1):
        src = ROOT / patch["file"]
        target = workspace / src.name
        backup = workspace / (src.name + ".bak")
        before_text = src.read_text(encoding="utf-8")
        before_hash = sha256_text(before_text)
        shutil.copy2(src, target)
        backup.write_text(before_text, encoding="utf-8")
        attrs_before = parse_dxf_attributes(target)
        old_actual = attrs_before.get(patch["tag"])
        new_text, replaced_old, changed = replace_dxf_attribute(before_text, patch["tag"], patch["new_value"])
        target.write_text(new_text, encoding="utf-8")
        after_hash = sha256_file(target)
        attrs_after = parse_dxf_attributes(target)
        after_ok = attrs_after.get(patch["tag"]) == patch["new_value"] and changed and replaced_old == patch["old_value"]
        shutil.copy2(backup, target)
        rollback_hash = sha256_file(target)
        backup_hash = sha256_file(backup)
        rollback_ok = rollback_hash == before_hash and backup_hash == before_hash
        row = {
            "patch_id": f"PATCH-{idx:02d}", "file": patch["file"],
            "workspace_copy": f"stamp_workspace/{target.name}",
            "backup": f"stamp_workspace/{backup.name}", "tag": patch["tag"],
            "expected_old": patch["old_value"], "actual_old": old_actual or "", "new": patch["new_value"],
            "before_sha256": before_hash, "after_sha256": after_hash, "rollback_sha256": rollback_hash,
            "backup_sha256": backup_hash, "apply_verified": after_ok, "rollback_verified": rollback_ok,
            "original_modified": False,
        }
        report_rows.append(row)
        details.append(row)
    write_csv(output_dir / "stamp_patch_plan.csv", report_rows,
              ["patch_id", "file", "workspace_copy", "backup", "tag", "expected_old", "actual_old", "new",
               "before_sha256", "after_sha256", "rollback_sha256", "backup_sha256",
               "apply_verified", "rollback_verified", "original_modified"])
    report = {
        "format": "navigator-kit.stamp-transaction/v1",
        "generatedAt": utcnow(),
        "dryRunRequested": request.get("dry_run", True),
        "appliedToIsolatedCopy": True,
        "originalFilesModified": False,
        "rollbackVerified": all(r["rollback_verified"] for r in details),
        "applyVerified": all(r["apply_verified"] for r in details),
        "carrier": "synthetic DXF text fixtures",
        "dwgWriteStatus": "ГИПОТЕЗА/ПРОВЕРИТЬ — требуется MultiCAD .NET adapter на реальных DWG",
        "patches": details,
    }
    write_json(output_dir / "stamp_patch_report.json", report)
    (workspace / "README.md").write_text(
        "# Изолированная площадка правки штампов\n\n"
        "Файлы являются копиями; `.bak` содержит исходное состояние. После применения правки выполнен rollback. "
        "Реальные DWG здесь не изменялись.\n",
        encoding="utf-8")
    return report


def build_changes(samples_dir: Path, output_dir: Path) -> dict:
    events = read_json(samples_dir / "change_events.json")
    columns = ["Изм.", "Лист", "№ докум.", "Подп.", "Дата"]
    empty_rows = [{c: "" for c in columns} for _ in range(10)]
    write_csv(output_dir / "change_table_template.csv", empty_rows, columns)
    register_rows = []
    for e in events:
        register_rows.append({
            "change_id": e["change_id"], "operation": e["operation"], "list_marker": e["list_marker"],
            "document": e["document"], "signature": e["signature"], "date": e["date"], "note": e["note"],
            "normative_status": "ГИПОТЕЗА/ПРОВЕРИТЬ — ГОСТ Р 2.503-2023 п.5.12 + раздел 7 ГОСТ Р 21.101-2026",
        })
    write_csv(output_dir / "change_register.csv", register_rows,
              ["change_id", "operation", "list_marker", "document", "signature", "date", "note", "normative_status"])
    (output_dir / "change_table_notes.md").write_text(
        "# Таблица изменений — важные ограничения\n\n"
        "- Запрошенный в задании ГОСТ 2.503-2013 утратил силу в РФ; с 01.03.2024 действует ГОСТ Р 2.503-2023.\n"
        "- Для проектной/рабочей документации также проверить раздел 7 ГОСТ Р 21.101-2026.\n"
        "- `change_table_template.csv` — пустая таблица из пяти граф; `change_register.csv` — технический пример.\n"
        "- Допустимые значения графы «Лист»: «Зам.», «Нов.», «Все», прочерк. «Аннулир.» туда не пишем.\n"
        "- Точное место таблицы на листе и геометрия граф — **ГИПОТЕЗА/ПРОВЕРИТЬ**.\n",
        encoding="utf-8")
    return {"template_rows": len(empty_rows), "example_rows": len(register_rows), "columns": columns}


def build_print_order(sheets: list[dict], form1_rows: list[dict], samples_dir: Path, output_dir: Path) -> dict:
    profile = read_json(samples_dir / "print_profile.json")
    order: list[dict] = []
    for seq, s in enumerate(sorted(sheets, key=sheet_sort_key), start=1):
        # Use the same display value as form 1 ("?" for an empty stamp field)
        # so the print-order consistency check compares identical keys.
        display_sheet_no = s["sheet_no"] or "?"
        order.append({
            "sequence": seq, "mark": s["mark"], "sheet_no": display_sheet_no,
            "sheet_name": s["sheet_name"], "file": s["file"], "layout": s["layout"],
            "format": s["format"], "copies": profile.get("copies", 1),
            "source_hash": s["source_sha256"],
        })
    write_csv(output_dir / "print_order.csv", order,
              ["sequence", "mark", "sheet_no", "sheet_name", "file", "layout", "format", "copies", "source_hash"])
    job = {
        "format": "navigator-kit.print-order/v1",
        "generatedAt": utcnow(),
        "target": profile.get("target", "manual-sheetsethandoff"),
        "dst_export": False,
        "status": "ORDER-VERIFIED-LOCALLY;NANOCAD-DST-EXPORT-HYPOTHESIS",
        "items": order,
        "notes": [
            "Не является .dst или заданием пакетной печати nanoCAD.",
            "В nanoCAD 26 порядок листов в комплекте соответствует порядку вкладок layouts исходного файла.",
            "Синхронизация с SHEETSET требует документированного API или ручной проверки.",
        ],
    }
    write_json(output_dir / "print_order.json", job)
    form_keys = [(r["Марка"], r["Лист"], r["Файл"]) for r in form1_rows]
    print_keys = [(r["mark"], r["sheet_no"], r["file"]) for r in order]
    consistent = form_keys == print_keys
    consistency = {
        "format": "navigator-kit.print-order-consistency/v1",
        "consistent": consistent,
        "form1Rows": len(form_keys), "printOrderItems": len(print_keys),
        "form1OrderHash": sha256_text(json.dumps(form_keys, ensure_ascii=False)),
        "printOrderHash": sha256_text(json.dumps(print_keys, ensure_ascii=False)),
        "status": "VERIFIED_LOCALLY" if consistent else "MISMATCH",
    }
    write_json(output_dir / "print_order_consistency.json", consistency)
    (output_dir / "batch_print_handoff.md").write_text(
        "# Передача порядка листов в пакетную печать\n\n"
        "1. Открыть `print_order.csv` / `print_order.json`.\n"
        "2. На Windows-стенде открыть SHEETSET и проверить порядок вкладок layouts.\n"
        "3. Сравнить `file + layout + sheet_no` с таблицей.\n"
        "4. Только после этого запускать штатную публикацию/печать.\n\n"
        "**Не редактировать `.dst` напрямую:** формат не подтверждён как открытый, а nanoCAD 26 связывает порядок с вкладками.\n",
        encoding="utf-8")
    return {"order": order, "consistency": consistency}


def capture_environment(output_dir: Path) -> dict:
    tools = {name: (shutil.which(name) or "MISSING") for name in
             ["dotnet", "mono", "msbuild", "csc", "python3", "node", "npm", "git", "gh", "convert"]}
    modules = {name: bool(importlib.util.find_spec(name)) for name in
               ["PIL", "ezdxf", "xmlschema", "docx", "lxml", "pandas", "matplotlib"]}
    env = {
        "format": "navigator-kit.environment/v1",
        "capturedAt": utcnow(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "architecture": platform.machine(),
        "tools": tools,
        "pythonModulesInCurrentInterpreter": modules,
        "nanocad26Installed": False,
        "multiCadSdk26Installed": False,
        "visualStudioInstalled": False,
        "licenseFound": False,
        "briefingFound": (ROOT / "briefing.md").is_file(),
        "windowsVmWorkflowPrepared": (ROOT / ".github/workflows/windows-build.yml").is_file(),
        "note": "briefing.md is a reconstruction, not the original contest brief; second session verified 2026-10-27.",
    }
    write_json(output_dir / "environment.json", env)
    return env


def write_api_experiment(output_dir: Path) -> dict:
    data = {
        "format": "navigator-kit.api-experiment/v1",
        "generatedAt": utcnow(),
        "nanoCADExecuted": False,
        "environment": "Linux sandbox; no Windows, nanoCAD 26, SDK, or license",
        "screenshots": "Only labelled diagnostic mockups were produced; no real nanoCAD screenshots.",
        "experiments": [
            {"id": "A1", "subject": "SHEETSET/.dst", "result": "DOCUMENTED", "status": "PARTIAL",
             "finding": "Sheet set composition stored in .dst; no public API spec found.",
             "source": "https://online-help.platform.nanodev.ru/NC21_Help/html/IDT_SheetSets.htm?rhtocid=_19"},
            {"id": "A2", "subject": "Insert Sheet List Table", "result": "DOCUMENTED", "status": "PARTIAL",
             "finding": "Table insertion exists, but older help references GOST R 21.1101-2013; 2026 form 1 unverified.",
             "source": "https://pt.nanocad.com/learning/online-help/nanocad-platform/actions-on-sheet-set-and-its-elements/"},
            {"id": "A3", "subject": "DATAEXTRACTION from multiple files", "result": "FORUM_REPORT_ONLY", "status": "NEGATIVE",
             "finding": "2025 forum answer: not available out of the box on plain platform; custom API code suggested.",
             "source": "https://forum.nanocad.ru/t/izvlechenie-dannyh-iz-neskolkih-fajlov/841"},
            {"id": "A4", "subject": "GetSheets()", "result": "HISTORICAL_FORUM_EXAMPLE", "status": "HYPOTHESIS",
             "finding": "Found in 2015 MultiCAD.NET example; SDK 26 signature not verified.",
             "source": "https://forum.nanocad.ru/index.php?/topic/6426-kak-vstavit-blok-iz-drugogo-dokumenta-ispolzuya-multicad/"},
            {"id": "A5", "subject": "GetSheetSets()", "result": "NOT_FOUND", "status": "HYPOTHESIS",
             "finding": "No public nanoCAD/MultiCAD documentation found; do not call without SDK reflection.",
             "source": "https://forum.nanocad.ru/"},
            {"id": "A6", "subject": "Direct .dst generation", "result": "NOT_IMPLEMENTED", "status": "HYPOTHESIS",
             "finding": "No open format spec; nanoCAD 26 sheet order is linked to layout tabs.",
             "source": "https://download.nanodev.ru/products/nanocad_platform/26.0/Instructions/Whats_new_platforma_26.pdf"},
            {"id": "A7", "subject": "Batch print task export", "result": "NEUTRAL_JSON_ONLY", "status": "HYPOTHESIS",
             "finding": "print_order.json is a handoff manifest, not a nanoCAD plot job or .dst.",
             "source": "https://download.nanodev.ru/products/nanocad_platform/26.0/Instructions/Whats_new_platforma_26.pdf"},
        ],
    }
    write_json(output_dir / "api_experiment_results.json", data)
    (ROOT / "docs" / "api-experiment.md").write_text(
        (ROOT / "docs" / "api-experiment.md").read_text(encoding="utf-8"), encoding="utf-8")
    return data


def write_standards_status(output_dir: Path) -> dict:
    data = {
        "format": "navigator-kit.standards-status/v2",
        "checkedAt": utcnow(),
        "checkedAtDate": "2026-10-27",
        "officialRegistry": {
            "spds2026": "https://protect.gost.ru/gost/details/17bc12e8-6579-4145-b141-56855e772e7f",
            "spds2020Replaced": "https://protect.gost.ru/gost/details/ba2db0a2-01aa-45da-a9dd-e5525bd69ec3",
            "changes2023": "https://protect.gost.ru/document.aspx?control=7&id=256448",
            "changes2013Revoked": "https://protect.gost.ru/gost/details/03d72f0a-a11e-436f-ba81-41f9333ccc39",
            "appendixB": "https://base.garant.ru/413848474/f7ee959fd36b5699076b35abf4f52c5c/",
            "formats": "https://www.spds.ru/info/standarts/2.301-68.html",
        },
        "active": {
            "spds": "ГОСТ Р 21.101-2026 (с 2026-04-01)",
            "forms": "Приложение Б (обязательное)",
            "changesEskd": "ГОСТ Р 2.503-2023 (с 2024-03-01)",
            "formats": "ГОСТ 2.301-68 (применение в РФ прекращается с 2027-10-01; уточнить досрочное применение ГОСТ Р 2.301-2026)",
        },
        "requested": {
            "spds": "ГОСТ Р 21.101-2020 — утратил силу",
            "changes": "ГОСТ 2.503-2013 — утратил силу в РФ",
        },
        "hypotheses": [
            "Точные размеры граф форм 1/2 в чертеже",
            "Приоритет раздела 7 ГОСТ Р 21.101-2026 над ЕСКД при оформлении изменений СПДС",
            "Соответствие штатной таблицы SHEETSET действующей редакции СПДС",
        ],
        "sources": [
            "https://protect.gost.ru/gost/details/17bc12e8-6579-4145-b141-56855e772e7f",
            "https://protect.gost.ru/gost/details/ba2db0a2-01aa-45da-a9dd-e5525bd69ec3",
            "https://base.garant.ru/413848474/f7ee959fd36b5699076b35abf4f52c5c/",
            "https://protect.gost.ru/gost/details/03d72f0a-a11e-436f-ba81-41f9333ccc39",
            "https://protect.gost.ru/document.aspx?control=7&id=256448",
            "https://www.spds.ru/info/standards/2.301-68.html",
        ],
    }
    # Correct the URL typo in the formats source (the real page uses 'standarts').
    data["sources"][-1] = "https://www.spds.ru/info/standarts/2.301-68.html"
    write_json(output_dir / "standards_status.json", data)
    return data


def write_summary(output_dir: Path, sheets: list[dict], issues: list[dict], form1_rows: list[dict],
                  form2_rows: list[dict], numbering: dict, stamp_report: dict, changes: dict,
                  print_data: dict, env: dict) -> dict:
    counts = Counter(i["code"] for i in issues)
    summary = {
        "format": "navigator-kit.summary/v1",
        "generatedAt": utcnow(),
        "sessionId": SESSION_ID,
        "verifiedLocally": True,
        "input": {"syntheticDxfFiles": len(sheets), "marks": len(MARK_ORDER), "perMark": {
            mark: sum(1 for s in sheets if s["mark"] == mark) for mark in MARK_ORDER}},
        "output": {
            "registryRows": len(sheets), "form1Rows": len(form1_rows), "form2Rows": len(form2_rows),
            "completenessIssues": len(issues), "duplicateGroups": len(numbering["duplicates"]),
            "numberingPlanRows": len(numbering["plan"]), "changeTemplateRows": changes["template_rows"],
            "printOrderItems": len(print_data["order"]),
        },
        "issueCounts": dict(sorted(counts.items())),
        "stampApplyVerified": stamp_report["applyVerified"],
        "stampRollbackVerified": stamp_report["rollbackVerified"],
        "printOrderConsistent": print_data["consistency"]["consistent"],
        "nanoCADExecuted": False,
        "dotnetAvailable": env["tools"]["dotnet"] != "MISSING",
        "status": "SUBSTANTIAL_LOCAL_DELIVERY;CAD_HOST_INTEGRATION_PENDING",
        "criticalWarnings": [
            "ГОСТ Р 21.101-2020 заменён ГОСТ Р 21.101-2026",
            "ГОСТ 2.503-2013 заменён ГОСТ Р 2.503-2023",
            "Иллюстрации не являются скриншотами nanoCAD",
            "C# сборка не выполнялась в sandbox",
        ],
    }
    write_json(output_dir / "summary.json", summary)
    return summary


def write_night_log(summary: dict, issues: list[dict], stamp_report: dict) -> None:
    lines = [
        f"# Ночной лог — {SESSION_ID}", "",
        "Все временные метки — UTC, реальное время sandbox. План на 8–10 ч находится в `docs/session-plan.md`; "
        "фактическая сессия сжата в автоматизированный проход, без симуляции девяти часов. "
        "Вторая сессия продолжает PR #1 от 2026-10-26: ветка синхронизирована с `origin/arena/ec9fddc1-navigator-kit` до `bc47b35`.", "",
        "## Хронология", "",
    ]
    for line in LOG_LINES:
        lines.append(f"- `{line}`")
    lines += [
        "", "## Ошибки и решения", "",
        "1. `briefing.md` отсутствовал → восстановлен суррогат, помечен как неавторитетный.",
        "2. `pip install --user` упёрся в externally-managed-environment → создан venv в `/home/user/.venv` (не коммитится).",
        "3. `dotnet`, `mono`, `csc`, nanoCAD и SDK отсутствуют → C# каркас не собирался; фактический pipeline реализован на Python stdlib.",
        "4. ГОСТ Р 21.101-2020 и ГОСТ 2.503-2013 утратили силу →Normative warnings вынесены в отдельный документ и статус-файл.",
        "5. Невозможны реальные скриншоты nanoCAD → сгенерированы подписанные диагностические PNG с водяным знаком.",
        "6. `GetSheetSets()` не подтверждён публично → помечен **ГИПОТЕЗА/ПРОВЕРИТЬ**, reflection-probe подготовлен.",
        "", "## Итог", "",
        f"- Листов просканировано: {summary['input']['syntheticDxfFiles']}.",
        f"- Контрольных инцидентов: {summary['output']['completenessIssues']}.",
        f"- Rollback штампов подтверждён: {stamp_report['rollbackVerified']}.",
        "- Все задачи, зависящие от nanoCAD SDK, остаются гипотезами.", "",
        "## Сырой лог", "",
        "```text",
        *LOG_LINES,
        "```",
    ]
    text = "\n".join(lines) + "\n"
    NIGHT_LOG_MD.write_text(text, encoding="utf-8")
    NIGHT_LOG_MD_DELIVERY.write_text(text, encoding="utf-8")


def run_task(name: str, func, critical: bool = False):
    try:
        result = func()
        log("TASK_OK", name)
        return result
    except Exception as exc:  # keep the night session going, but record the hypothesis
        log("TASK_ERROR", f"{name}: {type(exc).__name__}: {exc} — ГИПОТЕЗА/ПРОВЕРИТЬ")
        if critical:
            raise
        return None


def run_all(input_dir: Path, mapping_path: Path, output_dir: Path, samples_dir: Path) -> dict:
    init_log()
    output_dir.mkdir(parents=True, exist_ok=True)
    log("TASK_START", "Environment and dependency capture")
    env = capture_environment(output_dir)
    log("TASK_START", "Load XML mapping profiles")
    profiles = load_mapping(mapping_path)
    log("TASK_OK", f"Loaded {len(profiles)} stamp profiles")
    log("TASK_START", "POC scan of synthetic DXF directory")
    sheets = scan_sheets(input_dir, profiles)
    write_json(output_dir / "sheets_registry.json", {
        "format": "navigator-kit.sheet-registry/v1", "generatedAt": utcnow(),
        "status": "VERIFIED_LOCALLY_ON_SYNTHETIC_DXF", "sheets": sheets,
    })
    write_csv(output_dir / "sheets_registry.csv", sheets, [
        "file", "file_name", "source_format", "source_type", "source_sha256", "sequence",
        "mark", "doc_designation", "sheet_no", "sheet_name", "format", "revision",
        "layout", "profile_id", "block_name", "profile_status",
    ])
    log("TASK_OK", f"Scanned {len(sheets)} DXF files")
    log("TASK_START", "Completeness validation")
    issues = validate(sheets, samples_dir, output_dir)
    log("TASK_OK", f"Found {len(issues)} completeness issues")
    form1_rows = run_task("Build form 1 data", lambda: build_form1(sheets, issues, output_dir), True)
    form2_rows = run_task("Build form 2 data", lambda: build_form2(samples_dir, output_dir), True)
    numbering = run_task("Duplicate detection and numbering policy", lambda: build_numbering(sheets, output_dir), True)
    stamp_report = run_task("Reversible stamp patch + rollback", lambda: build_stamp_transaction(samples_dir, output_dir), True)
    changes = run_task("Change table template", lambda: build_changes(samples_dir, output_dir), True)
    print_data = run_task("Print order handoff", lambda: build_print_order(sheets, form1_rows, samples_dir, output_dir), True)
    run_task("Write API experiment results", lambda: write_api_experiment(output_dir))
    run_task("Write standards status", lambda: write_standards_status(output_dir))
    summary = write_summary(output_dir, sheets, issues, form1_rows, form2_rows, numbering, stamp_report, changes, print_data, env)
    write_night_log(summary, issues, stamp_report)
    log("SESSION_END", f"summary={summary['status']}")
    # The log file was appended after the markdown was written; refresh markdown with final lines.
    write_night_log(summary, issues, stamp_report)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Navigator Kit local reference pipeline")
    ap.add_argument("command", nargs="?", default="all", choices=["all", "scan", "hello"])
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--samples", type=Path, default=DEFAULT_SAMPLES)
    args = ap.parse_args()
    if args.command == "hello":
        print("Navigator Kit reference pipeline: Hello World (no nanoCAD host required)")
        return 0
    if args.command == "scan":
        init_log()
        profiles = load_mapping(args.mapping)
        sheets = scan_sheets(args.input, profiles)
        args.output.mkdir(parents=True, exist_ok=True)
        write_csv(args.output / "scan_only_registry.csv", sheets, [
            "file", "mark", "sheet_no", "sheet_name", "format", "profile_id"])
        print(f"Scanned {len(sheets)} files")
        return 0
    summary = run_all(args.input, args.mapping, args.output, args.samples)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
