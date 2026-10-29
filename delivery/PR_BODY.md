## Комплект-Навигатор — финальный Linux-этап, 2026-10-29

### Проверенные результаты
- Python: 28 pytest PASS; независимая перечитка 12 DXF и 12 рендеров 1600×1200.
- Delivery: 59 checks / 0 failed.
- Portable C# parser: **COMPILED_AND_28_XUNIT_PASS**, actual cases: 28.
  Сборка, xUnit и explicit TRX gate: https://github.com/Igorr112323/NAVIGATOR-KIT/actions/runs/40832412743. Локального dotnet нет.
- 120 synthetic DXF: реестр, 16 инцидентов,
  4 группы дублей, .bak/rollback SHA-256, порядок печати.

### Что добавлено
1. `tools/geometry_audit.py` → `delivery/linux-stand/geometry_audit.md/json`.
   12 образцов: project/reference checks PASS, **формы 1/2 NOT_ASSESSED**.
2. `docs/windows-stand-setup.md`: законная лицензия, VS/SDK, TFM/DLL,
   точные исходные имена NK_HELLO/NK_SDK_PROBE и текстовый dump.
3. `src/CSharpAdapter/`: ParseFile/ParseText без CAD API, 28 xUnit cases
   (12 общих fixtures + 16 сценариев), CI; это частичный перенос, не готовый host-adapter.
4. `docs/gif-demo-scenario.md`: будущая реальная съёмка, gate перед запуском,
   корректные ffmpeg palettegen/paletteuse без выдуманного UI.
5. `delivery/README_night-session-final.md`, финальный ZIP ≤3 MB.
   Вложенные ZIP исключены; исходники/данные runner включены.

### Пакеты
- `delivery/navigator-kit-final-session.zip`
- `delivery/navigator-kit-test-runner.zip` (распаковка + полный pytest проверяются сборщиком)
- `delivery/navigator-kit-linux-stand.zip`
Все ограничены 3 000 000 байт; точные размеры — в комментарии с результатом сборки.

### Что сделать до следующего раза
1. **P0:** официальные размеры форм/рамки, проверка в реальном nanoCAD по тексту ГОСТ.
2. **P0:** реальный Windows/SDK/лицензия, NK_HELLO/NK_SDK_PROBE и снимки.
3. **P1:** host-адаптер DWG, профили штампа, транзакции/rollback, layouts/Tables.
4. **P1:** реальная съёмка по GIF-сценарию ≤3 MB.
5. **P2:** senior review и конкурсная заявка человеком; не создавать фиктивные акты внедрения.

**Ограничения:** nanoCAD не запускался, SDK API не подтверждены, геометрия ГОСТ не закрыта.
Это пакет исходников/тестов, не nanoCAD-плагин. Windows/macOS не тестировались.
Метки ГИПОТЕЗА/ПРОВЕРИТЬ сохранены. Исторические нормативные ссылки оставлены для аудита.
