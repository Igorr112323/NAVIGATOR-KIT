# Senior review — session 3 (2026-10-28)

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
