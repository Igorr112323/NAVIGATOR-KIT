#!/usr/bin/env python3
"""Session-3 production pipeline wrapper.

Two backends are exposed:

* ``synthetic`` — Works today. Reads the 120 DXF R2010 fixtures via the
  stdlib reference scanner, writes sheets_registry.csv/json with SHA-256,
  runs completeness validation, and regenerates the report/chart.
* ``multicad`` — Not implemented here on purpose. It requires Windows,
  nanoCAD 26, a license, and a verified MultiCAD .NET SDK 26. The Python
  script records the missing dependency instead of inventing Database,
  Transaction, or BlockReference APIs.

The companion C# readiness checklist lives in
src/NavigatorKit.NanoCad/DwgReadiness.cs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
DELIVERY = ROOT / "delivery"
SESSION3 = DELIVERY / "session-3"
DEFAULT_INPUT = ROOT / "samples" / "synthetic_sets"
DEFAULT_MAPPING = DELIVERY / "xml" / "stamp_mapping.xml"
DEFAULT_SAMPLES = ROOT / "samples"
DEFAULT_OUTPUT = DELIVERY / "data"
WATERMARK = "nanoCAD НЕ запускался / не скриншот CAD"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp, delimiter=";"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def md_cell(value) -> str:
    return str(value or "").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def generate_report_and_chart(out: Path) -> dict:
    """Regenerate completeness_report.md/chart from the freshly written CSV."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    issues = read_csv(out / "completeness_report.csv")
    duplicates = read_csv(out / "duplicate_report.csv")
    assert len(issues) == 16, f"expected 16 seeded issues, got {len(issues)}"
    assert len(duplicates) == 4, f"expected 4 duplicate groups, got {len(duplicates)}"

    frame = pd.DataFrame(issues)
    counts = frame["code"].value_counts().sort_index().to_dict()
    severity_counts = frame["severity"].value_counts().sort_index().to_dict()

    chart_path = out / "completeness_chart.png"
    fig, ax = plt.subplots(figsize=(11, 6))
    codes = list(counts.keys())
    bars = ax.bar(codes, [counts[c] for c in codes], color="#f59e0b", edgecolor="#7c2d12")
    ax.bar_label(bars, padding=3, fontsize=10)
    ax.set_title("Контроль комплектности: 16 инцидентов / 8 категорий", fontsize=14, fontweight="bold")
    ax.set_ylabel("Количество", fontsize=11)
    ax.tick_params(axis="x", rotation=35, labelsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.text(0.98, 0.02, WATERMARK, ha="right", va="bottom", color="#b91c1c",
             alpha=0.65, fontsize=10, fontweight="bold",
             bbox=dict(facecolor="white", edgecolor="none", alpha=0.45, pad=4))
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)

    write_json(out / "completeness_chart.json", {
        "format": "navigator-kit.completeness-chart/v2",
        "sessionId": "night-session-20261028",
        "generatedAt": utcnow(),
        "generatedBy": "tools/pipeline.py + matplotlib",
        "incidents": len(issues),
        "duplicateGroups": len(duplicates),
        "watermark": WATERMARK,
        "nanoCADScreenshot": False,
    })

    count_lines = "\n".join(f"| `{code}` | {count} |" for code, count in counts.items())
    issue_lines = "\n".join(
        "| " + " | ".join(md_cell(i.get(k, "")) for k in
                          ("issue_id", "code", "severity", "mark", "sheet_no", "field", "message", "suggestion")) + " |"
        for i in issues)
    duplicate_lines = "\n".join(
        "| " + " | ".join(md_cell(d.get(k, "")) for k in
                          ("mark", "sheet_no", "count", "keeper", "files", "recommendation")) + " |"
        for d in duplicates)
    text = f"""# Отчёт о комплектности — session 3 (2026-10-28)

> Сгенерировано `tools/pipeline.py` из 120 синтетических DXF R2010. nanoCAD **не запускался**. График и PNG — диагностические материалы с водяным знаком.

## Сводка

| Показатель | Значение |
|---|---:|
| Инцидентов | **{len(issues)}** |
| Категорий | {len(counts)} |
| Групп дублей | **{len(duplicates)}** |
| Уровни критичности | {', '.join(f'{k}: {v}' for k, v in severity_counts.items())} |

Обнаружено 4 группы дублей и 16 инцидентов.

**Важно:** нельзя утверждать, что все 16 инцидентов — «есть в ведомости, нет файла»: это сумма разных классов.

![График инцидентов](data/completeness_chart.png)

## Распределение по кодам

| Код | Количество |
|---|---:|
{count_lines}

## Все 16 инцидентов

| ID | Код | Уровень | Марка | Лист | Поле | Сообщение | Рекомендация |
|---|---|---|---|---|---|---|---|
{issue_lines}

## 4 группы дублей

| Марка | Лист | Кол-во | Хранитель | Файлы | Рекомендация |
|---|---|---:|---|---|---|
{duplicate_lines}

## Статус production DWG

Реальные DWG и MultiCAD .NET SDK 26 отсутствуют. Этот отчёт подтверждает воспроизводимость synthetic backend, а не чтение production DWG. См. `delivery/session-3/p1_production_dwg.json`.
"""
    (out / "completeness_report.md").write_text(text, encoding="utf-8")
    # Canonical location expected by the delivery bundle.
    (DELIVERY / "completeness_report.md").write_text(text, encoding="utf-8")
    return {"incidents": len(issues), "duplicateGroups": len(duplicates), "counts": counts,
            "chart": chart_path.relative_to(ROOT).as_posix()}


def run_synthetic(args) -> dict:
    nk = load_module("navigator_kit_pipeline", TOOLS / "navigator_kit.py")
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    summary = nk.run_all(args.input, args.mapping, out, args.samples)
    report = generate_report_and_chart(out)
    registry_json = json.loads((out / "sheets_registry.json").read_text(encoding="utf-8"))
    sheets = registry_json.get("sheets", [])
    return {
        "backend": "synthetic-dxf",
        "status": "VERIFIED_LOCALLY_SYNTHETIC_ONLY",
        "input": args.input.relative_to(ROOT).as_posix() if args.input.is_relative_to(ROOT) else str(args.input),
        "output": out.relative_to(ROOT).as_posix() if out.is_relative_to(ROOT) else str(out),
        "syntheticDxfProcessed": len(sheets),
        "realDwgProcessed": 0,
        "registryRows": len(sheets),
        "sha256AllPresent": all(s.get("source_sha256") for s in sheets),
        "registryJsonSha256": sha256_file(out / "sheets_registry.json"),
        "completeness": report,
        "summaryStatus": summary.get("status"),
        "nanoCADExecuted": False,
        "multiCadSdkUsed": False,
        "rollbackVerified": summary.get("stampRollbackVerified"),
        "printOrderConsistent": summary.get("printOrderConsistent"),
    }


def run_multicad(args) -> dict:
    status = {
        "backend": "multicad-dwg",
        "status": "EXTERNAL_DEPENDENCY_NOT_IMPLEMENTED",
        "hypothesis": "ГИПОТЕЗА/ПРОВЕРИТЬ",
        "realDwgProcessed": 0,
        "nanoCADExecuted": False,
        "multiCadSdkUsed": False,
        "reason": "Windows, nanoCAD 26, license, and verified SDK 26 Database/Transaction APIs are unavailable in this sandbox.",
        "requiredChecks": [
            "Run tools/windows_stand_check.ps1 on a real Windows host",
            "Run NK_HELLO and SDK_PROBE inside nanoCAD 26",
            "Confirm TFM, x64, DLL names, NETLOAD/APPLOAD",
            "Verify background Database open and Transaction via reflection dump",
            "Verify AttributeReference read/write and .bak + SHA-256 rollback",
        ],
        "csharpReadiness": "src/NavigatorKit.NanoCad/DwgReadiness.cs",
        "windowsWorkflow": ".github/workflows/windows-build.yml",
    }
    write_json(SESSION3 / "multicad_backend_status.json", status)
    return status


def copy_registry_to_session3(out: Path) -> None:
    dest = SESSION3 / "data"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("sheets_registry.csv", "sheets_registry.json", "completeness_report.csv",
                 "duplicate_report.csv", "numbering_plan.csv", "print_order.csv", "print_order.json"):
        src = out / name
        if src.is_file():
            shutil.copy2(src, dest / name)


def main() -> int:
    ap = argparse.ArgumentParser(description="Navigator Kit session-3 production pipeline wrapper")
    ap.add_argument("--backend", choices=["synthetic", "multicad"], default="synthetic")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    ap.add_argument("--samples", type=Path, default=DEFAULT_SAMPLES)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--report-json", type=Path, default=SESSION3 / "p1_production_dwg.json")
    args = ap.parse_args()
    SESSION3.mkdir(parents=True, exist_ok=True)
    result = run_synthetic(args) if args.backend == "synthetic" else run_multicad(args)
    if args.backend == "synthetic":
        copy_registry_to_session3(args.output)
    result["format"] = "navigator-kit.session3-pipeline/v1"
    result["sessionId"] = "night-session-20261028"
    result["generatedAt"] = utcnow()
    write_json(args.report_json, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
