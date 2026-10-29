#!/usr/bin/env python3
"""v1: stdlib ASCII-DXF demo audit; not a GOST conformity certificate."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from linux_stand.independent_reader import inspect
ROOT = Path(__file__).resolve().parents[1]
# Reference basic paper sizes, mm. Not title-block/form geometry or drawing frame margins.
PAPER_MM = {'A0': (841, 1189), 'A1': (594, 841), 'A2': (420, 594),
            'A3': (297, 420), 'A4': (210, 297)}

def evaluate(data):
    attrs = data['attributes']; bounds = data['frameBounds']
    matched = []; mismatch = []; unverified = []
    sheet = attrs.get('SHEET', '')
    (matched if sheet.isascii() and sheet.isdecimal() and int(sheet) > 0 else mismatch).append(
        {'rule': 'project_positive_sheet', 'actual': sheet, 'expected': 'positive integer (project rule, not fixed by GOST)', 'codes': 'ATTRIB:2=SHEET,1=value'})
    fmt = attrs.get('FORMAT', '')
    size = sorted([bounds[2] - bounds[0], bounds[3] - bounds[1]])
    expected = PAPER_MM.get(fmt)
    ok = expected is not None and all(abs(a-b) < .01 for a,b in zip(size, expected))
    (matched if ok else mismatch).append({'rule': 'demo_outer_rectangle_vs_paper_reference',
        'actual': size, 'expected': list(expected) if expected else None,
        'codes': 'LWPOLYLINE:10/20; ATTRIB:2=FORMAT,1=value',
        'note': 'Only demo outer rectangle; not a normative drawing-frame margin check'})
    for tag in ('DESIGNATION', 'SHEET', 'TITLE', 'FORMAT'):
        (matched if attrs.get(tag, '').strip() else mismatch).append(
            {'rule': f'project_field_{tag}', 'actual': attrs.get(tag), 'expected': 'non-empty', 'codes': f'ATTRIB:2={tag},1=value'})
    for layer in ('FRAME', 'STAMP', 'NOTES'):
        (matched if layer in data['layers'] else mismatch).append(
            {'rule': 'project_layer', 'actual': layer in data['layers'], 'expected': layer, 'codes': '8', 'note': 'Layer names are project conventions, not GOST requirements'})
    unverified += ['ГОСТ Р 21.101-2026, Приложение Б: no form 1/2 tables in these samples; geometry NOT_ASSESSED',
                   'ГОСТ 2.301-68: paper-size reference only; official text and allowed orientation/margins require norm control',
                   'MARK attribute absent; DESIGNATION suffix must not be silently treated as mark']
    return {'matched': matched, 'mismatch': mismatch, 'unverified': unverified,
            'sheet': sheet, 'format': fmt, 'mark': attrs.get('MARK'), 'layers': data['layers'],
            'status': 'DEMO_CHECKS_PASS;NORMATIVE_NOT_ASSESSED' if not mismatch else 'DEMO_MISMATCH;NORMATIVE_NOT_ASSESSED'}

def self_test():
    good = {'attributes': {'DESIGNATION':'NK', 'SHEET':'1', 'TITLE':'T', 'FORMAT':'A4'}, 'frameBounds':[0,0,297,210], 'layers':['FRAME','STAMP','NOTES']}
    assert not evaluate(good)['mismatch']
    for sheet in ('0', '-1', '１', ''):
        assert evaluate({**good, 'attributes':{**good['attributes'], 'SHEET':sheet}})['mismatch']
    assert evaluate({**good, 'attributes':{**good['attributes'], 'FORMAT':'A1'}})['mismatch']
    assert evaluate({**good, 'layers':[]})['mismatch']
    assert evaluate(good)['mark'] is None
    print('geometry_audit self-tests: 8 PASS')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--input', type=Path, default=ROOT/'delivery/linux-stand/samples')
    ap.add_argument('--output', type=Path, default=ROOT/'delivery/linux-stand'); args=ap.parse_args()
    if args.self_test: self_test()
    results=[]
    for p in sorted(args.input.glob('*.dxf')):
        try: result={'file':p.name, **evaluate(inspect(p))}
        except (ValueError, KeyError, StopIteration) as exc:
            result={'file':p.name,'status':'PARSE_FAILED','error':str(exc),'matched':[],'mismatch':[{'rule':'parse_error'}]}
        results.append(result)
    if not results: raise SystemExit('No DXF samples found')
    report={'version':'1.0','normativeStatus':'ГИПОТЕЗА/ПРОВЕРИТЬ — NOT_ASSESSED',
        'references':[{'norm':'ГОСТ Р 21.101-2026','scope':'Appendix B forms 1/2 not present in samples','source':'docs/official-text-extract.md'},
                      {'norm':'ГОСТ 2.301-68','scope':'basic paper-size reference; not verified official text in this session','paper_mm':PAPER_MM}],
        'groupCodeCorrections':{'9':'HEADER variable name, not sheet number','70':'entity-specific flags, not paper format','2':'ATTRIB tag','1':'ATTRIB value','40':'TEXT/ATTRIB height','39':'thickness'},
        'files':results, 'demoMismatchCount':sum(len(r['mismatch']) for r in results)}
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'geometry_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Геометрический аудит 12 демонстрационных DXF', '', 'Версия скрипта 1.0. Чтение group codes без ezdxf. Это НЕ заключение о соответствии ГОСТ.',
           'ГОСТ Р 21.101-2026, Приложение Б: образцы не содержат таблиц форм 1/2 — NOT_ASSESSED.',
           'ГОСТ 2.301-68: сверена только внешняя тестовая прямоугольная граница с reference-размерами бумаги A0–A4. Официальный текст повторно не получен.', '',
           '| Файл | Лист (файл) | Лист (ГОСТ) | Формат (файл) | Формат (reference) | Марка | Слои | Примечание |',
           '|---|---|---|---|---|---|---|---|']
    for r in results:
        lines.append(f"| {r['file']} | {r.get('sheet','?')} | не предписывает конкретный номер | {r.get('format','?')} | A4: 210×297 mm | {r.get('mark') or 'отсутствует'} | {', '.join(r.get('layers',[]))} | {r['status']} |")
    lines += ['', '## Расхождения и непроверенное',f"- Отклонений от demo/project-контракта: {report['demoMismatchCount']}.",
              '- Во всех 12 файлах отсутствует отдельный MARK. Это ограничение данных, не доказанное нарушение ГОСТ.',
              '- Формы 1/2 отсутствуют: нельзя доказать их геометрию по штампу и рамке.',
              '- Имена слоёв и номер листа не предписываются приведённой reference-таблицей ГОСТ.',
              '', '## Примечания',
              '- GROUP 9 не номер листа; GROUP 70 не универсальный формат. Номер и формат — ATTRIB с tag 2 и значением 1.',
              '- Вложенные блоки, поворот/масштаб INSERT, DWG, расположение полей штампа и margins не проверяются.',
              '- Windows: python tools/geometry_audit.py --self-test. Затем открыть DXF в nanoCAD, проверить units, масштабы, рамку и реальные формы по официальному изданию.',
              '- ГИПОТЕЗА/ПРОВЕРИТЬ: нормативная геометрия остаётся открытой; визуальная проверка сама по себе не заменяет сверку размеров по ГОСТ.']
    for r in results:
        for issue in r['mismatch']:lines.append(f"- {r['file']}: {issue}")
    (args.output/'geometry_audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f"Audit: {len(results)} DXF, {report['demoMismatchCount']} demo mismatches; normative NOT_ASSESSED")
    if report['demoMismatchCount']:raise SystemExit(1)

if __name__=='__main__':main()
