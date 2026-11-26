#!/usr/bin/env python3
"""Lista las leyendas de figura de un capítulo, con página impresa.

Uso:
    python3 _build/fig_candidates.py --chapter 19
    python3 _build/fig_candidates.py --all
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_build"))
from figtool import norm_number  # noqa: E402

OCR = ROOT.parent / "Anatopato" / "Capitulos" / "ocr"
OUT = ROOT / "_build" / "figures" / "cand"
PAGES = json.loads((ROOT / "_build" / "manifest.json").read_text(encoding="utf-8"))["pages"]


def page_range(chapter: int) -> tuple[int, int]:
    page = next(p for p in PAGES if p["kind"] == "chapter" and p["num"] == chapter)
    lo, _, hi = str(page["printed"]).partition("-")
    return int(lo), int(hi or lo)


def pages(chapter: int) -> list[tuple[int, str]]:
    text = (OCR / f"Cap{chapter:02d}.md").read_text(encoding="utf-8")
    parts = re.split(r"<!-- ===== Pagina impresa (\d+) \(PDF cap \d+\) ===== -->", text)
    return [(int(parts[i]), parts[i + 1]) for i in range(1, len(parts), 2) if parts[i + 1].strip()]


def captions(chapter: int) -> list[dict]:
    lo, hi = page_range(chapter)
    found: dict[str, dict] = {}
    for page, text in pages(chapter):
        for m in re.finditer(r"Figura\s*[.:]?\s*([I1l0-9]{1,2})\s*(\d{0,2})\s*[.,]\s*([I1l0-9]{1,2})", text):
            raw = m.group(0)
            number = norm_number(raw)
            if not number:
                continue
            prefix = int(number.split(".")[0])
            if prefix != chapter:
                continue
            start = m.start()
            snippet = " ".join(text[start:start + 420].split())
            # La leyenda termina antes de la página siguiente; recortar en el
            # primer "Figura" posterior o en un marcador de sección.
            snippet = re.split(r"\sFigura\s+[I1l0-9]", snippet)[0]
            snippet = snippet[:360].strip()
            if number not in found or len(snippet) > len(found[number]["caption"]):
                found[number] = {"number": number, "page": page, "caption": snippet}
    return sorted(found.values(), key=lambda x: (int(x["number"].split(".")[0]), int(x["number"].split(".")[1])))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    chapters = list(range(1, 27)) if args.all else [args.chapter]
    if not all(chapters):
        ap.error("Indica --chapter N o --all")
    OUT.mkdir(parents=True, exist_ok=True)
    for chapter in chapters:
        items = captions(chapter)
        path = OUT / f"cap{chapter:02d}.json"
        path.write_text(json.dumps({"chapter": chapter, "figures": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Cap{chapter:02d}: {len(items)} figuras -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
