#!/usr/bin/env python3
"""Corrige secciones H3 y anclajes de las selecciones de figuras."""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
SEL = BUILD / "figures" / "sel"
RES = ROOT.parent / "Anatopato" / "Capitulos" / "resumenes"


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def norm(text: str) -> str:
    text = strip_accents(text).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def clean_md(md: str) -> str:
    md = re.sub(r"\[p\.\s*[0-9][0-9,\-\s]*?\]", " ", md)
    md = md.replace("**", "").replace("__", "").replace("`", "")
    md = re.sub(r"(?<!\w)[*_](?=\S)|(?<=\S)[*_](?!\w)", "", md)
    return re.sub(r"\s+", " ", md).strip()


def headings(md: str):
    current = None
    h2 = []
    mapping = {}
    norm_map = {}
    for line in md.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if not m:
            continue
        level, title = len(m.group(1)), m.group(2).strip()
        if level == 2:
            current = title
            h2.append(title)
        if current:
            mapping.setdefault(title, current)
            norm_map.setdefault(norm(title), current)
    return h2, mapping, norm_map


STOP = set("para como con que los las del por una uno sus mas más los se su al es en la el de y o a".split())


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{4,}", norm(text)) if w not in STOP}


def paragraphs(md: str):
    out = []
    for block in re.split(r"\n\s*\n", md):
        block = block.strip()
        if not block or block.startswith("#") or block.startswith("|"):
            continue
        text = clean_md(block)
        if len(text) > 40:
            out.append(text)
    return out


def fix_anchor(anchor: str, plain: str, paras: list[str]) -> str:
    if anchor in plain:
        return anchor
    low = plain.lower()
    pos = low.find(anchor.lower())
    if pos != -1:
        return plain[pos:pos + len(anchor)]

    best = max(paras, key=lambda p: len(words(p) & words(anchor)), default="")
    if not best:
        return ""
    # Elegir una frase exacta del párrafo cercana a las palabras del ancla.
    tokens = best.split()
    key = words(anchor)
    center = 0
    for i, tok in enumerate(tokens):
        if words(tok) & key:
            center = i
            break
    start = max(0, center - 4)
    end = min(len(tokens), start + 10)
    phrase = " ".join(tokens[start:end]).strip(" .,;:")
    if len(phrase) < 15:
        phrase = " ".join(tokens[:10]).strip(" .,;:")
    return phrase


def main() -> None:
    changed = []
    for cap in range(1, 19):
        sel_path = SEL / f"cap{cap:02d}.json"
        if not sel_path.exists():
            continue
        data = json.loads(sel_path.read_text(encoding="utf-8"))
        md = (RES / f"Cap{cap:02d}.md").read_text(encoding="utf-8")
        plain = clean_md(md)
        h2, mapping, norm_map = headings(md)
        h2_norm = {norm(x): x for x in h2}
        paras = paragraphs(md)

        for fig in data["figures"]:
            sec = fig.get("section", "")
            if sec not in h2:
                mapped = mapping.get(sec) or norm_map.get(norm(sec))
                if not mapped:
                    mapped = max(h2, key=lambda x: len(words(x) & words(sec)), default=h2[0])
                fig["section"] = mapped
                changed.append(f"Cap{cap:02d} {fig['number']}: sección {sec!r} -> {mapped!r}")

            anchor = fig.get("after_text", "")
            fixed = fix_anchor(anchor, plain, paras)
            if cap == 18 and fig["number"] == "18.35":
                fixed = "fibrosis periductal"
            if fixed != anchor:
                if not fixed:
                    fixed = ""
                fig["after_text"] = fixed
                changed.append(f"Cap{cap:02d} {fig['number']}: ancla {anchor!r} -> {fixed!r}")

        sel_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    for c in changed:
        print(c)
    print(f"\n{len(changed)} cambios")


if __name__ == "__main__":
    main()
