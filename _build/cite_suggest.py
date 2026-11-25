#!/usr/bin/env python3
"""Genera citas candidatas por bloque para los resúmenes del Certamen 1.

No modifica los resúmenes: escribe una copia de trabajo con una cita base y un
JSON con las páginas candidatas para que un revisor las confirme contra el OCR.

Uso:
    python3 _build/cite_suggest.py --chapter 1
    python3 _build/cite_suggest.py --all
"""
import argparse
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANATOPATO = ROOT.parent / "Anatopato"
RES = ANATOPATO / "Capitulos" / "resumenes"
OCR = ANATOPATO / "Capitulos" / "ocr"
WORK = ROOT / "_build" / "cites" / "work"
CAND = ROOT / "_build" / "cites" / "cand"
DEC = ROOT / "_build" / "cites" / "decisions"
FINAL = ROOT / "_build" / "cites" / "final"
PAGES = json.loads((ROOT / "_build" / "manifest.json").read_text(encoding="utf-8"))["pages"]

STOP = set(
    "de la el los las un una unos unas y o u que en con por para del al se su sus "
    "es son como mas menos no ni a e the of to and in on for with".split()
)


def norm(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.findall(r"[a-z0-9]+", text)


def tokens(text: str) -> list[str]:
    return [w for w in norm(text) if len(w) > 2 and w not in STOP]


def page_range(chapter: int) -> tuple[int, int]:
    page = next(
        p for p in PAGES if p["kind"] == "chapter" and p["num"] == chapter
    )
    lo, _, hi = str(page["printed"]).partition("-")
    return int(lo), int(hi or lo)


def load_pages(chapter: int) -> list[dict]:
    text = (OCR / f"Cap{chapter:02d}.md").read_text(encoding="utf-8")
    parts = re.split(r"<!-- ===== Pagina impresa (\d+) \(PDF cap \d+\) ===== -->", text)
    pages = []
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        if not body.strip():
            continue
        pages.append({"page": int(parts[i]), "text": body, "tokens": tokens(body)})
    return pages


class Index:
    def __init__(self, pages: list[dict]):
        self.pages = pages
        df = Counter()
        for p in pages:
            df.update(set(p["tokens"]))
        n = len(pages)
        self.idf = {t: math.log((n + 1) / (df[t] + 1)) + 1 for t in df}

    def vec(self, toks: list[str]) -> dict[str, float]:
        count = Counter(toks)
        return {t: (1 + math.log(n)) * self.idf.get(t, 1) for t, n in count.items()}

    def cosine(self, a: dict, b: dict) -> float:
        if not a or not b:
            return 0.0
        dot = sum(v * b.get(t, 0) for t, v in a.items())
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    def best(self, query: str, top: int = 3) -> list[dict]:
        qv = self.vec(tokens(query))
        scored = []
        for p in self.pages:
            pv = self.vec(p["tokens"])
            scored.append((self.cosine(qv, pv), p))
        scored.sort(key=lambda x: -x[0])
        out = []
        for score, p in scored[:top]:
            out.append(
                {
                    "page": p["page"],
                    "score": round(score, 3),
                    "snippet": self.snippet(query, p["text"]),
                }
            )
        return out

    def snippet(self, query: str, page_text: str, limit: int = 360) -> str:
        q = set(tokens(query))
        sentences = re.split(r"(?<=[.;:])\s+", page_text)
        best = ""
        best_hits = -1
        for s in sentences:
            hits = len(q & set(tokens(s)))
            if hits > best_hits:
                best_hits = hits
                best = s
        best = " ".join(best.split())
        return best[:limit]


CITE_RE = re.compile(r"\s*\[p\.\s*\d[0-9,\-\s]*\]")
TABLE_SOURCE_RE = re.compile(r"^Fuente:\s*\[p\.")


def strip_md(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"(?<!\w)[*_](?=\S)|(?<=\S)[*_](?!\w)", "", text)
    return " ".join(text.split())


def parse_blocks(lines: list[str]) -> list[dict]:
    """Bloques citables: párrafos, ítems de lista y tablas."""
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("#"):
            i += 1
            continue
        if stripped == "---":
            i += 1
            continue
        if stripped.startswith("Fuente: [p."):
            i += 1
            continue
        if stripped.startswith("|"):
            start = i
            while i < n and lines[i].strip().startswith("|"):
                i += 1
            blocks.append({"kind": "table", "start": start, "end": i - 1})
            continue
        if re.match(r"^\s*(?:[-*+]|\d+\.)\s+", line):
            start = i
            i += 1
            while i < n:
                nxt = lines[i]
                if not nxt.strip():
                    break
                if re.match(r"^\s*(?:[-*+]|\d+\.)\s+", nxt):
                    break
                if nxt.strip().startswith(("#", "|", "---")):
                    break
                if not nxt.startswith((" ", "\t")):
                    break
                i += 1
            blocks.append({"kind": "item", "start": start, "end": i - 1})
            continue
        start = i
        i += 1
        while i < n:
            nxt = lines[i]
            if not nxt.strip():
                break
            if re.match(r"^\s*(?:[-*+]|\d+\.)\s+", nxt):
                break
            if nxt.strip().startswith(("#", "|", "---")):
                break
            i += 1
        blocks.append({"kind": "paragraph", "start": start, "end": i - 1})
    return blocks


def block_text(lines: list[str], block: dict) -> str:
    return "\n".join(lines[block["start"]:block["end"] + 1])


def insert_cite(line: str, cite: str) -> str:
    raw = line.rstrip("\r\n")
    ending = line[len(raw):]
    s = raw.rstrip()
    if s and s[-1] in ".!?":
        return s[:-1] + f" {cite}" + s[-1] + ending
    return s + f" {cite}" + ending


def table_source(pages: list[int]) -> str:
    lo, hi = min(pages), max(pages)
    return f"Fuente: [p. {lo}]." if lo == hi else f"Fuente: [p. {lo}-{hi}]."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    chapters = list(range(1, 11)) if args.all else [args.chapter]
    if not all(chapters):
        ap.error("Indica --chapter N o --all")

    WORK.mkdir(parents=True, exist_ok=True)
    CAND.mkdir(parents=True, exist_ok=True)
    DEC.mkdir(parents=True, exist_ok=True)

    for chapter in chapters:
        lo, hi = page_range(chapter)
        pages = load_pages(chapter)
        idx = Index(pages)
        src = RES / f"Cap{chapter:02d}.md"
        text = src.read_text(encoding="utf-8")
        lines = text.splitlines()
        blocks = parse_blocks(lines)

        heading = ""
        records = []
        out = []
        cursor = 0
        for b, block in enumerate(blocks):
            # Conservar todo el texto previo al bloque.
            while cursor < block["start"]:
                out.append(lines[cursor])
                cursor += 1
            raw = block_text(lines, block)
            for line in lines[block["start"]:block["end"] + 1]:
                if line.strip().startswith("#"):
                    heading = line.strip("# ").strip()
            if block["kind"] == "table":
                cands = idx.best((heading + " " + raw)[:4000], top=4)
                chosen = sorted({c["page"] for c in cands[:2]})
                # Insertar o reemplazar la línea Fuente inmediatamente después.
                while cursor <= block["end"]:
                    out.append(lines[cursor])
                    cursor += 1
                nxt = cursor
                if nxt < len(lines) and TABLE_SOURCE_RE.match(lines[nxt].strip()):
                    out.append(table_source(chosen))
                    cursor = nxt + 1
                elif nxt < len(lines) and not lines[nxt].strip():
                    out.append("")
                    out.append(table_source(chosen))
                    cursor = nxt + 1
                else:
                    out.append("")
                    out.append(table_source(chosen))
                records.append(
                    {
                        "id": b,
                        "kind": "table",
                        "heading": heading,
                        "text": strip_md(raw)[:1200],
                        "candidates": cands,
                        "baseline": table_source(chosen),
                    }
                )
                continue

            cands = idx.best(heading + " " + strip_md(raw), top=3)
            chosen = cands[0]["page"] if cands else lo
            cite = f"[p. {chosen}]"
            # Cita base antes del punto final del último renglón.
            insert_at = block["end"]
            for j in range(block["start"], block["end"] + 1):
                out.append(lines[j] if j != insert_at else insert_cite(lines[j], cite))
            cursor = block["end"] + 1
            records.append(
                {
                    "id": b,
                    "kind": block["kind"],
                    "heading": heading,
                    "text": strip_md(raw)[:1200],
                    "candidates": cands,
                    "baseline": cite,
                }
            )

        while cursor < len(lines):
            out.append(lines[cursor])
            cursor += 1

        (WORK / f"cap{chapter:02d}.md").write_text("\n".join(out) + "\n", encoding="utf-8")
        (CAND / f"cap{chapter:02d}.json").write_text(
            json.dumps(
                {"chapter": chapter, "range": [lo, hi], "blocks": records},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        decisions = {}
        for r in records:
            m = re.search(r"\[p\.\s*([0-9][0-9,\-\s]*)\]", r["baseline"])
            decisions[str(r["id"])] = m.group(1).strip() if m else ""
        (DEC / f"cap{chapter:02d}.json").write_text(
            json.dumps({"chapter": chapter, "cites": decisions}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            f"Cap{chapter:02d}: {len(blocks)} bloques, "
            f"{sum(1 for r in records if r['kind'] != 'table')} citas base, "
            f"{sum(1 for r in records if r['kind'] == 'table')} tablas"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
