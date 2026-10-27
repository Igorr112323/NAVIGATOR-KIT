# Зависимости и состояние окружения

Дата первой проверки: 2026‑10‑26. Повторная проверка: **2026‑10‑27** (вторая ночная сессия).

## Что реально есть в sandbox

| Элемент | Результат |
|---|---|
| ОС | Debian 12, Linux x86_64 |
| Python | 3.11.2, стандартная библиотека |
| Node.js / npm | установлены |
| Python tooling | `/home/user/.venv`: `ezdxf`, `Pillow`, `xmlschema`, `tree_sitter`, `python-docx`, `lxml`, `pandas`, `matplotlib` |
| `dotnet`, `mono`, `msbuild`, `csc` | **отсутствуют** |
| Visual Studio 2022 / Rider | **отсутствуют** |
| nanoCAD 26 | **отсутствует** |
| MultiCAD .NET SDK 26, `mapimgd.dll`, `hostmgd.dll`, `hostdbmgd.dll` | **отсутствуют** |
| Лицензия nanoCAD | не обнаружена |
| `briefing.md` | исходный отсутствует; в репозитории reconstruction |
| Реальные DWG (3 × 40) | отсутствуют; созданы синтетические DXF |

`lk.nanocad.ru/education/request` перенаправляет на nanoPassport и требует авторизации/капчу. Автономно получить образовательную лицензию невозможно; это задача человека.

## Python 3.11: воспроизводимый набор

`requirements.txt` зафиксирован и содержит:

- `ezdxf==1.4.5` — генерация 120 DXF R2010;
- `Pillow==11.3.0` — 12 PNG 1600×1200;
- `xmlschema==4.1.0` — XSD-валидация;
- `tree_sitter==0.25.2`, `tree_sitter_c_sharp==0.23.5` — синтаксический разбор C# без `dotnet`;
- `python-docx==1.2.0` — `wo1_template.docx`;
- `lxml==6.1.3`, `pandas==3.1.0`, `matplotlib==3.11.2` — XML/аналитика и график инцидентов.

`requirements-analysis.txt` дублирует аналитическую часть для будущей Windows-VM. Ядро `tools/navigator_kit.py` по-прежнему работает на стандартной библиотеке.

## GitHub Actions

- `.github/workflows/verify.yml` — regeneration, Python pipeline, second-session artifacts, screenshots, unit tests, manifest/ZIP, verification.
- `.github/workflows/dotnet-build.yml` — ручная сборка portable .NET 8 Core/CLI.
- `.github/workflows/windows-build.yml` — **подготовленная** ручная сборка на `windows-latest`; условно собирает nanoCAD-адаптер при наличии `NANOCAD_SDK_PATH`. См. `docs/windows-vm-build.md`.

## Что нужно на Windows‑стенде

1. nanoCAD 26 (демо/образовательная/разработчика) и действующая лицензия.
2. Клуб разработчиков nanoCAD + SDK 26: официальная страница API — <https://www.nanocad.ru/developers/>.
3. Visual Studio 2022 с C# и workload под targeting pack, который требует SDK 26.
4. Реальные шаблоны СПДС и 3 × 40 DWG с известными именами блоков/тегов атрибутов.
5. Проверить через SDK: точный `TargetFramework`, разрядность, DLL, способ загрузки, read-only opening, транзакции, доступ к layouts, API комплектов документации.
6. Официальные тексты действующих ГОСТ и требования конкурса к редакции стандарта.

## NuGet / Python

- C# Core и CLI: **нет внешних NuGet‑пакетов** (только BCL).
- Python CLI: только стандартная библиотека.
- Тесты C# (xUnit/NUnit) не добавлены, так как сборка в sandbox невозможна.

## Артефакт проверки

Машиночитаемая среда: `delivery/data/environment.json`. Матрица доверия: `delivery/data/verification_results.json`. Локальный контур не запускал nanoCAD; Windows-VM workflow подготовлен, но не выполнялся в этом sandbox.
