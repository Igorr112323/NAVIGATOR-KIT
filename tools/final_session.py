#!/usr/bin/env python3
"""Final-session preparation/packaging; --all repeats the full Linux chain."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'delivery'

def prepare():
    audit = json.loads((D/'linux-stand/geometry_audit.json').read_text(encoding='utf-8'))
    tests = json.loads((D/'linux-stand/test_report.json').read_text(encoding='utf-8'))
    ci_path = D/'linux-stand/csharp_ci_validation.json'
    ci = json.loads(ci_path.read_text(encoding='utf-8')) if ci_path.exists() else {'status':'NOT_VERIFIED', 'detail':'No local dotnet; consult GitHub Actions'}
    summary = {'date':'2026-10-29', 'pythonTests':tests['tests_passed'],
               'geometryFiles':len(audit['files']), 'demoMismatches':audit['demoMismatchCount'],
               'normativeGeometry':'NOT_ASSESSED', 'csharp':ci, 'nanoCADExecuted':False,
               'nestedArchives':'Excluded to avoid recursive bundles; source/data of test runner included'}
    (D/'linux-stand/final_session_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    next_steps='''# Что сделать до следующего раза — 2026-10-29

1. **P0 — Нормоконтроль:** получить/сверить официальные размеры форм 1/2 и рамки;
   12 демо-DXF не содержат ведомостей, поэтому NOT_ASSESSED не закрыт.
2. **P0 — Windows-стенд:** выполнить docs/windows-stand-setup.md; подтвердить лицензию,
   DLL/TFM, NK_HELLO и NK_SDK_PROBE, сохранить реальные снимки и текстовый dump.
3. **P1 — Реальный адаптер, пилот на реальных DWG:** интегрировать portable C#-контракт с подтверждённым SDK,
   добавить DWG, реальные профили штампов, транзакции/.bak/rollback, layouts и Tables.
4. **P1 — Демо:** пройти gate docs/gif-demo-scenario.md и снять реальное видео/GIF ≤3 MB.
5. **P2 — Сдача:** senior review, проверка конкурсных условий и прав на материалы;
   акты внедрения/подписи/заявку оформляет уполномоченный человек, не генерировать фиктивные.
'''
    (D/'next_steps.md').write_text(next_steps,encoding='utf-8')
    report=f'''# Финальная Linux-сессия — 2026-10-29

## Что сделано

- Независимый stdlib-аудит: **{len(audit['files'])} DXF**, **{audit['demoMismatchCount']}** отклонений от demo/project-контракта.
  [geometry_audit.md](linux-stand/geometry_audit.md), [JSON](linux-stand/geometry_audit.json).
  Бумага A4 210×297 проверена только как reference; формы 1/2 отсутствуют.
- Нормативная геометрия: **NOT_ASSESSED / ГИПОТЕЗА/ПРОВЕРИТЬ**, не сертификат ГОСТ.
- [Windows-инструкция](../docs/windows-stand-setup.md): лицензия, VS, SDK/TFM,
  portable build/test, настоящие имена NK_HELLO/NK_SDK_PROBE и формат вывода probe.
- [CSharpAdapter](../src/CSharpAdapter/README.md): ParseFile/ParseText, ATTRIB,
  слои, границы первой LWPOLYLINE. 28 xUnit cases (12 общих DXF + 16 сценариев),
  без выдуманных DLL. C# CI: **{ci.get('status')}**; доказательство:
  [csharp_ci_validation.json](linux-stand/csharp_ci_validation.json).
  В локальном sandbox dotnet отсутствует, Windows/CAD не запускались.
- [GIF-сценарий](../docs/gif-demo-scenario.md): gate перед съёмкой, тайминг,
  правдивые подписи, корректные palettegen/paletteuse. Реальный GIF ещё не снят.
- Python pytest: **{tests['tests_passed']} PASS**. Delivery checks — отдельный verifier,
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

{next_steps}
'''
    (D/'README_night-session-final.md').write_text(report,encoding='utf-8')

def package():
    bundle=D/'navigator-kit-final-session.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for folder in ('delivery','docs','src','tools','tests','samples','linux_stand','logs','.github/workflows'):
            for p in sorted((ROOT/folder).rglob('*')):
                if p.is_file() and p.suffix not in ('.zip','.pyc') and not {'__pycache__','bin','obj'}.intersection(p.parts):
                    z.write(p,p.relative_to(ROOT))
        for name in ('README.md','README_test_runner.md','requirements.txt','requirements-test-runner.txt','requirements-analysis.txt','briefing.md','night-log.md','.gitignore'):
            z.write(ROOT/name,name)
        z.write(D/'README_night-session.md','README_night-session.md')
    if bundle.stat().st_size > 3_000_000:raise RuntimeError(f'ZIP exceeds 3MB: {bundle.stat().st_size}')
    with zipfile.ZipFile(bundle) as z:
        assert z.testzip() is None
        assert 'src/CSharpAdapter/Tests/DxfParserTests.cs' in z.namelist()
        assert not any(n.endswith('.zip') for n in z.namelist())
    print(f'Final-session ZIP PASS: {bundle.stat().st_size} bytes; no nested ZIPs')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--all',action='store_true');ap.add_argument('--prepare',action='store_true');ap.add_argument('--package',action='store_true');args=ap.parse_args()
    if args.all:
        commands=[['tools/generate_fixtures.py'],['tools/navigator_kit.py','all'],['tools/night_session_2.py'],['tools/session3_runner.py'],['tools/render_screenshots.py'],['tools/run_linux_stand.py'],['tools/complete_linux_stand.py'],['tools/geometry_audit.py','--self-test'],['-m','pytest','tests/','--collect-only','-q'],['-m','pytest','tests/','-v','--tb=short']]
        logdir=ROOT/'logs';logdir.mkdir(exist_ok=True)
        with (logdir/'final-session.log').open('w',encoding='utf-8') as log:
            for command in commands:
                run=subprocess.run([sys.executable,*command],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                log.write(f'$ python {" ".join(command)}\n{run.stdout}\nexit={run.returncode}\n');log.flush()
                if command[:4]==['-m','pytest','tests/','--collect-only']:(D/'linux-stand/collect_log.txt').write_text(run.stdout,encoding='utf-8')
                elif command[:3]==['-m','pytest','tests/']:(D/'linux-stand/pytest_output.log').write_text(run.stdout,encoding='utf-8')
                if run.returncode:raise SystemExit(run.returncode)
        prepare()
        for command in ('tools/finalize_delivery.py','tools/finalize_linux_stand.py','tools/build_test_runner.py'):
            subprocess.run([sys.executable,command],cwd=ROOT,check=True)
        package()
        subprocess.run([sys.executable,'tools/verify_delivery.py','--check-only'],cwd=ROOT,check=True)
    else:
        if args.prepare:prepare()
        if args.package:package()
        if not(args.prepare or args.package):ap.error('Choose --all, --prepare or --package')

if __name__=='__main__':main()
