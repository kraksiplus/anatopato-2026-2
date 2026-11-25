#!/usr/bin/env python3
"""Inventario de figuras por capítulo a partir del OCR y del resumen."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OCR = ROOT.parent / "Anatopato" / "Capitulos" / "ocr"
RES = ROOT.parent / "Anatopato" / "Capitulos" / "resumenes"
OUT = ROOT / "_build" / "figures" / "inventory"

FIG_RE = re.compile(r"Figura\s+([I1l0-9]{1,2})\s*(\d{0,2})\s*[.,]\s*(\d{1,2})", re.I)


def norm(match) -> str:
    prefix = (match.group(1) + match.group(2)).replace("I", "1").replace("l", "1")
    return f"{int(prefix)}.{int(match.group(3))}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for cap in range(1, 19):
        ocr = OCR / f"Cap{cap:02d}.md"
        res = RES / f"Cap{cap:02d}.md"
        if not ocr.exists() or not res.exists():
            print(f"Falta Cap{cap:02d}")
            continue
        text = ocr.read_text(encoding="utf-8")
        parts = re.split(r"<!-- ===== Pagina impresa (\d+) \(PDF cap (\d+)\) ===== -->", text)
        found: dict[str, dict] = {}
        for i in range(1, len(parts), 3):
            printed, body = int(parts[i]), parts[i + 2]
            for m in FIG_RE.finditer(body):
                num = norm(m)
                if num in found:
                    continue
                start = max(0, m.start() - 5)
                end = min(len(body), m.start() + 320)
                snippet = " ".join(body[start:end].split())
                found[num] = {"number": num, "page": printed, "caption": snippet}
        figs = sorted(found.values(), key=lambda x: [int(n) for n in x["number"].split(".")])
        nums = [int(f["number"].split(".")[1]) for f in figs]
        missing = [n for n in range(1, max(nums) + 1) if n not in nums] if nums else []
        headings = re.findall(r"^## (.+)$", res.read_text(encoding="utf-8"), re.M)
        data = {
            "chapter": cap,
            "headings": headings,
            "figures": figs,
            "missing": missing,
            "note": "caption es un recorte OCR para elegir; la leyenda final se redacta desde la imagen y el texto.",
        }
        out = OUT / f"cap{cap:02d}.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Cap{cap:02d}: {len(figs)} figuras, faltan {missing}")


if __name__ == "__main__":
    main()
