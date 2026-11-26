#!/usr/bin/env python3
"""Genera el sitio de Anatomía Patológica (C1 y C2) desde los resúmenes Markdown.

Uso:
    python build.py                 # todas las páginas + índices
    python build.py --page c2-11    # una página
    python build.py --indexes       # índices y portada
"""
import argparse
import html
import json
import re
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
CSS = (BUILD / "theme.css").read_text(encoding="utf-8")
JS = (BUILD / "theme.js").read_text(encoding="utf-8")
TPL = (BUILD / "template.html").read_text(encoding="utf-8")
PAGES = json.loads((BUILD / "manifest.json").read_text(encoding="utf-8"))["pages"]

EMDASH = "\u2014"


def clean(text: str) -> str:
    """Sin em dash: celdas vacías pasan a "No aplica" y el resto a coma."""
    text = re.sub(r"(?<=\|)\s*(?:\*\*)?[\u2014\u2013](?:\*\*)?\s*(?=\|)", " No aplica ", text)
    text = text.replace(EMDASH, ", ")
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"\(\s*,\s*", "(", text)
    text = re.sub(r",\s*\)", ")", text)
    text = re.sub(r",\s*([.;:!?])", r"\1", text)
    return text


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:64] or "seccion"


def pandoc(md: str) -> str:
    proc = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none"],
        input=md, capture_output=True, text=True, check=True,
    )
    return proc.stdout


def inline(md: str) -> str:
    out = pandoc(citations(clean(md))).strip()
    return re.sub(r"^<p>|</p>$", "", out)


def citations(md: str) -> str:
    return re.sub(
        r"\[p\.\s*([0-9][0-9,\-\s]*?)\]",
        r'<span class="cite">p. \1</span>',
        md,
    )


def text_of(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    return html.unescape(text).strip()


def load_enrich(page_id: str) -> dict:
    path = BUILD / "enrich" / f"{page_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def load_figures(page_id: str) -> dict:
    path = BUILD / "figures" / f"{page_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"figures": []}


def figure_anchor(page_id: str, number: str) -> str:
    return "fig-" + number.replace(".", "-")


def find_anchor_html(fragment: str, anchor: str) -> int | None:
    """Posición en el HTML de un texto que puede estar partido por etiquetas."""
    chars = []
    positions = []
    i = 0
    while i < len(fragment):
        if fragment[i] == "<":
            j = fragment.find(">", i)
            if j == -1:
                break
            i = j + 1
            continue
        chars.append(fragment[i])
        positions.append(i)
        i += 1
    start = "".join(chars).find(anchor)
    return positions[start] if start != -1 else None


def figure_html(fig: dict, page: dict) -> str:
    num = fig["number"]
    fid = figure_anchor(page["id"], num)
    img = "../" + fig["image"]
    caption_html = inline(fig["caption"])
    alt = html.escape(
        f"Figura {num}. {fig['caption']} Robbins y Cotran, 10ª ed., p. {fig['page']}.",
        quote=True,
    )
    data_caption = html.escape(f"Figura {num}. {fig['caption']}", quote=True)
    source = (
        f"Robbins y Cotran, <em>Patología estructural y funcional</em>, "
        f"10ª ed., Elsevier España, 2021, p. {fig['page']}."
    )
    return f"""<figure class="fig" id="{fid}">
  <a class="fig-open" href="{img}" data-caption="{data_caption}" data-alt="{alt}">
    <img src="{img}" width="{fig['width']}" height="{fig['height']}" loading="lazy" decoding="async" alt="{alt}">
  </a>
  <figcaption>
    <strong>Figura {num}.</strong> {caption_html}
    <span class="fig-source">{source} <a href="../creditos.html#{fid}">Ver créditos</a></span>
  </figcaption>
</figure>"""


def insert_figure(section: str, fig: dict, page: dict) -> tuple[str, bool]:
    block = figure_html(fig, page)
    anchor = (fig.get("after_text") or "").strip()
    if not anchor:
        return section.replace("</section>", block + "\n</section>"), True
    start = find_anchor_html(section, anchor)
    if start is None:
        return section.replace("</section>", block + "\n</section>"), False

    li_open = section.rfind("<li", 0, start)
    p_close = section.find("</p>", start)
    if li_open != -1 and section.find("</li>", li_open, start) == -1:
        # El ancla está dentro de una lista: la figura va después de la lista
        # completa, no como hijo directo de <ul>.
        closes = [c for c in (section.find("</ul>", start), section.find("</ol>", start)) if c != -1]
        if closes:
            pos = min(closes) + 5
        elif p_close != -1:
            pos = p_close + len("</p>")
        else:
            pos = len(section)
    elif p_close != -1:
        pos = p_close + len("</p>")
    else:
        pos = section.find("</section>", start)
        if pos == -1:
            pos = len(section)
    return section[:pos] + "\n" + block + section[pos:], True


def atlas_html(figures: list, page: dict) -> str:
    if not figures:
        return ""
    items = []
    for fig in figures:
        fid = figure_anchor(page["id"], fig["number"])
        img = "../" + fig["image"]
        items.append(
            f'<a class="fig-thumb" href="#{fid}" aria-label="Figura {fig["number"]}">'
            f'<img src="{img}" loading="lazy" decoding="async" alt="Figura {fig["number"]}">'
            f'<span>Figura {fig["number"]}</span></a>'
        )
    return (
        '<section id="atlas" class="card">\n'
        '<div class="section-kicker"><span class="n">★</span> Atlas</div>\n'
        "<h2>Figuras del capítulo</h2>\n"
        '<p class="small">Toca una miniatura para volver a la figura en su sección.</p>\n'
        f'<div class="fig-grid">{"".join(items)}</div>\n'
        "</section>"
    )


def manual_atlas_html(figures: list) -> str:
    if not figures:
        return ""
    items = []
    for fig in figures:
        fid = figure_anchor("", fig["number"])
        href = f"{fig['chapter_file']}#{fid}"
        img = "../" + fig["image"]
        alt = html.escape(f"Figura {fig['number']}. {fig['caption']}", quote=True)
        items.append(
            f'<a class="fig-thumb" href="{href}" aria-label="Figura {fig["number"]}">'
            f'<img src="{img}" loading="lazy" decoding="async" alt="{alt}">'
            f'<span>Figura {fig["number"]}</span><small>Cap. {fig["chapter"]}</small></a>'
        )
    return (
        '<section id="atlas" class="card">\n'
        '<div class="section-kicker"><span class="n">★</span> Atlas</div>\n'
        "<h2>Atlas visual del Certamen 1</h2>\n"
        '<p class="small">Treinta figuras de los capítulos, para repaso rápido. Toca una para abrirla en su guía. La fuente y titularidad de cada figura está en su capítulo y en <a href="../creditos.html">Créditos de las figuras</a>.</p>\n'
        f'<div class="fig-grid">{"".join(items)}</div>\n'
        "</section>"
    )


def table_wrap(fragment: str, label: str) -> str:
    def repl(match):
        return (
            f'<div class="table-wrap" role="region" aria-label="Tabla: {html.escape(label)}" '
            f'tabindex="0">{match.group(0)}</div>'
        )
    return re.sub(r"<table>.*?</table>", repl, fragment, flags=re.S)


def page_range(fragment: str) -> str:
    nums = [int(n) for n in re.findall(r'<span class="cite">p\.\s*(\d+)', fragment)]
    if not nums:
        return ""
    lo, hi = min(nums), max(nums)
    return f"pp. {lo}" if lo == hi else f"pp. {lo}-{hi}"


def section_title(fragment: str) -> str:
    m = re.search(r"<h2[^>]*>(.*?)</h2>", fragment, re.S)
    return text_of(m.group(1)) if m else ""


def process_section(fragment: str, idx: int, page: dict) -> tuple[str, str]:
    title = section_title(fragment)
    sid = f"sec-{idx:02d}-{slug(title)}"
    fragment = re.sub(r"<h2[^>]*>", "<h2>", fragment, count=1)
    fragment = table_wrap(fragment, title)
    fragment = re.sub(r"<th([^>]*)>\s*</th>", r"<th\1>Característica</th>", fragment)
    fragment = re.sub(r"<p>(Fuente:)", r'<p class="small table-source">\1', fragment)

    if "ideas clave" in title.lower():
        fragment = fragment.replace(
            "<ul>", '<div class="keybox"><span class="box-title">Ideas clave</span><ul>', 1
        )
        fragment = fragment.replace("</ul>", "</ul></div>", 1, )
    if "puntos de examen" in title.lower():
        fragment = fragment.replace("<ul>", '<ul class="exam-list">', 1)

    rng = page_range(fragment)
    kicker = f'<div class="section-kicker"><span class="n">{idx:02d}</span> {html.escape(rng) if rng else "Sección"}</div>'
    wrapped = f'<section id="{sid}" class="card">\n{kicker}\n{fragment}\n</section>'
    return wrapped, title


def build_body(page: dict) -> tuple[str, list, dict]:
    src = (ROOT / page["source"]).resolve()
    md = src.read_text(encoding="utf-8")
    md = clean(md)
    words = len(re.findall(r"\w+", md))
    body = pandoc(citations(md))
    body = re.sub(r"<h1[^>]*>.*?</h1>", "", body, count=1, flags=re.S)

    parts = re.split(r"(?=<h2\b)", body)
    head = parts[0].strip()
    raw_sections = [p for p in parts[1:] if p.strip()]

    enrich = load_enrich(page["id"])
    callouts = enrich.get("callouts", [])
    fig_data = load_figures(page["id"])
    figures = fig_data.get("figures", [])
    atlas_only = bool(fig_data.get("atlas_only"))

    sections = []
    titles = []
    for i, frag in enumerate(raw_sections, 1):
        wrapped, title = process_section(frag, i, page)
        sections.append(wrapped)
        titles.append(title)

    if callouts:
        for co in callouts:
            match = co.get("section", "").lower()
            for i, title in enumerate(titles):
                if match and match in title.lower():
                    box = (
                        f'<div class="warnbox"><span class="box-title">{inline(co.get("title", "Perla"))}</span>'
                        f'{inline(co.get("text", ""))}</div>'
                    )
                    sections[i] = sections[i].replace("</section>", box + "\n</section>")
                    break

    def section_rank(title: str, wanted: str) -> tuple[int, int]:
        tl, wl = title.lower(), wanted.lower()
        if tl == wl:
            return (0, len(tl))
        if tl.startswith(wl):
            return (1, len(tl))
        if wl in tl:
            return (2, len(tl))
        return (9, len(tl))

    inserted_ids = set()
    for fig in ([] if atlas_only else reversed(figures)):
        wanted = fig.get("section", "")
        ranked = [(section_rank(t, wanted), i) for i, t in enumerate(titles)]
        ranked.sort()
        target = ranked[0][1] if ranked and ranked[0][0][0] < 9 else None
        if target is None:
            print(f"AVISO {page['id']}: figura {fig['number']} sin sección")
            continue
        sections[target], ok = insert_figure(sections[target], fig, page)
        if not ok:
            print(f"AVISO {page['id']}: figura {fig['number']} sin ancla, al final de la sección")
        inserted_ids.add(fig["number"])
    inserted = figures if atlas_only else [fig for fig in figures if fig["number"] in inserted_ids]

    cite_spans = len(re.findall(r'<span class="cite">', "".join(sections)))
    tables = len(re.findall(r"<table>", "".join(sections)))
    rows = len(re.findall(r"<tr", "".join(sections)))
    stats = {"words": words, "cites": cite_spans, "tables": tables, "rows": rows,
             "sections": len(sections), "titles": titles, "figures": inserted}

    essentials = enrich.get("essentials", [])
    if essentials:
        items = "".join(f"<li>{inline(x)}</li>" for x in essentials)
        essential_block = (
            '<section id="esencial" class="card">'
            '<div class="section-kicker"><span class="n">★</span> Repaso rápido</div>'
            "<h2>Lo esencial en 60 segundos</h2>"
            f'<div class="keybox"><span class="box-title">Si solo te llevas estas ideas</span><ul>{items}</ul></div>'
            "</section>"
        )
    else:
        essential_block = ""

    if page["kind"] == "manual":
        alcance = (
            '<section id="alcance" class="card">'
            '<div class="section-kicker"><span class="n">00</span> Alcance</div>'
            "<h2>Qué cubre este manual</h2>"
            '<div class="keybox"><span class="box-title">Alcance</span>'
            "Manual integrado del Certamen 1, construido desde los apuntes de las 11 clases "
            "(192 páginas) y contrastado con Robbins y Cotran, 10ª edición. Está ordenado por peso "
            "en el certamen, no por número de clase. Incluye las 40 cifras de mayor rendimiento, "
            "12 temas integrados, el rango de páginas del Robbins por tema y las correcciones a los apuntes."
            "</div>"
            '<p class="small">Este manual se construyó desde los apuntes de clase. Las guías de los '
            "capítulos 1 a 10 llevan cita por página del Robbins; aquí se usan rangos por tema, "
            "con el índice tema-clase-Robbins en el apéndice B.</p>"
            "</section>"
        )
    elif page.get("cites"):
        alcance = (
            '<section id="alcance" class="card">'
            '<div class="section-kicker"><span class="n">00</span> Alcance y método</div>'
            "<h2>Qué cubre esta guía</h2>"
            '<div class="keybox"><span class="box-title">Alcance</span>'
            f"Capítulo {page['num']} del Robbins y Cotran, 10ª edición: páginas impresas "
            f"{page['printed']} ({page['pages']} páginas), contrastadas con el OCR del capítulo. "
            "Cada afirmación clínica lleva la página de origen."
            "</div>"
            '<p class="small">Las citas <span class="cite">p. N</span> corresponden a la página impresa '
            "del libro. El texto se contrastó con el OCR del capítulo.</p>"
            "</section>"
        )
    else:
        alcance = (
            '<section id="alcance" class="card">'
            '<div class="section-kicker"><span class="n">00</span> Alcance y método</div>'
            "<h2>Qué cubre esta guía</h2>"
            '<div class="keybox"><span class="box-title">Alcance</span>'
            f"Capítulo {page['num']} del Robbins y Cotran, 10ª edición: páginas impresas "
            f"{page['printed']} ({page['pages']} páginas)."
            "</div>"
            '<p class="small">Este resumen del Certamen 1 se redactó antes de adoptar la cita por '
            "página; se publica sin reescribirlo. El <a href=\"manual.html\">Manual del Certamen 1</a> "
            "incluye el índice tema-clase-Robbins y las fuentes.</p>"
            "</section>"
        )

    atlas = manual_atlas_html(inserted) if atlas_only else atlas_html(inserted, page)
    body_html = alcance + essential_block + "".join(sections) + atlas
    return head + body_html, stats, enrich


def hero_html(page: dict, stats: dict) -> str:
    c = page["certamen"]
    if page["kind"] == "manual":
        eyebrow = "Certamen 1 · Anatomía Patológica"
        figs = len(stats.get("figures", []))
        lede = page.get("lede", "")
        if figs:
            lede += f" Incluye un atlas de {figs} figuras."
        meta = [
            ("Temas", "12"), ("Clases", "11"), ("Filas de tabla", str(stats["rows"])),
            ("Fuente", "Apuntes + Robbins 10ª ed."), ("Ramo", "Anatomía Patológica · UBB 2026-2"),
        ]
        if figs:
            meta.insert(3, ("Figuras", str(figs)))
        h1 = page["title"]
    else:
        eyebrow = f"Certamen {c} · Anatomía Patológica"
        figs = len(stats.get("figures", []))
        fig_txt = f" {figs} figuras seleccionadas." if figs else ""
        lede = (
            f"Guía {page['num'] if c == 1 else page['num'] - 10:02d} de {page['of']:02d}. "
            f"Resumen completo del capítulo {page['num']} con "
            + (f"{stats['cites']} citas por página y {stats['rows']} filas de tabla."
               if page.get("cites") else
               f"{stats['rows']} filas de tabla. Sin citas por página: material del Certamen 1.")
            + fig_txt
        )
        meta = [
            ("Guía", f"{page['num'] if c == 1 else page['num'] - 10:02d} de {page['of']:02d}"),
            ("Capítulo", str(page["num"])),
            ("Páginas", page["printed"]),
            ("Citas", str(stats["cites"]) if page.get("cites") else "sin cita por página"),
            ("Tablas", str(stats["rows"])),
            ("Fuente", "Robbins y Cotran, 10ª ed."),
        ]
        if figs:
            meta.insert(4, ("Figuras", str(figs)))
        h1 = f"Capítulo {page['num']}. {page['title']}"

    meta_html = "".join(
        f"<div><span>{html.escape(k)}</span><strong>{html.escape(v)}</strong></div>" for k, v in meta
    )
    return f"""<header class="hero">
  <div class="hero-inner">
    <p class="eyebrow">{html.escape(eyebrow)}</p>
    <h1>{html.escape(h1)}</h1>
    <p class="lede">{html.escape(lede)}</p>
    <div class="meta-grid">{meta_html}</div>
    <div class="hero-actions">
      <button class="btn primary" id="printBtn" type="button">Imprimir / guardar PDF</button>
      <button class="btn" id="themeBtn" type="button" aria-pressed="false">Modo oscuro</button>
      <a class="btn" href="#alcance">Empezar por el alcance</a>
    </div>
  </div>
</header>"""


def toc_html(page: dict, stats: dict, enrich: dict) -> str:
    items = []
    if enrich.get("essentials"):
        items.append('<li><a href="#esencial">Lo esencial en 60 segundos</a></li>')
    items.append('<li><a href="#alcance">Alcance y método</a></li>')
    for i, title in enumerate(stats["titles"]):
        sid = f"sec-{i + 1:02d}-{slug(title)}"
        items.append(f'<li><a href="#{sid}">{html.escape(title)}</a></li>')
    if stats.get("figures"):
        items.append('<li><a href="#atlas">Atlas de figuras</a></li>')
    return "\n".join("        " + x for x in items)


def nav_html(page: dict) -> str:
    if page["certamen"] == 1:
        idx = "index.html"
        label = "Índice C1"
    else:
        idx = "index.html"
        label = "Índice C2"
    siblings = [p for p in PAGES if p["certamen"] == page["certamen"] and p["kind"] == "chapter"]
    siblings.sort(key=lambda p: p["num"])
    links = [f'<a href="{idx}" title="{label}">{label}</a>']
    for s in siblings:
        if s["id"] == page["id"]:
            continue
        if abs(s["num"] - page["num"]) == 1:
            n = s["num"] if page["certamen"] == 1 else s["num"] - 10
            links.append(f'<a href="{Path(s["file"]).name}" title="{html.escape(s["title"])}">{n:02d}</a>')
    if page["kind"] == "chapter" and page["certamen"] == 1:
        links.append('<a href="manual.html" title="Manual del Certamen 1">Manual</a>')
    return "\n        ".join(links)


def build_page(page: dict) -> Path:
    body, stats, enrich = build_body(page)
    title = f"{page['title']} · Anatomía Patológica UBB"
    desc = (
        f"{page['title']}. "
        + ("Resumen con citas por página del Robbins y Cotran, 10ª ed."
           if page.get("cites") else "Material de estudio del Certamen 1 de Anatomía Patológica.")
    )
    out = TPL
    for key, val in {
        "%%TITLE%%": html.escape(title),
        "%%DESC%%": html.escape(desc),
        "%%CSS%%": CSS,
        "%%HERO%%": hero_html(page, stats),
        "%%TOC%%": toc_html(page, stats, enrich),
        "%%NAV%%": nav_html(page),
        "%%BODY%%": body,
        "%%JS%%": JS,
        "%%CREDITS%%": "../creditos.html",
    }.items():
        out = out.replace(key, val)
    if EMDASH in out:
        raise SystemExit(f"Em dash detectado en {page['file']}")
    dest = ROOT / page["file"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"{page['id']}: {dest.relative_to(ROOT)} ({stats['cites']} citas, {stats['rows']} filas)")
    return dest


def card(page: dict) -> str:
    enrich = load_enrich(page["id"])
    topics = enrich.get("topics") or []
    topic_html = ", ".join(html.escape(t) for t in topics[:5]) or "Resumen completo del capítulo."
    if page["kind"] == "manual":
        n = "M"
        badges = ["11 clases", "12 temas", f"{len(enrich.get('topics', [])) or 12} ejes"]
    else:
        n = f"{page['num'] if page['certamen'] == 1 else page['num'] - 10:02d}"
        badges = [f"{page['printed']} pp."]
        if page.get("cites"):
            badges.append("con citas")
        else:
            badges.append("sin citas por página")
    return f"""    <a href="{Path(page['file']).name}">
      <span class="gn">{n}</span>
      <h3>{html.escape(page['title'])}</h3>
      <p>{topic_html}</p>
      <div class="badges">{''.join(f'<span>{html.escape(b)}</span>' for b in badges)}</div>
    </a>"""


def index_page(cert: int) -> str:
    pages = [p for p in PAGES if p["certamen"] == cert]
    chapters = [p for p in pages if p["kind"] == "chapter"]
    manual = next((p for p in pages if p["kind"] == "manual"), None)
    total_cites = sum(1 for p in chapters if p.get("cites"))
    figs_by_page = {p["id"]: len(load_figures(p["id"]).get("figures", [])) for p in chapters}
    total_figs = sum(figs_by_page.values())
    if cert == 1:
        h1 = "Certamen 1<br>Patología general"
        lede = "Diez capítulos del Robbins, con citas por página, y el Manual integrado del Certamen 1. La base conceptual de la Anatomía Patológica."
        eyebrow = "Anatomía Patológica · Certamen 1"
    else:
        h1 = "Certamen 2<br>Patología sistémica"
        lede = f"{len(chapters)} capítulos del Robbins, con citas por página, tablas comparativas y puntos de examen."
        eyebrow = "Anatomía Patológica · Certamen 2"

    order = [manual] + chapters if manual else chapters
    cards = "\n".join(card(p) for p in order)
    if cert == 1:
        steps = (
            "<li><strong>Manual:</strong> empieza por el mapa y las cifras. "
            "Fija qué entra y qué no.</li>"
            "<li><strong>Capítulos en orden:</strong> cada guía cubre un capítulo "
            "completo del Robbins.</li>"
        )
    else:
        steps = (
            "<li><strong>Capítulos en orden:</strong> sigue la secuencia del Robbins, "
            "de vasos sanguíneos a huesos y partes blandas.</li>"
            "<li><strong>Puntos de examen:</strong> cierra cada guía con esa lista "
            "para repasar sin releer.</li>"
        )
    rows = "".join(
        f"<tr><td>{i + 1}</td><td><a href=\"{Path(p['file']).name}\">{html.escape(p['title'])}</a></td>"
        f"<td>{p['printed']}</td><td>{p['pages']}</td>"
        f"<td>{figs_by_page[p['id']]}</td><td>{'Sí' if p.get('cites') else 'No'}</td></tr>"
        for i, p in enumerate(chapters)
    )
    total_pages = sum(p["pages"] for p in chapters)
    hero = f"""<header class="hero">
  <div class="hero-inner">
    <p class="eyebrow">{eyebrow}</p>
    <h1>{h1}</h1>
    <p class="lede">{lede}</p>
    <div class="meta-grid">
      <div><span>Capítulos</span><strong>{len(chapters)}</strong></div>
      <div><span>Páginas del libro</span><strong>{total_pages}</strong></div>
      <div><span>Manual</span><strong>{'Sí' if manual else 'No'}</strong></div>
      <div><span>Citas por página</span><strong>{'Sí' if total_cites else 'No'}</strong></div>
      <div><span>Figuras</span><strong>{total_figs}</strong></div>
      <div><span>Ramo</span><strong>Anatomía Patológica · UBB 2026-2</strong></div>
    </div>
    <div class="hero-actions">
      <button class="btn primary" id="printBtn" type="button">Imprimir / guardar PDF</button>
      <button class="btn" id="themeBtn" type="button" aria-pressed="false">Modo oscuro</button>
      <a class="btn" href="../index.html">Todos los certámenes</a>
    </div>
  </div>
</header>"""
    body = f"""<section id="guias" class="card">
  <div class="section-kicker"><span class="n">01</span> Material</div>
  <h2>Guías del certamen</h2>
  <div class="guide-grid">
{cards}
  </div>
</section>

<section id="orden" class="card">
  <div class="section-kicker"><span class="n">02</span> Método</div>
  <h2>Orden de estudio sugerido</h2>
  <ol>
    {steps}
  </ol>
  <div class="keybox"><span class="box-title">Cómo citar</span>
    En el Certamen 1 y en el Certamen 2 cada afirmación lleva <span class="cite">p. N</span>, la página impresa del Robbins.
    El Manual del Certamen 1 declara el rango de páginas por tema y el índice del apéndice B.
  </div>
</section>

<section id="cobertura" class="card">
  <div class="section-kicker"><span class="n">03</span> Verificación</div>
  <h2>Cobertura</h2>
  <div class="table-wrap" role="region" aria-label="Cobertura por capítulo" tabindex="0">
    <table>
      <thead><tr><th>#</th><th>Capítulo</th><th>Páginas impresas</th><th>Páginas</th><th>Figuras</th><th>Citas</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</section>

<section id="fuentes" class="card">
  <div class="section-kicker"><span class="n">04</span> Fuentes</div>
  <h2>Notas de fuente</h2>
  <ul>
    <li>Robbins y Cotran, <em>Patología Estructural y Funcional</em>, 10ª edición.</li>
    <li>Las figuras provienen de Robbins y Cotran, 10ª ed. (Elsevier España, 2021) y pertenecen a Elsevier y a los autores. Se usan con fines educativos y sin fines comerciales. <a href="../creditos.html">Créditos de las figuras</a>.</li>
    <li>Los PDF originales y el OCR crudo no se publican; solo el HTML de estudio.</li>
    <li>Material docente, no una recomendación clínica.</li>
  </ul>
</section>"""
    toc = """<li><a href="#guias">Guías del certamen</a></li>
        <li><a href="#orden">Orden de estudio</a></li>
        <li><a href="#cobertura">Cobertura</a></li>
        <li><a href="#fuentes">Fuentes</a></li>"""
    nav = '<a href="../index.html">Portada</a>'
    out = TPL
    for key, val in {
        "%%TITLE%%": f"Certamen {cert} · Anatomía Patológica UBB",
        "%%DESC%%": lede,
        "%%CSS%%": CSS,
        "%%HERO%%": hero,
        "%%TOC%%": toc,
        "%%NAV%%": nav,
        "%%BODY%%": body,
        "%%JS%%": JS,
        "%%CREDITS%%": "../creditos.html",
    }.items():
        out = out.replace(key, val)
    if EMDASH in out:
        raise SystemExit("Em dash detectado en índice")
    dest = ROOT / f"c{cert}" / "index.html"
    dest.write_text(out, encoding="utf-8")
    print(f"índice C{cert}: {dest.relative_to(ROOT)}")
    return out


def root_page() -> str:
    c1 = [p for p in PAGES if p["certamen"] == 1 and p["kind"] == "chapter"]
    c2 = [p for p in PAGES if p["certamen"] == 2 and p["kind"] == "chapter"]
    c1_figs = sum(len(load_figures(p["id"]).get("figures", [])) for p in c1)
    c2_figs = sum(len(load_figures(p["id"]).get("figures", [])) for p in c2)
    total_figs = c1_figs + c2_figs
    total_chapters = len(c1) + len(c2)
    total_guides = total_chapters + sum(1 for p in PAGES if p["kind"] == "manual")
    c2_cites = sum(
        len(re.findall(r"\[p\.\s*\d", (ROOT / p["source"]).resolve().read_text(encoding="utf-8")))
        for p in c2 if p.get("cites")
    )
    c2_cites_fmt = f"{c2_cites:,}".replace(",", ".")
    hero = f"""<header class="hero">
  <div class="hero-inner">
    <p class="eyebrow">Medicina UBB · 2026-2</p>
    <h1>Anatomía Patológica<br>Certámenes 1 y 2</h1>
    <p class="lede">Todo el material de estudio en un solo lugar: patología general y patología sistémica, capítulo por capítulo.</p>
    <div class="meta-grid">
      <div><span>Certámenes</span><strong>2</strong></div>
      <div><span>Capítulos</span><strong>{total_chapters}</strong></div>
      <div><span>Guías</span><strong>{total_guides}</strong></div>
      <div><span>Figuras</span><strong>{total_figs}</strong></div>
      <div><span>Fuente</span><strong>Robbins y Cotran, 10ª ed.</strong></div>
      <div><span>Ramo</span><strong>Anatomía Patológica · UBB 2026-2</strong></div>
    </div>
  </div>
</header>"""
    body = f"""<section id="certamenes" class="card">
  <div class="section-kicker"><span class="n">01</span> Material</div>
  <h2>Elige el certamen</h2>
  <div class="cert-grid">
    <a class="cert-card" href="c1/index.html">
      <p class="eyebrow">Certamen 1</p>
      <div class="big">01</div>
      <h3>Patología general</h3>
      <p>10 capítulos del Robbins y el Manual integrado: lesión celular, inflamación, hemodinamia, genética, inmunidad, neoplasias, infecciosas, ambientales y pediatría.</p>
      <div class="badges"><span>10 capítulos</span><span>Manual</span><span>con citas por página</span><span>{c1_figs} figuras</span></div>
    </a>
    <a class="cert-card" href="c2/index.html">
      <p class="eyebrow">Certamen 2</p>
      <div class="big">02</div>
      <h3>Patología sistémica</h3>
      <p>{len(c2)} capítulos del Robbins con citas por página: de vasos sanguíneos a huesos, articulaciones y partes blandas.</p>
      <div class="badges"><span>{len(c2)} capítulos</span><span>con citas</span><span>{c2_cites_fmt} citas</span><span>{c2_figs} figuras</span></div>
    </a>
  </div>
</section>

<section id="orden" class="card">
  <div class="section-kicker"><span class="n">02</span> Método</div>
  <h2>Cómo usar el sitio</h2>
  <ol>
    <li><strong>Si vas por el C1:</strong> abre el Manual primero, luego los capítulos que el manual marque como prioritarios.</li>
    <li><strong>Si vas por el C2:</strong> estudia los {len(c2)} capítulos en orden y cierra con los Puntos de examen de cada guía.</li>
    <li><strong>Repaso:</strong> usa "Lo esencial en 60 segundos" al inicio de cada página.</li>
  </ol>
  <div class="keybox"><span class="box-title">Offline</span>
    Cada guía es un HTML autocontenido: se abre sin internet, guarda el tema elegido y se imprime o exporta a PDF.
  </div>
</section>

<section id="fuentes" class="card">
  <div class="section-kicker"><span class="n">03</span> Fuentes</div>
  <h2>Trazabilidad</h2>
  <ul>
    <li>Robbins y Cotran, <em>Patología Estructural y Funcional</em>, 10ª edición.</li>
    <li>Las figuras provienen de Robbins y Cotran, 10ª ed. (Elsevier España, 2021) y pertenecen a Elsevier y a los autores. Se usan con fines educativos y sin fines comerciales. <a href="creditos.html">Créditos de las figuras</a>.</li>
    <li>Certamen 2: resúmenes construidos desde el OCR de los capítulos 11 a 26, con cita de la página impresa.</li>
    <li>Certamen 1: capítulos 1 a 10 y Manual integrado de las clases, con citas por página en los capítulos.</li>
    <li>No se publican PDFs ni OCR crudo. Material docente, no una recomendación clínica.</li>
  </ul>
</section>"""
    toc = """<li><a href="#certamenes">Elige el certamen</a></li>
        <li><a href="#orden">Cómo usar el sitio</a></li>
        <li><a href="#fuentes">Fuentes</a></li>"""
    out = TPL
    for key, val in {
        "%%TITLE%%": "Anatomía Patológica UBB 2026-2 · Certámenes 1 y 2",
        "%%DESC%%": "Material de estudio de Anatomía Patológica, certámenes 1 y 2, basado en Robbins y Cotran 10ª ed.",
        "%%CSS%%": CSS,
        "%%HERO%%": hero,
        "%%TOC%%": toc,
        "%%NAV%%": '<a href="c1/index.html">C1</a> &nbsp;·&nbsp; <a href="c2/index.html">C2</a>',
        "%%BODY%%": body,
        "%%JS%%": JS,
        "%%CREDITS%%": "creditos.html",
    }.items():
        out = out.replace(key, val)
    if EMDASH in out:
        raise SystemExit("Em dash detectado en portada")
    (ROOT / "index.html").write_text(out, encoding="utf-8")
    print("portada: index.html")
    return out


def credits_page() -> str:
    items = []
    for page in PAGES:
        if page["kind"] == "manual":
            continue
        for fig in load_figures(page["id"]).get("figures", []):
            items.append((page, fig))
    items.sort(
        key=lambda x: (
            x[0]["certamen"],
            x[0]["num"] or 0,
            [int(n) for n in x[1]["number"].split(".")],
        )
    )

    rows = []
    for page, fig in items:
        fid = figure_anchor(page["id"], fig["number"])
        rows.append(
            f'<tr id="{fid}"><td><a href="{page["file"]}#{fid}">Figura {fig["number"]}</a></td>'
            f'<td>{html.escape(page["title"])}</td>'
            f'<td>{fig["page"]}</td>'
            f'<td>C{page["certamen"]}</td></tr>'
        )
    body_rows = "".join(rows) or '<tr><td colspan="4">Sin figuras registradas.</td></tr>'
    chapters = len({p["id"] for p, _ in items})

    hero = f"""<header class="hero">
  <div class="hero-inner">
    <p class="eyebrow">Anatomía Patológica · Fuentes</p>
    <h1>Créditos de las figuras</h1>
    <p class="lede">Cada figura de las guías, con su capítulo y su página impresa. La titularidad es de Elsevier y de los autores de la obra.</p>
    <div class="meta-grid">
      <div><span>Figuras</span><strong>{len(items)}</strong></div>
      <div><span>Capítulos</span><strong>{chapters}</strong></div>
      <div><span>Fuente</span><strong>Robbins y Cotran, 10ª ed.</strong></div>
      <div><span>Editorial</span><strong>Elsevier, 2021</strong></div>
      <div><span>Uso</span><strong>Educativo, sin fines comerciales</strong></div>
    </div>
    <div class="hero-actions">
      <a class="btn primary" href="index.html">Volver a la portada</a>
      <button class="btn" id="themeBtn" type="button" aria-pressed="false">Modo oscuro</button>
    </div>
  </div>
</header>"""
    body = f"""<section id="aviso" class="card">
  <div class="section-kicker"><span class="n">01</span> Aviso</div>
  <h2>Fuente y titularidad</h2>
  <div class="warnbox"><span class="box-title">Robbins y Cotran, 10ª edición</span>
    Las figuras provienen de Robbins y Cotran, <em>Patología estructural y funcional</em>, 10ª edición
    (Elsevier España, 2021). La titularidad corresponde a Elsevier y a los autores de la obra.
    Se reproducen con fines exclusivamente educativos y sin fines comerciales, citando el número de
    figura y la página impresa. Los PDF originales y el OCR crudo no se distribuyen.
  </div>
  <p class="small">Si eres titular de derechos y deseas la retirada de una figura, abre un
    <a href="https://github.com/kraksiplus/anatopato-2026-2/issues">issue en el repositorio</a>.
    El sitio puede regenerarse sin imágenes sin romper el texto.</p>
</section>

<section id="listado" class="card">
  <div class="section-kicker"><span class="n">02</span> Listado</div>
  <h2>Todas las figuras</h2>
  <div class="table-wrap" role="region" aria-label="Listado de figuras y fuentes" tabindex="0">
    <table>
      <thead><tr><th>Figura</th><th>Capítulo</th><th>Página</th><th>Guía</th></tr></thead>
      <tbody>{body_rows}</tbody>
    </table>
  </div>
</section>"""
    toc = """<li><a href="#aviso">Aviso</a></li>
        <li><a href="#listado">Listado</a></li>"""
    out = TPL
    for key, val in {
        "%%TITLE%%": "Créditos de las figuras · Anatomía Patológica UBB",
        "%%DESC%%": "Fuente, página y titularidad de cada figura usada en las guías de Anatomía Patológica.",
        "%%CSS%%": CSS,
        "%%HERO%%": hero,
        "%%TOC%%": toc,
        "%%NAV%%": '<a href="index.html">Portada</a>',
        "%%BODY%%": body,
        "%%JS%%": JS,
        "%%CREDITS%%": "creditos.html",
    }.items():
        out = out.replace(key, val)
    if EMDASH in out:
        raise SystemExit("Em dash detectado en créditos")
    (ROOT / "creditos.html").write_text(out, encoding="utf-8")
    print(f"créditos: creditos.html ({len(items)} figuras)")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page")
    ap.add_argument("--indexes", action="store_true")
    args = ap.parse_args()
    if args.page:
        page = next(p for p in PAGES if p["id"] == args.page)
        build_page(page)
        credits_page()
        return
    if not args.indexes:
        for page in PAGES:
            build_page(page)
    index_page(1)
    index_page(2)
    root_page()
    credits_page()


if __name__ == "__main__":
    main()
