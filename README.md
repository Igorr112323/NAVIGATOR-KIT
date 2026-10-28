# Комплект‑Навигатор — ночные сеансы 2026‑10‑26 → 2026‑10‑27 → 2026‑10‑28

Автономный каркас для конкурсной работы: реестр листов, ведомости форм 1/2, контроль комплектности, детектор дублей, обратимая правка штампов, таблица изменений и порядок печати.

> **Жёсткая честность.** В репозитории нет `briefing.md` пользователя, Windows, nanoCAD 26, MultiCAD .NET SDK и лицензии. Всё, что реально выполнено в этом Linux‑sandbox, помечено `VERIFIED_LOCALLY`; всё, что требует nanoCAD/SDK, помечено **ГИПОТЕЗА/ПРОВЕРИТЬ**. PNG в `delivery/screenshots/` — честно подписанные диагностические макеты вывода CLI, а не снимки nanoCAD.

> **Нормативное предупреждение.** На 2026‑10‑27 действует ГОСТ Р 21.101‑2026, а не указанный в задании ГОСТ Р 21.101‑2020; формы 1/2 теперь в обязательном приложении Б. ГОСТ 2.503‑2013 также утратил силу в РФ и заменён ГОСТ Р 2.503‑2023. Повторная проверка официального реестра и аудит: [`docs/standards-warning.md`](docs/standards-warning.md), [`docs/normative-audit.md`](docs/normative-audit.md).

> **Вторая сессия.** Продолжение собрано в PR #1: именованные отчёты/шаблоны в `delivery/`, 12 PNG с постоянным водяным знаком, Windows-VM workflow и финальный отчёт от 2026‑10‑27. nanoCAD 26 по-прежнему не запускался.
>
> **Третья сессия 2026‑10‑28.** Выполнен P0–P2 проход: официальная выписка по ГОСТ Р 21.101‑2026, подготовка Windows-стенда, `tools/pipeline.py`, SHEETSET probe, GIF‑демо ≤3 МБ и senior review. Результаты — в `delivery/session-3/`. Метки **ГИПОТЕЗА/ПРОВЕРИТЬ** сохранены до реального CAD‑стенда.

## Быстрый старт (без nanoCAD)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tools/generate_fixtures.py
.venv/bin/python tools/navigator_kit.py all
.venv/bin/python tools/night_session_2.py
.venv/bin/python tools/session3_runner.py
.venv/bin/python tools/render_screenshots.py
.venv/bin/python tools/finalize_delivery.py
.venv/bin/python tools/verify_delivery.py --check-only
```

Главные результаты: [`delivery/README_night-session.md`](delivery/README_night-session.md), [`delivery/index.html`](delivery/index.html), [`delivery/data/`](delivery/data/), [`delivery/xml/`](delivery/xml/), [`delivery/screenshots/`](delivery/screenshots/).

## C#‑каркас

`src/NavigatorKit.Core`, `src/NavigatorKit.Cli` — переносимый .NET 8 код без NuGet‑зависимостей. `src/NavigatorKit.NanoCad` — условно компилируемый адаптер; он **не подключает выдуманные API**. Точный TFM и состав DLL для nanoCAD 26 нужно сверить с SDK. См. [`docs/nanocad-integration.md`](docs/nanocad-integration.md).

```bash
dotnet build src/NavigatorKit.Cli/NavigatorKit.Cli.csproj -c Release
dotnet run --project src/NavigatorKit.Cli -- --input samples/synthetic_sets --output delivery/data/csharp-preview
```

## Проверка статуса

| Компонент | Статус |
|---|---|
| Python CLI, 120 синтетических DXF, CSV/JSON/XML, rollback | `VERIFIED_LOCALLY` |
| C# Core/CLI | исходный код; сборка в sandbox невозможна (`dotnet` отсутствует) |
| MultiCAD .NET / nanoCAD 26 / `.dst` / реальные DWG | **ГИПОТЕЗА/ПРОВЕРИТЬ** |
| Скриншоты nanoCAD | не создавались; заменены подписанными макетами |

## Артефакты второй сессии

- `delivery/completeness_report.md` — 16 инцидентов, 4 группы дублей, рекомендации.
- `delivery/data/wo1_template.csv`, `delivery/data/wo1_template.docx`, `delivery/data/wo2_template.csv` — формы 1/2 по Приложению Б ГОСТ Р 21.101‑2026.
- `delivery/numbering_patch.py` — подготовка minimal patch и full shift; исходники не трогает.
- `delivery/changes_table.md` — нормативная таблица ГОСТ Р 2.503‑2023 и отдельная операционная таблица.
- `delivery/next_steps.md` — 5 задач P0–P2.
- `delivery/night-session-2.md`, `logs/night-session.log` — хронология продолжения.
- `.github/workflows/windows-build.yml` — ручная сборка на будущей Windows-VM.

## Артефакты третьей сессии

- `delivery/session-3/` — все результаты P0–P2, manifest, логи и GIF.
- `delivery/session-3/demo.gif` — 6-кадровое демо ≤3 МБ с двойным watermark.
- `delivery/data/norms_registry.json` — нормы с полями `norm`, `edition`, `date_force`, `source`.
- `tools/pipeline.py` — synthetic backend + честная заглушка MultiCAD.
- `tools/sheetset_probe.py` — проверка `print_order` и гипотез SHEETSET/Tables.
- `tools/make_demo_gif.py` — генератор GIF без CAD-скриншотов.
- `docs/windows-stand-setup.md`, `tools/windows_stand_check.ps1` — инструкция и чек будущего Windows-стенда.
- `delivery/session-3/senior_review.md` — что проверено и что осталось **ГИПОТЕЗА/ПРОВЕРИТЬ**.
