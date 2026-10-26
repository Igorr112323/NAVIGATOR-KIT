# Интеграция с nanoCAD 26: что известно и что проверять

## Проверено по открытым источникам

1. MultiCAD .NET и классический .NET API существуют; C# — поддерживаемый язык. SDK распространяется через клуб разработчиков. [Официальная страница API](https://www.nanocad.ru/developers/).
2. MultiCAD.NET сборкиhistorically загружаются командами `NETLOAD`/`APPLOAD`. [Официальный блог](https://developer.nanocad.com/blog/2014/10/14/multicad-enabler-for-autocad-and-zwcad/). **ГИПОТЕЗА/ПРОВЕРИТЬ:** одинаков ли путь загрузки в nanoCAD 26.
3. Классический .NET API historically требует `hostmgd.dll`, `hostdbmgd.dll`; MultiCAD .NET — `mapimgd.dll` и companion DLL. [Официальный блог](https://developer.nanocad.com/blog/page/2/) и [примеры сообщества](https://forum.dwg.ru/showthread.php?t=170802). **ГИПОТЕЗА/ПРОВЕРИТЬ:** точные имена, TFM, разрядность и зависимости SDK 26.
4. Комплект документации хранит состав в `.dst`; inclusion листа не перемещает чертёж. [Справка NC21](https://online-help.platform.nanodev.ru/NC21_Help/html/IDT_SheetSets.htm?rhtocid=_19).
5. В nanoCAD 26 порядок листов в комплекте отображается аналогично порядку вкладок листов исходного файла. [What’s new 26](https://download.nanodev.ru/products/nanocad_platform/26.0/Instructions/Whats_new_platforma_26.pdf). Это означает, что `print_order.json` нужно сверять с порядком layouts, а не «взломать» `.dst`.
6. Штатная команда вставки «ведомости листов» документирована, но старая справка ссылается на ГОСТ Р 21.1101‑2013. [Help](https://pt.nanocad.com/learning/online-help/nanocad-platform/actions-on-sheet-set-and-its-elements/). **ГИПОТЕЗА/ПРОВЕРИТЬ:** соответствует ли шаблон 2026 году.
7. Извлечение атрибутов из нескольких файлов «из коробки» в чистой платформе недоступно по сообщению на форуме 2025 года; предлагается собственный код через API. [Forum](https://forum.nanocad.ru/t/izvlechenie-dannyh-iz-neskolkih-fajlov/841).

## `GetSheets()` и `GetSheetSets()`

- `GetSheets()` встречается в публичном примере MultiCAD.NET 2015 года как метод `McDocument`: [forum.nanocad.ru](https://forum.nanocad.ru/index.php?/topic/6426-kak-vstavit-blok-iz-drugogo-dokumenta-ispolzuya-multicad/). Это **историческая** улика, а не гарантия API 26.
- `GetSheetSets()` в открытой документации и поиске по forum.nanocad.ru не подтверждён. Не используйте имя метода в коде до проверки reflection или SDK CHM.

## Практический probe

`src/NavigatorKit.NanoCad/SdkProbe.cs` не зависит от конкретных типов SDK. После загрузки плагина вызовите `SdkProbe.Run(@"C:\temp\nk-sdk-probe.txt")`; он перечислит все загруженные сборки, публичные типы и методы, содержащие `Sheet`, `Layout`, `Attribute`, `Block`, `Database`. Это позволит подтвердить реальные сигнатуры без догадок.

## План адаптера (не выполнено)

1. `NanoCadSdkReferences.props.example` → локальный `NanoCadSdkReferences.props` с реальными путями DLL.
2. `dotnet build` с проверенным TFM; переменная `NANOCAD_SDK_PATH` включает `NANOCAD_SDK`.
3. `NETLOAD` → `NK_HELLO`; сохранить настоящий скриншот окна nanoCAD.
4. Открыть DWG read‑only/background, прочитать layouts и атрибуты block reference в транзакции.
5. Сверить field mapping с `delivery/xml/stamp_mapping.xml`.
6. Сгенерировать таблицу средствами проверенного Tables API либо вставить CSV как промежуточную демонстрацию.
7. Записать изменённые атрибуты в копии DWG, сделать `.bak`, проверить rollback.
8. Синхронизировать порядок layouts и `.dst` через документированный API/UI; не редактировать `.dst` как текст.

Каждый пункт 3–8 остаётся **ГИПОТЕЗА/ПРОВЕРИТЬ** до запуска в nanoCAD 26.
