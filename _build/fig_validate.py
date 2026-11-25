#!/usr/bin/env python3
"""Valida las selecciones de figuras antes de extraerlas."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
SEL = BUILD / "figures" / "sel"
INV = BUILD / "figures" / "inventory"
RES = ROOT.parent / "Anatopato" / "Capitulos" / "resumenes"
EMDASH = "\u2014"


def plain(md: str) -> str:
    md = re.sub(r"\[p\.\s*[0-9][0-9,\-\s]*?\]", " ", md)
    md = md.replace("**", "").replace("__", "").replace("`", "")
    md = re.sub(r"(?<!\w)[*_](?=\S)|(?<=\S)[*_](?!\w)", "", md)
    return re.sub(r"\s+", " ", md)


def main() -> int:
    errors = []
    warnings = []
    total = 0
    for cap in range(1, 19):
        sel_path = SEL / f"cap{cap:02d}.json"
        inv_path = INV / f"cap{cap:02d}.json"
        res_path = RES / f"Cap{cap:02d}.md"
        if not sel_path.exists():
            warnings.append(f"Cap{cap:02d}: sin selección")
            continue
        data = json.loads(sel_path.read_text(encoding="utf-8"))
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        summary = plain(res_path.read_text(encoding="utf-8"))
        nums = {f["number"] for f in inv["figures"]}
        headings = set(inv["headings"])
        figs = data.get("figures", [])
        total += len(figs)
        if not 6 <= len(figs) <= 8:
            errors.append(f"Cap{cap:02d}: {len(figs)} figuras (deben ser 6 a 8)")
        seen = set()
        for f in figs:
            tag = f"Cap{cap:02d} {f.get('number')}"
            if f.get("number") not in nums:
                errors.append(f"{tag}: no está en el inventario")
            if f.get("number") in seen:
                errors.append(f"{tag}: repetida")
            seen.add(f.get("number"))
            if f.get("section") not in headings:
                errors.append(f"{tag}: sección no exacta: {f.get('section')!r}")
            anchor = f.get("after_text", "")
            if anchor and anchor not in summary:
                errors.append(f"{tag}: after_text no aparece: {anchor!r}")
            if EMDASH in json.dumps(f, ensure_ascii=False):
                errors.append(f"{tag}: em dash")
            if not f.get("caption") or len(f["caption"]) < 20:
                warnings.append(f"{tag}: caption corta")
        mech = sum(1 for f in figs if f.get("kind") == "mechanism")
        diag = sum(1 for f in figs if f.get("kind") == "diagnostic")
        print(f"Cap{cap:02d}: {len(figs)} figuras ({mech} mecanismos, {diag} diagnósticas)")
    print(f"\nTotal seleccionadas: {total}")
    for w in warnings:
        print("AVISO:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"\n{len(errors)} errores")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
