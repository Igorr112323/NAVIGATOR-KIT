#!/usr/bin/env python3
"""Generate the 2026-10-27 continuation artifacts for PR #1.

The script runs after tools/navigator_kit.py all. It creates the named
deliverables requested in the second night-session prompt, a machine-readable
normative audit, a DOCX/CSV form package, a numbering patch CLI, a separated
changes table, next steps, logs, and session-2 summary files.

It uses Python 3.11 packages from requirements.txt: python-docx, pandas,
matplotlib. The core DXF pipeline itself remains standard-library only.
"""
from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "delivery"
DATA = DELIVERY / "data"
XML = DELIVERY / "xml"
DOCS = ROOT / "docs"
LOGS = ROOT / "logs"
SESSION_ID = "night-session-20261027"
CHECKED_AT = "2026-10-27"
WATERMARK = "nanoCAD НЕ запускался / не скриншот CAD"
PR_URL = "https://github.com/Igorr112323/NAVIGATOR-KIT/pull/1"
PR_LABELS = ["good first issue", "night-session"]

OFFICIAL_REGISTRY = {
    "spds2026": "https://protect.gost.ru/gost/details/17bc12e8-6579-4145-b141-56855e772e7f",
    "spds2020Replaced": "https://protect.gost.ru/gost/details/ba2db0a2-01aa-45da-a9dd-e5525bd69ec3",
    "appendixB": "https://base.garant.ru/413848474/f7ee959fd36b5699076b35abf4f52c5c/",
    "changes2023": "https://protect.gost.ru/document.aspx?control=7&id=256448",
    "changes2013Revoked": "https://protect.gost.ru/gost/details/03d72f0a-a11e-436f-ba81-41f9333ccc39",
    "formats": "https://www.spds.ru/info/standarts/2.301-68.html",
}

LOG_LINES: list[str] = []
RESULTS: dict = {}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(event: str, detail: str = "") -> None:
    LOG_LINES.append(f"{utcnow()}Z {event} {detail}".rstrip())


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp, delimiter=";"))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def md_cell(value) -> str:
    return str(value or "").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def append_logs() -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    (DELIVERY / "logs").mkdir(parents=True, exist_ok=True)
    raw = "\n".join(LOG_LINES) + "\n"
    (LOGS / "night-session-2.log").write_text(raw, encoding="utf-8")
    (DELIVERY / "logs" / "night-session-2.log").write_text(raw, encoding="utf-8")
    for path in (LOGS / "night-session.log", DELIVERY / "logs" / "night-session.log"):
        existing = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        if "SESSION_2_START" not in existing:
            with path.open("a", encoding="utf-8") as fp:
                fp.write("\n" + raw)


def run_task(name: str, func) -> None:
    try:
        func()
        log("TASK_OK", name)
    except Exception as exc:
        log("TASK_ERROR", f"{name}: {type(exc).__name__}: {exc} — ГИПОТЕЗА/ПРОВЕРИТЬ")
        raise


def normative_audit() -> None:
    dash = r"[\s\-‑–—]*"
    patterns = {
        "GOST-R-21.101-2020": re.compile(r"ГОСТ\s*Р\s*21\.101" + dash + r"2020", re.I),
        "GOST-R-21.1101-2013": re.compile(r"ГОСТ\s*Р\s*21\.1101" + dash + r"2013", re.I),
        "GOST-2.503-2013": re.compile(r"ГОСТ\s*2\.503" + dash + r"2013", re.I),
    }
    skip_suffixes = {".png", ".jpg", ".jpeg", ".zip", ".dxf", ".pyc", ".bak", ".docx"}
    occurrences: Counter[str] = Counter()
    files_with_hits: dict[str, set[str]] = {key: set() for key in patterns}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or ".venv" in path.parts:
            continue
        if path.suffix.lower() in skip_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(ROOT).as_posix()
        for key, pattern in patterns.items():
            hits = pattern.findall(text)
            if hits:
                occurrences[key] += len(hits)
                files_with_hits[key].add(rel)

    historical_prefixes = (
        "briefing.md", "README.md", "docs/standards-warning.md", "docs/sources.md",
        "docs/normative-audit.md", "delivery/README_night-session.md", "delivery/PR_BODY.md",
        "delivery/CHAT_REPLY.md", "delivery/xml/", "delivery/data/standards_status.json",
        "tools/navigator_kit.py", "tools/finalize_delivery.py", "tools/night_session_2.py",
    )
    legacy_help_prefixes = (
        "docs/api-experiment.md", "docs/sources.md", "delivery/data/api_experiment_results.json",
    )
    executable_prefixes = (
        "tools/navigator_kit.py", "delivery/xml/", "delivery/data/standards_status.json",
        "delivery/data/form1_", "delivery/data/form2_", "delivery/data/wo1_template",
        "delivery/data/wo2_template", "delivery/data/change_table",
    )
    all_hit_files = sorted(set().union(*files_with_hits.values()))

    def classify(prefixes: tuple[str, ...]) -> list[str]:
        return [p for p in all_hit_files if any(p.startswith(prefix) for prefix in prefixes)]

    audit = {
        "format": "navigator-kit.normative-audit/v1",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "checkedAtDate": CHECKED_AT,
        "officialRegistry": OFFICIAL_REGISTRY,
        "activeProfiles": {
            "spds": "GOST-R-21.101-2026-Appendix-B",
            "changesEskd": "GOST-R-2.503-2023-section-5.12",
            "changesSpds": "GOST-R-21.101-2026-section-7",
            "formats": "GOST-2.301-68-Formats",
        },
        "oldReferenceOccurrences": dict(sorted(occurrences.items())),
        "classification": {
            "historicalDocumentation": classify(historical_prefixes),
            "legacyNanoCadHelp": classify(legacy_help_prefixes),
            "executableProfile": classify(executable_prefixes),
        },
        "hypotheses": [
            "Точная геометрия граф форм 1/2 в официальном издании",
            "Приоритет раздела 7 ГОСТ Р 21.101-2026 над ЕСКД для СПДС",
            "Соответствие штатной таблицы SHEETSET редакции 2026 года",
            "Tables API и .dst в nanoCAD 26",
        ],
        "conclusion": "Legacy standard mentions are historical references only; the executable profile is 2026/2023.",
    }
    write_json(DATA / "normative_audit.json", audit)
    RESULTS["normativeAudit"] = {
        "oldReferenceOccurrences": audit["oldReferenceOccurrences"],
        "classifiedFiles": len(all_hit_files),
    }


def generate_completeness_report() -> None:
    issues = read_csv(DATA / "completeness_report.csv")
    duplicates = read_csv(DATA / "duplicate_report.csv")
    assert len(issues) == 16, f"expected 16 completeness issues, got {len(issues)}"
    assert len(duplicates) == 4, f"expected 4 duplicate groups, got {len(duplicates)}"

    frame = pd.DataFrame(issues)
    counts = frame["code"].value_counts().sort_index().to_dict()
    severity_counts = frame["severity"].value_counts().sort_index().to_dict()

    fig, ax = plt.subplots(figsize=(11, 6))
    codes = list(counts.keys())
    values = [counts[c] for c in codes]
    bars = ax.bar(codes, values, color="#f59e0b", edgecolor="#7c2d12")
    ax.bar_label(bars, padding=3, fontsize=10)
    ax.set_title("Контроль комплектности: 16 инцидентов / 8 категорий", fontsize=14, fontweight="bold")
    ax.set_ylabel("Количество", fontsize=11)
    ax.tick_params(axis="x", rotation=35, labelsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.text(0.98, 0.02, WATERMARK, ha="right", va="bottom", color="#b91c1c",
             alpha=0.65, fontsize=10, fontweight="bold",
             bbox=dict(facecolor="white", edgecolor="none", alpha=0.45, pad=4))
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    chart_path = DATA / "completeness_chart.png"
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    write_json(DATA / "completeness_chart.json", {
        "format": "navigator-kit.completeness-chart/v1",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "generatedBy": "matplotlib",
        "incidents": len(issues),
        "duplicateGroups": len(duplicates),
        "watermark": WATERMARK,
        "nanoCADScreenshot": False,
    })

    count_lines = "\n".join(f"| `{code}` | {count} |" for code, count in counts.items())
    issue_lines = "\n".join(
        "| " + " | ".join(md_cell(i.get(k, "")) for k in
                          ("issue_id", "code", "severity", "mark", "sheet_no", "field", "message", "suggestion")) + " |"
        for i in issues)
    duplicate_lines = "\n".join(
        "| " + " | ".join(md_cell(d.get(k, "")) for k in
                          ("mark", "sheet_no", "count", "keeper", "files", "recommendation")) + " |"
        for d in duplicates)

    text = f"""# Отчёт о комплектности — {CHECKED_AT}

> **Честность:** отчёт построен по 120 синтетическим DXF. nanoCAD **не запускался**. График и все PNG — подписанные диагностические материалы, а не снимки CAD.

## Сводка

| Показатель | Значение |
|---|---:|
| Просканировано DXF | 120 |
| Строк в `sheets_registry.csv/json` | 120 |
| Инцидентов комплектности | **{len(issues)}** |
| Категорий инцидентов | {len(counts)} |
| Групп дублей | **{len(duplicates)}** |
| Уровни критичности | {', '.join(f'{k}: {v}' for k, v in severity_counts.items())} |

**Важно:** нельзя утверждать, будто все 16 инцидентов — «есть в ведомости, нет файла». Это сумма разных классов: пустые поля штампа, неверные форматы, дубли, пропуски последовательности, расхождения «файл ↔ реестр» и «документ ↔ файл».

![График инцидентов](data/completeness_chart.png)

## Распределение по кодам

| Код | Количество |
|---|---:|
{count_lines}

## Все 16 инцидентов

| ID | Код | Уровень | Марка | Лист | Поле | Сообщение | Рекомендация |
|---|---|---|---|---|---|---|---|
{issue_lines}

## 4 группы дублей

| Марка | Лист | Кол-во | Хранитель | Файлы | Рекомендация |
|---|---|---:|---|---|---|
{duplicate_lines}

## Действия ГИПа

1. Заполнить пустые `sheet_name` / `sheet_no` в штампах и повторить сканирование.
2. Исправить обозначения форматов `B4`, `A6`; для `A2x3` оставить как производный формат.
3. Утвердить `minimal patch` или `full shift` через `delivery/numbering_patch.py`; скрипт готовит план, но не меняет DXF без подтверждения.
4. Сверить reference documents с ведомостью и печатью; устранить `DOC_*` / `FILE_NOT_IN_REGISTRY` / `IN_REGISTRY_NO_FILE`.
5. После правок повторно запустить `tools/navigator_kit.py all` и `tools/verify_delivery.py`.
"""
    write_text(DELIVERY / "completeness_report.md", text)
    RESULTS["completeness"] = {"incidents": len(issues), "duplicateGroups": len(duplicates), "counts": counts}


def generate_wo_templates() -> None:
    issues = read_csv(DATA / "completeness_report.csv")
    issue_files: set[str] = set()
    for issue in issues:
        for value in (issue.get("file") or "").split(";"):
            value = value.strip()
            if value:
                issue_files.add(value)

    form1 = read_csv(DATA / "form1_vedomost.csv")
    form2 = read_csv(DATA / "form2_vedomost.csv")
    assert len(form1) == 120, f"expected 120 form 1 rows, got {len(form1)}"
    assert len(form2) >= 6, f"expected at least 6 form 2 rows, got {len(form2)}"

    def status_for(file_value: str) -> str:
        return "ЕСТЬ_ИНЦИДЕНТЫ" if file_value.strip() in issue_files else "OK"

    wo1_rows = [{
        "Марка": r["Марка"], "Лист": r["Лист"], "Наименование": r["Наименование"],
        "Примечание": r["Примечание"], "Статус": status_for(r.get("Файл", "")),
        "Файл": r.get("Файл", ""),
    } for r in form1]
    wo2_rows = [{
        "Раздел": r["Раздел"], "Обозначение": r["Обозначение"],
        "Наименование": r["Наименование"], "Примечание": r["Примечание"],
        "Статус": status_for(r.get("Файл", "")), "Файл": r.get("Файл", ""),
    } for r in form2]

    write_csv(DATA / "wo1_template.csv", wo1_rows,
              ["Марка", "Лист", "Наименование", "Примечание", "Статус", "Файл"])
    write_csv(DATA / "wo2_template.csv", wo2_rows,
              ["Раздел", "Обозначение", "Наименование", "Примечание", "Статус", "Файл"])

    doc = Document()
    doc.core_properties.title = "Комплект-Навигатор — форма 1 (данные)"
    doc.core_properties.subject = "ГОСТ Р 21.101-2026, Приложение Б"
    doc.core_properties.author = "ИИ-куратор / NAVIGATOR-KIT"
    doc.core_properties.keywords = "ГОСТ Р 21.101-2026; форма 1; ведомость; ГИПОТЕЗА/ПРОВЕРИТЬ"

    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)
    section.footer.paragraphs[0].text = WATERMARK

    title = doc.add_heading("Форма 1 — ведомость рабочих чертежей", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    warning = doc.add_paragraph()
    warning.add_run("Нормативная база: ").bold = True
    warning.add_run("ГОСТ Р 21.101-2026, обязательное Приложение Б. ")
    warning.add_run("Графы: «Лист», «Наименование», «Примечание». ").bold = False
    warning.add_run("Точные размеры таблицы — ГИПОТЕЗА/ПРОВЕРИТЬ.").bold = True
    doc.add_paragraph(
        "Этот DOCX содержит данные формы 1 и не является сертифицированным векторным чертежом. "
        "Полные 120 строк находятся в wo1_template.csv; исходный реестр — sheets_registry.csv/json."
    )
    doc.add_paragraph(WATERMARK).runs[0].bold = True

    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    headers = ("Лист", "Наименование", "Примечание")
    for idx, header in enumerate(headers):
        cell = table.rows[0].cells[idx]
        cell.text = header
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(10)
    for r in form1[:12]:
        cells = table.add_row().cells
        cells[0].text = r["Лист"]
        cells[1].text = r["Наименование"]
        cells[2].text = r["Примечание"] or "—"
    doc.add_paragraph(
        "Показаны первые 12 строк из 120. Технические колонки «Марка», «Статус», «Файл» "
        "вынесены в CSV и не вставляются в нормативную форму чертежа."
    )
    doc.save(DATA / "wo1_template.docx")

    # Ensure the DOCX is a valid OPC package, not an empty placeholder.
    with zipfile.ZipFile(DATA / "wo1_template.docx") as zf:
        assert "[Content_Types].xml" in zf.namelist()

    RESULTS["forms"] = {
        "form1Rows": len(wo1_rows), "form2Rows": len(wo2_rows),
        "wo1Docx": "delivery/data/wo1_template.docx",
    }


NUMBERING_SCRIPT = r'''#!/usr/bin/env python3
"""Prepare minimal or full-shift sheet-number patches from numbering_plan.csv.

This tool DOES NOT modify DXF/DWG files. It prints or writes a JSON patch plan
that a human or a verified CAD adapter can apply later.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "delivery" / "data"
PLAN = DATA / "numbering_plan.csv"
DUPLICATES = DATA / "duplicate_report.csv"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp, delimiter=";"))


def duplicate_groups() -> list[dict]:
    return read_csv(DUPLICATES)


def minimal_patch(rows: list[dict]) -> list[dict]:
    """Change only the non-keeper file of each duplicate group."""
    groups = duplicate_groups()
    targets: dict[str, str] = {}
    for group in groups:
        for value in (group.get("to_change") or "").split(";"):
            value = value.strip()
            if value:
                targets[value] = group.get("sheet_no", "")
    patches = []
    for row in rows:
        old = row.get("old_sheet_no", "")
        new = row.get("minimal_new_no", old)
        if old != new or row.get("file") in targets:
            patches.append({
                "file": row.get("file", ""), "old": old, "new": new,
                "strategy": "minimal", "action": "SET_SHEET_NO",
                "requires_approval": True,
            })
    return patches


def full_shift(rows: list[dict]) -> list[dict]:
    """Apply the precomputed full-shift numbering to all 120 rows."""
    patches = []
    for row in rows:
        old = row.get("old_sheet_no", "")
        new = row.get("full_shift_new_no", old)
        if old != new:
            patches.append({
                "file": row.get("file", ""), "old": old, "new": new,
                "strategy": "full_shift", "action": "SET_SHEET_NO",
                "requires_approval": True,
            })
    return patches


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare sheet-number patch plan")
    ap.add_argument("--strategy", choices=["minimal", "full"], default="minimal")
    ap.add_argument("--output", type=Path, help="Write JSON plan to this path instead of stdout")
    args = ap.parse_args()
    rows = read_csv(PLAN)
    patches = minimal_patch(rows) if args.strategy == "minimal" else full_shift(rows)
    result = {
        "format": "navigator-kit.numbering-patch/v1",
        "strategy": args.strategy,
        "planRows": len(rows),
        "patchCount": len(patches),
        "duplicateGroups": len(duplicate_groups()),
        "nanoCADExecuted": False,
        "appliedToFiles": False,
        "patches": patches,
        "warning": "Do not apply to production DWG without a verified MultiCAD .NET adapter, backup, and rollback test.",
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {len(patches)} patches to {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def generate_numbering_patch() -> None:
    write_text(DELIVERY / "numbering_patch.py", NUMBERING_SCRIPT)
    # Check that the generated script is syntactically valid without executing it.
    compile(NUMBERING_SCRIPT, str(DELIVERY / "numbering_patch.py"), "exec")
    RESULTS["numbering"] = {
        "script": "delivery/numbering_patch.py",
        "strategies": ["minimal", "full"],
        "planRows": len(read_csv(DATA / "numbering_plan.csv")),
        "duplicateGroups": len(read_csv(DATA / "duplicate_report.csv")),
    }


def generate_changes_table() -> None:
    normative_header = "| Изм. | Лист | № докум. | Подп. | Дата |"
    normative_sep = "|---|---|---|---|---|"
    normative_empty = "|  |  |  |  |  |"
    text = f"""# Таблица изменений — {CHECKED_AT}

В файле **две разные таблицы**. Их нельзя смешивать.

## 1. Нормативная таблица изменений основной надписи

Профиль: **ГОСТ Р 2.503-2023** (п. 5.12) и раздел 7 **ГОСТ Р 21.101-2026** для СПДС. Графы: `Изм.`, `Лист`, `№ докум.`, `Подп.`, `Дата`. Допустимые маркеры в графе «Лист»: `Зам.`, `Нов.`, `Все`, прочерк.

{normative_header}
{normative_sep}
{normative_empty}
{normative_empty}
{normative_empty}
{normative_empty}
{normative_empty}
{normative_empty}
{normative_empty}
{normative_empty}
{normative_empty}
{normative_empty}

**ГИПОТЕЗА/ПРОВЕРИТЬ:** приоритет требований раздела 7 ГОСТ Р 21.101-2026 над ЕСКД и точная геометрия таблицы в чертеже должны быть подтверждены нормоконтролёром. Запись «Аннулир.» **не** является значением графы «Лист».

## 2. Операционная таблица управления изменениями — НЕ ГОСТ

Эта таблица добавлена потому, что её колонки запрошены в задании (`Номер листа`, `Тип изменений`, `Дата`, `Автор`, `Статус`). Она **не заменяет** нормативную таблицу изменений в основной надписи и не претендует на соответствие ГОСТ Р 2.503-2023.

| Номер листа | Тип изменений | Дата | Автор | Статус |
|---|---|---|---|---|
| 3 | Замена блока «Резервуар» | {CHECKED_AT} | ИИ-куратор | Черновик |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

Связь: `delivery/data/change_table_template.csv` — пустая нормативная таблица; `delivery/data/change_register.csv` — технический реестр операций; `delivery/data/change_table_notes.md` — пояснение. До появления реального извещения об изменении все строки операционной таблицы остаются черновиками.
"""
    write_text(DELIVERY / "changes_table.md", text)
    RESULTS["changesTable"] = {"normativeColumns": 5, "operationalColumns": 5, "sampleRow": True}


def generate_next_steps() -> None:
    text = f"""# Что сделать до следующего раза — {CHECKED_AT}

Пять приоритетных задач. P0 — блокирует подачу, P1 — нужно для рабочего прототипа, P2 — повышает качество подачи.

| # | Приоритет | Задача | Критерий готовности | Почему сейчас |
|---|---|---|---|---|
| 1 | **P0** | Нормоконтроль по официальному тексту ГОСТ Р 21.101-2026 | Сверены геометрия форм 1/2, приоритет раздела 7 и требования конкурса к редакции стандарта | [Реестр Росстандарта]({OFFICIAL_REGISTRY['spds2026']}) подтверждает действие с 01.04.2026; точные размеры граф остаются **ГИПОТЕЗА/ПРОВЕРИТЬ** |
| 2 | **P0** | Windows-стенд + nanoCAD 26 + лицензия + SDK 26 | Запущены `NK_HELLO`, `SdkProbe`, собран `.github/workflows/windows-build.yml` на реальном runner | В Linux sandbox нет Windows, nanoCAD, SDK и лицензии; образовательная лицензия требует nanoPassport |
| 3 | **P1** | 3 × 40 реальных DWG и обратимая запись штампов | Проверены `Database`/`Transaction`, `.bak`, rollback SHA-256, атрибуты двух реальных шаблонов | Сейчас доказательства получены только на синтетических DXF |
| 4 | **P1** | Tables API, SHEETSET и `.dst` | Порядок layouts совпадает с `print_order.json`; прямая правка `.dst` не требуется | `GetSheetSets()` не подтверждён; `.dst` напрямую не редактировался |
| 5 | **P2** | Демо ≤3 МБ и senior code review | GIF «папка → реестр → правка → сдвиг → печать», устранены все **ГИПОТЕЗА/ПРОВЕРИТЬ**, обновлены скриншоты | Конкурсная подача требует короткого сценария «ночь ГИПа → 2 минуты» |

## Непосредственный чек-лист перед мержем PR #1

- [ ] Запустить Windows workflow и приложить логи `dotnet build`.
- [ ] Заменить 12 диагностических PNG реальными снимками только после запуска nanoCAD; до этого сохранять watermark «{WATERMARK}».
- [ ] Снять метки `good first issue` / `night-session` не требуется: они добавлены по запросу пользователя.
- [ ] Обновить `delivery/README_night-session.md` датой следующей сессии и новым commit SHA.
- [ ] Повторить `python tools/verify_delivery.py --check-only` после любых изменений в `delivery/`.
"""
    write_text(DELIVERY / "next_steps.md", text)
    RESULTS["nextSteps"] = {"tasks": 5, "priorities": ["P0", "P0", "P1", "P1", "P2"]}


def generate_night_session_2_log() -> None:
    task_rows = [
        ("Синхронизация GitHub", "DONE", "origin/arena/ec9fddc1-navigator-kit → bc47b35; PR #1 открыт"),
        ("Повторная проверка реестра ГОСТ", "DONE", "2026-10-27, официальные ссылки в normative_audit.json"),
        ("Windows-VM workflow", "PREPARED", "файл создан, реальный запуск вне sandbox"),
        ("XML-маппинг + XSD", "DONE", "keyAttributes sheet_no/format, XSD valid"),
        ("120 DXF → реестр", "DONE", "120 строк CSV/JSON, SHA-256"),
        ("Контроль комплектности", "DONE", "16 инцидентов, 4 группы дублей, график"),
        ("Формы 1/2", "DONE", "wo1_template.docx/csv, wo2_template.csv"),
        ("Нумератор", "DONE", "numbering_patch.py: minimal + full"),
        ("Таблица изменений", "DONE", "нормативная и операционная таблицы разделены"),
        ("PNG 1600×1200", "DONE", "12 макетов + постоянный watermark"),
        ("PR body / labels / ZIP", "DONE_AFTER_FINALIZE", "обновляются finalize_delivery.py и gh api"),
    ]
    rows = "\n".join(f"| {i+1} | {name} | `{status}` | {detail} |" for i, (name, status, detail) in enumerate(task_rows))
    text = f"""# Ночная сессия 2 — {SESSION_ID}

Дата: **{CHECKED_AT}**. Продолжение первой сессии от 2026-10-26, без создания второй ветки: работа ведётся в `arena/ec9fddc1-navigator-kit` и обновляет [PR #1]({PR_URL}).

## Статус честности

- nanoCAD 26, Windows, MultiCAD .NET SDK 26 и лицензия в sandbox **отсутствуют**.
- Все PNG — диагностические макеты с постоянным водяным знаком «{WATERMARK}», а не скриншоты CAD.
- C# сборка Portable Core/CLI подготовлена к Windows workflow, но в Linux sandbox не выполнялась.
- Всё, что связано с реальными DWG, `.dst`, Tables API и `GetSheetSets()`, остаётся **ГИПОТЕЗА/ПРОВЕРИТЬ**.

## Матрица задач

| # | Задача | Статус | Результат |
|---:|---|---|---|
{rows}

## Ключевые числа

- 120 синтетических DXF R2010, 120 строк `sheets_registry.csv/json`.
- 16 инцидентов комплектности в 8 категориях; 4 группы дублей.
- 120 строк формы 1, {RESULTS.get('forms', {}).get('form2Rows', 8)} строк формы 2.
- 12 PNG 1600×1200; `cornerWatermark: true` в `screenshots_manifest.json`.
- Rollback `True`, print order consistency `True`.

## Ошибки и ограничения

1. Локальная ветка была на `7e4fcf3`, а удалённая — на `bc47b35`; перед работой выполнен `git merge --ff-only origin/arena/ec9fddc1-navigator-kit`.
2. `/home/user/.venv` отсутствовал в обновлённом sandbox; создан заново, пакеты из `requirements.txt` установлены.
3. Исходный `briefing.md` по-прежнему отсутствует; файл в репозитории — reconstruction.
4. `good first issue` — стандартная метка GitHub; `night-session` создаётся через REST API перед назначением PR.
5. Workflow `.github/workflows/windows-build.yml` подготовлен статически; успешный запуск на реальной VM ещё не подтверждён.

## Сырой лог

```text
{{LOG_LINES}}
```
"""
    text = text.replace("{LOG_LINES}", "\n".join(LOG_LINES))
    write_text(DELIVERY / "night-session-2.md", text)


def generate_session2_summary() -> None:
    tasks = [
        {"id": 1, "task": "GitHub sync and re-read briefing", "status": "DONE"},
        {"id": 2, "task": "Environment and normative registry re-check", "status": "DONE"},
        {"id": 3, "task": "GitHub Actions Windows VM workflow", "status": "PREPARED_NOT_EXECUTED"},
        {"id": 4, "task": "XML stamp mapping with sheet/format key attributes", "status": "DONE_XSD_VALID"},
        {"id": 5, "task": "120 synthetic DXF to sheets_registry", "status": "DONE"},
        {"id": 6, "task": "completeness_report.md with 16 incidents and 4 duplicate groups", "status": "DONE"},
        {"id": 7, "task": "wo1_template.docx / wo1_template.csv / wo2_template.csv", "status": "DONE"},
        {"id": 8, "task": "numbering_patch.py with minimal patch and full shift", "status": "DONE"},
        {"id": 9, "task": "changes_table.md with normative and operational tables", "status": "DONE"},
        {"id": 10, "task": "12 PNG 1600x1200 with persistent watermark", "status": "DONE_BY_RENDERER"},
        {"id": 11, "task": "next_steps.md, report, PR body, labels, ZIP", "status": "DONE_AFTER_FINALIZE"},
    ]
    summary = {
        "format": "navigator-kit.session2-summary/v1",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "checkedAtDate": CHECKED_AT,
        "branch": "arena/ec9fddc1-navigator-kit",
        "baseRemoteCommit": "bc47b35",
        "prUrl": PR_URL,
        "requestedLabels": PR_LABELS,
        "officialRegistry": OFFICIAL_REGISTRY,
        "tasks": tasks,
        "results": RESULTS,
        "nanoCADExecuted": False,
        "dotnetBuildExecutedInSandbox": False,
        "windowsWorkflow": ".github/workflows/windows-build.yml",
        "watermark": WATERMARK,
        "remainingHypotheses": [
            "Form 1/2 exact geometry",
            "GOST R 21.101-2026 section 7 priority for SPDS",
            "MultiCAD .NET SDK 26 TFM/DLLs/API",
            "Tables API and .dst export",
            "Real DWG, license, and Windows VM workflow run",
        ],
    }
    write_json(DATA / "session2_summary.json", summary)
    write_json(DATA / "pr_labels.json", {
        "format": "navigator-kit.pr-labels/v1",
        "sessionId": SESSION_ID,
        "prUrl": PR_URL,
        "requestedLabels": PR_LABELS,
        "note": "Labels are applied via GitHub REST API; good first issue is built-in, night-session is created if absent.",
    })
    RESULTS["summary"] = {"tasks": len(tasks), "labels": PR_LABELS}


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    log("SESSION_2_START", f"id={SESSION_ID}; branch=arena/ec9fddc1-navigator-kit; pr={PR_URL}")
    run_task("normative_audit", normative_audit)
    run_task("completeness_report_and_chart", generate_completeness_report)
    run_task("wo1_wo2_templates", generate_wo_templates)
    run_task("numbering_patch", generate_numbering_patch)
    run_task("changes_table", generate_changes_table)
    run_task("next_steps", generate_next_steps)
    run_task("session2_log", generate_night_session_2_log)
    run_task("session2_summary", generate_session2_summary)
    log("SESSION_2_END", f"status=PASS; artifacts={len(RESULTS)} groups")
    append_logs()
    print(json.dumps({
        "status": "PASS",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "results": RESULTS,
        "log": "logs/night-session-2.log",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
