#!/usr/bin/env python3
"""Quita la cita de bloques que son solo rótulos introductorios.

Se apoya en el audit: bloques con cobertura 0, texto corto y dos puntos finales.
No toca bloques con contenido clínico.

Uso:
    python3 _build/cite_clean_leads.py --all
    python3 _build/cite_clean_leads.py --chapter 4
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_build"))
from cite_suggest import DEC, tokens  # noqa: E402

AUDIT = ROOT / "_build" / "cites" / "audit"


def clean(chapter: int) -> int:
    path = DEC / f"cap{chapter:02d}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    audit_path = AUDIT / f"cap{chapter:02d}.json"
    if not audit_path.exists():
        return 0
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    changed = 0
    for item in audit.get("low_overlap", []):
        text = item.get("text", "").strip()
        if not text.endswith(":"):
            continue
        if len(tokens(text)) > 7:
            continue
        if item.get("coverage", 1) > 0.15:
            continue
        key = str(item["id"])
        if data["cites"].get(key):
            data["cites"][key] = ""
            changed += 1
            print(f"Cap{chapter:02d} id {key}: sin cita ({text[:80]})")
    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    chapters = list(range(1, 11)) if args.all else [args.chapter]
    if not all(chapters):
        ap.error("Indica --chapter N o --all")
    total = sum(clean(c) for c in chapters)
    print(f"{total} bloques introductorios sin cita")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
