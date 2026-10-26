# Зависимости и состояние окружения

Дата проверки: 2026‑10‑26 (UTC).

## Что реально есть в sandbox

| Элемент | Результат |
|---|---|
| ОС | Debian 12, Linux x86_64 |
| Python | 3.11, стандартная библиотека |
| Node.js / npm | установлены |
| Pillow / ezdxf / xmlschema | установлены в `/home/user/.venv` только для генерации/проверки |
| `dotnet`, `mono`, `msbuild`, `csc` | **отсутствуют** |
| Visual Studio 2022 / Rider | **отсутствуют** |
| nanoCAD 26 | **отсутствует** |
| MultiCAD .NET SDK 26, `mapimgd.dll`, `hostmgd.dll`, `hostdbmgd.dll` | **отсутствуют** |
| Лицензия nanoCAD | не обнаружена |
| `briefing.md` | исходный отсутствует |
| Реальные DWG (3 × 40) | отсутствуют; созданы синтетические DXF |

`lk.nanocad.ru/education/request` перенаправляет на nanoPassport и требует авторизации/капчу. Автономно получить образовательную лицензию невозможно; это задача человека.

## Что нужно на Windows‑стенде

1. nanoCAD 26 (демо/образовательная/разработчика) и действующая лицензия.
2. Клуб разработчиков nanoCAD + SDK 26: официальная страница API — <https://www.nanocad.ru/developers/>.
3. Visual Studio 2022 с C# и workload под targeting pack, который требует SDK 26.
4. Реальные шаблоны СПДС и 3 × 40 DWG с известными именами блоков/тегов атрибутов.
5. Проверить через SDK: точный `TargetFramework`, разрядность, DLL, способ загрузки, read‑only opening, транзакции, доступ к layouts, API комплектов документации.
6. Официальные тексты действующих ГОСТ и требования конкурса к редакции стандарта.

## NuGet / Python

- C# Core и CLI: **нет внешних NuGet‑пакетов** (только BCL).
- Python CLI: только стандартная библиотека.
- Инструменты: `ezdxf==1.4.5`, `Pillow==11.3.0`, `xmlschema==4.1.0` (см. `requirements.txt`).
- Тесты C# (xUnit/NUnit) не добавлены, так как сборка в sandbox невозможна.

## Артефакт проверки

Машиночитаемая среда: `delivery/data/environment.json`. Матрица доверия: `delivery/data/verification_results.json`.
