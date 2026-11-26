#!/usr/bin/env python3
"""Prepara las solicitudes de extracción y fusiona los resultados."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
SEL = BUILD / "figures" / "sel"
IN = BUILD / "figures" / "in"
OUT = BUILD / "figures" / "out"
PAGES = json.loads((BUILD / "manifest.json").read_text(encoding="utf-8"))["pages"]
SOURCE = "Robbins y Cotran, Patología estructural y funcional, 10ª ed., Elsevier España, 2021"


def page_for(cap: int) -> dict | None:
    for p in PAGES:
        if p["kind"] == "chapter" and p["num"] == cap:
            return p
    return None


def prepare() -> None:
    IN.mkdir(parents=True, exist_ok=True)
    for cap in range(1, 27):
        sel = SEL / f"cap{cap:02d}.json"
        page = page_for(cap)
        if not sel.exists() or not page:
            continue
        data = json.loads(sel.read_text(encoding="utf-8"))
        start = int(str(page["printed"]).split("-")[0])
        dest = IN / f"cap{cap:02d}.json"
        previous = {}
        if dest.exists():
            try:
                old = json.loads(dest.read_text(encoding="utf-8"))
                previous = {f["number"]: f.get("bbox") for f in old.get("figures", [])}
            except (ValueError, KeyError):
                previous = {}
        figures = []
        for f in data["figures"]:
            entry = {"number": f["number"], "page": f["page"]}
            if previous.get(f["number"]):
                entry["bbox"] = previous[f["number"]]
            figures.append(entry)
        req = {"chapter": cap, "printed_start": start, "figures": figures}
        (IN / f"cap{cap:02d}.json").write_text(
            json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"in cap{cap:02d}: {len(req['figures'])} figuras, desde p. {start}")


def merge() -> None:
    missing = []
    for cap in range(1, 27):
        sel = SEL / f"cap{cap:02d}.json"
        out = OUT / f"cap{cap:02d}.json"
        page = page_for(cap)
        if not sel.exists() or not page:
            continue
        if not out.exists():
            print(f"AVISO cap{cap:02d}: sin extracción")
            continue
        selected = json.loads(sel.read_text(encoding="utf-8"))
        extracted = json.loads(out.read_text(encoding="utf-8"))
        by_num = {r["number"]: r for r in extracted.get("figures", []) if "error" not in r}
        merged = []
        for fig in selected["figures"]:
            got = by_num.get(fig["number"])
            if not got:
                missing.append(f"cap{cap:02d} {fig['number']}")
                continue
            merged.append({
                **fig,
                "image": got["image"],
                "width": got["width"],
                "height": got["height"],
            })
        dest = BUILD / "figures" / f"{page['id']}.json"
        dest.write_text(
            json.dumps(
                {"chapter": cap, "page_id": page["id"], "source": SOURCE, "figures": merged},
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        print(f"merge {page['id']}: {len(merged)}/{len(selected['figures'])}")
    if missing:
        print("\nFALTAN:")
        for m in missing:
            print(" ", m)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--merge", action="store_true")
    args = ap.parse_args()
    if args.prepare:
        prepare()
    if args.merge:
        merge()
    if not args.prepare and not args.merge:
        prepare()
