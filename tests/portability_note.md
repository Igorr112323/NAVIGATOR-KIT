# Portability / границы проверки

Полный pytest-набор использует Python 3.11, pytest, ezdxf, Pillow, matplotlib.
Установка: `python -m pip install -r requirements-test-runner.txt`.
Остальные зависимости requirements.txt нужны для полной регенерации delivery,
а не для запуска 28 тестов по уже подготовленным данным.

nanoCAD, SDK, .NET, Windows, DISPLAY, ffmpeg и CAD-программы не требуются.
Рендер использует Agg, шрифт DejaVuSans берётся из установленного matplotlib,
а не из системной папки. Пути к данным вычисляются от файлов исходников.
Запускать из корня распакованного архива; пути с кириллицей требуют UTF-8.
Windows/macOS в этой сессии НЕ запускались: переносимость обеспечена конструкцией,
но фраза «проверено на любой ОС / любой Python >=3.11» была бы недостоверной.
Python 3.11 на Linux — проверенная среда; другие версии требуют совместимых wheels.

Базовые проверки JSON/XML/SHA-256 и независимый читатель реализованы на stdlib.
Пример без pytest/ezdxf: `python tools/check_test_runner_data.py`.
Полный pytest без установки зависимостей не обещается: import errors не скрываются skips.
28 тестов включают 17 регрессионных тестов с 120 synthetic DXF и 11 тестов Linux-стенда.
Поэтому пакет содержит и 120 исходных фикстур, а не только 12 новых образцов.

`python -m pytest tests/ -v` автоматически обновляет test_report.json через conftest.
59 delivery checks — отдельная проверка tools/verify_delivery.py; pytest не выдаёт
их за свои asserts. Значения checks_* в отчёте ссылаются на последний snapshot.
Для полной повторной регенерации используйте README Linux-стенда и requirements.txt.
