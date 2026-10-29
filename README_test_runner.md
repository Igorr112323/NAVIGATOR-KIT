# Navigator-Kit Test Runner

Пакет повторяемых проверок, **не плагин nanoCAD**. CAD/.NET/Windows не требуются.
Проверенная среда: Linux, Python 3.11. Windows/macOS пока не проверены запуском.

## Как запустить

1. Установите Python 3.11 и распакуйте архив (или клонируйте репозиторий).
2. Откройте терминал в корне пакета, рядом с этим README.
3. Создайте venv: `python -m venv .venv`.
4. Активируйте его: Linux/macOS — `source .venv/bin/activate`;
   Windows PowerShell — `.venv\Scripts\Activate.ps1`.
5. Установите зависимости: `python -m pip install -r requirements-test-runner.txt`.
6. Выполните `python -m pytest tests/ -v --tb=short`.

`delivery/linux-stand/test_report.json` обновляется автоматически (pytest conftest).
Ненулевой exit code означает ошибку; исходные логи поставки не заменяют новый запуск.
Сбор тестов: `python -m pytest tests/ --collect-only -q`.
Без сторонних библиотек: `python tools/check_test_runner_data.py` (не полный pytest).
Для полной регенерации артефактов установите requirements.txt и следуйте
`delivery/linux-stand/README.md`. 59 delivery checks выполняются отдельно от pytest.
Архив не содержит вложенных ZIP и среды Python; установка пакетов требует интернета
или заранее подготовленного wheelhouse.

## Состав и ограничения

12 демонстрационных DXF: `delivery/linux-stand/samples/`;
12 соответствующих PNG: `delivery/screenshots/linux_stamp_*.png`.
Также включены 120 synthetic DXF, необходимые 17 прежним тестам, XML, исходники,
сохранённые данные и отчёты. В пакете есть и прежние 15 диагностических PNG —
они не выдаются за CAD-рендеры и не являются скриншотами nanoCAD.
Независимый парсер поддерживает подготовленные ASCII-DXF без вложенных блоков
и трансформаций; поля DESIGNATION/SHEET/TITLE/FORMAT, марка отдельно не выделена.
Геометрия демонстрационная, не подтверждена по ГОСТ. MultiCAD backend не реализован.
