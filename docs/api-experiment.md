# Эксперимент: штатное получение ведомости ф.1

**Статус:** документарный эксперимент. nanoCAD 26 не запускался: в sandbox нет Windows, лицензии и SDK. Настоящих скриншотов нет; приложены подписанные диагностические макеты.

## Проверенные гипотезы

| № | Способ | Источник | Результат |
|---|---|---|---|
| A1 | Панель `SHEETSET` / «Комплект документации» | [справка NC21](https://online-help.platform.nanodev.ru/NC21_Help/html/IDT_SheetSets.htm?rhtocid=_19) | Подтверждено существование `.dst` и набора листов; ф.1 2026 не подтверждена. |
| A2 | «Insert Sheet List Table» / «Вставить ведомость листов» | [nanoCAD help](https://pt.nanocad.com/learning/online-help/nanocad-platform/actions-on-sheet-set-and-its-elements/) | Штатная таблица с настраиваемыми столбцами существует; в старой справке указан ГОСТ Р 21.1101‑2013. Соответствие форме 1 ГОСТ Р 21.101‑2026 — **ГИПОТЕЗА/ПРОВЕРИТЬ**. |
| A3 | Извлечение данных из атрибутов нескольких DWG «из коробки» | [forum 2025](https://forum.nanocad.ru/t/izvlechenie-dannyh-iz-neskolkih-fajlov/841) | Ответ «Из коробки нет»; рекомендован собственный API‑код. |
| A4 | `GetSheets()` | [forum 2015](https://forum.nanocad.ru/index.php?/topic/6426-kak-vstavit-blok-iz-drugogo-dokumenta-ispolzuya-multicad/) | Метод встречается в старом примере MultiCAD.NET; в SDK 26 не проверен. |
| A5 | `GetSheetSets()` | поиск официальных страниц и forum.nanocad.ru | Публичного подтверждения не найдено. Не использовать без SDK reflection. |
| A6 | Прямая правка `.dst` | [справка](https://online-help.platform.nanodev.ru/NC21_Help/html/IDT_SheetSets.htm?rhtocid=_19), [What’s new 26](https://download.nanodev.ru/products/nanocad_platform/26.0/Instructions/Whats_new_platforma_26.pdf) | Не реализовано: формат `.dst` не документирован как открытый; в 26 порядок листов связан с вкладками layouts. |
| A7 | Batch printing order | [What’s new 26](https://download.nanodev.ru/products/nanocad_platform/26.0/Instructions/Whats_new_platforma_26.pdf) | Подготовлен нейтральный `print_order.json`; прямая генерация задания печати — **ГИПОТЕЗА/ПРОВЕРИТЬ**. |

## Вывод

Штатная таблица листов — самый короткий путь к демо, но она не заменяет чтение штампов и не гарантирует форму 1 по действующему ГОСТ Р 21.101‑2026. Надёжная архитектура: независимый реестр из штампов → генерация данных формы 1 → вставка через проверенный Tables API или экспорт в штатную таблицу → ручная/API‑синхронизация `.dst`.

## Что сделать на Windows‑стенде

1. Запустить `NK_HELLO` и `SdkProbe`, сохранить настоящие скриншоты.
2. Открыть реальный `.dst`, вызвать «Вставить ведомость листов», сравнить заголовки и ширины с приложением Б 2026.
3. Сделать reflection‑дамп всех методов с `Sheet`/`Layout`/`Attribute` и положить в `delivery/data/sdk_probe.txt`.
4. Только после этого заменить заглушки в `src/NavigatorKit.NanoCad`.

## Сессия 3 — SHEETSET/Tables probe

`tools/sheetset_probe.py` не вызывает CAD API, но проверяет готовность данных:

- читает статусы `GetSheets()` и `GetSheetSets()` из `api_experiment_results.json`;
- подтверждает совпадение `print_order.json` и формы 1 по хэшу;
- перегенерирует `wo1_template.csv` / `wo2_template.csv` по Приложению Б-2026;
- явно пишет `dstTouched: false`, `tablesApiVerified: false`, `getSheetSetsStatus: HYPOTHESIS`.

C#-класс `src/NavigatorKit.NanoCad/DwgReadiness.cs` перечисляет проверки `Database`/`Transaction`/`AttributeReference` без выдуманных сигнатур. Решение о снятии гипотез принимается только после `SDK_PROBE` на Windows-стенде.
