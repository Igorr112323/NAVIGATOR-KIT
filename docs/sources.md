# Источники и доверие

Проверено 2026‑10‑26; повторно сверено с официальным реестром Росстандарта **2026‑10‑27**; в третьей сессии **2026‑10‑28** дополнительно сверены официальное издание PDF, Приложение Б и раздел 7. Ссылки не означают, что API запускалось в nanoCAD.

| Тема | Источник | Что подтверждает | Уровень |
|---|---|---|---|
| Актуальность СПДС | <https://protect.gost.ru/gost/details/17bc12e8-6579-4145-b141-56855e772e7f> | ГОСТ Р 21.101‑2026 действует с 01.04.2026, приказ 129-ст от 12.02.2026, заменяет 21.101-2020 | официальный реестр Росстандарта |
| Официальное издание 2026 | <https://pravdaosro.ru/wp-content/uploads/2026/03/GOST-R-21.101-2026.pdf> | титул «Издание официальное», «ВЗАМЕН ГОСТ Р 21.101—2020», Приложение Б (обязательное), раздел 7 | официальный PDF, первые 30 страниц доступны через web-tool |
| Раздел 7 / форма 10 | `docs/official-text-extract.md` | изменения обозначаются порядковыми номерами; разрешение; новая версия ДЭ; таблица регистрации изменений форма 10 | выписка из официального PDF + ГАРАНТ |
| Заменённый СПДС | <https://protect.gost.ru/gost/details/ba2db0a2-01aa-45da-a9dd-e5525bd69ec3> | ГОСТ Р 21.101-2020 имеет «Обозначение заменяющего — ГОСТ Р 21.101-2026» | официальный реестр Росстандарта |
| Форма 1/2 | <https://base.garant.ru/413848474/f7ee959fd36b5699076b35abf4f52c5c/> | Приложение Б ГОСТ Р 21.101‑2026, обязательный состав граф | правовая база |
| Актуальные изменения | <https://protect.gost.ru/document.aspx?control=7&id=256448> | ГОСТ Р 2.503‑2023 действует с 01.03.2024, приказ 1374-ст | официальный реестр Росстандарта |
| Устаревшие изменения | <https://protect.gost.ru/gost/details/03d72f0a-a11e-436f-ba81-41f9333ccc39> | ГОСТ 2.503‑2013 «Утратил силу в РФ», использовать ГОСТ Р 2.503-2023 | официальный реестр Росстандарта |
| Текст 5.12 ГОСТ Р 2.503-2023 | <https://meganorm.ru/mega_doc/norm/gost-r_gosudarstvennyj-standart/0/gost_r_2_503-2023_natsionalnyy_standart_rossiyskoy.html> | графы «Изм.», «Лист», «№ докум.», «Подп.», «Дата»; маркеры «Зам.», «Нов.», «Все», прочерк | неофициальная публикация текста |
| Форматы | <https://www.spds.ru/info/standarts/2.301-68.html> | основные/производные форматы | справочник, сверить с официальным изданием |
| API nanoCAD | <https://www.nanocad.ru/developers/> | C#/.NET, MultiCAD .NET, ActiveX, LISP; клуб разработчиков для SDK | официальный, общий |
| nanoCAD 26 | <https://download.nanodev.ru/products/nanocad_platform/26.0/Instructions/Whats_new_platforma_26.pdf> | изменения комплекта документации, порядок листов соответствует вкладкам, пакетная обработка | официальный PDF |
| Комплект документации | <https://online-help.platform.nanodev.ru/NC21_Help/html/IDT_SheetSets.htm?rhtocid=_19> | данные комплекта хранятся в `.dst`; листы/виды физически не перемещаются | официальная справка NC21 |
| Sheet list table | <https://pt.nanocad.com/learning/online-help/nanocad-platform/actions-on-sheet-set-and-its-elements/> | «Insert Sheet List Table», настройка столбцов; старая ссылка на ГОСТ Р 21.1101‑2013 | официальная справка, версия требует проверки |
| Извлечение данных | <https://forum.nanocad.ru/t/izvlechenie-dannyh-iz-neskolkih-fajlov/841> | в 2025 году отвечают «Из коробки нет» для чистой платформы, но API позволяет свой обход | форум, не спецификация |
| `GetSheets()` | <https://forum.nanocad.ru/index.php?/topic/6426-kak-vstavit-blok-iz-drugogo-dokumenta-ispolzuya-multicad/> | исторический пример MultiCAD.NET 2015 с `refDoc.GetSheets()` | форум, версия 26 **не проверена** |
| `GetSheetSets()` | поиск по официальным ресурсам/forum.nanocad.ru | публичного подтверждения не найдено | **ГИПОТЕЗА/ПРОВЕРИТЬ** |
| Hello World / DLL | <https://developer.nanocad.com/blog/2014/10/14/multicad-enabler-for-autocad-and-zwcad/> | NETLOAD/APPLOAD для MultiCAD.NET сборок | официальный блог, старая версия |
| .NET host DLL | <https://developer.nanocad.com/blog/page/2/> | `hostmgd.dll`, `hostdbmgd.dll`, `CommandMethod` в классическом .NET API | официальный блог, старая версия |
| Образовательная лицензия | <https://lk.nanocad.ru/education/request> | требует nanoPassport/авторизацию/капчу | официальный портал |

Все утверждения в коде, зависящие от SDK 26, сопровождаются меткой **ГИПОТЕЗА/ПРОВЕРИТЬ** и не используются в фактически выполненном Python‑pipeline.
