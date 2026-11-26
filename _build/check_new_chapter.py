#!/usr/bin/env python3
"""Valida un resumen nuevo del C2 (capítulos 19-26).

Comprueba citas por bloque, páginas dentro del rango, fuentes de tabla,
em dash, anclas de figuras y citas de los textos de repaso.

Uso:
    python3 _build/check_new_chapter.py --chapter 19
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_build"))
from cite_suggest import parse_blocks, strip_md, tokens  # noqa: E402

RES = ROOT.parent / "Anatopato" / "Capitulos" / "resumenes"
SEL = ROOT / "_build" / "figures" / "sel"
ENRICH = ROOT / "_build" / "enrich"
PAGES = json.loads((ROOT / "_build" / "manifest.json").read_text(encoding="utf-8"))["pages"]


def page_range(chapter: int) -> tuple[int, int]:
    page = next(p for p in PAGES if p["kind"] == "chapter" and p["num"] == chapter)
    lo, _, hi = str(page["printed"]).partition("-")
    return int(lo), int(hi or lo)


def expand(value: str) -> list[int]:
    out = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def cite_pages(text: str) -> list[int]:
    out = []
    for raw in re.findall(r"\[p\.\s*([0-9][0-9,\-\s]*)\]", text):
        out.extend(expand(raw))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, required=True)
    args = ap.parse_args()
    chapter = args.chapter
    lo, hi = page_range(chapter)
    path = RES / f"Cap{chapter:02d}.md"
    if not path.exists():
        print(f"ERROR: falta {path}")
        return 1
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    blocks = parse_blocks(lines)

    errors = []
    missing = []
    invalid = []
    table_missing = []
    if "\u2014" in text:
        errors.append("em dash detectado")
    if not text.startswith(f"# Capítulo {chapter}."):
        errors.append("título inicial inesperado")

    for bid, block in enumerate(blocks):
        raw = "\n".join(lines[block["start"]:block["end"] + 1])
        plain = strip_md(raw)
        if block["kind"] == "table":
            after = lines[block["end"] + 1:block["end"] + 4]
            if not any(x.strip().startswith("Fuente: [p.") for x in after):
                table_missing.append((bid, plain[:100]))
            continue
        pages = cite_pages(raw)
        if not pages:
            if plain.strip().endswith(":") or len(tokens(plain)) < 8:
                continue
            missing.append((bid, block["kind"], plain[:120]))
            continue
        for page in pages:
            if not (lo <= page <= hi):
                invalid.append((bid, page))

    sel_path = SEL / f"cap{chapter:02d}.json"
    if not sel_path.exists():
        errors.append(f"falta {sel_path}")
    else:
        sel = json.loads(sel_path.read_text(encoding="utf-8"))
        figs = sel.get("figures", [])
        if not (6 <= len(figs) <= 8):
            errors.append(f"figuras seleccionadas: {len(figs)} (esperado 6-8)")
        headings = [ln[3:].strip() for ln in lines if ln.startswith("## ")]
        plain_text = " ".join(strip_md(text).split())
        for fig in figs:
            if fig.get("number") is None or not fig.get("caption") or not fig.get("page"):
                errors.append(f"figura incompleta: {fig}")
                continue
            if not (lo <= int(fig["page"]) <= hi):
                errors.append(f"figura {fig['number']} con página fuera de rango: {fig['page']}")
            section = fig.get("section", "")
            if section and not any(section.lower() in h.lower() or h.lower() in section.lower() for h in headings):
                errors.append(f"figura {fig['number']} con sección inexistente: {section}")
            anchor = " ".join(strip_md(fig.get("after_text", "")).split())
            if anchor and anchor not in plain_text:
                errors.append(f"figura {fig['number']} con after_text que no está en el resumen")

    enrich_path = ENRICH / f"c2-{chapter}.json"
    if enrich_path.exists():
        enrich = json.loads(enrich_path.read_text(encoding="utf-8"))
        for key in ("essentials", "topics", "callouts"):
            if key not in enrich:
                errors.append(f"enrich sin {key}")
        for item in enrich.get("essentials", []) + [c.get("text", "") for c in enrich.get("callouts", [])]:
            for page in cite_pages(item):
                if not (lo <= page <= hi):
                    errors.append(f"enrich con página fuera de rango: {page}")
    else:
        errors.append(f"falta {enrich_path}")

    print(f"Cap{chapter:02d}: {len(blocks)} bloques | rango {lo}-{hi}")
    print(f"  sin cita: {len(missing)} | páginas inválidas: {len(invalid)} | tablas sin fuente: {len(table_missing)} | errores: {len(errors)}")
    for m in missing:
        print("  SIN CITA", m)
    for m in table_missing:
        print("  TABLA SIN FUENTE", m)
    for m in invalid:
        print("  PÁGINA INVÁLIDA", m)
    for e in errors:
        print("  ERROR", e)
    return 1 if (missing or invalid or table_missing or errors) else 0


if __name__ == "__main__":
    raise SystemExit(main())
