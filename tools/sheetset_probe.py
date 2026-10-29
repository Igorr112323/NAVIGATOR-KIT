#!/usr/bin/env python3
"""Session-3 SHEETSET/Tables readiness probe.

No nanoCAD host or .dst file is touched. The script verifies the local
print-order handoff, regenerates Appendix-B CSV templates, and records which
SDK methods are still ГИПОТЕЗА/ПРОВЕРИТЬ.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "delivery"
DATA = DELIVERY / "data"
SESSION3 = DELIVERY / "session-3"
TOOLS = ROOT / "tools"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_night_session_2():
    spec = importlib.util.spec_from_file_location("night_session_2_probe", TOOLS / "night_session_2.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def method_status(api: dict, subject: str) -> str:
    for exp in api.get("experiments", []):
        if exp.get("subject") == subject:
            return exp.get("status", "UNKNOWN")
    return "NOT_FOUND"


def main() -> int:
    SESSION3.mkdir(parents=True, exist_ok=True)
    api = read_json(DATA / "api_experiment_results.json")
    consistency = read_json(DATA / "print_order_consistency.json")
    print_order = read_json(DATA / "print_order.json")
    form1 = read_json(DATA / "summary.json")

    # Regenerate the Appendix-B CSV templates via the session-2 generator.
    ns2 = load_night_session_2()
    ns2.generate_wo_templates()

    wo1 = DATA / "wo1_template.csv"
    wo2 = DATA / "wo2_template.csv"
    for src in (wo1, wo2):
        shutil.copy2(src, SESSION3 / src.name)

    verified_print_order = {
        "format": "navigator-kit.print-order-session3/v1",
        "sessionId": "night-session-20261028",
        "generatedAt": utcnow(),
        "source": "delivery/data/print_order.json",
        "sourceSha256": sha256_file(DATA / "print_order.json"),
        "form1OrderHash": consistency.get("form1OrderHash"),
        "printOrderHash": consistency.get("printOrderHash"),
        "printOrderItems": consistency.get("printOrderItems", len(print_order.get("items", []))),
        "layoutOrderMatchesPrintOrder": bool(consistency.get("consistent")),
        "dstTouched": False,
        "method": "Local handoff JSON only; nanoCAD layouts were NOT read.",
        "items": print_order.get("items", []),
    }
    write_json(SESSION3 / "print_order.json", verified_print_order)
    write_json(DATA / "print_order_session3.json", {
        k: v for k, v in verified_print_order.items() if k != "items"
    })

    get_sheets = method_status(api, "GetSheets()")
    get_sheet_sets = method_status(api, "GetSheetSets()")
    result = {
        "format": "navigator-kit.sheetset-tables-probe/v1",
        "sessionId": "night-session-20261028",
        "generatedAt": utcnow(),
        "status": "LOCAL_HANDOFF_VERIFIED;CAD_API_HYPOTHESIS",
        "getSheetsStatus": get_sheets,
        "getSheetSetsStatus": get_sheet_sets,
        "tablesApiVerified": False,
        "sheetSetApiVerified": False,
        "dstTouched": False,
        "nanoCADExecuted": False,
        "printOrderConsistent": bool(consistency.get("consistent")),
        "printOrderItems": verified_print_order["printOrderItems"],
        "form1Rows": form1["output"]["form1Rows"],
        "wo1Rows": sum(1 for _ in wo1.open(encoding="utf-8-sig")) - 1,
        "wo2Rows": sum(1 for _ in wo2.open(encoding="utf-8-sig")) - 1,
        "wo1Sha256": sha256_file(wo1),
        "wo2Sha256": sha256_file(wo2),
        "hypotheses": [
            "GetSheets() signature in MultiCAD .NET SDK 26",
            "GetSheetSets() existence and contract",
            "Tables API / sheet-list-table columns vs ГОСТ Р 21.101-2026 Appendix Б",
            "Documented .dst export or layout-order synchronisation",
        ],
        "nextWindowsSteps": [
            "Run SDK_PROBE and dump real method signatures",
            "Insert Sheet List Table and compare columns with wo1_template.csv",
            "Compare layout tab order with delivery/session-3/print_order.json",
        ],
    }
    write_json(SESSION3 / "p1_sheetset_tables.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["printOrderConsistent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
