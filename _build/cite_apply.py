#!/usr/bin/env python3
"""Aplica las decisiones de citas por bloque y genera la copia final.

Uso:
    python3 _build/cite_apply.py --chapter 1
    python3 _build/cite_apply.py --all
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_build"))
from cite_suggest import DEC, FINAL, RES, insert_cite, parse_blocks  # noqa: E402


def apply(chapter: int) -> tuple[int, int]:
    src = RES / f"Cap{chapter:02d}.md"
    decisions = json.loads((DEC / f"cap{chapter:02d}.json").read_text(encoding="utf-8"))
    cites = {int(k): (v or "").strip() for k, v in decisions["cites"].items()}
    lines = src.read_text(encoding="utf-8").splitlines()
    blocks = parse_blocks(lines)

    needed = set(range(len(blocks)))
    missing = sorted(needed - set(cites))
    extra = sorted(set(cites) - needed)
    if extra:
        raise SystemExit(f"Cap{chapter:02d}: decisiones con id inexistente: {extra}")

    out = []
    cursor = 0
    cited = 0
    for bid, block in enumerate(blocks):
        while cursor < block["start"]:
            out.append(lines[cursor])
            cursor += 1
        value = cites.get(bid, "")
        if block["kind"] == "table":
            while cursor <= block["end"]:
                out.append(lines[cursor])
                cursor += 1
            if value:
                if cursor < len(lines) and lines[cursor].strip().startswith("Fuente: [p."):
                    cursor += 1
                if cursor < len(lines) and not lines[cursor].strip():
                    cursor += 1
                out.append("")
                out.append(f"Fuente: [p. {value}].")
                if cursor < len(lines) and lines[cursor].strip():
                    out.append("")
                cited += 1
            continue

        for j in range(block["start"], block["end"] + 1):
            if j == block["end"] and value:
                out.append(insert_cite(lines[j], f"[p. {value}]"))
                cited += 1
            else:
                out.append(lines[j])
        cursor = block["end"] + 1

    while cursor < len(lines):
        out.append(lines[cursor])
        cursor += 1

    FINAL.mkdir(parents=True, exist_ok=True)
    (FINAL / f"Cap{chapter:02d}.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    if missing:
        print(f"AVISO Cap{chapter:02d}: {len(missing)} bloques sin decisión: {missing[:10]}")
    return cited, len(blocks)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    chapters = list(range(1, 11)) if args.all else [args.chapter]
    if not all(chapters):
        ap.error("Indica --chapter N o --all")
    for chapter in chapters:
        cited, blocks = apply(chapter)
        print(f"Cap{chapter:02d}: {cited}/{blocks} bloques con cita -> final/Cap{chapter:02d}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
