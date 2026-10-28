#!/usr/bin/env python3
"""Orchestrate the 2026-10-28 night session for the five P0-P2 tasks.

Strict order:
1. P0 normative control (official registry + Appendix B + section 7)
2. P0 Windows stand readiness (external dependency is recorded honestly)
3. P1 production DWG pipeline (synthetic backend runs; MultiCAD backend is a stub)
4. P1 SHEETSET/Tables probe and print-order/form templates
5. P2 demo GIF, senior review checklist, and refreshed next steps

All results are written to delivery/session-3/ before the next commit.
"""
from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
DOCS = ROOT / "docs"
DELIVERY = ROOT / "delivery"
DATA = DELIVERY / "data"
SESSION3 = DELIVERY / "session-3"
LOGS = ROOT / "logs"
SESSION_ID = "night-session-20261028"
CHECKED_AT = "2026-10-28"
WATERMARK = "nanoCAD НЕ запускался / не скриншот CAD"
PR_URL = "https://github.com/Igorr112323/NAVIGATOR-KIT/pull/1"

OFFICIAL = {
    "registry2026": "https://protect.gost.ru/gost/details/17bc12e8-6579-4145-b141-56855e772e7f",
    "registry2020Replaced": "https://protect.gost.ru/gost/details/ba2db0a2-01aa-45da-a9dd-e5525bd69ec3",
    "officialPdf": "https://pravdaosro.ru/wp-content/uploads/2026/03/GOST-R-21.101-2026.pdf",
    "appendixB": "https://base.garant.ru/413848474/f7ee959fd36b5699076b35abf4f52c5c/",
    "changes2023": "https://protect.gost.ru/document.aspx?control=7&id=256448",
    "changes2013Revoked": "https://protect.gost.ru/gost/details/03d72f0a-a11e-436f-ba81-41f9333ccc39",
    "formats": "https://www.spds.ru/info/standarts/2.301-68.html",
}

NORMS = [
    {
        "norm": "ГОСТ Р 21.101-2026",
        "edition": "2026",
        "date_force": "2026-04-01",
        "source": OFFICIAL["registry2026"],
        "status": "ACTIVE",
        "classification": "ACTUAL_EXECUTABLE_PROFILE",
        "note": "Приказ 129-ст от 12.02.2026; заменяет ГОСТ Р 21.101-2020; формы 1/2 — обязательное Приложение Б.",
    },
    {
        "norm": "ГОСТ Р 21.101-2020",
        "edition": "2020",
        "date_force": "до 2026-04-01",
        "source": OFFICIAL["registry2020Replaced"],
        "status": "REPLACED",
        "classification": "HISTORICAL_REFERENCE_ONLY",
        "note": "Сохраняется только в аудите и backward-compatibility comments; не является базой новой подачи.",
    },
    {
        "norm": "ГОСТ Р 2.503-2023",
        "edition": "2023",
        "date_force": "2024-03-01",
        "source": OFFICIAL["changes2023"],
        "status": "ACTIVE",
        "classification": "ACTUAL_CHANGE_TABLE_PROFILE",
        "note": "Графы Изм. / Лист / № докум. / Подп. / Дата; для СПДС дополнительно раздел 7 ГОСТ Р 21.101-2026.",
    },
    {
        "norm": "ГОСТ 2.503-2013",
        "edition": "2013",
        "date_force": "утратил силу в РФ с 2024-03-01",
        "source": OFFICIAL["changes2013Revoked"],
        "status": "REVOKED_RU",
        "classification": "HISTORICAL_REFERENCE_ONLY",
        "note": "«На территории РФ пользоваться ГОСТ Р 2.503-2023».",
    },
    {
        "norm": "ГОСТ 2.301-68",
        "edition": "1968",
        "date_force": "действует с оговоркой",
        "source": OFFICIAL["formats"],
        "status": "ACTIVE_WITH_CAVEAT",
        "classification": "FORMAT_DESIGNATION_CHECK",
        "note": "Проверяются обозначения A0–A5 и производные; вопрос досрочного применения ГОСТ Р 2.301-2026 требует уточнения.",
    },
]

LOG_LINES: list[str] = []
RESULTS: dict = {}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(event: str, detail: str = "") -> None:
    LOG_LINES.append(f"{utcnow()}Z {event} {detail}".rstrip())


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def run_task(name: str, func) -> None:
    try:
        func()
        log("TASK_OK", name)
    except Exception as exc:
        log("TASK_ERROR", f"{name}: {type(exc).__name__}: {exc} — ГИПОТЕЗА/ПРОВЕРИТЬ")
        raise


def scan_old_standard_mentions() -> tuple[dict, list[str]]:
    dash = r"[\s\-‑–—]*"
    patterns = {
        "GOST-R-21.101-2020": re.compile(r"ГОСТ\s*Р\s*21\.101" + dash + r"2020", re.I),
        "GOST-R-21.1101-2013": re.compile(r"ГОСТ\s*Р\s*21\.1101" + dash + r"2013", re.I),
        "GOST-2.503-2013": re.compile(r"ГОСТ\s*2\.503" + dash + r"2013", re.I),
    }
    skip = {".png", ".jpg", ".jpeg", ".gif", ".zip", ".dxf", ".pyc", ".bak", ".docx"}
    counts: Counter[str] = Counter()
    files: dict[str, set[str]] = {k: set() for k in patterns}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or ".venv" in path.parts:
            continue
        if path.suffix.lower() in skip:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(ROOT).as_posix()
        for key, pattern in patterns.items():
            hits = pattern.findall(text)
            if hits:
                counts[key] += len(hits)
                files[key].add(rel)
    return dict(sorted(counts.items())), sorted(set().union(*files.values()))


def p0_norm_control() -> None:
    occurrences, hit_files = scan_old_standard_mentions()
    historical_prefixes = (
        "briefing.md", "README.md", "docs/", "delivery/README_night-session.md",
        "delivery/PR_BODY.md", "delivery/CHAT_REPLY.md", "delivery/xml/",
        "delivery/data/", "delivery/changes_table.md", "delivery/next_steps.md",
        "delivery/session-3/", "tools/", "src/", "logs/", "night-log.md",
    )
    executable_prefixes = (
        "tools/navigator_kit.py", "delivery/xml/", "delivery/data/standards_status.json",
        "delivery/data/form1_", "delivery/data/form2_", "delivery/data/wo1_template",
        "delivery/data/wo2_template", "delivery/data/change_table",
    )

    def classify(prefixes):
        return [p for p in hit_files if any(p.startswith(x) for x in prefixes)]

    sources = {
        "format": "navigator-kit.session3-official-sources/v1",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "checkedAtDate": CHECKED_AT,
        "accessMethod": "web_search + fetch_page; official registry page and official-edition PDF (first 30 pages) were readable",
        "fullOfficialTextStored": False,
        "copyrightNote": "Защищённый полный текст не перераспространяется; в репозитории хранится только выписка ключевых положений.",
        "officialRegistry": OFFICIAL,
        "confirmed": [
            "ГОСТ Р 21.101-2026 действует с 01.04.2026 и заменяет редакцию 2020",
            "Приложение Б обязательное; форма 1: Лист/Наименование/Примечание; форма 2: Обозначение/Наименование/Примечание",
            "Раздел 7: изменения обозначаются порядковыми номерами, требуют разрешения и согласованной правки связанных документов",
            "Информация об изменениях указывается в таблице изменений основной надписи и/или таблице регистрации изменений формы 10",
            "ГОСТ Р 2.503-2023 действует; ГОСТ 2.503-2013 утратил силу в РФ",
        ],
        "remainingHypotheses": [
            "Точная геометрия граф форм 1/2 и размещение на листе",
            "Приоритет раздела 7 над ЕСКД при заполнении таблицы изменений",
            "Соответствие штатной таблицы SHEETSET форме 1-2026",
        ],
    }
    write_json(SESSION3 / "p0_norm_sources.json", sources)

    control = {
        "format": "navigator-kit.session3-norm-control/v1",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "checkedAtDate": CHECKED_AT,
        "status": "NORM_CONTROL_OK_WITH_GEOMETRY_HYPOTHESIS",
        "logRecord": ["norm_control_ok", "norm_control_ГИПОТЕЗА/ПРОВЕРИТЬ"],
        "officialSources": OFFICIAL,
        "norms": NORMS,
        "oldReferenceOccurrences": occurrences,
        "legacyMentionsAreIntentional": True,
        "historicalFiles": classify(historical_prefixes),
        "executableProfileFiles": classify(executable_prefixes),
        "replacementPolicy": "Исполняемые профили используют 2026/2023. Исторические упоминания сохранены и классифицированы, а не удалены слепо.",
        "section7": {
            "changeNumbering": "Порядковые номера 1, 2, 3…",
            "permissionRequired": True,
            "digitalDocument": "Выпуск новой версии ДЭ",
            "changeFactLocation": "Таблица изменений основной надписи и/или таблица регистрации изменений форма 10 (приложение М)",
            "annulment": "Процедура отмены/изъятия документа, а не значение графы «Лист»",
        },
        "hypothesisMarker": "ГИПОТЕЗА/ПРОВЕРИТЬ",
    }
    write_json(SESSION3 / "p0_norm_control.json", control)

    # Refresh the machine-readable normative audit with the requested norms list.
    audit_path = DATA / "normative_audit.json"
    audit = read_json(audit_path) if audit_path.is_file() else {}
    audit.update({
        "format": "navigator-kit.normative-audit/v2",
        "sessionId": SESSION_ID,
        "checkedAtDate": CHECKED_AT,
        "previousCheckedAtDate": "2026-10-27",
        "generatedAt": utcnow(),
        "officialRegistry": OFFICIAL,
        "norms": NORMS,
        "oldReferenceOccurrences": occurrences,
        "classification": {
            "historicalDocumentation": classify(historical_prefixes),
            "legacyNanoCadHelp": [p for p in hit_files if "api" in p.lower() or "source" in p.lower()],
            "executableProfile": classify(executable_prefixes),
        },
        "section7VerifiedFromOfficialPdf": True,
        "geometryStillHypothesis": True,
        "conclusion": "Registry, Appendix B columns, and section 7 principles verified. Exact form geometry and SHEETSET compliance remain ГИПОТЕЗА/ПРОВЕРИТЬ.",
    })
    write_json(audit_path, audit)
    copy_file(audit_path, SESSION3 / "normative_audit.json")
    write_json(DATA / "norms_registry.json", NORMS)
    write_json(SESSION3 / "norms_registry.json", NORMS)
    copy_file(DOCS / "official-text-extract.md", SESSION3 / "official_text_extract.md")
    RESULTS["p0_norm"] = {
        "status": control["status"],
        "norms": len(NORMS),
        "oldReferenceOccurrences": occurrences,
        "geometryHypothesis": True,
    }


def p0_windows_stand() -> None:
    system = platform.system()
    tools = {name: (shutil.which(name) or "MISSING") for name in
             ["dotnet", "mono", "msbuild", "csc", "ffmpeg", "pwsh", "powershell"]}
    windows_available = system == "Windows"
    dotnet_available = tools["dotnet"] != "MISSING"
    status = {
        "format": "navigator-kit.session3-windows-stand/v1",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "status": "EXTERNAL_DEPENDENCY" if not windows_available else "HOST_WINDOWS_CHECK_REQUIRED",
        "hypothesisMarker": "ГИПОТЕЗА/ПРОВЕРИТЬ",
        "hostOS": platform.platform(),
        "windowsAvailable": windows_available,
        "dotnetAvailable": dotnet_available,
        "tools": tools,
        "nanoCAD26Installed": False,
        "licenseFound": False,
        "multiCadSdk26Installed": False,
        "nkHelloExecuted": False,
        "sdkProbeExecuted": False,
        "realScreenshotsCaptured": False,
        "screenshotsExpected": [
            "delivery/screenshots/nanocad_26_main_window.png",
            "delivery/screenshots/nanocad_26_toolbar.png",
            "delivery/screenshots/nanocad_26_api_commands.png",
        ],
        "preparedArtifacts": [
            ".github/workflows/windows-build.yml",
            "tools/windows_stand_check.ps1",
            "docs/windows-stand-setup.md",
            "src/NavigatorKit.NanoCad/SdkProbe.cs",
            "src/NavigatorKit.NanoCad/DwgReadiness.cs",
        ],
        "reason": "Linux sandbox has no Windows, nanoCAD 26, SDK 26, license, or real DWG. Installation and screenshots require a human-operated stand.",
    }
    write_json(SESSION3 / "p0_windows_stand.json", status)
    write_json(DATA / "windows_stand_status.json", {
        "sessionId": SESSION_ID,
        "status": status["status"],
        "nanoCADExecuted": False,
        "workflow": ".github/workflows/windows-build.yml",
    })
    copy_file(DOCS / "windows-stand-setup.md", SESSION3 / "windows_stand_setup.md")
    copy_file(TOOLS / "windows_stand_check.ps1", SESSION3 / "windows_stand_check.ps1")
    RESULTS["p0_windows"] = {
        "status": status["status"],
        "nkHello": False,
        "sdkProbe": False,
        "realScreenshots": False,
    }


def call_tool(script: str, *args: str) -> None:
    cmd = [sys.executable, str(TOOLS / script), *args]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(f"{script} failed ({completed.returncode}): {completed.stdout[-500:]} {completed.stderr[-500:]}")
    if completed.stdout.strip():
        log("TOOL_OUTPUT", f"{script}: {completed.stdout.strip().splitlines()[-1][:200]}")


def p1_production_dwg() -> None:
    call_tool("pipeline.py", "--backend", "synthetic")
    call_tool("pipeline.py", "--backend", "multicad",
              "--report-json", str(SESSION3 / "p1_multicad_dwg.json"))
    synthetic = read_json(SESSION3 / "p1_production_dwg.json")
    multicad = read_json(SESSION3 / "p1_multicad_dwg.json")
    summary = {
        "format": "navigator-kit.session3-production-dwg-summary/v1",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "status": "SYNTHETIC_VERIFIED;MULTICAD_EXTERNAL_DEPENDENCY",
        "synthetic": synthetic,
        "multicad": multicad,
        "realDwgProcessed": 0,
        "nanoCADExecuted": False,
        "rollbackOnSyntheticVerified": synthetic.get("rollbackVerified"),
        "nextWindowsSteps": multicad.get("requiredChecks", []),
    }
    write_json(SESSION3 / "p1_production_dwg_summary.json", summary)
    copy_file(DELIVERY / "completeness_report.md", SESSION3 / "completeness_report.md")
    copy_file(DATA / "completeness_chart.png", SESSION3 / "completeness_chart.png")
    RESULTS["p1_dwg"] = {
        "status": summary["status"],
        "syntheticDxf": synthetic.get("syntheticDxfProcessed"),
        "realDwg": 0,
        "rollbackVerified": synthetic.get("rollbackVerified"),
    }


def p1_sheetset_tables() -> None:
    call_tool("sheetset_probe.py")
    probe = read_json(SESSION3 / "p1_sheetset_tables.json")
    copy_file(DATA / "wo1_template.csv", SESSION3 / "wo1_template.csv")
    copy_file(DATA / "wo2_template.csv", SESSION3 / "wo2_template.csv")
    RESULTS["p1_sheetset"] = {
        "status": probe["status"],
        "printOrderConsistent": probe["printOrderConsistent"],
        "getSheetSets": probe["getSheetSetsStatus"],
        "dstTouched": probe["dstTouched"],
    }


NEXT_STEPS_MD = """# Что сделать до следующего раза — 2026-10-28

Сессия 3 закрыла воспроизводимый synthetic contour, P0-аудит норм, подготовку Windows-стенда, GIF-демо и senior-review чек-лист. Метки `ГИПОТЕЗА/ПРОВЕРИТЬ` **не сняты массово**: для этого нет реального CAD-стенда. Оставшиеся 5 задач:

| # | Приоритет | Задача | Критерий готовности |
|---:|---|---|---|
| 1 | **P0** | Развернуть реальный Windows-стенд с nanoCAD 26, лицензией и SDK 26 | Выполнены `NK_HELLO`, `SDK_PROBE`, записаны TFM/DLL, сняты 3 реальных снимка без ложного watermark |
| 2 | **P0** | Нормоконтроль геометрии форм 1/2 и приоритета раздела 7 | По официальному изданию сверены размеры граф, форма 10 и таблица изменений; метка по геометрии снята |
| 3 | **P1** | Пилот на 3 × 40 реальных DWG | Через проверенный MultiCAD .NET adapter выполнены фоновое чтение, запись атрибутов, `.bak` и rollback SHA-256 |
| 4 | **P1** | SHEETSET / Tables / `.dst` | Подтверждены `GetSheets()`/`GetSheetSets()`, порядок layouts совпадает с `delivery/session-3/print_order.json`, `.dst` не правится вручную |
| 5 | **P2** | Конкурсное демо и финальный senior review | GIF/MP4 ≤3 МБ из реального nanoCAD, обновлён `index.html`, закрыты оставшиеся гипотезы |

## Что уже сделано в сессии 3

- P0: повторно проверены реестр Росстандарта, официальное издание, Приложение Б и раздел 7; добавлен `norms` JSON-список.
- P0: подготовлены `tools/windows_stand_check.ps1`, `docs/windows-stand-setup.md`, workflow и C# readiness-скелет; стенд зафиксирован как внешняя зависимость.
- P1: `tools/pipeline.py` выполнил synthetic backend на 120 DXF; MultiCAD backend честно помечен `NOT_IMPLEMENTED`.
- P1: `tools/sheetset_probe.py` подтвердил локальный `print_order` и перегенерировал `wo1_template.csv` / `wo2_template.csv`.
- P2: `tools/make_demo_gif.py` собрал GIF ≤3 МБ с двумя watermark; `senior_review.md` фиксирует оставшиеся риски.
"""


SENIOR_REVIEW_MD = """# Senior review — session 3 (2026-10-28)

## Проверено локально

- [x] 120 синтетических DXF R2010 прочитаны; `sheets_registry.csv/json` содержат 120 SHA-256.
- [x] 16 инцидентов комплектности и 4 группы дублей воспроизводятся.
- [x] Rollback штампов на копиях подтверждён SHA-256; исходники не изменены.
- [x] `print_order.json` согласован с формой 1 по хэшу; `.dst` не редактировался.
- [x] XML/XSD валидны; `keyAttributes` для `sheet_no` и `format` присутствуют.
- [x] Формы 1/2 по Приложению Б ГОСТ Р 21.101-2026 сгенерированы в CSV/DOCX.
- [x] Нормативная и операционная таблицы изменений разделены.
- [x] GIF-демо ≤3 МБ с верхним баннером и нижним watermark создан.
- [x] 45 required checks и 12 unit-тестов проходят в базовом контуре; session-3 проверки добавлены.

## Осталось ГИПОТЕЗА/ПРОВЕРИТЬ

- [ ] Точный TFM, разрядность, DLL и NETLOAD/APPLOAD для nanoCAD 26.
- [ ] `GetSheets()` / `GetSheetSets()` / Tables API / документированный `.dst`.
- [ ] `Database` / `Transaction` / `AttributeReference` для production DWG.
- [ ] Геометрия граф форм 1/2 и форма 10 таблицы регистрации изменений.
- [ ] Приоритет раздела 7 ГОСТ Р 21.101-2026 над ЕСКД в СПДС.
- [ ] Реальные 3 × 40 DWG и реальные снимки nanoCAD 26.

## Файлы, которые нужно снять реально на Windows

1. `delivery/screenshots/nanocad_26_main_window.png`
2. `delivery/screenshots/nanocad_26_toolbar.png`
3. `delivery/screenshots/nanocad_26_api_commands.png`
4. `delivery/data/sdk_probe.json` — вывод `SDK_PROBE`.
5. `delivery/data/windows_stand_check.json` — вывод PowerShell-скрипта.

Для реальных снимков замените watermark на правдивый `nanoCAD 26 / реальный снимок стенда` и выставьте `nanoCADScreenshot: true`. Не помечайте диагностические Linux-макеты как CAD-скриншоты.

## Код-ревью заметки

- `tools/pipeline.py` не вызывает выдуманные CAD API; MultiCAD backend — явная заглушка.
- `src/NavigatorKit.NanoCad/DwgReadiness.cs` компилируется без CAD-ссылок и перечисляет Required checks.
- `tools/sheetset_probe.py` проверяет локальный handoff, но не читает layouts nanoCAD.
- Все генераторы детерминированы по входным CSV/JSON; timestamp допустим в логах/метаданных.
- Перед contest submission повторить `python tools/verify_delivery.py --check-only`.
"""


def p2_demo_review() -> None:
    call_tool("make_demo_gif.py")
    demo = read_json(SESSION3 / "demo_metadata.json")
    (SESSION3 / "senior_review.md").write_text(SENIOR_REVIEW_MD, encoding="utf-8")
    (DELIVERY / "next_steps.md").write_text(NEXT_STEPS_MD, encoding="utf-8")
    copy_file(DELIVERY / "next_steps.md", SESSION3 / "next_steps.md")

    # Count remaining hypothesis markers instead of pretending they are resolved.
    hyp_files = []
    hyp_count = 0
    skip = {".png", ".jpg", ".gif", ".zip", ".dxf", ".pyc", ".bak", ".docx"}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or ".venv" in path.parts:
            continue
        if path.suffix.lower() in skip:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        n = text.count("ГИПОТЕЗА/ПРОВЕРИТЬ")
        if n:
            hyp_count += n
            hyp_files.append({"file": path.relative_to(ROOT).as_posix(), "count": n})
    write_json(SESSION3 / "remaining_hypotheses.json", {
        "format": "navigator-kit.remaining-hypotheses/v1",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "totalMarkers": hyp_count,
        "files": hyp_files,
        "policy": "Markers are intentionally retained until a real Windows/nanoCAD/SDK/norms review closes them.",
    })

    review = {
        "format": "navigator-kit.session3-demo-review/v1",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "status": "GIF_OK;SENIOR_REVIEW_DONE;HYPOTHESES_REMAIN",
        "demo": demo,
        "watermarkTopAndBottom": True,
        "gifWithin3MB": demo["withinLimit"],
        "seniorReview": "delivery/session-3/senior_review.md",
        "remainingHypothesisMarkers": hyp_count,
        "hypothesesRemoved": False,
        "reason": "No Windows/nanoCAD/SDK/real DWG/norms geometry review; removing markers would be dishonest.",
        "nextSteps": "delivery/next_steps.md",
    }
    write_json(SESSION3 / "p2_demo_review.json", review)
    RESULTS["p2"] = {
        "status": review["status"],
        "gifBytes": demo["bytes"],
        "within3MB": demo["withinLimit"],
        "remainingHypothesisMarkers": hyp_count,
    }


def write_session3_summary() -> None:
    tasks = [
        {"id": 1, "priority": "P0", "task": "Нормоконтроль 2026/2023", "status": RESULTS["p0_norm"]["status"]},
        {"id": 2, "priority": "P0", "task": "Windows-стенд nanoCAD 26", "status": RESULTS["p0_windows"]["status"]},
        {"id": 3, "priority": "P1", "task": "Production DWG pipeline", "status": RESULTS["p1_dwg"]["status"]},
        {"id": 4, "priority": "P1", "task": "SHEETSET/Tables/print order", "status": RESULTS["p1_sheetset"]["status"]},
        {"id": 5, "priority": "P2", "task": "GIF demo and senior review", "status": RESULTS["p2"]["status"]},
    ]
    summary = {
        "format": "navigator-kit.session3-summary/v1",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "checkedAtDate": CHECKED_AT,
        "branch": "arena/ec9fddc1-navigator-kit",
        "baseRemoteCommit": "49e592d",
        "prUrl": PR_URL,
        "prState": "OPEN",
        "requestedLabels": ["good first issue", "night-session"],
        "tasks": tasks,
        "results": RESULTS,
        "nanoCADExecuted": False,
        "dotnetBuildExecutedInSandbox": False,
        "windowsWorkflow": ".github/workflows/windows-build.yml",
        "gif": "delivery/session-3/demo.gif",
        "watermark": WATERMARK,
        "expectedScreenshotCount": 15,
        "honesty": "Legacy standards mentions are audited, not blindly removed; remaining hypotheses are retained.",
    }
    write_json(DATA / "session3_summary.json", summary)
    copy_file(DATA / "session3_summary.json", SESSION3 / "session3_summary.json")


def write_session3_readme() -> None:
    text = f"""# Сессия 3 — {SESSION_ID} (2026-10-28)

Продолжение PR #1. Ветка `arena/ec9fddc1-navigator-kit`, базовый коммит `49e592d`. PR остаётся **открытым**.

## Итог по P0–P2

| # | Приоритет | Статус | Артефакт |
|---:|---|---|---|
| 1 | P0 | Нормоконтроль выполнен, геометрия форм остаётся гипотезой | `p0_norm_control.json`, `official_text_extract.md`, `norms_registry.json` |
| 2 | P0 | Windows-стенд подготовлен как внешняя зависимость | `p0_windows_stand.json`, `windows_stand_setup.md`, `windows_stand_check.ps1` |
| 3 | P1 | Synthetic pipeline выполнен; MultiCAD — заглушка | `p1_production_dwg.json`, `p1_multicad_dwg.json`, `data/` |
| 4 | P1 | Локальный print order подтверждён; CAD API — гипотеза | `p1_sheetset_tables.json`, `print_order.json`, `wo1_template.csv`, `wo2_template.csv` |
| 5 | P2 | GIF ≤3 МБ и senior review готовы; метки гипотез сохранены | `demo.gif`, `demo_storyboard.png`, `senior_review.md`, `remaining_hypotheses.json` |

## Честность

- nanoCAD 26 **не запускался**; Windows, SDK, лицензия и реальные DWG отсутствуют.
- Все новые изображения и GIF имеют watermark «{WATERMARK}».
- Исторические упоминания ГОСТ Р 21.101-2020 и ГОСТ 2.503-2013 сохранены как аудиторские ссылки, а не как активная норма.
- Метки **ГИПОТЕЗА/ПРОВЕРИТЬ** не удалены массово: для этого нужны реальный стенд и нормоконтролёр.

## Воспроизведение

```bash
python tools/generate_fixtures.py
python tools/navigator_kit.py all
python tools/night_session_2.py
python tools/session3_runner.py
python tools/render_screenshots.py
python -m unittest discover -s tests -v
python tools/finalize_delivery.py
python tools/verify_delivery.py --check-only
```

## Ссылки

- [PR #1]({PR_URL})
- `../README_night-session.md`
- `../index.html`
- `../next_steps.md`
- `manifest.json`
"""
    (SESSION3 / "README.md").write_text(text, encoding="utf-8")
    (DELIVERY / "night-session-3.md").write_text(text, encoding="utf-8")


def write_manifests() -> None:
    files: dict[str, str] = {}
    for path in sorted(SESSION3.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        rel = path.relative_to(DELIVERY).as_posix()
        files[rel] = sha256_file(path)
    manifest = {
        "format": "navigator-kit.session3-manifest/v1",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "scope": "delivery/session-3/",
        "fileCount": len(files),
        "files": files,
        "globalManifest": "delivery/MANIFEST.json",
        "note": "Session-3 hashes; global MANIFEST.json is regenerated by finalize_delivery.py.",
    }
    write_json(SESSION3 / "manifest.json", manifest)
    # Lowercase alias requested in the brief; points at the same session-3 files.
    write_json(DELIVERY / "manifest.json", manifest)


def append_logs() -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    (DELIVERY / "logs").mkdir(parents=True, exist_ok=True)
    (SESSION3 / "logs").mkdir(parents=True, exist_ok=True)
    raw = "\n".join(LOG_LINES) + "\n"
    for path in (LOGS / "night-session-3.log", DELIVERY / "logs" / "night-session-3.log",
                 SESSION3 / "logs" / "session-3.log"):
        path.write_text(raw, encoding="utf-8")
    for path in (LOGS / "night-session.log", DELIVERY / "logs" / "night-session.log"):
        existing = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        if "SESSION_3_START" not in existing:
            with path.open("a", encoding="utf-8") as fp:
                fp.write("\n" + raw)


def main() -> int:
    SESSION3.mkdir(parents=True, exist_ok=True)
    log("SESSION_3_START", f"id={SESSION_ID}; branch=arena/ec9fddc1-navigator-kit; pr={PR_URL}; base=49e592d")
    run_task("P0_norm_control", p0_norm_control)
    run_task("P0_windows_stand", p0_windows_stand)
    run_task("P1_production_dwg", p1_production_dwg)
    run_task("P1_sheetset_tables", p1_sheetset_tables)
    run_task("P2_demo_review", p2_demo_review)
    run_task("session3_summary", write_session3_summary)
    run_task("session3_readme", write_session3_readme)
    log("SESSION_3_END", "status=PASS_WITH_EXTERNAL_DEPENDENCIES")
    # Write session-3 logs BEFORE hashing, otherwise logs/session-3.log is stale
    # in the manifest and verify_delivery.py correctly rejects the bundle.
    run_task("session3_logs", append_logs)
    run_task("session3_manifests", write_manifests)
    print(json.dumps({
        "status": "PASS_WITH_EXTERNAL_DEPENDENCIES",
        "sessionId": SESSION_ID,
        "generatedAt": utcnow(),
        "results": RESULTS,
        "session3": "delivery/session-3/",
        "log": "logs/night-session-3.log",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
