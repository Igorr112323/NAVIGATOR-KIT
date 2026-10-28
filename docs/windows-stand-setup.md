# Windows-стенд для nanoCAD 26 — инструкция third-session

Дата: **2026-10-28**. Документ подготовлен в Linux sandbox. Реальный стенд **не запускался**: нет Windows, nanoCAD 26, лицензии, MultiCAD .NET SDK 26 и `dotnet`. Поэтому все пункты ниже — чек-лист для человека, а не отчёт о выполненной установке.

## 0. Что уже подготовлено в репозитории

- `.github/workflows/windows-build.yml` — ручная сборка portable C# Core/CLI на `windows-latest`.
- `tools/windows_stand_check.ps1` — PowerShell-скрипт проверки готовности стенда.
- `src/NavigatorKit.NanoCad/SdkProbe.cs` — reflection-дамп реальных типов/методов SDK без выдуманных контрактов.
- `src/NavigatorKit.NanoCad/NanoCadCommands.cs` — команды `NK_HELLO` и `SDK_PROBE` (проверить по реальному SDK).
- `src/NavigatorKit.NanoCad/DwgReadiness.cs` — чек-лист готовности к чтению production DWG, без ссылок на непроверенные API.

## 1. Установка и лицензия

1. Установить nanoCAD 26 (x64) на Windows 10/11.
2. Получить действующую лицензию:
   - коммерческая/временная лицензия Nanosoft; или
   - образовательная лицензия через <https://lk.nanocad.ru/education/request>. Страница требует nanoPassport и капчу, автономно получить нельзя.
3. Запустить nanoCAD, убедиться, что лицензия активна и открывается новый чертёж.
4. Зафиксировать точную версию: `Help → About` или `%ProgramFiles%\Nanosoft\nanoCAD x64 26\...`.

## 2. SDK 26 и TFM

1. Вступить в клуб разработчиков nanoCAD: <https://www.nanocad.ru/developers/>.
2. Скачать MultiCAD .NET SDK именно для версии 26.
3. Сверить:
   - `TargetFramework` (в репозитории сейчас `net8.0` — **ГИПОТЕЗА/ПРОВЕРИТЬ**);
   - разрядность x64;
   - фактические DLL (`mapimgd.dll`, `hostmgd.dll`, `hostdbmgd.dll` — имена из старых примеров, для 26 не подтверждены);
   - способ загрузки (`NETLOAD` / `APPLOAD`).
4. Скопировать `src/NavigatorKit.NanoCad/NanoCadSdkReferences.props.example` в `NanoCadSdkReferences.props` и заменить пути/имена DLL на фактические.

## 3. Проверка окружения PowerShell

Выполнить в корне репозитория:

```powershell
powershell -ExecutionPolicy Bypass -File tools/windows_stand_check.ps1 `
  -NanoCadPath "C:\Program Files\Nanosoft\nanoCAD x64 26" `
  -SdkPath "C:\SDK\nanoCAD26" `
  -LicenseStatus "ACTIVE"
```

Скрипт пишет `delivery/data/windows_stand_check.json`. Он **не устанавливает** nanoCAD и не обходит лицензию.

## 4. Сборка и запуск команд

```powershell
$env:NANOCAD_SDK_PATH = "C:\SDK\nanoCAD26"
Copy-Item src/NavigatorKit.NanoCad/NanoCadSdkReferences.props.example src/NavigatorKit.NanoCad/NanoCadSdkReferences.props
dotnet build src/NavigatorKit.NanoCad/NavigatorKit.NanoCad.csproj -c Release -p:NANOCAD_SDK_PATH=$env:NANOCAD_SDK_PATH
```

Затем в nanoCAD:

1. `NETLOAD` → выбрать собранную DLL `NavigatorKit.NanoCad.dll`.
2. Выполнить команду `NK_HELLO` — ожидается сообщение в командной строке.
3. Выполнить `SDK_PROBE` — сохранить вывод в `delivery/data/sdk_probe.json`.
4. Скопировать реальные имена методов в `docs/api-experiment.md` и снять статус `HYPOTHESIS` только для подтверждённых методов.

## 5. Скриншоты

Нужны три реальных снимка 1600×1200:

| Файл | Сюжет |
|---|---|
| `delivery/screenshots/nanocad_26_main_window.png` | главное окно nanoCAD 26 с открытым чертежом |
| `delivery/screenshots/nanocad_26_toolbar.png` | панель/ лента с загруженным модулем |
| `delivery/screenshots/nanocad_26_api_commands.png` | командная строка с `NK_HELLO` / `SDK_PROBE` |

**Важно:** текущий водяной знак «nanoCAD НЕ запускался / не скриншот CAD» нельзя ставить на реальные снимки. Для реальных снимков используйте правдивый watermark, например `nanoCAD 26 / реальный снимок стенда`, и выставьте `nanoCADScreenshot: true` в `screenshots_manifest.json`. Диагностические PNG из Linux sandbox остаются с прежним предупреждением.

## 6. Что остаётся гипотезой до запуска

- Точный TFM и состав DLL SDK 26.
- `GetSheets()` / `GetSheetSets()` и подписи методов.
- `Database` / `Transaction` / `BlockReference` API для фонового чтения и записи атрибутов штампа.
- Tables API и документированный доступ к SHEETSET/`.dst`.
- Соответствие штатной «ведомости листов» форме 1 ГОСТ Р 21.101-2026.

См. также `docs/windows-vm-build.md` и `delivery/session-3/p0_windows_stand.json`.
