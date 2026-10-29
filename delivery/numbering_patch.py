#!/usr/bin/env python3
"""Prepare minimal or full-shift sheet-number patches from numbering_plan.csv.

This tool DOES NOT modify DXF/DWG files. It prints or writes a JSON patch plan
that a human or a verified CAD adapter can apply later.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "delivery" / "data"
PLAN = DATA / "numbering_plan.csv"
DUPLICATES = DATA / "duplicate_report.csv"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp, delimiter=";"))


def duplicate_groups() -> list[dict]:
    return read_csv(DUPLICATES)


def minimal_patch(rows: list[dict]) -> list[dict]:
    """Change only the non-keeper file of each duplicate group."""
    groups = duplicate_groups()
    targets: dict[str, str] = {}
    for group in groups:
        for value in (group.get("to_change") or "").split(";"):
            value = value.strip()
            if value:
                targets[value] = group.get("sheet_no", "")
    patches = []
    for row in rows:
        old = row.get("old_sheet_no", "")
        new = row.get("minimal_new_no", old)
        if old != new or row.get("file") in targets:
            patches.append({
                "file": row.get("file", ""), "old": old, "new": new,
                "strategy": "minimal", "action": "SET_SHEET_NO",
                "requires_approval": True,
            })
    return patches


def full_shift(rows: list[dict]) -> list[dict]:
    """Apply the precomputed full-shift numbering to all 120 rows."""
    patches = []
    for row in rows:
        old = row.get("old_sheet_no", "")
        new = row.get("full_shift_new_no", old)
        if old != new:
            patches.append({
                "file": row.get("file", ""), "old": old, "new": new,
                "strategy": "full_shift", "action": "SET_SHEET_NO",
                "requires_approval": True,
            })
    return patches


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare sheet-number patch plan")
    ap.add_argument("--strategy", choices=["minimal", "full"], default="minimal")
    ap.add_argument("--output", type=Path, help="Write JSON plan to this path instead of stdout")
    args = ap.parse_args()
    rows = read_csv(PLAN)
    patches = minimal_patch(rows) if args.strategy == "minimal" else full_shift(rows)
    result = {
        "format": "navigator-kit.numbering-patch/v1",
        "strategy": args.strategy,
        "planRows": len(rows),
        "patchCount": len(patches),
        "duplicateGroups": len(duplicate_groups()),
        "nanoCADExecuted": False,
        "appliedToFiles": False,
        "patches": patches,
        "warning": "Do not apply to production DWG without a verified MultiCAD .NET adapter, backup, and rollback test.",
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {len(patches)} patches to {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
