# Подготовка сборки на Windows-VM

Дата: 2026-10-27. Workflow подготовлен, но **не запускался в текущем Linux sandbox**, потому что здесь нет Windows, nanoCAD 26, MultiCAD .NET SDK 26 и лицензии.

## Что уже есть в GitHub Actions

| Workflow | Назначение | Статус |
|---|---|---|
| `.github/workflows/verify.yml` |регенерация fixtures, Python pipeline, second-session artifacts, 12 PNG, unit tests, manifest/ZIP, verification | запускается на `push`, `pull_request`, `workflow_dispatch`; в PR #1 зелёный |
| `.github/workflows/dotnet-build.yml` | ручная сборка переносимых .NET 8 Core/CLI на Ubuntu | подготовлен, требует `workflow_dispatch` |
| `.github/workflows/windows-build.yml` | **новая** ручная сборка C# на `windows-latest`, запуск CLI и условная сборка nanoCAD-адаптера | подготовлен для будущей VM; требует `workflow_dispatch` |

## Как запустить Windows workflow

1. Открыть GitHub → Actions → **Build C# on Windows VM (manual)** → Run workflow.
2. Обычный запуск собирает `src/NavigatorKit.Cli/NavigatorKit.Cli.csproj` и выполняет CLI на 120 синтетических DXF.
3. Для попытки сборки `src/NavigatorKit.NanoCad` нужно:
   - заранее положить SDK 26 на runner (self-hosted runner или шаг, который распаковывает SDK в каталог);
   - задать repository variable `NANOCAD_SDK_PATH` с путём к SDK;
   - включить input `include_nanocad_adapter = true`;
   - workflow скопирует `NanoCadSdkReferences.props.example` в `NanoCadSdkReferences.props` и передаст `-p:NANOCAD_SDK_PATH=...`. Имена DLL в example (`mapimgd.dll`, `hostmgd.dll`, `hostdbmgd.dll`) и точный TFM остаются **ГИПОТЕЗА/ПРОВЕРИТЬ** для SDK 26.
4. Артефакты сборки выгружаются через `actions/upload-artifact@v4`.

> GitHub-hosted `windows-latest` **не содержит** nanoCAD 26 и SDK. Workflow не «устанавливает nanoCAD магически»: он даёт воспроизводимую точку входа, когда появится стенд с SDK и лицензией.

## Что должен сделать человек на стенде

1. Установить nanoCAD 26 и получить действующую лицензию (образовательная лицензия требует nanoPassport и капчу; автономно недоступна).
2. Получить SDK 26 через клуб разработчиков nanoCAD; официальная страница API — <https://www.nanocad.ru/developers/>.
3. Сверить TFM, разрядность, набор DLL и способ загрузки (`NETLOAD`/`APPLOAD`).
4. Запустить `NK_HELLO` и `SdkProbe` из `src/NavigatorKit.NanoCad`, сохранить reflection-дамп в `delivery/data/`.
5. Заменить hypothesis-метки в `docs/api-experiment.md` и `delivery/data/api_experiment_results.json` только после фактической проверки.
6. Прогнать 3 × 40 реальных DWG и повторить rollback/печать уже через проверенный API.

## Честные ограничения

- `dotnet build` portable Core/CLI ещё не выполнялся в этом sandbox: `dotnet`, `mono`, `msbuild`, `csc` отсутствуют.
- `windows-build.yml` статически подготовлен; его YAML-корректность проверена локально, но реальный запуск GitHub Actions находится вне этого сеанса.
- Production DWG, `Database`/`Transaction`, Tables API и `.dst` остаются **ГИПОТЕЗА/ПРОВЕРИТЬ**.
