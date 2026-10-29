#!/usr/bin/env python3
"""Build a <=3 MB diagnostic GIF storyboard for the contest demo.

Frames are drawn from local data, not captured from nanoCAD. Every frame has
a top disclaimer banner and a bottom persistent watermark.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "delivery"
DATA = DELIVERY / "data"
SESSION3 = DELIVERY / "session-3"
OUT_GIF = SESSION3 / "demo.gif"
OUT_STORYBOARD = SESSION3 / "demo_storyboard.png"
OUT_META = SESSION3 / "demo_metadata.json"
W, H = 960, 720
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_REG = FONT_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
WATERMARK = "nanoCAD НЕ запускался / не скриншот CAD"
MAX_BYTES = 3_000_000
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


def f(size: int, bold: bool = False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REG), size)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp, delimiter=";"))


def base_frame(step: int, title: str, accent: tuple[int, int, int]) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 82), fill=(48, 24, 32), outline=(135, 55, 68), width=2)
    d.text((24, 14), "СИНТЕТИЧЕСКИЙ ДИАГНОСТИЧЕСКИЙ МАКЕТ", font=f(22, bold=True), fill=RED)
    d.text((24, 46), "nanoCAD НЕ ЗАПУСКАЛСЯ • НЕ ЯВЛЯЕТСЯ СКРИНШОТОМ CAD", font=f(18, bold=True), fill=RED)
    d.rectangle((0, 95, W, 97), fill=accent)
    d.text((28, 112), f"{step:02d}. {title}", font=f(30, bold=True), fill=TEXT)
    # bottom persistent watermark
    d.rectangle((0, H - 58, W, H), fill=(48, 20, 28))
    d.text((W - 26, H - 40), WATERMARK, font=f(18, bold=True), fill=(255, 175, 175), anchor="ra")
    d.text((24, H - 40), "Комплект-Навигатор • session 3 • 2026-10-28", font=f(16), fill=MUTED)
    return img, d


def card(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, heading: str,
         lines: list[str], color: tuple[int, int, int] = BLUE, value: str | None = None):
    d.rounded_rectangle((x, y, x + w, y + h), radius=12, fill=PANEL, outline=BORDER, width=2)
    d.rectangle((x, y, x + 7, y + h), fill=color)
    d.text((x + 20, y + 14), heading, font=f(20, bold=True), fill=color)
    yy = y + 50
    if value is not None:
        d.text((x + 20, yy), value, font=f(38, bold=True), fill=TEXT)
        yy += 60
    for line in lines:
        d.text((x + 20, yy), line, font=f(17), fill=MUTED)
        yy += 26


def progress(d: ImageDraw.ImageDraw, step: int) -> None:
    for i in range(1, 7):
        x = 28 + (i - 1) * 150
        color = GREEN if i <= step else BORDER
        d.ellipse((x, 172, x + 22, 194), fill=color)
        d.text((x + 30, 172), str(i), font=f(18, bold=True), fill=TEXT)


def frame_01() -> Image.Image:
    img, d = base_frame(1, "Папка с чертежами", GREEN)
    progress(d, 1)
    card(d, 28, 220, 430, 380, "Вход", [
        "samples/synthetic_sets/АР/*.dxf",
        "samples/synthetic_sets/КР/*.dxf",
        "samples/synthetic_sets/ОВ/*.dxf",
        "Формат: DXF R2010",
        "Профили штампа: 2 XML",
    ], GREEN, value="120")
    for i, name in enumerate(["АР_001.dxf", "КР_001.dxf", "ОВ_001.dxf", "АР_040.dxf"]):
        y = 240 + i * 72
        d.rounded_rectangle((490, y, 920, y + 54), radius=8, fill=PANEL2, outline=BORDER, width=2)
        d.text((506, y + 14), name, font=f(20), fill=TEXT)
    d.text((28, 630), "Реальные DWG заказчика отсутствуют: это воспроизводимый synthetic fixture.", font=f(17), fill=AMBER)
    return img


def frame_02(registry: list[dict]) -> Image.Image:
    img, d = base_frame(2, "Реестр листов", BLUE)
    progress(d, 2)
    headers = ["Файл", "Марка", "Лист", "Формат", "SHA-256"]
    widths = [260, 90, 90, 100, 360]
    x0, y0 = 28, 220
    x = x0
    for head, w in zip(headers, widths):
        d.rectangle((x, y0, x + w, y0 + 42), fill=PANEL2)
        d.text((x + 10, y0 + 8), head, font=f(17, bold=True), fill=BLUE)
        x += w
    for idx, r in enumerate(registry[:8]):
        y = y0 + 42 + idx * 40
        cells = [r["file_name"], r["mark"], r["sheet_no"] or "—", r["format"], r["source_sha256"][:14] + "…"]
        x = x0
        for cell, w in zip(cells, widths):
            d.rectangle((x, y, x + w, y + 40), fill=(17, 27, 45) if idx % 2 == 0 else PANEL)
            d.text((x + 10, y + 9), str(cell), font=f(16), fill=TEXT)
            x += w
    d.text((28, 630), "sheets_registry.csv/json: 120 строк, SHA-256 для каждого файла.", font=f(17), fill=MUTED)
    return img


def frame_03() -> Image.Image:
    img, d = base_frame(3, "Обратимая правка штампа", CYAN)
    progress(d, 3)
    card(d, 28, 220, 430, 180, "Было", ["ATTRIB SHEET = 15", "Файл: АР_016.dxf"], CYAN, value="15")
    card(d, 500, 220, 430, 180, "Стало", ["ATTRIB SHEET = 16", ".bak создан перед записью"], GREEN, value="16")
    card(d, 28, 420, 902, 180, "Rollback", [
        "SHA-256 исходного == SHA-256 после отката",
        "Исходные synthetic DXF не изменены",
        "Для production DWG нужен проверенный MultiCAD .NET API",
    ], AMBER, value="VERIFIED")
    return img


def frame_04() -> Image.Image:
    img, d = base_frame(4, "Сдвиг нумерации", PURPLE)
    progress(d, 4)
    card(d, 28, 220, 430, 180, "Дубли", ["4 группы повторяющихся номеров", "Пропуски последовательности: 3"], RED, value="4")
    card(d, 500, 220, 430, 180, "Стратегии", ["minimal patch · 4 правки", "full shift · 5 правок", "plan rows: 120"], PURPLE, value="2")
    d.rounded_rectangle((28, 430, 902, 610), radius=12, fill=PANEL, outline=BORDER, width=2)
    d.text((48, 450), "Сценарий «ночь ГИПа → 2 минуты»", font=f(24, bold=True), fill=TEXT)
    d.text((48, 492), "План готовится заранее,применяется к DXF только после подтверждения.", font=f(19), fill=MUTED)
    d.text((48, 526), "numbering_patch.py не трогает исходники без approve.", font=f(19), fill=AMBER)
    return img


def frame_05() -> Image.Image:
    img, d = base_frame(5, "Порядок печати", CYAN)
    progress(d, 5)
    card(d, 28, 220, 280, 180, "Элементов", ["form 1 == print order"], GREEN, value="120")
    card(d, 340, 220, 280, 180, "Consistency", ["hash совпадает"], GREEN, value="OK")
    card(d, 652, 220, 280, 180, ".dst", ["не редактировался", "layouts не читались"], AMBER, value="NO")
    for i in range(1, 6):
        x = 40 + (i - 1) * 180
        d.rounded_rectangle((x, 460, x + 150, 560), radius=10, fill=PANEL2, outline=CYAN, width=2)
        d.text((x + 54, 485), str(i), font=f(36, bold=True), fill=CYAN)
    return img


def frame_06() -> Image.Image:
    img, d = base_frame(6, "Итог за 2 минуты", GREEN)
    progress(d, 6)
    card(d, 28, 220, 280, 180, "Форма 1", ["Приложение Б-2026", "120 строк"], GREEN, value="OK")
    card(d, 340, 220, 280, 180, "Инциденты", ["8 категорий", "4 дубля"], AMBER, value="16")
    card(d, 652, 220, 280, 180, "Проверки", ["45 required", "12 unit tests"], BLUE, value="PASS")
    d.text((28, 440), "Остаётся внешняя зависимость:", font=f(22, bold=True), fill=RED)
    d.text((28, 478), "Windows + nanoCAD 26 + SDK 26 + лицензия + реальные DWG.", font=f(20), fill=TEXT)
    d.text((28, 516), "Все непроверенные API помечены ГИПОТЕЗА/ПРОВЕРИТЬ.", font=f(20), fill=AMBER)
    return img


def make_storyboard(frames: list[Image.Image]) -> Image.Image:
    board = Image.new("RGB", (1600, 1200), BG)
    d = ImageDraw.Draw(board)
    d.rectangle((0, 0, 1600, 12), fill=GREEN)
    d.text((40, 34), "GIF-демо: папка → реестр → штамп → нумерация → печать → итог", font=f(34, bold=True), fill=TEXT)
    d.text((42, 84), "Кадры 960×720, 6 шагов, палитра 64 цвета, ≤3 МБ, постоянный watermark.", font=f(20), fill=MUTED)
    for idx, frame in enumerate(frames):
        thumb = frame.resize((500, 375), Image.Resampling.LANCZOS)
        x = 40 + (idx % 3) * 520
        y = 150 + (idx // 3) * 500
        board.paste(thumb, (x, y))
        d.rectangle((x, y, x + 500, y + 375), outline=BORDER, width=2)
        d.text((x + 8, y + 380), f"Кадр {idx+1}", font=f(20, bold=True), fill=BLUE)
    d.rectangle((0, 1150, 1600, 1200), fill=(48, 20, 28))
    d.text((1560, 1174), WATERMARK, font=f(20, bold=True), fill=(255, 175, 175), anchor="ra")
    return board


def main() -> int:
    SESSION3.mkdir(parents=True, exist_ok=True)
    registry = read_csv(DATA / "sheets_registry.csv")
    frames = [frame_01(), frame_02(registry), frame_03(), frame_04(), frame_05(), frame_06()]

    # Palette-reduce to keep the GIF well below the 3 MB contest limit.
    palettes = [fr.quantize(colors=64, method=Image.MEDIANCUT, dither=Image.Dither.NONE) for fr in frames]
    duration = 900
    palettes[0].save(
        OUT_GIF, save_all=True, append_images=palettes[1:],
        duration=[duration] * len(palettes), loop=0, optimize=True, disposal=2,
    )
    gif_bytes = OUT_GIF.stat().st_size
    assert gif_bytes <= MAX_BYTES, f"GIF too large: {gif_bytes} > {MAX_BYTES}"

    storyboard = make_storyboard(frames)
    storyboard.save(OUT_STORYBOARD, optimize=True)

    meta = {
        "format": "navigator-kit.demo-gif/v1",
        "sessionId": "night-session-20261028",
        "generatedAt": utcnow(),
        "path": "delivery/session-3/demo.gif",
        "storyboard": "delivery/session-3/demo_storyboard.png",
        "frameCount": len(frames),
        "frameSize": [W, H],
        "durationMsPerFrame": duration,
        "loop": True,
        "paletteColors": 64,
        "bytes": gif_bytes,
        "maxBytes": MAX_BYTES,
        "withinLimit": gif_bytes <= MAX_BYTES,
        "watermark": WATERMARK,
        "topBanner": True,
        "bottomWatermark": True,
        "nanoCADScreenshot": False,
        "source": "locally generated diagnostic frames from delivery/data/*",
    }
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
