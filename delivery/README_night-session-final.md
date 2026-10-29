# Финальная Linux-сессия — 2026-10-29

## Что сделано

- Независимый stdlib-аудит: **12 DXF**, **0** отклонений от demo/project-контракта.
  [geometry_audit.md](linux-stand/geometry_audit.md), [JSON](linux-stand/geometry_audit.json).
  Бумага A4 210×297 проверена только как reference; формы 1/2 отсутствуют.
- Нормативная геометрия: **NOT_ASSESSED / ГИПОТЕЗА/ПРОВЕРИТЬ**, не сертификат ГОСТ.
- [Windows-инструкция](../docs/windows-stand-setup.md): лицензия, VS, SDK/TFM,
  portable build/test, настоящие имена NK_HELLO/NK_SDK_PROBE и формат вывода probe.
- [CSharpAdapter](../src/CSharpAdapter/README.md): ParseFile/ParseText, ATTRIB,
  слои, границы первой LWPOLYLINE. 28 xUnit cases (12 общих DXF + 16 сценариев),
  без выдуманных DLL. C# CI: **BUILD_AND_XUNIT_PASS**; доказательство:
  [csharp_ci_validation.json](linux-stand/csharp_ci_validation.json).
  В локальном sandbox dotnet отсутствует, Windows/CAD не запускались.
- [GIF-сценарий](../docs/gif-demo-scenario.md): gate перед съёмкой, тайминг,
  правдивые подписи, корректные palettegen/paletteuse. Реальный GIF ещё не снят.
- Python pytest: **28 PASS**. Delivery checks — отдельный verifier,
  фактические числа в [test_report.json](linux-stand/test_report.json) и verification_results.json.
- Финальный ZIP собирается без вложенных ZIP, чтобы сохранить лимит ≤3 000 000 байт.
  Включены исходники/fixtures/результаты runner; отдельные архивы доступны рядом.

## Пакеты

- [navigator-kit-final-session.zip](navigator-kit-final-session.zip) — пакет этого этапа.
- [navigator-kit-test-runner.zip](navigator-kit-test-runner.zip) — самостоятельный Python runner.
- [README_test_runner.md](../README_test_runner.md) — минимальная установка.

Точный размер каждого архива проверяется сборщиком и указывается в комментарии PR.
Финальный пакет — не установщик плагина и не заявление о готовности к конкурсу.

## Полная воспроизводимая цепочка

```sh
python -m pip install -r requirements.txt
python tools/final_session.py --all
```

Для сборки C#: dotnet test src/CSharpAdapter/Tests/CSharpAdapter.Tests.csproj -c Release.
NuGet restore требует сети. CI использует .NET 8; host-TFM проверяется отдельно.
Детали ограничений: src/CSharpAdapter/README.md. Логи Linux: logs/final-session.log.

# Что сделать до следующего раза — 2026-10-29

1. **P0 — Нормоконтроль:** получить/сверить официальные размеры форм 1/2 и рамки;
   12 демо-DXF не содержат ведомостей, поэтому NOT_ASSESSED не закрыт.
2. **P0 — Windows-стенд:** выполнить docs/windows-stand-setup.md; подтвердить лицензию,
   DLL/TFM, NK_HELLO и NK_SDK_PROBE, сохранить реальные снимки и текстовый dump.
3. **P1 — Реальный адаптер, пилот на реальных DWG:** интегрировать portable C#-контракт с подтверждённым SDK,
   добавить DWG, реальные профили штампов, транзакции/.bak/rollback, layouts и Tables.
4. **P1 — Демо:** пройти gate docs/gif-demo-scenario.md и снять реальное видео/GIF ≤3 MB.
5. **P2 — Сдача:** senior review, проверка конкурсных условий и прав на материалы;
   акты внедрения/подписи/заявку оформляет уполномоченный человек, не генерировать фиктивные.

