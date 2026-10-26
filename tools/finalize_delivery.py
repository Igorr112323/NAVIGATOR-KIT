#!/usr/bin/env python3
"""Build the chat-ready report, dashboard, manifest, and ZIP bundle."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
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
SESSION = "night-session-20261026"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_readme(summary: dict, verification: dict, commit: str, pr_url: str, branch: str) -> str:
    shots = read_json(SHOTS / "screenshots_manifest.json")["images"]
    shot_lines = "\n".join(
        f"| {i+1:02d} | `{Path(s['file']).name}` | {html.escape(s['title'])} |" for i, s in enumerate(shots))
    issue_lines = "\n".join(f"- `{k}` — {v}" for k, v in summary["issueCounts"].items())
    pr_text = f"[{pr_url}]({pr_url})" if pr_url.startswith("http") else "`PR будет создан после push`"
    return f"""# Ночной отчет ИИ-куратора — 2026-10-26

> **Статус честности:** локальный контур `VERIFIED_LOCALLY`, nanoCAD 26 **не запускался**. Все PNG — подписанные диагностические макеты, а не снимки CAD. C# код синтаксически разобран tree-sitter, но не скомпилирован (`dotnet` отсутствует).

## Что сделано за ночь

1. **Загрузка контекста** — репозиторий был пустым: только `README.md` из 16 байт и initial commit `7e4fcf3`. Issue/PR на старте отсутствовали. Восстановлен суррогат `briefing.md` с явной пометкой, что оригинал отсутствует.
2. **Зависимости** — проверены OS, Python, Node, .NET, nanoCAD, SDK, лицензия. `lk.nanocad.ru/education/request` требует nanoPassport; лицензию автономно получить нельзя.
3. **POC-сканер** — созданы и реально прочитаны **120 валидных DXF R2010** (3 марки × 40 листов) с атрибутами штампов. Получены `sheets_registry.csv/json`, 120 SHA-256.
4. **Штатная ф.1** — документарный эксперимент по SHEETSET, «Insert Sheet List Table», извлечению данных, `GetSheets()` и `GetSheetSets()`. Последний публично не подтверждён; прямая генерация `.dst` не выполнялась.
5. **XML-профиль** — master `stamp_mapping.xml`, два примера `spds_template_a.xml`/`spds_template_b.xml`, XSD-схема; атрибуты ↔ поля реестра.
6. **Обратимая правка** — dry-run → `.bak` → apply → verify → rollback на изолированных DXF-копиях; SHA-256 исходного и восстановленного совпадают. Исходники не изменены.
7. **Ведомости ф.1/ф.2** — CSV с строгими графами, мастер-файлы с техническими колонками, markdown-черновики. Нормативная база переключена на приложение Б ГОСТ Р 21.101-2026.
8. **Контроль комплектности** — {summary['output']['completenessIssues']} инцидентов, включая дубли, пустые графы, неверные форматы, « file ↔ registry » и « doc ↔ file » расхождения.
9. **Нумератор** — {summary['output']['duplicateGroups']} групп дублей; prepared minimal patch и full shift на 120 листов, без автоматической правки исходников.
10. **Таблица изменений** — пустой шаблон из 5 граф и технический реестр операций. Исправлена ошибка задания: «Аннулир.» не является значением графы «Лист».
11. **Порядок печати** — 120 элементов, совпадение с формой 1 по хэшу; `.dst` не редактировался.
12. **Код и визуализация** — C# Core/CLI/плагин-скелет, Python reference CLI, 12 PNG 1600×1200, HTML dashboard, log, manifest, ZIP.

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
- Коммит: `{commit}`.
- PR: {pr_text}.
- Push: `git push origin {branch}`.
- PR body: `delivery/PR_BODY.md`.

## Что сделать до следующего раза (3–5 пунктов)

1. **P0 — Нормоконтроль.** Получить официальный текст ГОСТ Р 21.101-2026 и сверить геометрию форм 1/2; подтвердить редакцию стандарта у организаторов конкурса.
2. **P0 — Windows/SDK.** Установить nanoCAD 26, получить лицензию и SDK 26, запустить `NK_HELLO` + `SdkProbe`, заменить макеты настоящими скриншотами.
3. **P1 — Production DWG.** На 3 × 40 реальных DWG реализовать background read, транзакции, запись атрибутов штампов и rollback.
4. **P1 — Tables/`.dst`.** Проверить Tables API и документированный доступ к SHEETSET; синхронизировать `print_order.json` с layouts без прямой правки `.dst`.
5. **P2 — Демо.** Снять GIF ≤3 МБ «папка → реестр → правка → сдвиг → печать», провести senior code review и убрать все `ГИПОТЕЗА/ПРОВЕРИТЬ`.

## Воспроизведение

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tools/generate_fixtures.py
python3 tools/navigator_kit.py all
.venv/bin/python tools/render_screenshots.py
python3 tools/finalize_delivery.py
python3 tools/verify_delivery.py --check-only
```

---
**Конец отчета.**
"""


def build_pr_body(summary: dict, verification: dict) -> str:
    return f"""## Ночная сессия «Комплект-Навигатор» — 2026-10-26

Автономно собран воспроизводимый каркас: {summary['input']['syntheticDxfFiles']} синтетических DXF, реестр, формы 1/2, контроль комплектности, нумератор, rollback, таблица изменений, порядок печати, C# скелеты, {len(read_json(SHOTS / 'screenshots_manifest.json')['images'])} подписанных PNG-макетов, HTML dashboard и ZIP.

### Доказательно выполнено
- Python reference CLI просканировал 120 DXF R2010 и записал CSV/JSON.
- Обнаружено {summary['output']['completenessIssues']} контрольных инцидентов и {summary['output']['duplicateGroups']} групп дублей.
- Rollback штампов подтверждён SHA-256; исходные файлы не изменены.
- Порядок печати совпадает с формой 1.
- XSD/JSON/CSV/PNG проверены; C# синтаксис разобран tree-sitter.

### Критические ограничения
- nanoCAD 26 / SDK / .NET / Windows / лицензия в sandbox отсутствуют.
- PNG — **не скриншоты nanoCAD**, а честно помеченные диагностические макеты.
- Production DWG, `Database`/`Transaction`, Tables API и `.dst` остаются непроверенными.
- **ГОСТ Р 21.101-2020 заменён ГОСТ Р 21.101-2026**; ГОСТ 2.503-2013 заменён ГОСТ Р 2.503-2023.

### Что сделать до следующего раза
1. **P0:** нормоконтроль по официальному тексту ГОСТ Р 21.101-2026 и геометрии форм 1/2.
2. **P0:** Windows-стенд с nanoCAD 26, лицензией и SDK; запустить `NK_HELLO` + `SdkProbe`, снять реальные скриншоты.
3. **P1:** реализовать фоновое чтение 3 × 40 реальных DWG и обратимую запись штампов через проверенный API.
4. **P1:** проверить Tables API и SHEETSET/`.dst`, синхронизировать порядок layouts.
5. **P2:** GIF-демо ≤3 МБ, senior review, устранение всех `ГИПОТЕЗА/ПРОВЕРИТЬ`.

Верификация: `{verification['status']}`, required checks: {verification['requiredChecks']}, failed: {verification['failedRequiredChecks']}.
"""


def build_chat_reply(summary: dict, verification: dict, commit: str, pr_url: str, branch: str) -> str:
    pr = pr_url if pr_url.startswith("http") else "PR будет создан после push"
    return f"""# Готовый ответ в чат

Ночная сессия завершена. Ветка `{branch}`, коммит `{commit}`, PR: {pr}.

**Сделано:** 120 синтетических DXF → реестр CSV/JSON, формы 1/2, {summary['output']['completenessIssues']} инцидентов комплектности, {summary['output']['duplicateGroups']} групп дублей, rollback с проверкой SHA-256, порядок печати на 120 листов, XML/XSD-маппинг, C# каркас, 12 PNG 1600×1200, HTML-дашборд и ZIP.

**Важно:** nanoCAD/SDK здесь не запускались. PNG — подписанные диагностические макеты, не скриншоты CAD. Обнаружено, что ГОСТ Р 21.101-2020 и ГОСТ 2.503-2013 утратили силу; отчёт содержит предупреждение и переключение на актуальные редакции.

**Артефакты:** `delivery/README_night-session.md`, `delivery/index.html`, `delivery/data/`, `delivery/xml/`, `delivery/screenshots/`, `delivery/navigator-kit-night-session.zip`.

**Следующий шаг:** Windows + nanoCAD 26 + SDK, `NK_HELLO`/`SdkProbe`, реальные DWG и нормоконтроль форм 1/2 по ГОСТ Р 21.101-2026.

Верификация: `{verification['status']}`.
"""


def build_dashboard(summary: dict, verification: dict, standards: dict, commit: str, pr_url: str) -> str:
    shots = read_json(SHOTS / "screenshots_manifest.json")["images"]
    cards = "".join(
        f'<article class="card"><img src="screenshots/{html.escape(Path(s["file"]).name)}" alt="{html.escape(s["title"])}"><div><h3>{i+1:02d}. {html.escape(s["title"])}</h3><p>{html.escape(Path(s["file"]).name)} • 1600×1200 • НЕ nanoCAD</p></div></article>'
        for i, s in enumerate(shots))
    issue_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>" for k, v in summary["issueCounts"].items())
    check_rows = "".join(
        f'<tr class="{"ok" if c["ok"] else "bad"}"><td>{"OK" if c["ok"] else "FAIL"}</td><td>{html.escape(c["name"])}</td><td>{html.escape(c["detail"])}</td></tr>'
        for c in verification["checks"])
    tpl = Template("""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Комплект-Навигатор — ночной отчет</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#142036;--line:#344a6c;--text:#e9f1ff;--muted:#9aafca;--green:#4ade80;--amber:#fbbf24;--red:#f87171;--blue:#60a5fa}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}.wrap{max-width:1440px;margin:auto;padding:32px}.hero{border:2px solid var(--red);background:linear-gradient(135deg,#311b26,#101b2d);border-radius:22px;padding:34px}.hero h1{font-size:44px;margin:0 0 8px}.hero p{color:var(--muted);font-size:20px;margin:6px 0}.badge{display:inline-block;margin-top:12px;padding:8px 14px;border-radius:999px;background:#48222b;color:#fca5a5;font-weight:700}.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin:24px 0}.kpi{background:var(--panel);border:2px solid var(--line);border-radius:18px;padding:20px}.kpi b{display:block;font-size:40px;color:var(--green)}.kpi span{color:var(--muted)}h2{margin-top:42px;font-size:30px;border-bottom:1px solid var(--line);padding-bottom:10px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.card{background:var(--panel);border:2px solid var(--line);border-radius:18px;overflow:hidden}.card img{display:block;width:100%;height:auto}.card div{padding:14px 18px}.card h3{margin:0;font-size:20px}.card p{margin:4px 0;color:var(--muted)}table{width:100%;border-collapse:collapse;background:var(--panel);border-radius:14px;overflow:hidden}th,td{padding:10px 12px;border-bottom:1px solid #263956;text-align:left;vertical-align:top}th{background:#1c2c48;color:var(--blue)}tr.ok td:first-child{color:var(--green);font-weight:700}tr.bad td:first-child{color:var(--red);font-weight:700}.warn{border-left:6px solid var(--amber);background:#332711;padding:18px;border-radius:12px}.links a{color:var(--blue);margin-right:16px}code{background:#1d2b43;padding:2px 6px;border-radius:5px}footer{margin:50px 0 20px;color:var(--muted);font-size:14px}@media(max-width:1000px){.kpis{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
<section class="hero"><h1>Комплект-Навигатор</h1><p>Ночная сессия • 2026-10-26 • branch $branch • commit $commit</p><p>$sheets DXF • $issues инцидентов • $duplicates групп дублей • $shots PNG-макетов</p><div class="badge">nanoCAD НЕ запускался • все изображения — подписанные диагностические макеты</div></section>
<section class="kpis"><div class="kpi"><b>$sheets</b><span>DXF R2010</span></div><div class="kpi"><b>$registry</b><span>строк реестра</span></div><div class="kpi"><b>$issues</b><span>инцидентов</span></div><div class="kpi"><b>$duplicates</b><span>групп дублей</span></div><div class="kpi"><b>$shots</b><span>PNG 1600×1200</span></div><div class="kpi"><b>$verification</b><span>required checks</span></div></section>
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
        active_spds=html.escape(standards["active"]["spds"]), active_changes=html.escape(standards["active"]["changesEskd"]),
        issue_rows=issue_rows, cards=cards, check_rows=check_rows,
        pr_url=html.escape(pr_url if pr_url.startswith("http") else "pending"),
    )


def build_manifest() -> None:
    excluded = {"delivery/MANIFEST.json", "delivery/manifest.sha256", "delivery/navigator-kit-night-session.zip"}
    files: dict[str, str] = {}
    for p in sorted(DELIVERY.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel in excluded or "__pycache__" in p.parts:
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
    include_roots = ["delivery", "docs", "src", "tools", "tests", "samples", ".github/workflows"]
    extra_files = ["README.md", "briefing.md", "requirements.txt", ".gitignore", "night-log.md"]
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
                if rel.endswith("navigator-kit-night-session.zip") or "__pycache__" in p.parts or p.suffix == ".pyc":
                    continue
                zf.write(p, f"navigator-kit/{rel}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", default="pending")
    ap.add_argument("--pr-url", default="pending")
    ap.add_argument("--branch", default="arena/ec9fddc1-navigator-kit")
    args = ap.parse_args()

    summary = read_json(DATA / "summary.json")
    standards = read_json(DATA / "standards_status.json")

    def write_text_artifacts(state: dict) -> None:
        write_text(DELIVERY / "README_night-session.md",
                   build_readme(summary, state, args.commit, args.pr_url, args.branch))
        write_text(DELIVERY / "PR_BODY.md", build_pr_body(summary, state))
        write_text(DELIVERY / "CHAT_REPLY.md",
                   build_chat_reply(summary, state, args.commit, args.pr_url, args.branch))
        write_text(DELIVERY / "index.html",
                   build_dashboard(summary, state, standards, args.commit, args.pr_url))

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
        "zipBytes": BUNDLE.stat().st_size, "commit": args.commit, "prUrl": args.pr_url,
        "requiredChecks": final["requiredChecks"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
