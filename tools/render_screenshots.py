#!/usr/bin/env python3
"""Render honest diagnostic PNG mockups from actual generated artifacts.

Every image is 1600x1200 and carries a permanent watermark. These are NOT
screenshots of nanoCAD; no CAD host was available in this Linux sandbox.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "delivery" / "data"
OUT = ROOT / "delivery" / "screenshots"
XML = ROOT / "delivery" / "xml"
W, H = 1600, 1200
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_REG = FONT_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
FONT_MONO = FONT_DIR / "DejaVuSansMono.ttf"
BG = (11, 18, 31)
PANEL = (20, 31, 50)
PANEL2 = (26, 39, 62)
BORDER = (54, 76, 108)
TEXT = (232, 240, 252)
MUTED = (150, 168, 194)
GREEN = (74, 222, 128)
AMBER = (251, 191, 36)
RED = (248, 113, 113)
BLUE = (96, 165, 250)
PURPLE = (167, 139, 250)
CYAN = (34, 211, 238)


def f(size: int, bold: bool = False, mono: bool = False):
    path = FONT_MONO if mono else (FONT_BOLD if bold else FONT_REG)
    return ImageFont.truetype(str(path), size)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp, delimiter=";"))


def clip(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    text = str(text)
    if draw.textlength(text, font=font) <= max_width:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi) // 2
        candidate = text[:mid].rstrip() + "…"
        if draw.textlength(candidate, font=font) <= max_width:
            lo = mid + 1
        else:
            hi = mid
    n = max(0, min(len(text), lo - 1))
    return text[:n].rstrip() + "…"


def canvas(title: str, subtitle: str, accent: tuple[int, int, int] = BLUE):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for y in range(0, H, 4):
        if y % 80 == 0:
            d.line((0, y, W, y), fill=(15, 25, 43), width=1)
    d.rectangle((0, 0, W, 12), fill=accent)
    d.rounded_rectangle((40, 38, 58, 132), radius=8, fill=accent)
    d.text((78, 38), title, font=f(40, bold=True), fill=TEXT)
    d.text((80, 95), subtitle, font=f(21), fill=MUTED)
    d.text((W - 400, 48), "2026-10-26 • NIGHT SESSION", font=f(20, mono=True), fill=accent)
    d.rounded_rectangle((40, 158, W - 40, 208), radius=12, fill=(48, 24, 32), outline=(135, 55, 68), width=2)
    d.text((62, 171), "СИНТЕТИЧЕСКИЙ ДИАГНОСТИЧЕСКИЙ МАКЕТ • nanoCAD НЕ ЗАПУСКАЛСЯ • НЕ ЯВЛЯЕТСЯ СКРИНШОТОМ CAD",
           font=f(21, bold=True), fill=RED)
    d.line((40, 226, W - 40, 226), fill=BORDER, width=2)
    return img, d


def card(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, heading: str,
         lines: list[str], color: tuple[int, int, int] = BLUE, value: str | None = None):
    d.rounded_rectangle((x, y, x + w, y + h), radius=16, fill=PANEL, outline=BORDER, width=2)
    d.rectangle((x, y, x + 8, y + h), fill=color)
    d.text((x + 24, y + 18), heading, font=f(23, bold=True), fill=color)
    if value is not None:
        d.text((x + 24, y + 55), value, font=f(48, bold=True), fill=TEXT)
        yy = y + 120
    else:
        yy = y + 60
    for line in lines:
        d.text((x + 24, yy), clip(d, line, f(20), w - 48), font=f(20), fill=MUTED)
        yy += 31


def table(d: ImageDraw.ImageDraw, x: int, y: int, widths: list[int], headers: list[str],
          rows: list[list[str]], row_h: int = 43, font_size: int = 19,
          highlight_first_col: bool = False):
    total = sum(widths)
    d.rounded_rectangle((x, y, x + total, y + row_h * (len(rows) + 1) + 12),
                        radius=12, fill=PANEL, outline=BORDER, width=2)
    cx = x
    for i, h in enumerate(headers):
        d.rectangle((cx, y, cx + widths[i], y + row_h), fill=PANEL2)
        d.text((cx + 12, y + 9), clip(d, h, f(font_size, bold=True), widths[i] - 24),
               font=f(font_size, bold=True), fill=BLUE)
        cx += widths[i]
    for r_idx, row in enumerate(rows):
        yy = y + row_h * (r_idx + 1)
        if r_idx % 2 == 0:
            d.rectangle((x, yy, x + total, yy + row_h), fill=(17, 27, 45))
        cx = x
        for i, cell in enumerate(row):
            color = GREEN if (highlight_first_col and i == 0 and str(cell) == "OK") else TEXT
            d.text((cx + 12, yy + 9), clip(d, cell, f(font_size), widths[i] - 24),
                   font=f(font_size), fill=color)
            cx += widths[i]
        d.line((x, yy + row_h, x + total, yy + row_h), fill=(35, 50, 73), width=1)


def footer(d: ImageDraw.ImageDraw, source: str):
    d.text((42, 1140), "Источник: " + source, font=f(18), fill=MUTED)
    d.text((42, 1165), "Все данные получены из локальных CSV/JSON; CAD-хост не запускался.",
           font=f(18), fill=(185, 110, 110))


def save(img: Image.Image, name: str, manifest: list[dict], title: str, source: str) -> None:
    path = OUT / name
    img.save(path, optimize=True)
    manifest.append({
        "file": f"delivery/screenshots/{name}", "width": img.width, "height": img.height,
        "title": title, "source": source, "nanoCADScreenshot": False,
        "watermark": True, "sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
    })


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob("*.png"):
        p.unlink()
    manifest: list[dict] = []
    summary = read_json(DATA / "summary.json")
    env = read_json(DATA / "environment.json")
    issues = read_csv(DATA / "completeness_report.csv")
    registry = read_csv(DATA / "sheets_registry.csv")
    api = read_json(DATA / "api_experiment_results.json")
    stamp = read_json(DATA / "stamp_patch_report.json")
    consistency = read_json(DATA / "print_order_consistency.json")
    standards = read_json(DATA / "standards_status.json")

    # 01 Environment
    img, d = canvas("01 • Окружение и зависимости", "Фактическая проверка Linux sandbox / нет nanoCAD, SDK и .NET", RED)
    card(d, 40, 250, 360, 175, "DXF-фикстуры", [], GREEN, value="120")
    card(d, 420, 250, 360, 175, "Марки", [], BLUE, value="3 × 40")
    card(d, 800, 250, 360, 175, "nanoCAD запусков", [], RED, value="0")
    card(d, 1180, 250, 380, 175, "C# сборок здесь", [], AMBER, value="0")
    rows = [[k, "OK" if v != "MISSING" else "MISSING"] for k, v in env["tools"].items()]
    table(d, 40, 455, [430, 250], ["Инструмент", "Статус"], rows[:10], row_h=38, font_size=19, highlight_first_col=False)
    card(d, 760, 455, 800, 435, "Критические ограничения", [
        "• " + env["os"], "• Python " + env["python"],
        "• dotnet/mono/msbuild/csc: MISSING",
        "• nanoCAD 26 / SDK 26 / лицензия: отсутствуют",
        "• briefing.md восстановлен из сообщения пользователя",
        "• pip install --user → externally managed environment; solution: venv",
        "• исходные DWG заказчика отсутствуют",
        "• реальные скриншоты nanoCAD невозможны",
    ], RED)
    footer(d, "delivery/data/environment.json")
    save(img, "screenshot_01_environment.png", manifest, "Окружение", "environment.json")

    # 02 POC scan
    img, d = canvas("02 • POC-сканер: реестр листов", "Чтение ATTRIB из 120 синтетических DXF / два XML-профиля штампа", GREEN)
    card(d, 40, 250, 360, 160, "Строк реестра", [], GREEN, value="120")
    card(d, 420, 250, 360, 160, "Профилей", [], BLUE, value="2")
    card(d, 800, 250, 360, 160, "Инцидентов", [], AMBER, value=str(summary["output"]["completenessIssues"]))
    card(d, 1180, 250, 380, 160, "SHA-256 файлов", [], PURPLE, value="120")
    rows = [[r["file_name"], r["mark"], r["sheet_no"] or "—", r["sheet_name"], r["format"], r["profile_id"]] for r in registry[:16]]
    table(d, 40, 445, [245, 90, 100, 510, 110, 425],
          ["Файл", "Марка", "Лист", "Наименование", "Формат", "Профиль"], rows, row_h=38, font_size=18)
    d.text((42, 1110), "Формат входа: DXF R2010. Для production DWG необходим проверенный MultiCAD .NET адаптер — ГИПОТЕЗА/ПРОВЕРИТЬ.",
           font=f(20), fill=AMBER)
    footer(d, "delivery/data/sheets_registry.csv + sheets_registry.json")
    save(img, "screenshot_02_poc_scan.png", manifest, "POC-сканер", "sheets_registry.csv")

    # 03 API experiment
    img, d = canvas("03 • Попытка штатной ведомости ф.1", "Документарный эксперимент: SHEETSET, DATAEXTRACTION, GetSheets, .dst", AMBER)
    rows = [[e["id"], e["subject"], e["result"], e["status"], e["finding"]] for e in api["experiments"]]
    table(d, 40, 255, [70, 300, 300, 170, 640], ["ID", "Способ", "Результат", "Статус", "Вывод"], rows, row_h=76, font_size=19)
    card(d, 40, 875, 1480, 225, "Итог эксперимента", [
        "• Штатная «ведомость листов» существует, но старая справка ссылается на ГОСТ Р 21.1101‑2013.",
        "• `GetSheets()` найден только в историческом примере 2015 года; `GetSheetSets()` публично не подтверждён.",
        "• Извлечение данных из нескольких файлов «из коробки» недоступно по форуму 2025 года.",
        "• .dst напрямую не редактировался: формат не подтверждён как открытый.",
    ], AMBER)
    footer(d, "delivery/data/api_experiment_results.json + docs/api-experiment.md")
    save(img, "screenshot_03_api_attempt.png", manifest, "API-эксперимент", "api_experiment_results.json")

    # 04 XML mapping
    img, d = canvas("04 • XML-профиль маппинга штампов", "Два условных эталонных шаблона СПДС / атрибут ↔ поле реестра", PURPLE)
    xml_lines = (XML / "stamp_mapping.xml").read_text(encoding="utf-8").splitlines()
    start_y = 255
    d.rounded_rectangle((40, start_y, 1010, 1085), radius=12, fill=(8, 14, 25), outline=BORDER, width=2)
    for idx, line in enumerate(xml_lines[:34], start=1):
        d.text((58, start_y + 16 + (idx - 1) * 23), f"{idx:02d}", font=f(17, mono=True), fill=(95, 115, 145))
        d.text((100, start_y + 16 + (idx - 1) * 23), clip(d, line, f(17, mono=True), 880), font=f(17, mono=True), fill=TEXT)
    card(d, 1040, 255, 520, 385, "Профиль A", [
        "id: SPDS_FORM3_CLASSIC", "block: SPDS_FORM3",
        "MARK → mark", "SHEET → sheet_no", "TITLE → sheet_name",
        "FORMAT → format", "DESIGNATION → designation",
    ], BLUE)
    card(d, 1040, 660, 520, 385, "Профиль B", [
        "id: SPDS_FORM3_ALT", "block: FORMAT_A3_SPDS",
        "MARKA → mark", "LIST → sheet_no", "NAIM → sheet_name",
        "FORM → format", "OBOZN → designation",
    ], PURPLE)
    d.text((42, 1095), "Имена блоков и тегов — ГИПОТЕЗА/ПРОВЕРИТЬ на реальных шаблонах СПДС.", font=f(20), fill=AMBER)
    footer(d, "delivery/xml/stamp_mapping.xml + stamp_mapping.xsd")
    save(img, "screenshot_04_xml_profile.png", manifest, "XML-маппинг", "stamp_mapping.xml")

    # 05 Form 1
    form1 = read_csv(DATA / "form1_AR.csv")
    img, d = canvas("05 • Ведомость форма 1 — данные", "ГОСТ Р 21.101-2026, приложение Б / колонки: Лист, Наименование, Примечание", GREEN)
    rows = [[r["Лист"], r["Наименование"], r["Примечание"]] for r in form1[:16]]
    table(d, 40, 255, [150, 900, 410], ["Лист", "Наименование", "Примечание"], rows, row_h=43, font_size=19)
    d.rounded_rectangle((40, 1010, 1560, 1100), radius=12, fill=PANEL, outline=AMBER, width=2)
    d.text((62, 1024), "Нормативный статус: точные размеры граф и место таблицы — ГИПОТЕЗА/ПРОВЕРИТЬ.",
           font=f(20, bold=True), fill=AMBER)
    d.text((62, 1058), "CSV содержит данные формы 1, но не является сертифицированным векторным чертежом.",
           font=f(20), fill=TEXT)
    footer(d, "delivery/data/form1_AR.csv + form1_AR.csv")
    save(img, "screenshot_05_form1.png", manifest, "Форма 1", "form1_AR.csv")

    # 06 Form 2
    form2 = read_csv(DATA / "form2_vedomost.csv")
    img, d = canvas("06 • Ведомость форма 2 — данные", "Ссылочные и прилагаемые документы / версия ДЭ и имя файла в примечании", CYAN)
    rows = [[r["Обозначение"] or "—", r["Наименование"], r["Примечание"]] for r in form2]
    table(d, 40, 255, [330, 600, 530], ["Обозначение", "Наименование", "Примечание"], rows, row_h=66, font_size=19)
    card(d, 40, 885, 1480, 220, "Контроль формы 2", [
        "• Заголовки разделов «Ссылочные документы» и «Прилагаемые документы» подчёркивают в графе «Наименование».",
        "• Для электронных документов в примечании указаны версия/номер изменения ДЭ и имя файла (Б.5).",
        "• Технические колонки «Раздел», «Файл», «НормативныйСтатус» не вставляются в чертёж.",
    ], CYAN)
    footer(d, "delivery/data/form2_vedomost.csv + form2_strict.csv")
    save(img, "screenshot_06_form2.png", manifest, "Форма 2", "form2_vedomost.csv")

    # 07 Completeness
    counts = Counter(i["code"] for i in issues)
    img, d = canvas("07 • Контроль комплектности", "Реестр ↔ файлы ↔ штампы ↔ ведомость / 16 намеренных дефектов", RED)
    x = 40
    for idx, (code, count) in enumerate(sorted(counts.items())):
        if idx == 4:
            x = 40
        y = 250 + (idx // 4) * 155
        card(d, x, y, 360, 135, code.replace("_", " "), [], AMBER if count < 3 else RED, value=str(count))
        x += 380
    rows = [[i["code"], i["severity"], i["mark"] or "—", i["sheet_no"] or "—", i["message"]] for i in issues[:10]]
    table(d, 40, 590, [310, 110, 100, 90, 850], ["Код", "Уровень", "Марка", "Лист", "Сообщение"], rows, row_h=44, font_size=18)
    footer(d, "delivery/data/completeness_report.csv")
    save(img, "screenshot_07_completeness.png", manifest, "Контроль комплектности", "completeness_report.csv")

    # 08 Numbering
    duplicates = read_csv(DATA / "duplicate_report.csv")
    plan = read_csv(DATA / "numbering_plan.csv")
    img, d = canvas("08 • Дубли и сквозная нумерация", "Граф файл ↔ лист ↔ штамп ↔ ведомость ↔ печать", PURPLE)
    d.text((42, 250), f"Обнаружено групп дублей: {len(duplicates)}", font=f(28, bold=True), fill=RED)
    rows = [[r["mark"], r["sheet_no"], r["count"], r["files"], r["recommendation"]] for r in duplicates]
    table(d, 40, 300, [100, 100, 90, 780, 390], ["Марка", "Лист", "Кол-во", "Файлы", "Рекомендация"], rows, row_h=72, font_size=18)
    rows = [[r["file"], r["old_sheet_no"], r["minimal_new_no"], r["full_shift_new_no"], r["action"]] for r in plan[:10]]
    table(d, 40, 675, [720, 160, 190, 190, 200], ["Файл", "Старый", "Minimal", "Full shift", "Действие"], rows, row_h=38, font_size=18)
    d.text((42, 1110), "Ни один вариант не применён к исходным файлам без подтверждения ГИПа.", font=f(20), fill=AMBER)
    footer(d, "delivery/data/duplicate_report.csv + numbering_plan.csv")
    save(img, "screenshot_08_numbering.png", manifest, "Нумерация", "duplicate_report.csv")

    # 09 Stamp rollback
    img, d = canvas("09 • Обратимая правка штампов", "dry-run → .bak → apply → verify → rollback на изолированных копиях", GREEN)
    ok = stamp["rollbackVerified"] and stamp["applyVerified"]
    card(d, 40, 250, 720, 180, "Rollback", [], GREEN if ok else RED, value="VERIFIED" if ok else "FAILED")
    card(d, 780, 250, 780, 180, "Исходные файлы", [], BLUE, value="НЕ ИЗМЕНЕНЫ")
    rows = []
    for r in stamp["patches"]:
        rows.append([Path(r["file"]).name, r["tag"], r["expected_old"], r["new"],
                     r["before_sha256"][:16], r["after_sha256"][:16], r["rollback_sha256"][:16],
                     "OK" if r["rollback_verified"] else "FAIL"])
    table(d, 40, 470, [240, 100, 100, 100, 230, 230, 230, 100],
          ["Файл", "Тег", "Было", "Стало", "До SHA", "После SHA", "Rollback SHA", "Итог"], rows,
          row_h=70, font_size=18, highlight_first_col=False)
    card(d, 40, 700, 1480, 390, "Что доказано и что нет", [
        "ДОКАЗАНО: замена значения ATTRIB в DXF-копии и восстановление из .bak по SHA-256.",
        "ДОКАЗАНО: исходные фикстуры не модифицировались.",
        "НЕ ДОКАЗАНО: запись атрибутов внутри реального DWG.",
        "ГИПОТЕЗА/ПРОВЕРИТЬ: MultiCAD .NET Database/Transaction/BlockReference API для nanoCAD 26.",
        "Перед записью в production DWG обязательны бэкап, транзакция и повторный контроль штампа.",
    ], AMBER)
    footer(d, "delivery/data/stamp_patch_report.json + stamp_workspace/")
    save(img, "screenshot_09_stamp_rollback.png", manifest, "Обратимая правка", "stamp_patch_report.json")

    # 10 Change table
    change_cols = ["Изм.", "Лист", "№ докум.", "Подп.", "Дата"]
    img, d = canvas("10 • Таблица изменений", "Пустая таблица + технический реестр операций", AMBER)
    table(d, 40, 255, [180, 180, 350, 220, 220], change_cols,
          [["", "", "", "", ""] for _ in range(10)], row_h=54, font_size=20)
    card(d, 1210, 255, 350, 600, "Допустимо в «Лист»", [
        "• Зам.", "• Нов.", "• Все", "• прочерк", "",
        "«Аннулир.» НЕ пишем", "",
        "Актуально:",
        "ГОСТ Р 2.503-2023",
        "2.503-2013 утратил силу",
    ], RED)
    d.text((42, 900), "ГОСТ Р 21.101-2026 раздел 7 + ГОСТ Р 2.503-2023 п. 5.12 — требуется нормоконтроль.",
           font=f(21), fill=TEXT)
    d.text((42, 935), "Точная геометрия таблицы и приоритет требований для СПДС: ГИПОТЕЗА/ПРОВЕРИТЬ.",
           font=f(21), fill=AMBER)
    footer(d, "delivery/data/change_table_template.csv + change_register.csv")
    save(img, "screenshot_10_change_table.png", manifest, "Таблица изменений", "change_table_template.csv")

    # 11 Print order
    order = read_csv(DATA / "print_order.csv")
    img, d = canvas("11 • Порядок пакетной печати", "Нейтральный handoff-манифест / синхронизация с формой 1", CYAN)
    card(d, 40, 250, 480, 170, "Consistency", [], GREEN if consistency["consistent"] else RED,
         value="OK" if consistency["consistent"] else "MISMATCH")
    card(d, 540, 250, 480, 170, "Элементов", [], BLUE, value=str(consistency["printOrderItems"]))
    card(d, 1040, 250, 520, 170, ".dst export", [], AMBER, value="NOT DONE")
    rows = [[r["sequence"], r["mark"], r["sheet_no"], r["file"], r["layout"], r["format"]] for r in order[:14]]
    table(d, 40, 455, [100, 100, 100, 780, 190, 190], ["№", "Марка", "Лист", "Файл", "Layout", "Формат"], rows, row_h=40, font_size=18)
    d.text((42, 1090), "В nanoCAD 26 порядок листов в SHEETSET связан с вкладками layouts; .dst напрямую не редактировался.",
           font=f(20), fill=AMBER)
    footer(d, "delivery/data/print_order.csv + print_order.json")
    save(img, "screenshot_11_print_order.png", manifest, "Порядок печати", "print_order.csv")

    # 12 Architecture
    img, d = canvas("12 • Архитектура решения", "Фактически выполненный контур и непроверенный CAD-адаптер", BLUE)
    boxes = [
        (60, 280, 420, 435, "ВХОД", ["120 синтетических DXF", "2 XML-профиля штампа", "reference/expected реестры"], GREEN),
        (520, 280, 900, 435, "СКАНЕР", ["DXF ATTRIB reader", "SHA-256 + mapping", "реестр листов CSV/JSON"], BLUE),
        (950, 280, 1330, 435, "DOMAIN", ["комплектность", "дубли и нумерация", "формы 1/2"], PURPLE),
        (60, 500, 420, 665, "ОБРАТИМОСТЬ", ["dry-run + .bak", "apply + verify", "rollback по SHA"], CYAN),
        (520, 500, 900, 665, "ОТЧЁТЫ", ["CSV / JSON / XML", "12 PNG-макетов", "HTML dashboard"], AMBER),
        (950, 500, 1330, 665, "ПЕЧАТЬ", ["print_order.json", "сверка с layouts", ".dst: НЕ тронут"], GREEN),
        (60, 740, 1330, 900, "PRODUCTION DWG / nanoCAD 26 — ГИПОТЕЗА/ПРОВЕРИТЬ", [
            "MultiCAD .NET SDK 26 • Database/Transaction • Sheet Set API",
            "Tables API • NETLOAD/APPLOAD • реальные скриншоты",
        ], RED),
        (60, 940, 620, 1090, "C# CORE / CLI", ["net8.0 • portable • tree-sitter syntax OK", "не скомпилирован: нет dotnet в sandbox"], BLUE),
        (650, 940, 1330, 1090, "NANOCAD ADAPTER", ["SdkProbe через reflection", "без выдуманных GetSheetSets()", "TFM/DLL требуют проверки"], PURPLE),
    ]
    for x1, y1, x2, y2, title, lines, color in boxes:
        d.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=PANEL, outline=color, width=3)
        d.text((x1 + 24, y1 + 18), title, font=f(24, bold=True), fill=color)
        yy = y1 + 58
        for line in lines:
            d.text((x1 + 24, yy), clip(d, line, f(20), x2 - x1 - 48), font=f(20), fill=TEXT)
            yy += 30
    for x in [490, 920]:
        d.line((x, 345, x + 30, 345), fill=BLUE, width=5)
        d.polygon([(x + 30, 345), (x + 18, 338), (x + 18, 352)], fill=BLUE)
    for y in [460, 700, 920]:
        d.line((800, y - 20, 800, y), fill=MUTED, width=3)
    footer(d, "docs/nanocad-integration.md + src/*")
    save(img, "screenshot_12_architecture.png", manifest, "Архитектура", "architecture summary")

    write_json = lambda p, data: p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_json(OUT / "screenshots_manifest.json", {
        "format": "navigator-kit.screenshots/v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "nanoCADExecuted": False,
        "disclaimer": "All PNGs are explicitly labelled synthetic diagnostic mockups, not nanoCAD screenshots.",
        "minResolution": {"width": W, "height": H},
        "count": len(manifest),
        "images": manifest,
    })
    print(f"Rendered {len(manifest)} images at {W}x{H}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
