#!/usr/bin/env python3
"""Extrae figuras seleccionadas de los PDFs escaneados de Robbins.

Se ejecuta con el venv de OCR:
    /home/kraksiplus/Documents/Universidad/2026-2/Anatopato/.ocr/venv/bin/python \
        _build/figtool.py --chapter 11

Entrada: _build/figures/in/cap11.json
Salida:  assets/fig/cap11/fig-11-01.webp
         _build/figures/out/cap11.json
         /tmp/opencode/anatopato_fig/preview/fig-11-01.png
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageOps
from rapidocr_onnxruntime import RapidOCR

ROOT = Path(__file__).resolve().parent.parent
ANATOPATO = ROOT.parent / "Anatopato"
MODELS = ANATOPATO / ".ocr" / "models" / "latin"
PDFS = ANATOPATO / "Capitulos"
PREVIEW = Path("/tmp/opencode/anatopato_fig/preview")
DPI = 200

FIG_RE = re.compile(r"Fig[uú]ra\s+([I1l0-9]{1,2})\s*(\d{0,2})\s*[.,]\s*([I1l0-9]{1,2})", re.I)

_engine = None


def engine():
    global _engine
    if _engine is None:
        _engine = RapidOCR(
            rec_model_path=str(MODELS / "inference.onnx"),
            rec_keys_path=str(MODELS / "latin_dict_full.txt"),
        )
    return _engine


def chapter_pdf(chapter: int) -> Path:
    hits = sorted(PDFS.glob(f"Cap{chapter:02d} -*.pdf"))
    if not hits:
        raise SystemExit(f"No encontré el PDF del capítulo {chapter:02d}")
    return hits[0]


def is_figure_start(text: str) -> bool:
    plain = "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )
    return plain.strip().lower().startswith("figura")


def norm_number(raw: str) -> str | None:
    """Convierte 'Figura I 1.10' o 'Figura 11.10' al número '11.10'."""
    m = FIG_RE.search(raw)
    if not m:
        return None
    prefix = (m.group(1) + m.group(2)).replace("I", "1").replace("l", "1")
    suffix = m.group(3).replace("I", "1").replace("l", "1")
    return f"{int(prefix)}.{int(suffix)}"


def render_page(pdf: pdfium.PdfDocument, page_no: int) -> np.ndarray:
    page = pdf[page_no - 1]
    bitmap = page.render(scale=DPI / 72.0)
    try:
        pil = bitmap.to_pil()
    except AttributeError:
        arr = bitmap.to_numpy()
        if arr.ndim == 2:
            pil = Image.fromarray(arr)
        else:
            pil = Image.fromarray(arr[:, :, :3])
    return np.array(pil.convert("RGB"))


def ocr_items(img: np.ndarray) -> list[dict]:
    result, _ = engine()(img)
    items = []
    for box, text, score in result or []:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        items.append(
            {
                "x0": float(min(xs)),
                "x1": float(max(xs)),
                "y0": float(min(ys)),
                "y1": float(max(ys)),
                "text": text.strip(),
                "score": float(score),
            }
        )
    return items


def number_matches(got: str | None, target: str) -> bool:
    if not got:
        return False
    if got == target:
        return True
    # El OCR a veces agrega o pierde un "1" al final del número.
    if got.startswith(target) and len(got) == len(target) + 1 and got.endswith("1"):
        return True
    if target.startswith(got) and len(target) == len(got) + 1 and target.endswith("1"):
        return True
    return False


def find_caption(items: list[dict], number: str) -> dict | None:
    target = number.replace(" ", "")
    hits = [it for it in items if number_matches(norm_number(it["text"]), target)]
    if not hits:
        return None
    # La leyenda real parte con "Figura" y es larga. Una referencia en el
    # cuerpo ("fig. 11.10") es corta y no debe usarse como ancla.
    long_hits = [
        it for it in hits
        if is_figure_start(it["text"]) and len(it["text"]) > 30
    ]
    pool = long_hits or hits
    return max(pool, key=lambda x: x["y0"])


def header_bottom(items: list[dict], h: int, w: int) -> float:
    # La cabecera es una línea ancha en el borde superior. No confundirla con
    # las etiquetas de la figura, que son cortas.
    top = [
        it for it in items
        if it["y0"] < 0.05 * h
        and (it["x1"] - it["x0"]) > 0.22 * w
        and norm_number(it["text"]) is None
        and not is_figure_start(it["text"])
    ]
    if top:
        return min(0.09 * h, max(it["y1"] for it in top) + 5)
    return 0.055 * h


def body_bottom(items: list[dict], caption: dict, page_w: int, header_y: float,
                col_left: float, col_right: float, full: bool) -> float:
    """Última línea de texto de cuerpo justificada antes de la figura."""
    floor = max(header_y, 0)
    if full:
        mid = (col_left + col_right) / 2
        zones = [
            (col_left, col_right),
            (col_left, mid),
            (mid, col_right),
        ]
    else:
        zones = [(col_left, col_right)]

    candidates = []
    for it in items:
        if it["y1"] > caption["y0"] - 6 or it["y1"] < floor:
            continue
        for L, R in zones:
            if (abs(it["x0"] - L) < 18 and abs(it["x1"] - R) < 30
                    and (it["x1"] - it["x0"]) > 0.35 * (R - L)
                    and (it["y1"] - it["y0"]) < 170):
                candidates.append(it)
                break
    if not candidates:
        return floor

    last = max(candidates, key=lambda x: x["y1"])
    bottom = last["y1"]
    L, R = min(zones, key=lambda z: abs(z[0] - last["x0"]))
    # Extender por la última línea corta del mismo párrafo.
    for it in sorted(items, key=lambda x: x["y0"]):
        if it["y0"] < bottom - 1 or it["y0"] > caption["y0"] - 6:
            continue
        if abs(it["x0"] - L) < 18 and it["x1"] <= R + 12 and (it["y0"] - bottom) < 34:
            bottom = max(bottom, it["y1"])
    return bottom


def find_top(img: np.ndarray, body_y: float, caption_y: float,
             x0: float, x1: float) -> float:
    """Primer trazo de tinta después del hueco que sigue al texto de cuerpo."""
    gray = np.array(ImageOps.grayscale(Image.fromarray(img)))
    top_scan = max(0, int(body_y) + 2)
    bottom_scan = max(top_scan + 10, int(caption_y) - 4)
    if bottom_scan - top_scan < 20:
        return float(top_scan)
    strip = gray[top_scan:bottom_scan, int(x0):int(x1)]
    ink = (strip < 235).mean(axis=1)
    white = ink < 0.006
    run = 0
    gap_start = None
    for i, is_white in enumerate(white):
        if is_white:
            if run == 0:
                gap_start = i
            run += 1
        else:
            if run >= 4 and gap_start is not None:
                return float(top_scan + i - 1)
            run = 0
            gap_start = None
    return float(top_scan)


def ink_x(img: np.ndarray, y0: float, y1: float, x0: float, x1: float) -> tuple[int, int]:
    gray = np.array(ImageOps.grayscale(Image.fromarray(img)))
    strip = gray[max(0, int(y0)):int(y1), max(0, int(x0)):int(x1)]
    ys, xs = np.where(strip < 235)
    if len(xs) == 0:
        return int(x0), int(x1)
    return max(0, int(x0) + int(xs.min()) - 10), min(img.shape[1], int(x0) + int(xs.max()) + 10)


def art_runs(img: np.ndarray, items: list[dict], header_y: float) -> list[dict]:
    """Regiones de tinta que no son texto: la figura, no la prosa."""
    h, w = img.shape[:2]
    gray = np.array(ImageOps.grayscale(Image.fromarray(img)))
    mask = gray < 235
    for it in items:
        x0 = max(0, int(it["x0"]) - 2)
        x1 = min(w, int(it["x1"]) + 2)
        y0 = max(0, int(it["y0"]) - 2)
        y1 = min(h, int(it["y1"]) + 2)
        mask[y0:y1, x0:x1] = False

    y_min = max(0, int(header_y))
    y_max = min(h, int(0.94 * h))
    cols = {
        "left": (int(0.05 * w), int(0.49 * w)),
        "right": (int(0.51 * w), int(0.95 * w)),
        "full": (int(0.05 * w), int(0.95 * w)),
    }
    runs = []
    for name, (x0, x1) in cols.items():
        if x1 <= x0:
            continue
        density = mask[y_min:y_max, x0:x1].mean(axis=1)
        active = density > 0.002
        idx = np.where(active)[0]
        if len(idx) == 0:
            continue
        blocks = []
        start = prev = int(idx[0])
        for i in idx[1:]:
            i = int(i)
            if i - prev > 15:
                blocks.append((start, prev))
                start = i
            prev = i
        blocks.append((start, prev))
        for a, b in blocks:
            if b - a < 100:
                continue
            ya, yb = y_min + a, y_min + b
            sub = mask[ya:yb + 1, x0:x1]
            ys, xs = np.where(sub)
            if len(xs) == 0:
                continue
            rx0 = max(0, x0 + int(xs.min()) - 22)
            rx1 = min(w, x0 + int(xs.max()) + 22)
            runs.append({
                "col": name, "x0": rx0, "x1": rx1,
                "y0": max(0, ya - 12), "y1": min(h, yb + 12),
                "height": yb - ya, "width": rx1 - rx0,
            })
    return runs


def pick_run(runs: list[dict], caption: dict, w: int) -> dict | None:
    cap_full = (caption["x1"] - caption["x0"]) > 0.55 * w
    cap_col = "left" if (caption["x0"] + caption["x1"]) / 2 < w / 2 else "right"
    same = [r for r in runs if r["col"] == ("full" if cap_full else cap_col)]

    above = [r for r in same if -20 <= caption["y0"] - r["y1"] < 260]
    if above:
        return min(above, key=lambda r: caption["y0"] - r["y1"])

    if not cap_full:
        opposite = "right" if cap_col == "left" else "left"
        side = [
            r for r in runs
            if r["col"] == opposite
            and r["y0"] < caption["y1"] + 80
            and r["y1"] > caption["y0"] - 80
        ]
        if side:
            return max(side, key=lambda r: r["height"] * r["width"])

    below = [r for r in same if -20 <= r["y0"] - caption["y1"] < 260]
    if below:
        return min(below, key=lambda r: r["y0"] - caption["y1"])

    pool = same or runs
    return min(pool, key=lambda r: abs(r["y0"] - caption["y0"])) if pool else None


def page_captions(items: list[dict]) -> list[dict]:
    """Leyendas completas de la página, ordenadas de arriba abajo."""
    by_num: dict[str, dict] = {}
    for it in items:
        num = norm_number(it["text"])
        if not num:
            continue
        if not is_figure_start(it["text"]):
            continue
        if len(it["text"]) < 30:
            continue
        if num not in by_num or it["y0"] < by_num[num]["y0"]:
            by_num[num] = it
    return sorted(by_num.values(), key=lambda x: x["y0"])


def crop_figure(img: np.ndarray, fig: dict) -> tuple[np.ndarray, dict]:
    h, w = img.shape[:2]
    items = ocr_items(img)
    number = fig["number"]
    caption = find_caption(items, number)
    if caption is None:
        raise RuntimeError(f"No encontré la leyenda de la figura {number}")

    full = (caption["x1"] - caption["x0"]) > 0.55 * w
    cap_col = "left" if (caption["x0"] + caption["x1"]) / 2 < w / 2 else "right"
    header_y = header_bottom(items, h, w)
    footer_y = 0.95 * h
    runs = art_runs(img, items, header_y)
    if not runs:
        raise RuntimeError(f"No encontré tinta de figura para {number}")

    # ¿La figura está al lado de la leyenda, como en la 11.10? Solo puede
    # pasar con leyenda de columna; una leyenda a todo el ancho es de figura
    # a todo el ancho.
    opposite = "right" if cap_col == "left" else "left"
    side = [
        r for r in runs
        if r["col"] == opposite
        and r["y0"] < caption["y1"] + 60
        and r["y1"] > caption["y0"] - 60
        and r["height"] > 120
    ]
    same_near = [
        r for r in runs
        if r["col"] == cap_col
        and r["height"] > 150
        and r["y0"] < caption["y1"] + 300
        and r["y1"] > caption["y0"] - 300
    ]
    side_by_side = (not full) and bool(side) and not same_near
    if side_by_side:
        col = opposite
        window = (header_y, footer_y)
        figure_above = False
    else:
        caps = page_captions(items)
        pos = next((i for i, c in enumerate(caps) if abs(c["y0"] - caption["y0"]) < 3), None)
        prev = caps[pos - 1] if pos is not None and pos > 0 else None
        nxt = caps[pos + 1] if pos is not None and pos + 1 < len(caps) else None
        col = "full" if full else cap_col
        same = [r for r in runs if r["col"] == col]
        above = [
            r for r in same
            if r["y1"] <= caption["y0"] + 20
            and r["y1"] > (prev["y1"] + 5 if prev else header_y)
        ]
        below = [
            r for r in same
            if r["y0"] >= caption["y1"] - 20
            and r["y0"] < (nxt["y0"] - 5 if nxt else footer_y)
        ]
        gap_above = caption["y0"] - max((r["y1"] for r in above), default=-10**9)
        gap_below = min((r["y0"] for r in below), default=10**9) - caption["y1"]
        if above and (not below or gap_above <= gap_below):
            figure_above = True
            window = (prev["y1"] + 5 if prev else header_y, caption["y0"] - 5)
        elif below:
            figure_above = False
            window = (caption["y1"] + 5, nxt["y0"] - 5 if nxt else footer_y)
        else:
            figure_above = caption["y0"] >= 0.25 * h
            if figure_above:
                window = (prev["y1"] + 5 if prev else header_y, caption["y0"] - 5)
            else:
                window = (caption["y1"] + 5, nxt["y0"] - 5 if nxt else footer_y)

    pool = [
        r for r in runs
        if r["col"] == col and r["y1"] > window[0] and r["y0"] < window[1]
    ]
    if not pool:
        pool = [r for r in runs if r["col"] == col] or runs

    if side_by_side:
        sel = pool
    else:
        # Ancla: la región más cercana a la leyenda; luego se unen las
        # partes de la misma figura que quedaron separadas por blanco.
        if figure_above:
            anchor = min(pool, key=lambda r: abs(caption["y0"] - r["y1"]))
        else:
            anchor = min(pool, key=lambda r: abs(r["y0"] - caption["y1"]))
        lo, hi = anchor["y0"] - 230, anchor["y1"] + 230
        sel = [r for r in pool if r["y1"] >= lo and r["y0"] <= hi]

    y0 = max(window[0], min(r["y0"] for r in sel) - 8)
    y1 = min(window[1], max(r["y1"] for r in sel) + 8)

    # Recuperar las etiquetas de la figura que el OCR descontó como texto:
    # subir hasta el final del último párrafo justificado.
    if not side_by_side:
        if figure_above:
            # Figura arriba de la leyenda: la leyenda fija el borde inferior.
            body_y = body_bottom(items, {"y0": anchor["y0"]}, w, header_y,
                                 caption["x0"], caption["x1"], full)
            if body_y > header_y + 10:
                y0 = max(window[0], min(y0, body_y + 6))
            elif y0 - header_y < 250:
                y0 = header_y
            y1 = min(window[1], caption["y0"] - 4)
        else:
            # Figura debajo de la leyenda: la leyenda fija el borde superior.
            y0 = max(window[0], caption["y1"] + 5)
            if footer_y - y1 < 250:
                y1 = footer_y
    else:
        y0 = header_y if y0 - header_y < 250 else y0
        y1 = footer_y if footer_y - y1 < 250 else y1

    if col == "full":
        x0, x1 = int(0.05 * w), int(0.95 * w)
    elif col == "left":
        x0, x1 = int(0.045 * w), int(0.512 * w)
    else:
        x0, x1 = int(0.493 * w), int(0.955 * w)

    # Texto vertical de copyright en el margen izquierdo.
    guard = 0
    for it in items:
        tw = it["x1"] - it["x0"]
        th = it["y1"] - it["y0"]
        if th > 2 * tw and it["x0"] < 0.12 * w and it["x1"] < 0.12 * w:
            guard = max(guard, it["x1"] + 4)
    if guard:
        x0 = max(x0, int(guard))

    # Usar el canal blanco entre columnas si existe.
    if col != "full":
        gray = np.array(ImageOps.grayscale(Image.fromarray(img)))
        gx0, gx1 = int(0.45 * w), int(0.55 * w)
        strip = gray[int(header_y):int(footer_y), gx0:gx1]
        dens = (strip < 235).mean(axis=0)
        white = dens < 0.008
        best = None
        start = None
        for i, v in enumerate(white):
            if v and start is None:
                start = i
            if (not v or i == len(white) - 1) and start is not None:
                end = i if not v else i + 1
                if end - start >= 8:
                    if best is None or end - start > best[1] - best[0]:
                        best = (start, end)
                start = None
        if best:
            gut_left = gx0 + best[0]
            gut_right = gx0 + best[1]
            if col == "left":
                x1 = min(x1, int(gut_left) + 2)
            else:
                x0 = max(x0, int(gut_right) - 2)

    # Override manual: [x0, y0, x1, y1] en píxeles a 200 DPI.
    if fig.get("bbox"):
        x0, y0, x1, y1 = [int(v) for v in fig["bbox"]]

    crop = img[int(y0):int(y1), int(x0):int(x1)]
    info = {
        "caption_bbox": [round(caption["x0"]), round(caption["y0"]), round(caption["x1"]), round(caption["y1"])],
        "bbox": [int(x0), int(y0), int(x1), int(y1)],
        "col": col,
        "side_by_side": side_by_side,
        "full_width": bool(full),
        "width": int(crop.shape[1]),
        "height": int(crop.shape[0]),
    }
    return crop, info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--in", dest="inp", default=None)
    ap.add_argument("--out", dest="out", default=None)
    args = ap.parse_args()

    chapter = args.chapter
    inp = Path(args.inp) if args.inp else ROOT / "_build" / "figures" / "in" / f"cap{chapter:02d}.json"
    out = Path(args.out) if args.out else ROOT / "_build" / "figures" / "out" / f"cap{chapter:02d}.json"
    data = json.loads(inp.read_text(encoding="utf-8"))
    pdf_path = Path(data.get("pdf") or chapter_pdf(chapter))
    printed_start = int(data.get("printed_start") or 0)
    if not printed_start:
        raise SystemExit("Falta printed_start en el JSON de entrada")

    doc = pdfium.PdfDocument(str(pdf_path))
    results = []
    PREVIEW.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    img_dir = ROOT / "assets" / "fig" / f"cap{chapter:02d}"
    img_dir.mkdir(parents=True, exist_ok=True)

    for fig in data["figures"]:
        number = fig["number"].replace(" ", "")
        page = int(fig.get("page") or 0)
        if not page:
            raise SystemExit(f"Falta page para la figura {number}")
        pdf_page = page - printed_start + 1
        if not (1 <= pdf_page <= len(doc)):
            raise SystemExit(f"Página fuera de rango para {number}: {pdf_page}")
        img = render_page(doc, pdf_page)
        try:
            crop, info = crop_figure(img, {**fig, "number": number})
        except RuntimeError as exc:
            print(f"ERROR {number}: {exc}", file=sys.stderr)
            results.append({"number": number, "page": page, "error": str(exc)})
            continue

        pil = Image.fromarray(crop)
        if pil.width > 1600:
            ratio = 1600 / pil.width
            pil = pil.resize((1600, round(pil.height * ratio)), Image.LANCZOS)
        slug = number.replace(".", "-")
        webp = img_dir / f"fig-{slug}.webp"
        png = PREVIEW / f"fig-{slug}.png"
        pil.save(webp, "WEBP", quality=85, method=6)
        pil.save(png, "PNG")
        rec = {
            "number": number,
            "page": page,
            "pdf_page": pdf_page,
            "image": str(webp.relative_to(ROOT)),
            "width": pil.width,
            "height": pil.height,
            **info,
        }
        results.append(rec)
        print(f"{number} p.{page} -> {webp.relative_to(ROOT)} {pil.width}x{pil.height} bbox={info['bbox']}")

    out.write_text(json.dumps({"chapter": chapter, "figures": results}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"Escrito {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
