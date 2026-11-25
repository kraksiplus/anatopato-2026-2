#!/usr/bin/env python3
"""Muestra bloques con su cita actual y las páginas candidatas, para revisión.

Uso:
    python3 _build/cite_review.py --chapter 1
    python3 _build/cite_review.py --chapter 1 --from 0 --to 19
    python3 _build/cite_review.py --chapter 1 --only 3,7,12
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_build"))
from cite_suggest import DEC, RES, parse_blocks, tokens  # noqa: E402


def block_text(lines, b):
    return "\n".join(lines[b["start"]:b["end"] + 1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--to", dest="end", type=int, default=10**9)
    ap.add_argument("--only", default="")
    ap.add_argument("--low", action="store_true", help="solo bloques dudosos o tablas")
    args = ap.parse_args()

    cap = args.chapter
    lines = (RES / f"Cap{cap:02d}.md").read_text(encoding="utf-8").splitlines()
    blocks = parse_blocks(lines)
    cand = json.loads((ROOT / "_build" / "cites" / "cand" / f"cap{cap:02d}.json").read_text(encoding="utf-8"))
    dec = json.loads((DEC / f"cap{cap:02d}.json").read_text(encoding="utf-8"))
    by_id = {b["id"]: b for b in cand["blocks"]}
    only = {int(x) for x in args.only.split(",") if x.strip()} if args.only else None

    for bid, block in enumerate(blocks):
        if only is not None and bid not in only:
            continue
        if only is None and not (args.start <= bid <= args.end):
            continue
        text = block_text(lines, block)
        current = dec["cites"].get(str(bid), "")
        c = by_id.get(bid, {})
        if args.low:
            cands = c.get("candidates", [])
            top = cands[0]["score"] if cands else 0
            if block["kind"] != "table" and len(tokens(text)) >= 10 and top >= 0.18 and current:
                continue
        print(f"\n--- id={bid} {block['kind']} | actual: {('p. ' + current) if current else 'SIN CITA'}")
        print("TEXTO:", " ".join(text.split())[:900])
        for x in c.get("candidates", []):
            print(f"  p. {x['page']} ({x['score']}): {x['snippet'][:260]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
