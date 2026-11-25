# Anatomía Patológica UBB 2026-2

Material de estudio de Anatomía Patológica, certámenes 1 y 2, en un solo sitio.

Publicado en https://kraksiplus.github.io/anatopato-2026-2/

## Contenido

| Certamen | Qué incluye |
|---|---|
| [Certamen 1](c1/index.html) | 10 capítulos del Robbins y el Manual integrado del Certamen 1 |
| [Certamen 2](c2/index.html) | 8 capítulos del Robbins, con cita de la página impresa |

Cada guía es un HTML autocontenido: funciona sin internet, guarda el tema claro u oscuro y se imprime o exporta a PDF desde el navegador.

## Fuentes

- Robbins y Cotran, *Patología Estructural y Funcional*, 10ª edición.
- Certamen 2: resúmenes construidos desde el OCR de los capítulos 11 a 18, con cita `[p. N]` de la página impresa.
- Certamen 1: capítulos 1 a 10 y Manual integrado de las clases. Los resúmenes del C1 no tienen cita por página y cada guía lo advierte.
- No se publican los PDF originales ni el OCR crudo.

## Estructura

```
index.html          Portada de los dos certámenes
c1/                 Certamen 1: índice, manual y 10 capítulos
c2/                 Certamen 2: índice y 8 capítulos
_build/             Plantilla, estilos, manifiesto y generador
```

Para regenerar el sitio:

```bash
python3 _build/build.py
python3 _build/qa.py
```

El generador lee los resúmenes Markdown desde `../Anatopato/`, fuera de este repositorio. El repositorio publicado solo contiene el HTML final.

## Notas

- Material docente, no una recomendación clínica.
- Sin datos de pacientes.
- Sin em dash en el texto generado.
