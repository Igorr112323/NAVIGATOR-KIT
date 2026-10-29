# Геометрический аудит 12 демонстрационных DXF

Версия скрипта 1.0. Чтение group codes без ezdxf. Это НЕ заключение о соответствии ГОСТ.
ГОСТ Р 21.101-2026, Приложение Б: образцы не содержат таблиц форм 1/2 — NOT_ASSESSED.
ГОСТ 2.301-68: сверена только внешняя тестовая прямоугольная граница с reference-размерами бумаги A0–A4. Официальный текст повторно не получен.

| Файл | Лист (файл) | Лист (ГОСТ) | Формат (файл) | Формат (reference) | Марка | Слои | Примечание |
|---|---|---|---|---|---|---|---|
| stamp_01.dxf | 1 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |
| stamp_02.dxf | 2 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |
| stamp_03.dxf | 3 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |
| stamp_04.dxf | 4 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |
| stamp_05.dxf | 5 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |
| stamp_06.dxf | 6 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |
| stamp_07.dxf | 7 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |
| stamp_08.dxf | 8 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |
| stamp_09.dxf | 9 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |
| stamp_10.dxf | 10 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |
| stamp_11.dxf | 11 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |
| stamp_12.dxf | 12 | не предписывает конкретный номер | A4 | A4: 210×297 mm | отсутствует | FRAME, NOTES, STAMP | DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED |

## Расхождения и непроверенное
- Отклонений от demo/project-контракта: 0.
- Во всех 12 файлах отсутствует отдельный MARK. Это ограничение данных, не доказанное нарушение ГОСТ.
- Формы 1/2 отсутствуют: нельзя доказать их геометрию по штампу и рамке.
- Имена слоёв и номер листа не предписываются приведённой reference-таблицей ГОСТ.

## Примечания
- GROUP 9 не номер листа; GROUP 70 не универсальный формат. Номер и формат — ATTRIB с tag 2 и значением 1.
- Вложенные блоки, поворот/масштаб INSERT, DWG, расположение полей штампа и margins не проверяются.
- Windows: python tools/geometry_audit.py --self-test. Затем открыть DXF в nanoCAD, проверить units, масштабы, рамку и реальные формы по официальному изданию.
- ГИПОТЕЗА/ПРОВЕРИТЬ: нормативная геометрия остаётся открытой; визуальная проверка сама по себе не заменяет сверку размеров по ГОСТ.
