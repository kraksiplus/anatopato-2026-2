#!/usr/bin/env python3
"""Busca una frase o términos en el OCR y devuelve página impresa y contexto.

Uso:
    python3 _build/cite_lookup.py --chapter 2 --query "necrosis coagulativa"
    python3 _build/cite_lookup.py --chapter 2 --query "coagulativa arquitectura"
"""
import argparse
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OCR = ROOT.parent / "Anatopato" / "Capitulos" / "ocr"


def fold(text: str):
    out, pos = [], []
    for i, ch in enumerate(text):
        for c in unicodedata.normalize("NFKD", ch):
            if unicodedata.combining(c):
                continue
            out.append(c.lower())
            pos.append(i)
    return "".join(out), pos


def pages(chapter: int):
    text = (OCR / f"Cap{chapter:02d}.md").read_text(encoding="utf-8")
    parts = re.split(r"<!-- ===== Pagina impresa (\d+) \(PDF cap \d+\) ===== -->", text)
    return [(int(parts[i]), parts[i + 1]) for i in range(1, len(parts), 2) if parts[i + 1].strip()]


def window(text: str, folded: str, pos: list[int], start: int, end: int, pad: int = 220) -> str:
    a = max(0, pos[start] - pad)
    b = min(len(text), pos[min(end, len(pos) - 1)] + pad)
    return " ".join(text[a:b].split())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()

    q, _ = fold(args.query)
    words = [w for w in re.findall(r"[a-z0-9]+", q) if len(w) > 2]
    hits = []
    for page, text in pages(args.chapter):
        folded, pos = fold(text)
        exact = folded.find(q) if q else -1
        score = sum(folded.count(w) for w in words)
        if exact != -1 or score:
            hits.append((exact != -1, score, page, text, folded, pos))

    hits.sort(key=lambda x: (-x[0], -x[1]))
    if not hits:
        print("Sin coincidencias")
        return 0
    for exact, score, page, text, folded, pos in hits[:args.limit]:
        if exact != -1:
            snippet = window(text, folded, pos, exact, exact + len(q))
        else:
            first = folded.find(words[0]) if words else 0
            snippet = window(text, folded, pos, max(0, first), max(0, first) + 1)
        print(f"\n[p. {page}] exacta={exact} score={score}\n{snippet[:700]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
