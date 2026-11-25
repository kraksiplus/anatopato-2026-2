# Anatomía Patológica UBB 2026-2

Material de estudio de Anatomía Patológica, certámenes 1 y 2, en un solo sitio.

Publicado en https://kraksiplus.github.io/anatopato-2026-2/

## Contenido

| Certamen | Qué incluye |
|---|---|
| [Certamen 1](c1/index.html) | 10 capítulos del Robbins, el Manual integrado y un atlas visual de 30 figuras |
| [Certamen 2](c2/index.html) | 8 capítulos del Robbins, con cita de la página impresa |

Cada guía es un HTML autocontenido: funciona sin internet, guarda el tema claro u oscuro y se imprime o exporta a PDF desde el navegador.

## Figuras

- 141 figuras seleccionadas de los 18 capítulos, entre 6 y 8 por capítulo.
- Mezcla de mecanismos (diagramas de patogenia) e imágenes diagnósticas (macroscopía, histología, imágenes clínicas).
- Recortadas desde el escaneo del libro a 200 DPI y guardadas en WebP.
- Cada figura lleva su leyenda, la página impresa y un enlace a sus créditos.
- El Manual del Certamen 1 incluye un atlas de 30 figuras, reutilizadas de los capítulos.
- Página de créditos: https://kraksiplus.github.io/anatopato-2026-2/creditos.html

Las figuras provienen de Robbins y Cotran, *Patología estructural y funcional*, 10ª edición (Elsevier España, 2021). La titularidad corresponde a Elsevier y a los autores de la obra. Se reproducen con fines exclusivamente educativos y sin fines comerciales, citando figura y página. Si eres titular de derechos y deseas la retirada de una figura, abre un issue en el repositorio.

## Fuentes

- Robbins y Cotran, *Patología Estructural y Funcional*, 10ª edición.
- Certamen 2: resúmenes construidos desde el OCR de los capítulos 11 a 18, con cita `[p. N]` de la página impresa.
- Certamen 1: capítulos 1 a 10 y Manual integrado de las clases. Los resúmenes del C1 no tienen cita por página y cada guía lo advierte.
- No se publican los PDF originales ni el OCR crudo.

## Estructura

```
index.html          Portada de los dos certámenes
creditos.html       Fuente y titularidad de cada figura
c1/                 Certamen 1: índice, manual y 10 capítulos
c2/                 Certamen 2: índice y 8 capítulos
assets/fig/         Figuras recortadas en WebP
_build/             Plantilla, estilos, manifiesto, generador y metadatos de figuras
```

Para regenerar el HTML:

```bash
python3 _build/build.py
python3 _build/qa.py
```

El generador lee los resúmenes Markdown desde `../Anatopato/`, fuera de este repositorio. El repositorio publicado solo contiene el HTML final y las figuras seleccionadas.

Para regenerar las figuras se necesitan los PDFs de los capítulos y el entorno de OCR:

```bash
# Una figura o un capítulo
../Anatopato/.ocr/venv/bin/python \
  _build/figtool.py --chapter 11

# Fusionar los recortes con las leyendas y secciones
python3 _build/fig_merge.py --merge

# Reconstruir el sitio
python3 _build/build.py
python3 _build/qa.py
```

## Notas

- Material docente, no una recomendación clínica.
- Sin datos de pacientes.
- Sin em dash en el texto generado.
- Las figuras son de Elsevier y se usan con fines educativos; no se reclama su autoría.
