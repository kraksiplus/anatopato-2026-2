#!/usr/bin/env python3
"""QA del sitio: HTML, anclas, enlaces, em dash y paridad con el Markdown."""
import json
import re
import sys
from pathlib import Path

from lxml import html

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
PAGES = json.loads((BUILD / "manifest.json").read_text(encoding="utf-8"))["pages"]
EMDASH = "\u2014"
errors = []
warnings = []


def load_figures(page_id: str) -> list:
    path = BUILD / "figures" / f"{page_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")).get("figures", [])
    return []


CREDITS = ROOT / "creditos.html"
CREDITS_IDS = set()
if CREDITS.exists():
    _cdoc = html.fromstring(CREDITS.read_text(encoding="utf-8"))
    CREDITS_IDS = {e.get("id") for e in _cdoc.xpath("//*[@id]")}


def count_md(md: str, pattern: str) -> int:
    return len(re.findall(pattern, md, re.M))


def check_page(page: dict) -> None:
    path = ROOT / page["file"]
    if not path.exists():
        errors.append(f"{page['file']}: no existe")
        return
    raw = path.read_text(encoding="utf-8")
    doc = html.fromstring(raw)

    ids = [e.get("id") for e in doc.xpath("//*[@id]")]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errors.append(f"{page['file']}: ids duplicados {sorted(dup)}")

    toc = [a.get("href")[1:] for a in doc.xpath('//ul[contains(@class,"toc")]//a[starts-with(@href,"#")]')]
    missing = [t for t in toc if t not in ids]
    if missing:
        errors.append(f"{page['file']}: anclas del TOC sin destino {missing}")
    if not toc:
        errors.append(f"{page['file']}: TOC vacío")

    for href in doc.xpath("//a/@href"):
        if href.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = (path.parent / href.split("#")[0]).resolve()
        if not target.exists():
            errors.append(f"{page['file']}: enlace roto {href}")

    figs_expected = load_figures(page["id"])
    fig_data_path = BUILD / "figures" / f"{page['id']}.json"
    atlas_only = False
    if fig_data_path.exists():
        atlas_only = bool(json.loads(fig_data_path.read_text(encoding="utf-8")).get("atlas_only"))
    fig_nodes = doc.xpath('//figure[contains(@class,"fig")]')
    if atlas_only:
        thumbs = doc.xpath('//section[@id="atlas"]//a[contains(@class,"fig-thumb")]')
        if len(thumbs) != len(figs_expected):
            errors.append(f"{page['file']}: atlas {len(thumbs)} vs JSON {len(figs_expected)}")
    else:
        if len(fig_nodes) != len(figs_expected):
            errors.append(f"{page['file']}: figuras HTML {len(fig_nodes)} vs JSON {len(figs_expected)}")
    seen_figs = set()
    for node in ([] if atlas_only else fig_nodes):
        fid = node.get("id") or ""
        if not fid:
            errors.append(f"{page['file']}: figura sin id")
        elif fid in seen_figs:
            errors.append(f"{page['file']}: figura repetida {fid}")
        seen_figs.add(fid)
        if not node.xpath("./figcaption"):
            errors.append(f"{page['file']}: figura {fid} sin leyenda")
        if not node.xpath("./figcaption//span[contains(@class,'fig-source')]"):
            errors.append(f"{page['file']}: figura {fid} sin fuente")
        imgs = node.xpath("./a[contains(@class,'fig-open')]/img")
        if not imgs:
            errors.append(f"{page['file']}: figura {fid} sin imagen")
        else:
            im = imgs[0]
            if not (im.get("alt") or "").strip():
                errors.append(f"{page['file']}: figura {fid} sin alt")
            if not im.get("width") or not im.get("height"):
                warnings.append(f"{page['file']}: figura {fid} sin width/height")
        for a in node.xpath("./figcaption//a[contains(@href,'creditos.html#')]"):
            frag = a.get("href").split("#", 1)[1]
            if frag not in CREDITS_IDS:
                errors.append(f"{page['file']}: crédito sin ancla {frag}")

    for img in doc.xpath("//img"):
        src = img.get("src") or ""
        if not src or src.startswith("data:"):
            continue
        target = (path.parent / src).resolve()
        if not target.exists():
            errors.append(f"{page['file']}: imagen rota {src}")

    for a in doc.xpath('//section[@id="atlas"]//a[contains(@class,"fig-thumb")]'):
        href = a.get("href") or ""
        if "#" not in href:
            continue
        rel, frag = href.split("#", 1)
        if not rel:
            continue
        target = (path.parent / rel).resolve()
        if target.exists():
            tdoc = html.parse(str(target))
            if not tdoc.xpath(f'//*[@id="{frag}"]'):
                errors.append(f"{page['file']}: ancla de atlas sin destino {href}")

    if not doc.xpath('//footer//a[contains(@href,"creditos.html")]'):
        errors.append(f"{page['file']}: footer sin enlace a créditos")

    if EMDASH in raw:
        errors.append(f"{page['file']}: contiene em dash")

    if "%%" in raw:
        errors.append(f"{page['file']}: placeholder sin reemplazar")

    md = (ROOT / page["source"]).resolve().read_text(encoding="utf-8")
    md_h2 = count_md(md, r"^## ")
    html_h2 = len(doc.xpath("//main//h2"))
    if page["kind"] == "manual":
        expected_cites = 0
    else:
        expected_cites = len(re.findall(r"\[p\.\s*\d", md))
    cites = len(doc.xpath('//span[contains(@class,"cite")]'))
    if page.get("cites") and expected_cites and cites == 0:
        errors.append(f"{page['file']}: sin citas")
    if page.get("cites") and expected_cites and abs(cites - expected_cites) > 2:
        warnings.append(f"{page['file']}: citas HTML {cites} vs MD {expected_cites}")

    print(
        f"{page['id']:<12} h2={html_h2:<3} md_h2={md_h2:<3} "
        f"citas={cites:<4} tablas={len(doc.xpath('//table')):<3} "
        f"img={len(doc.xpath('//img'))} ext={len(doc.xpath('//script[@src] | //link[@rel=\"stylesheet\"]'))}"
    )


def check_indexes() -> None:
    for rel in ["index.html", "c1/index.html", "c2/index.html", "creditos.html"]:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"{rel}: no existe")
            continue
        raw = path.read_text(encoding="utf-8")
        doc = html.fromstring(raw)
        if EMDASH in raw:
            errors.append(f"{rel}: contiene em dash")
        for href in doc.xpath("//a/@href"):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = (path.parent / href.split("#")[0]).resolve()
            if not target.exists():
                errors.append(f"{rel}: enlace roto {href}")
        if not doc.xpath("//h1"):
            errors.append(f"{rel}: sin h1")
        print(f"{rel:<16} enlaces={len(doc.xpath('//a'))} h1={len(doc.xpath('//h1'))}")


def main() -> int:
    for page in PAGES:
        check_page(page)
    check_indexes()
    expected = sum(len(load_figures(p["id"])) for p in PAGES if p["kind"] != "manual")
    if CREDITS.exists():
        cdoc = html.fromstring(CREDITS.read_text(encoding="utf-8"))
        rows = cdoc.xpath('//tr[@id]')
        if len(rows) != expected:
            errors.append(f"creditos.html: filas {len(rows)} vs figuras {expected}")
    else:
        errors.append("creditos.html: no existe")
    print()
    for w in warnings:
        print("AVISO:", w)
    for e in errors:
        print("ERROR:", e)
    if errors:
        print(f"\n{len(errors)} errores")
        return 1
    print(f"OK: {len(PAGES) + 4} páginas sin errores")
    return 0


if __name__ == "__main__":
    sys.exit(main())
