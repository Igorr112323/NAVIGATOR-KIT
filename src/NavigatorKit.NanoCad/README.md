# NavigatorKit.NanoCad — адаптер-скелет

**Статус:** **ГИПОТЕЗА/ПРОВЕРИТЬ**. В sandbox нет nanoCAD 26 и SDK; эта сборка не запускалась в CAD-хосте.

Проект по умолчанию компилирует только host-independent `SdkProbe` и заглушку. Когда переменная `NANOCAD_SDK_PATH` определена и существует локальный `NanoCadSdkReferences.props`, определяется константа `NANOCAD_SDK`, и компилируются команды `NK_HELLO`, `NK_SDK_PROBE`.

## Проверка на Windows

1. Установить nanoCAD 26 и SDK из Клуба разработчиков.
2. Сверить target framework и реальные DLL. `net8.0` здесь — кандидат, а не гарантия.
3. Скопировать `NanoCadSdkReferences.props.example` в `NanoCadSdkReferences.props`, поправить пути.
4. `dotnet build src/NavigatorKit.NanoCad/NavigatorKit.NanoCad.csproj -c Release`.
5. `NETLOAD` собранного DLL → `NK_HELLO` → сделать настоящий скриншот nanoCAD.
6. `NK_SDK_PROBE` → сохранить `navigator-kit-sdk-probe.txt` в `delivery/data/`.
7. Только после анализа дампа писать реальный `Dwg/Database/Transaction` адаптер.

## Чего здесь нет

- Нет вызовов `GetSheetSets()` — метод публично не подтверждён.
- Нет прямой записи `.dst` — формат не подтверждён как открытый.
- Нет Tables API — его сигнатуры нужно взять из SDK 26.
- Нет правки реальных DWG — reversible transaction показана на текстовых DXF-копиях в Python/C# Core.

## Session 3 readiness

`DwgReadiness.cs` is a compile-safe checklist for production DWG. It intentionally does not reference `Database`, `Transaction`, or `BlockReference` until SDK 26 signatures are confirmed with `SDK_PROBE`. See `delivery/session-3/p1_production_dwg.json` and `tools/pipeline.py --backend multicad`.
