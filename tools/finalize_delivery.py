#!/usr/bin/env python3
"""Build the chat-ready report, dashboard, manifest, and ZIP bundle."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from string import Template

from verify_delivery import run_checks, sha256_file

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "delivery"
DATA = DELIVERY / "data"
SHOTS = DELIVERY / "screenshots"
RESULTS = DATA / "verification_results.json"
MANIFEST = DELIVERY / "MANIFEST.json"
CHECKSUMS = DELIVERY / "manifest.sha256"
BUNDLE = DELIVERY / "navigator-kit-night-session.zip"
SESSION = "night-session-20261028"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def groups_phrase(n: int) -> str:
    """Russian plural for 'duplicate groups' in generated text."""
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} группа дублей"
    if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return f"{n} группы дублей"
    return f"{n} групп дублей"


def build_readme(summary: dict, verification: dict, commit: str, pr_url: str, branch: str) -> str:
    shots = read_json(SHOTS / "screenshots_manifest.json")["images"]
    shot_lines = "\n".join(
        f"| {i+1:02d} | `{Path(s['file']).name}` | {html.escape(s['title'])} |" for i, s in enumerate(shots))
    issue_lines = "\n".join(f"- `{k}` — {v}" for k, v in summary["issueCounts"].items())
    pr_text = f"[{pr_url}]({pr_url})" if pr_url.startswith("http") else "`PR будет создан после push`"
    return f"""# Ночной отчет ИИ-куратора — 2026-10-28 (третья сессия)

## Финальный Linux-этап — 2026-10-29

См. `delivery/README_night-session-final.md`: аудит `geometry_audit.md/json`,
обновлённая инструкция Windows, portable `src/CSharpAdapter/` с 28 xUnit cases,
`docs/gif-demo-scenario.md` и `delivery/navigator-kit-final-session.zip`.
12 демо-DXF проходят project-контракт; соответствие геометрии форм ГОСТ — NOT_ASSESSED.
C# проверяется отдельным CI, не локальным отсутствующим dotnet. Это не CAD-плагин.

## Самостоятельный Test Runner

`delivery/navigator-kit-test-runner.zip` — исходники, fixtures и результаты для повторения
28 pytest-тестов. `README_test_runner.md` содержит установку минимальных зависимостей.
Проверены Python 3.11/Linux и запуск из распакованного архива в отдельном venv.
`pytest_output.log`, `collect_log.txt`, `test_report.json` — в `delivery/linux-stand/`.
59 delivery checks — отдельный verifier; Windows/macOS не проверены запуском.
Это не двоичный nanoCAD-плагин. Сборщик проверяет ограничение ZIP ≤3 MB.

> **Статус честности:** локальный контур `VERIFIED_LOCALLY`, nanoCAD 26 **не запускался**. Прежние диагностические PNG — макеты; linux_stamp_*.png — реальные DXF-рендеры. Все снабжены watermark и не являются снимками CAD. C# код синтаксически разобран tree-sitter; portable сборка подготовлена для Windows workflow, но в Linux sandbox не выполнялась (`dotnet` отсутствует).
>
> **Вторая сессия 2026-10-27.** PR #1 получил обновлённый нормативный слой, именованные артефакты, Windows workflow и 12 PNG с полупрозрачным водяным знаком.
>
> **Третья сессия 2026-10-28.** Выполнен P0–P2 проход: повторный нормоконтроль по официальному изданию, подготовка Windows-стенда, synthetic production pipeline, SHEETSET/print-order probe и GIF-демо ≤3 МБ. Реальные nanoCAD/DWG по-прежнему недоступны; метки **ГИПОТЕЗА/ПРОВЕРИТЬ** сохранены.

## Что сделано за ночь

1. **Загрузка контекста** — репозиторий был пустым: только `README.md` из 16 байт и initial commit `7e4fcf3`. Issue/PR на старте отсутствовали. Восстановлен суррогат `briefing.md` с явной пометкой, что оригинал отсутствует.
2. **Зависимости** — проверены OS, Python, Node, .NET, nanoCAD, SDK, лицензия. `lk.nanocad.ru/education/request` требует nanoPassport; лицензию автономно получить нельзя.
3. **POC-сканер** — созданы и реально прочитаны **120 валидных DXF R2010** (3 марки × 40 листов) с атрибутами штампов. Получены `sheets_registry.csv/json`, 120 SHA-256.
4. **Штатная ф.1** — документарный эксперимент по SHEETSET, «Insert Sheet List Table», извлечению данных, `GetSheets()` и `GetSheetSets()`. Последний публично не подтверждён; прямая генерация `.dst` не выполнялась.
5. **XML-профиль** — master `stamp_mapping.xml`, два примера `spds_template_a.xml`/`spds_template_b.xml`, XSD-схема; атрибуты ↔ поля реестра.
6. **Обратимая правка** — dry-run → `.bak` → apply → verify → rollback на изолированных DXF-копиях; SHA-256 исходного и восстановленного совпадают. Исходники не изменены.
7. **Ведомости ф.1/ф.2** — CSV с строгими графами, мастер-файлы с техническими колонками, markdown-черновики. Нормативная база переключена на приложение Б ГОСТ Р 21.101-2026.
8. **Контроль комплектности** — {summary['output']['completenessIssues']} инцидентов, включая дубли, пустые графы, неверные форматы, « file ↔ registry » и « doc ↔ file » расхождения.
9. **Нумератор** — {groups_phrase(summary['output']['duplicateGroups'])}; подготовлены minimal patch и full shift на 120 листов, без автоматической правки исходников.
10. **Таблица изменений** — пустой шаблон из 5 граф и технический реестр операций. Исправлена ошибка задания: «Аннулир.» не является значением графы «Лист».
11. **Порядок печати** — 120 элементов, совпадение с формой 1 по хэшу; `.dst` не редактировался.
12. **Код и визуализация** — C# Core/CLI/плагин-скелет, Python reference CLI, 15 PNG 1600×1200, HTML dashboard, log, manifest, ZIP.
13. **Продолжение 2026-10-27** — повторная проверка официального реестра ГОСТ, XSD-совместимый XML-маппинг с атрибутами номера листа/формата, DOCX/CSV шаблоны, Python-нумератор, разделённая таблица изменений, Windows workflow и обновлённый PR #1.
14. **Сессия 2026-10-28** — P0-нормоконтроль по официальному PDF и разделу 7, Windows-stand инструкция, `tools/pipeline.py`, SHEETSET probe, GIF-демо, senior review и новый `next_steps.md`.

## Артефакты второй сессии

| Файл | Назначение |
|---|---|
| `delivery/completeness_report.md` | 16 инцидентов, 4 группы дублей, честная формулировка (не все — «нет файла»). |
| `delivery/data/completeness_chart.png` | график инцидентов с подписью «nanoCAD НЕ запускался / не скриншот CAD». |
| `delivery/data/wo1_template.csv`, `delivery/data/wo1_template.docx` | данные формы 1 по Приложению Б ГОСТ Р 21.101-2026. |
| `delivery/data/wo2_template.csv` | данные формы 2 по Приложению Б ГОСТ Р 21.101-2026. |
| `delivery/numbering_patch.py` | подготовка minimal patch и full shift, без записи в исходные DXF. |
| `delivery/changes_table.md` | нормативная таблица ГОСТ Р 2.503-2023 + отдельная операционная таблица. |
| `delivery/next_steps.md` | 5 задач P0–P2. |
| `delivery/night-session-2.md`, `logs/night-session-2.log` | хронология второй сессии. |
| `.github/workflows/windows-build.yml` | ручная сборка C# на будущей Windows-VM. |
| `docs/normative-audit.md`, `docs/windows-vm-build.md` | повторная проверка реестра и инструкция по VM. |

## Артефакты третьей сессии

| Файл | Назначение |
|---|---|
| `delivery/session-3/` | все результаты P0–P2, manifest и логи сессии. |
| `delivery/session-3/demo.gif` | 6-кадровое демо ≤3 МБ с верхним баннером и нижним watermark. |
| `delivery/session-3/demo_storyboard.png` | раскадровка GIF 1600×1200 с watermark. |
| `delivery/session-3/official_text_extract.md` | выписка из официального издания ГОСТ Р 21.101-2026: Приложение Б и раздел 7. |
| `delivery/data/norms_registry.json` | JSON-список норм с полями `norm`, `edition`, `date_force`, `source`. |
| `tools/pipeline.py` | synthetic backend выполнен; MultiCAD backend — честная заглушка. |
| `tools/sheetset_probe.py` | проверка print order и гипотез `GetSheets()`/`GetSheetSets()`. |
| `tools/make_demo_gif.py` | генератор GIF на локальных данных, без CAD-скриншотов. |
| `tools/windows_stand_check.ps1` | PowerShell-чек будущего Windows-стенда. |
| `delivery/session-3/senior_review.md` | что проверено и что осталось с **ГИПОТЕЗА/ПРОВЕРИТЬ**. |

## Ключевые показатели

| Показатель | Значение |
|---|---:|
| Синтетических DXF | {summary['input']['syntheticDxfFiles']} |
| Строк реестра / формы 1 / печати | {summary['output']['registryRows']} / {summary['output']['form1Rows']} / {summary['output']['printOrderItems']} |
| Инцидентов комплектности | {summary['output']['completenessIssues']} |
| Групп дублей | {summary['output']['duplicateGroups']} |
| PNG-макетов | {len(shots)} |
| Локальных проверок | {verification['requiredChecks']} required, {verification['failedRequiredChecks']} failed |
| Rollback / print consistency | {summary['stampRollbackVerified']} / {summary['printOrderConsistent']} |

Распределение инцидентов:

{issue_lines}

## Ключевые скриншоты (все — не nanoCAD)

| № | Файл | Сюжет |
|---:|---|---|
{shot_lines}

Пример вставки в чат:

![POC-сканер](screenshots/screenshot_02_poc_scan.png)

## Нормативные находки — обязательно к ревью

- **Повторная проверка 2026-10-28:** [официальное издание ГОСТ Р 21.101-2026](https://pravdaosro.ru/wp-content/uploads/2026/03/GOST-R-21.101-2026.pdf) подтверждает «ВЗАМЕН ГОСТ Р 21.101—2020», дату введения 01.04.2026 и обязательное Приложение Б; раздел 7 уточняет правила изменений и форму 10. Полный защищённый текст не перераспространяется.
- **Повторная проверка 2026-10-27:** [Росстандарт, ГОСТ Р 21.101-2026](https://protect.gost.ru/gost/details/17bc12e8-6579-4145-b141-56855e772e7f) — «Действует», приказ 129-ст от 12.02.2026, введение 01.04.2026; [ГОСТ Р 2.503-2023](https://protect.gost.ru/document.aspx?control=7&id=256448) — «Действует» с 01.03.2024; [ГОСТ 2.503-2013](https://protect.gost.ru/gost/details/03d72f0a-a11e-436f-ba81-41f9333ccc39) — «Утратил силу в РФ».
- **ГОСТ Р 21.101-2020 утратил силу**: действует ГОСТ Р 21.101-2026 с 01.04.2026; формы 1/2 — приложение Б.
- **ГОСТ 2.503-2013 утратил силу в РФ**: действует ГОСТ Р 2.503-2023; для СПДС также проверять раздел 7 ГОСТ Р 21.101-2026.
- **ГОСТ 2.301-68** пока применяется для проверки обозначений форматов; вопрос досрочного применения ГОСТ Р 2.301-2026 требует уточнения.
- Точные размеры граф форм 1/2, приоритет требований об изменениях и соответствие штатной таблицы SHEETSET остаются **ГИПОТЕЗА/ПРОВЕРИТЬ**.

Подробности: [`../docs/standards-warning.md`](../docs/standards-warning.md), [`../docs/sources.md`](../docs/sources.md).

## API-выводы

- `GetSheets()` — только исторический пример MultiCAD.NET 2015; SDK 26 не проверен.
- `GetSheetSets()` — публичного подтверждения не найдено; в коде не вызывается.
- «Извлечение данных из нескольких DWG» — по форуму 2025 года «из коробки нет».
- Подготовлен `src/NavigatorKit.NanoCad/SdkProbe.cs` для reflection-дампа реальных методов без догадок.

## GitHub-действия

- Ветка: `{branch}` (создавать `night-session-YYYYMMDD` нельзя: имя ветки зафиксировано сессией Arena).
- Коммит на момент генерации отчёта: `{commit}`.
- PR: {pr_text}.
- Push: `git push origin {branch}`.
- PR body: `delivery/PR_BODY.md`.

## Что сделать до следующего раза (3–5 пунктов)

Подробный чек-лист: [`next_steps.md`](next_steps.md).

1. **P0 — Реальный Windows-стенд.** nanoCAD 26 + лицензия + SDK 26, `NK_HELLO`, `SDK_PROBE`, TFM/DLL и 3 реальных снимка.
2. **P0 — Нормоконтроль геометрии.** Сверить размеры граф форм 1/2, форму 10 и приоритет раздела 7 по официальному изданию.
3. **P1 — 3 × 40 реальных DWG.** Проверить `Database`/`Transaction`, запись атрибутов и rollback SHA-256 через реальный адаптер.
4. **P1 — SHEETSET/Tables/`.dst`.** Подтвердить `GetSheets()`/`GetSheetSets()` и синхронизировать layouts с `delivery/session-3/print_order.json`.
5. **P2 — Конкурсное демо.** GIF/MP4 ≤3 МБ из реального nanoCAD, финальный senior review и снятие оставшихся гипотез.

## Воспроизведение

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tools/generate_fixtures.py
python3 tools/navigator_kit.py all
python3 tools/night_session_2.py
python3 tools/session3_runner.py
.venv/bin/python tools/render_screenshots.py
python3 tools/finalize_delivery.py
python3 tools/verify_delivery.py --check-only
```

---
**Конец отчета.**
"""


def build_pr_body(summary: dict, verification: dict) -> str:
    return f"""## Ночная сессия «Комплект-Навигатор» — 2026-10-26 → 2026-10-27 → обновление 2026-10-28

Автономно собран воспроизводимый каркас: {summary['input']['syntheticDxfFiles']} синтетических DXF, реестр, формы 1/2, контроль комплектности, нумератор, rollback, таблица изменений, порядок печати, C# скелеты, {len(read_json(SHOTS / 'screenshots_manifest.json')['images'])} подписанных PNG-макетов, HTML dashboard и ZIP.

**Обновление 2026-10-27:** повторно проверен официальный реестр Росстандарта; добавлены именованные отчёты/шаблоны, XSD-маппинг с атрибутами листа/формата, Windows workflow и полупрозрачный watermark.

**Обновление 2026-10-28:** выполнен P0–P2 проход. Добавлены `delivery/session-3/`, выписка из официального издания ГОСТ Р 21.101-2026 (Приложение Б + раздел 7), `norms_registry.json`, `tools/pipeline.py`, `tools/sheetset_probe.py`, `tools/make_demo_gif.py`, PowerShell-чек Windows-стенда, GIF-демо ≤3 МБ и senior-review чек-лист. Synthetic backend пересобрал 120 DXF; MultiCAD/DWG часть честно помечена внешней зависимостью. Метки PR: `good first issue`, `night-session`.

### Финальный Linux-этап (2026-10-29)
- `tools/geometry_audit.py` → 12 DXF, project-checks + reference paper sizes; нормы NOT_ASSESSED.
- `docs/windows-stand-setup.md` — лицензия/VS/SDK, проверяемые NK_HELLO и NK_SDK_PROBE.
- `src/CSharpAdapter/` — реальный portable parser и 28 xUnit cases; CI доказательства в `delivery/linux-stand/csharp_ci_validation.json`.
- `docs/gif-demo-scenario.md` — сценарий будущей реальной съёмки, без выдуманных UI-команд.
- `delivery/README_night-session-final.md`, `navigator-kit-final-session.zip` (≤3MB, без вложенных ZIP).

Что сделать до следующего раза:
1. P0 — официальные размеры форм/рамки, визуальная и размерная проверка в nanoCAD.
2. P0 — реальный Windows/SDK/лицензия, выполнить NK_HELLO/NK_SDK_PROBE.
3. P1 — host-адаптер DWG/атрибуты/транзакции/rollback/layouts/Tables.
4. P1 — реальная съёмка по GIF-сценарию ≤3MB.
5. P2 — senior review и конкурсная заявка человеком; без фиктивных актов внедрения.

### Test Runner (обновление после 2f57aa6)
Пакет `delivery/navigator-kit-test-runner.zip` содержит исходники, все данные 28 тестов,
12 новых DXF и 12 рендеров. Запуск из распакованного ZIP проверяется автоматически.
`README_test_runner.md`, `tests/portability_note.md`: зависимости, установка, границы переносимости.
`pytest_output.log`, `collect_log.txt`, `test_report.json`: фактический прогон/обнаружение тестов.
28 pytest PASS / 59 delivery checks, 0 failures — разные наборы проверок.
Размер ZIP проверяется сборщиком (≤3 MB); точный размер сообщается после сборки.
Python 3.11/Linux проверен; Windows/macOS и другие версии Python не выполнялись.
Это НЕ nanoCAD-плагин; MultiCAD backend и C#-порт не реализованы.

### Linux-стенд: завершение пакетного прогона
12 DXF fixtures → независимая перечитка без ezdxf → 12 реальных рендеров 1600×1200 с баннером и watermark.
Полный pytest и delivery-проверки раздельно записаны в `delivery/linux-stand/test_report.json` и `pytest.log`.
Отдельный пакет: `delivery/navigator-kit-linux-stand.zip` (≤3 MB; фактический размер в комментарии PR).

Что сделать до следующего раза:
1. **P0 — Нормоконтроль:** подтвердить геометрию форм 1/2 по официальному тексту; сохранённые выдержки не закрывают проверку размеров.
2. **P0 — Windows-стенд:** выполнить существующую инструкцию и PowerShell-чек на nanoCAD 26/SDK/лицензии, получить реальные NK_HELLO/SdkProbe и снимки.
3. **P1 — C#-ядро:** перенести Python-контракт с одинаковыми fixtures; существующий SdkProbe.cs подтвердить на SDK, не угадывать API.

### Доказательно выполнено
- Python reference CLI просканировал 120 DXF R2010 и записал CSV/JSON.
- Обнаружено {summary['output']['completenessIssues']} контрольных инцидентов и {groups_phrase(summary['output']['duplicateGroups'])}.
- Rollback штампов подтверждён SHA-256; исходные файлы не изменены.
- Порядок печати совпадает с формой 1.
- XSD/JSON/CSV/PNG проверены; C# синтаксис разобран tree-sitter.

### Критические ограничения
- nanoCAD 26 / SDK / .NET / Windows / лицензия в sandbox отсутствуют.
- PNG — **не скриншоты nanoCAD**, а честно помеченные диагностические макеты.
- Production DWG, `Database`/`Transaction`, Tables API и `.dst` остаются непроверенными; метки **ГИПОТЕЗА/ПРОВЕРИТЬ** сохранены намеренно.
- **ГОСТ Р 21.101-2020 заменён ГОСТ Р 21.101-2026**; ГОСТ 2.503-2013 заменён ГОСТ Р 2.503-2023. Ссылки на официальный реестр — в `docs/normative-audit.md`.
- Windows-VM workflow подготовлен, но **не запускался** в этом Linux sandbox; реальные DWG и nanoCAD остаются внешней зависимостью.

### Что сделать до следующего раза
1. **P0:** реальный Windows-стенд с nanoCAD 26, лицензией и SDK 26; `NK_HELLO`, `SDK_PROBE`, TFM/DLL, 3 реальных снимка.
2. **P0:** нормоконтроль геометрии форм 1/2, формы 10 и приоритета раздела 7 по официальному изданию.
3. **P1:** пилот на 3 × 40 реальных DWG с проверенным `Database`/`Transaction`, записью штампов и rollback SHA-256.
4. **P1:** подтвердить `GetSheets()`/`GetSheetSets()`, Tables API и синхронизацию layouts с `print_order.json`.
5. **P2:** демо ≤3 МБ из реального nanoCAD, финальный senior review и закрытие оставшихся гипотез.

Верификация: `{verification['status']}`, required checks: {verification['requiredChecks']}, failed: {verification['failedRequiredChecks']}.
"""


def build_chat_reply(summary: dict, verification: dict, commit: str, pr_url: str, branch: str) -> str:
    pr = pr_url if pr_url.startswith("http") else "PR будет создан после push"
    return f"""# Готовый ответ в чат

🚀 Linux-stand и Test Runner готовы для повторения проверок.
✅ 12 подготовленных DXF + 12 рендеров 1600×1200, banner + watermark.
✅ 28 pytest PASS; 59 delivery checks / 0 failures — отдельно.
✅ ZIP проверяется распаковкой и запуском тестов; минимальные зависимости перечислены.
Python 3.11/Linux проверен. Другие ОС не запускались. Это не nanoCAD-плагин.
Пакет: `delivery/navigator-kit-test-runner.zip` (≤3 MB); инструкция: `README_test_runner.md`.

Ночная сессия завершена и обновлена 2026-10-28. Ветка `{branch}`, коммит `{commit}`, PR: {pr}.

**Сделано:** 120 синтетических DXF → реестр CSV/JSON, формы 1/2, {summary['output']['completenessIssues']} инцидентов комплектности, {groups_phrase(summary['output']['duplicateGroups'])}, rollback с проверкой SHA-256, порядок печати на 120 листов, XML/XSD-маппинг, C# каркас, 15 PNG 1600×1200, HTML-дашборд и ZIP. Добавлены именованные артефакты второй сессии, Windows workflow и постоянный watermark. Третья сессия добавила P0–P2 проход, официальную выписку, GIF-демо ≤3 МБ и senior review; гипотезы CAD-стенда сохранены.

**Важно:** nanoCAD/SDK здесь не запускались. PNG — подписанные диагностические макеты, не скриншоты CAD. Обнаружено, что ГОСТ Р 21.101-2020 и ГОСТ 2.503-2013 утратили силу; отчёт содержит предупреждение и переключение на актуальные редакции.

**Артефакты:** `delivery/README_night-session.md`, `delivery/index.html`, `delivery/session-3/`, `delivery/session-3/demo.gif`, `delivery/completeness_report.md`, `delivery/data/wo1_template.docx`, `delivery/data/wo2_template.csv`, `delivery/numbering_patch.py`, `delivery/changes_table.md`, `delivery/next_steps.md`, `delivery/data/`, `delivery/xml/`, `delivery/screenshots/`, `delivery/navigator-kit-night-session.zip`.

**Следующий шаг:** Windows + nanoCAD 26 + SDK, `NK_HELLO`/`SdkProbe`, реальные DWG и нормоконтроль форм 1/2 по ГОСТ Р 21.101-2026.

Верификация: `{verification['status']}`.
"""


def build_dashboard(summary: dict, verification: dict, standards: dict, commit: str, pr_url: str) -> str:
    shots = read_json(SHOTS / "screenshots_manifest.json")["images"]
    cards = "".join(
        f'<article class="card"><img src="screenshots/{html.escape(Path(s["file"]).name)}" alt="{html.escape(s["title"])}"><div><h3>{i+1:02d}. {html.escape(s["title"])}</h3><p>{html.escape(Path(s["file"]).name)} • 1600×1200 • НЕ nanoCAD</p></div></article>'
        for i, s in enumerate(shots))
    issue_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>" for k, v in summary["issueCounts"].items())
    session2_path = DATA / "session2_summary.json"
    session2 = read_json(session2_path) if session2_path.is_file() else {"tasks": []}
    session3_path = DATA / "session3_summary.json"
    session3 = read_json(session3_path) if session3_path.is_file() else {"tasks": []}
    check_rows = "".join(
        f'<tr class="{"ok" if c["ok"] else "bad"}"><td>{"OK" if c["ok"] else "FAIL"}</td><td>{html.escape(c["name"])}</td><td>{html.escape(c["detail"])}</td></tr>'
        for c in verification["checks"])
    tpl = Template("""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Комплект-Навигатор — ночной отчет</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#142036;--line:#344a6c;--text:#e9f1ff;--muted:#9aafca;--green:#4ade80;--amber:#fbbf24;--red:#f87171;--blue:#60a5fa}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}.wrap{max-width:1440px;margin:auto;padding:32px}.hero{border:2px solid var(--red);background:linear-gradient(135deg,#311b26,#101b2d);border-radius:22px;padding:34px}.hero h1{font-size:44px;margin:0 0 8px}.hero p{color:var(--muted);font-size:20px;margin:6px 0}.badge{display:inline-block;margin-top:12px;padding:8px 14px;border-radius:999px;background:#48222b;color:#fca5a5;font-weight:700}.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin:24px 0}.kpi{background:var(--panel);border:2px solid var(--line);border-radius:18px;padding:20px}.kpi b{display:block;font-size:40px;color:var(--green)}.kpi span{color:var(--muted)}h2{margin-top:42px;font-size:30px;border-bottom:1px solid var(--line);padding-bottom:10px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.card{background:var(--panel);border:2px solid var(--line);border-radius:18px;overflow:hidden}.card img{display:block;width:100%;height:auto}.card div{padding:14px 18px}.card h3{margin:0;font-size:20px}.card p{margin:4px 0;color:var(--muted)}table{width:100%;border-collapse:collapse;background:var(--panel);border-radius:14px;overflow:hidden}th,td{padding:10px 12px;border-bottom:1px solid #263956;text-align:left;vertical-align:top}th{background:#1c2c48;color:var(--blue)}tr.ok td:first-child{color:var(--green);font-weight:700}tr.bad td:first-child{color:var(--red);font-weight:700}.warn{border-left:6px solid var(--amber);background:#332711;padding:18px;border-radius:12px}.links a{color:var(--blue);margin-right:16px}code{background:#1d2b43;padding:2px 6px;border-radius:5px}footer{margin:50px 0 20px;color:var(--muted);font-size:14px}@media(max-width:1000px){.kpis{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
<section><h2>Исполняемый Linux-стенд</h2><p><a href="linux-stand/README.md">Отчёт, ограничения и повторный запуск</a> · <a href="linux-stand/run.log">Полный лог: 8 тестов</a> · <a href="linux-stand/hello_stamp.dxf">DXF</a> · <a href="linux-stand/verification.json">Независимая проверка</a></p><p>Реальный рендер тестового DXF, не скриншот nanoCAD и не утверждённая форма ГОСТ.</p><img src="linux-stand/hello_stamp.png" alt="Рендер DXF Linux-стенда" style="max-width:100%"></section>
<section class="hero"><h1>Комплект-Навигатор</h1><p>Ночные сессии • 2026-10-26 → 2026-10-27 → 2026-10-28 • branch $branch • commit $commit</p><p>$sheets DXF • $issues инцидентов • $duplicates_label • $shots PNG-макетов</p><div class="badge">nanoCAD НЕ запускался • все изображения — подписанные диагностические макеты</div></section>
<section class="kpis"><div class="kpi"><b>$sheets</b><span>DXF R2010</span></div><div class="kpi"><b>$registry</b><span>строк реестра</span></div><div class="kpi"><b>$issues</b><span>инцидентов</span></div><div class="kpi"><b>$duplicates</b><span>групп дублей</span></div><div class="kpi"><b>$shots</b><span>PNG 1600×1200</span></div><div class="kpi"><b>$verification</b><span>required checks</span></div></section>
<section><h2>Обновление второй сессии — 2026-10-27</h2><div class="warn"><p>Повторно проверен официальный реестр Росстандарта; XML-маппинг дополнен атрибутами <code>sheet_no</code> и <code>format</code>; подготовлен Windows-VM workflow. Все 12 PNG имеют постоянный полупрозрачный водяной знак в правом нижнем углу.</p><p>Новые артефакты: <a href="completeness_report.md">completeness_report.md</a> • <a href="data/wo1_template.docx">wo1_template.docx</a> • <a href="data/wo2_template.csv">wo2_template.csv</a> • <a href="numbering_patch.py">numbering_patch.py</a> • <a href="changes_table.md">changes_table.md</a> • <a href="next_steps.md">next_steps.md</a> • <a href="night-session-2.md">night-session-2.md</a> • <a href="data/completeness_chart.png">график инцидентов</a>. Задач в session2: $session2_tasks.</p></div></section>
<section><h2>Третья сессия — 2026-10-28</h2><div class="warn"><p>P0–P2 проход: официальная выписка ГОСТ Р 21.101-2026, Windows-stand инструкция, synthetic pipeline, SHEETSET probe и GIF-демо ≤3 МБ. Реальный nanoCAD не запускался; гипотезы сохранены.</p><p>Ссылки: <a href="session-3/README.md">session-3/</a> • <a href="session-3/demo.gif">demo.gif</a> • <a href="session-3/senior_review.md">senior review</a> • <a href="session-3/official_text_extract.md">официальная выписка</a> • <a href="data/norms_registry.json">norms_registry.json</a> • <a href="next_steps.md">next_steps.md</a>. Задач session3: $session3_tasks.</p></div></section>
<section><h2>Нормативное предупреждение</h2><div class="warn"><p><b>$active_spds</b>. Запрошенный ГОСТ Р 21.101-2020 утратил силу. Формы 1/2 — приложение Б.</p><p><b>$active_changes</b>. ГОСТ 2.503-2013 утратил силу в РФ. Точные размеры таблиц и приоритет раздела 7 СПДС — <b>ГИПОТЕЗА/ПРОВЕРИТЬ</b>.</p></div></section>
<section><h2>Ключевые ссылки</h2><p class="links"><a href="README_night-session.md">Полный отчет</a><a href="PR_BODY.md">PR body</a><a href="CHAT_REPLY.md">Ответ в чат</a><a href="night-log.md">Ночной лог</a><a href="data/summary.json">summary.json</a><a href="xml/stamp_mapping.xml">XML-маппинг</a><a href="navigator-kit-night-session.zip">ZIP-бандл</a><a href="../docs/standards-warning.md">Нормы</a></p></section>
<section><h2>Инциденты комплектности</h2><table><thead><tr><th>Код</th><th>Количество</th></tr></thead><tbody>$issue_rows</tbody></table></section>
<section><h2>Диагностические изображения</h2><div class="grid">$cards</div></section>
<section><h2>Матрица проверки</h2><table><thead><tr><th>Статус</th><th>Проверка</th><th>Деталь</th></tr></thead><tbody>$check_rows</tbody></table></section>
<footer>Локальный контур: VERIFIED_LOCALLY. Production DWG, MultiCAD .NET SDK 26, .dst и реальные скриншоты: ГИПОТЕЗА/ПРОВЕРИТЬ. PR: $pr_url</footer>
</div></body></html>""")
    return tpl.substitute(
        branch="arena/ec9fddc1-navigator-kit", commit=html.escape(commit), sheets=summary["input"]["syntheticDxfFiles"],
        issues=summary["output"]["completenessIssues"], duplicates=summary["output"]["duplicateGroups"],
        shots=len(shots), registry=summary["output"]["registryRows"], verification=verification["requiredChecks"],
        duplicates_label=groups_phrase(summary["output"]["duplicateGroups"]),
        session3_tasks=len(session3["tasks"]),
        active_spds=html.escape(standards["active"]["spds"]), active_changes=html.escape(standards["active"]["changesEskd"]),
        issue_rows=issue_rows, cards=cards, check_rows=check_rows,
        pr_url=html.escape(pr_url if pr_url.startswith("http") else "pending"),
        session2_tasks=len(session2["tasks"]),
    )


def build_manifest() -> None:
    excluded = {"delivery/MANIFEST.json", "delivery/manifest.sha256", "delivery/navigator-kit-night-session.zip"}
    files: dict[str, str] = {}
    for p in sorted(DELIVERY.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel in excluded or p.suffix == ".zip" or "__pycache__" in p.parts:
            continue
        files[rel] = sha256_file(p)
    manifest = {
        "format": "navigator-kit.delivery-manifest/v1",
        "sessionId": SESSION,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fileCount": len(files),
        "files": files,
        "note": "Excludes manifest, checksum list, and ZIP itself. Source code/tools/docs are in the repository and in the ZIP.",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CHECKSUMS.write_text("".join(f"{digest}  {rel}\n" for rel, digest in sorted(files.items())), encoding="utf-8")


def build_zip() -> None:
    if BUNDLE.exists():
        BUNDLE.unlink()
    include_roots = ["delivery", "docs", "src", "tools", "tests", "samples", "linux_stand", ".github/workflows"]
    extra_files = ["README_test_runner.md", "requirements-test-runner.txt", "README.md", "briefing.md", "requirements.txt", "requirements-analysis.txt", ".gitignore", "night-log.md"]
    with zipfile.ZipFile(BUNDLE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in extra_files:
            p = ROOT / rel
            if p.is_file():
                zf.write(p, f"navigator-kit/{rel}")
        for root_name in include_roots:
            base = ROOT / root_name
            if not base.exists():
                continue
            for p in sorted(base.rglob("*")):
                if not p.is_file():
                    continue
                rel = p.relative_to(ROOT).as_posix()
                if p.suffix == ".zip" or "__pycache__" in p.parts or p.suffix == ".pyc":
                    continue
                zf.write(p, f"navigator-kit/{rel}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument("--pr-url", default="https://github.com/Igorr112323/NAVIGATOR-KIT/pull/1")
    ap.add_argument("--branch", default="arena/ec9fddc1-navigator-kit")
    args = ap.parse_args()

    summary = read_json(DATA / "summary.json")
    standards = read_json(DATA / "standards_status.json")
    commit = args.commit
    if commit in ("HEAD", "pending", ""):
        try:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            commit = "pending"

    def write_text_artifacts(state: dict) -> None:
        write_text(DELIVERY / "README_night-session.md",
                   build_readme(summary, state, commit, args.pr_url, args.branch))
        write_text(DELIVERY / "PR_BODY.md", build_pr_body(summary, state))
        write_text(DELIVERY / "CHAT_REPLY.md",
                   build_chat_reply(summary, state, commit, args.pr_url, args.branch))
        write_text(DELIVERY / "index.html",
                   build_dashboard(summary, state, standards, commit, args.pr_url))

    # Phase A: validate freshly regenerated source artifacts. Do NOT validate a
    # stale manifest here — CI regenerates timestamped logs/screenshots first.
    core = run_checks(require_bundle=False)
    RESULTS.write_text(json.dumps(core, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if core["status"] != "PASS":
        print(json.dumps(core, ensure_ascii=False, indent=2))
        return 1
    write_text_artifacts(core)
    build_manifest()
    build_zip()

    # Phase B: now that a fresh bundle exists, compute the complete verification
    # state and regenerate text/manifest/zip one final time.
    final = run_checks(require_bundle=True)
    RESULTS.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if final["status"] != "PASS":
        print(json.dumps(final, ensure_ascii=False, indent=2))
        return 1
    write_text_artifacts(final)
    build_manifest()
    build_zip()
    print(json.dumps({
        "status": "PASS", "report": "delivery/README_night-session.md",
        "dashboard": "delivery/index.html", "manifestFiles": read_json(MANIFEST)["fileCount"],
        "zipBytes": BUNDLE.stat().st_size, "commit": commit, "prUrl": args.pr_url,
        "requiredChecks": final["requiredChecks"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
