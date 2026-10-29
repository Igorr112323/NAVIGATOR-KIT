# Windows-стенд «Комплект-Навигатор»

Обновлено 2026-10-29 в Linux. Это инструкция, НЕ отчёт об установке.
Windows/nanoCAD/лицензия/SDK здесь отсутствуют. Указанные ниже шаги требуют
проверки по текущему установщику и документации поставщика.

## 1. Лицензия и nanoCAD 26

1. Открыть официальный сайт nanoCAD и личный кабинет. Для образования исходная
   ссылка: <https://lk.nanocad.ru/education/request> (доступность/условия в этой
   сессии не проверены). Указать реальные данные организации/учебного заведения.
2. Дождаться решения поставщика; срок 1–2 дня и право на бесплатную лицензию
   не гарантируются. Секреты/ключи в Git и отчёты НЕ помещать.
3. Скачать nanoCAD 26 из официального кабинета; установить по инструкции Nanosoft.
   Повышение прав — только если требует установщик. Путь установки не фиксирован.
4. Активировать законную лицензию (или официальный пробный режим, если доступен).
   Зафиксировать версию/build и разрядность из окна «О программе» без ключа лицензии.

## 2. Visual Studio / SDK / TFM

1. Установить Visual Studio 2022 Community, если подходит лицензия Microsoft,
   с нагрузкой «Разработка классических приложений .NET» и .NET 8 SDK для
   **portable parser**. На Windows: `dotnet --info`.
2. Через <https://www.nanocad.ru/developers/> получить официальный MultiCAD .NET SDK
   для nanoCAD 26. Условия доступа/регистрация определяются поставщиком.
3. Папка примера `C:\SDK\MultiCAD26` — не обязательный путь. Сохранить список
   DLL, версии сборок и документацию. **ГИПОТЕЗА/ПРОВЕРИТЬ:** реальные DLL, TFM,
   разрядность и загрузчик host-плагина. .NET 8 portable-парсера НЕ доказывает TFM SDK.
4. Не создавать ссылку на выдуманную `MultiCAD26.dll`. Исторические mapimgd/hostmgd/
   hostdbmgd в props.example — только гипотезы; сверить с SDK 26.

## 3. Сначала portable C# (CAD не нужен)

Из корня репозитория в PowerShell:
```powershell
dotnet build src/CSharpAdapter/CSharpAdapter.csproj -c Release
dotnet test src/CSharpAdapter/Tests/CSharpAdapter.Tests.csproj -c Release --logger trx
dotnet run --project src/CSharpAdapter -- delivery/linux-stand/samples/stamp_01.dxf
```
Ожидается 28 xUnit cases; сохранить фактические логи. NuGet restore требует сети.
Этот EXE не загружается в nanoCAD как плагин.

## 4. Готовность реального host-стенда

```powershell
powershell -ExecutionPolicy Bypass -File tools/windows_stand_check.ps1 `
  -NanoCadPath "C:\фактический-путь-nanoCAD" `
  -SdkPath "C:\SDK\MultiCAD26" -LicenseStatus "ACTIVE"
```
`ACTIVE` здесь — заявление оператора, не автоматическая проверка лицензии.
Не использовать эту строку как доказательство активации. Скрипт только инвентаризирует.

После проверки имён/TFM: адаптировать
`src/NavigatorKit.NanoCad/NanoCadSdkReferences.props.example`, сохранить рядом как
`NanoCadSdkReferences.props`, сверить условие `NANOCAD_SDK` в проекте, затем:
```powershell
$env:NANOCAD_SDK_PATH = "C:\SDK\MultiCAD26"
dotnet build src/NavigatorKit.NanoCad/NavigatorKit.NanoCad.csproj -c Release -p:NANOCAD_SDK_PATH=$env:NANOCAD_SDK_PATH
```
Это шаблон, не гарантия сборки с SDK26. Способ загрузки DLL взять из SDK, не угадывать
NETLOAD/APPLOAD. В исходнике условно объявлены команды `NK_HELLO` и **`NK_SDK_PROBE`**,
не `SdkProbe`, не `SDK_PROBE`, не `_-NKHELLO`. Они существуют в nanoCAD только после
проверки атрибута регистрации и загрузки совместимой DLL. NK_HELLO пишет сообщение,
не диаграмму. NK_SDK_PROBE пишет текстовый reflection dump в temp
`navigator-kit-sdk-probe.txt`, **не JSON** и не специальное меню nanoCAD.

## 5. Доказательства и критерии приёмки

- [ ] Лицензия и nanoCAD build проверены оператором без публикации секретов.
- [ ] Сохранён dotnet --info; portable parser собран, xUnit фактически прошёл.
- [ ] Реальные SDK DLL/TFM/методы записаны; наличие числа 26 в версии не единственный критерий.
- [ ] NK_HELLO и NK_SDK_PROBE зарегистрированы/выполнены в nanoCAD; сохранён вывод.
- [ ] Сняты главное окно, загруженный модуль и результаты команд; по возможности 1600×1200,
      оригиналы сохраняются без изменения масштаба для доказательств.
- [ ] Имена: nanocad_26_main_window.png, nanocad_26_toolbar.png, nanocad_26_api_commands.png.

Реальный снимок помечать `nanoCAD 26 / реальный снимок стенда`, а не «nanoCAD НЕ
запускался». В манифесте `nanoCADScreenshot: true` только после проверки происхождения.
Локальные Linux PNG сохраняют прежнее предупреждение. В Git не публиковать ключи,
персональные данные и закрытые SDK DLL без разрешения.

Гипотезы GetSheets/GetSheetSets, Tables, .dst, Database/Transaction остаются открыты.
См. `docs/api-experiment.md`, `src/CSharpAdapter/README.md`, `docs/gif-demo-scenario.md`.
