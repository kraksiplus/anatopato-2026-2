#!/usr/bin/env python3
"""Audita las citas por página de una copia revisada del resumen.

Uso:
    python3 _build/cite_audit.py --chapter 1
    python3 _build/cite_audit.py --all
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_build"))
from cite_suggest import CITE_RE, load_pages, parse_blocks, strip_md, tokens  # noqa: E402

RES = ROOT.parent / "Anatopato" / "Capitulos" / "resumenes"
FINAL = ROOT / "_build" / "cites" / "final"
CAND = ROOT / "_build" / "cites" / "cand"
OUT = ROOT / "_build" / "cites" / "audit"
PAGES = json.loads((ROOT / "_build" / "manifest.json").read_text(encoding="utf-8"))["pages"]


def page_range(chapter: int) -> tuple[int, int]:
    page = next(p for p in PAGES if p["kind"] == "chapter" and p["num"] == chapter)
    lo, _, hi = str(page["printed"]).partition("-")
    return int(lo), int(hi or lo)


def expand_pages(value: str) -> list[int]:
    pages = []
    for part in re.split(r"[,]", value):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = [int(x.strip()) for x in part.split("-", 1)]
            pages.extend(range(min(a, b), max(a, b) + 1))
        else:
            pages.append(int(part))
    return pages


def citations(text: str) -> list[int]:
    pages = []
    for raw in re.findall(r"\[p\.\s*([0-9][0-9,\-\s]*)\]", text):
        pages.extend(expand_pages(raw))
    return sorted(set(pages))


def plain(text: str) -> str:
    text = CITE_RE.sub("", text)
    return " ".join(strip_md(text).split())


def block_text(lines: list[str], block: dict) -> str:
    return "\n".join(lines[block["start"]:block["end"] + 1])


def audit(chapter: int) -> dict:
    lo, hi = page_range(chapter)
    original = (RES / f"Cap{chapter:02d}.md").read_text(encoding="utf-8")
    reviewed = (FINAL / f"Cap{chapter:02d}.md").read_text(encoding="utf-8")
    cand_path = CAND / f"Cap{chapter:02d}.json"
    cand = json.loads(cand_path.read_text(encoding="utf-8")) if cand_path.exists() else {"blocks": []}
    cand_by_id = {b["id"]: b for b in cand.get("blocks", [])}
    page_tokens = {p["page"]: set(p["tokens"]) for p in load_pages(chapter)}

    orig_lines = original.splitlines()
    rev_lines = reviewed.splitlines()
    orig_blocks = parse_blocks(orig_lines)
    rev_blocks = parse_blocks(rev_lines)

    errors = []
    missing = []
    invalid = []
    weak = []
    low_overlap = []
    mismatch = []
    cite_count = 0
    table_missing = []

    if len(orig_blocks) != len(rev_blocks):
        errors.append(f"bloques {len(rev_blocks)} vs original {len(orig_blocks)}")

    for bid, (ob, rb) in enumerate(zip(orig_blocks, rev_blocks)):
        otext = plain(block_text(orig_lines, ob))
        rtext = plain(block_text(rev_lines, rb))
        if otext != rtext:
            mismatch.append({"id": bid, "kind": ob["kind"], "orig": otext[:160], "rev": rtext[:160]})
        if ob["kind"] == "table":
            after = rev_lines[rb["end"] + 1:rb["end"] + 4]
            if not any(x.strip().startswith("Fuente: [p.") for x in after):
                table_missing.append({"id": bid, "text": otext[:160]})
            continue

        got = citations(block_text(rev_lines, rb))
        cite_count += len(got)
        if not got:
            missing.append({"id": bid, "kind": ob["kind"], "text": otext[:180]})
            continue
        for p in got:
            if not (lo <= p <= hi):
                invalid.append({"id": bid, "page": p, "range": [lo, hi]})
        c = cand_by_id.get(bid)
        if c and c.get("candidates"):
            top = [x["page"] for x in c["candidates"]]
            best_score = c["candidates"][0]["score"]
            if got[0] not in top and best_score >= 0.15:
                weak.append(
                    {
                        "id": bid,
                        "kind": ob["kind"],
                        "cited": got,
                        "top": [(x["page"], x["score"]) for x in c["candidates"]],
                        "text": otext[:180],
                    }
                )
        key = {t for t in set(tokens(otext)) if len(t) >= 5}
        if key:
            union = set()
            for p in got:
                union |= page_tokens.get(p, set())
            coverage = len(key & union) / len(key)
            if coverage < 0.25:
                low_overlap.append(
                    {
                        "id": bid,
                        "kind": ob["kind"],
                        "cited": got,
                        "coverage": round(coverage, 2),
                        "missing": sorted(key - union)[:12],
                        "text": otext[:180],
                    }
                )

    for line in rev_lines:
        if line.strip().startswith("#") and "[p." in line:
            errors.append("cita en un título: " + line.strip()[:120])
    if "\u2014" in reviewed:
        errors.append("em dash detectado")

    result = {
        "chapter": chapter,
        "range": [lo, hi],
        "blocks": len(rev_blocks),
        "citations": cite_count,
        "tables": sum(1 for b in rev_blocks if b["kind"] == "table"),
        "missing": missing,
        "invalid": invalid,
        "weak": weak,
        "low_overlap": low_overlap,
        "table_missing": table_missing,
        "mismatch": mismatch,
        "errors": errors,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"cap{chapter:02d}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    chapters = list(range(1, 11)) if args.all else [args.chapter]
    if not all(chapters):
        ap.error("Indica --chapter N o --all")

    bad = 0
    for chapter in chapters:
        path = FINAL / f"Cap{chapter:02d}.md"
        if not path.exists():
            print(f"Cap{chapter:02d}: falta {path}")
            bad += 1
            continue
        r = audit(chapter)
        flags = (
            len(r["missing"]) + len(r["invalid"]) + len(r["weak"])
            + len(r["low_overlap"])
            + len(r["table_missing"]) + len(r["mismatch"]) + len(r["errors"])
        )
        print(
            f"Cap{chapter:02d}: {r['citations']} citas, {r['blocks']} bloques, "
            f"{r['tables']} tablas | faltan {len(r['missing'])}, "
            f"páginas inválidas {len(r['invalid'])}, débiles {len(r['weak'])}, "
            f"bajo solape {len(r['low_overlap'])}, "
            f"tablas sin fuente {len(r['table_missing'])}, "
            f"texto alterado {len(r['mismatch'])}, errores {len(r['errors'])}"
        )
        if flags:
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
