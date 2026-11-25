# Reporte de revisión de citas: Capítulo 1

Revisión bloque a bloque (0–127) contra el OCR (`Capitulos/ocr/Cap01.md`), con verificación de
contexto vía `cite_lookup` y lectura directa del OCR. No se modificó el texto del resumen.

## Cifras

- Bloques: 128 (0–127), más 15 tablas con línea `Fuente:`.
- Citas aplicadas: 115 bloques citados (audit: 109 citas en bloques + 15 tablas).
- Bloques sin cita: 13, todos intencionales (frases de transición o anuncios de lista/figura,
  según la regla del flujo): ids 12, 19, 25, 34, 51, 56, 59, 71, 76, 78, 84, 96, 107.
- Audit final: páginas inválidas 0, débiles 0, tablas sin fuente 0, texto alterado 0, errores 0.
- Cobertura de páginas: todas las citas quedan entre 1 y 32. La p. 31 es bibliografía
  (lecturas recomendadas) y la p. 32 no tiene texto reconocible en el OCR; ninguna cita las usa.

## Correcciones importantes

- id 22 (exportación del pre-miARN al citoplasma): citaba p. 10 (transporte de membrana);
  el pasaje correcto es p. 5 ("Tras la exportación fuera del núcleo por medio de proteínas
  transportadoras específicas...").
- id 63 (factores solubles: factores de crecimiento y citocinas): citaba p. 20; el listado de
  grupos de señales ("Moléculas secretadas") está en p. 17.
- id 84 ("Espectro de tipos con datos del texto"): citaba p. 32, que no tiene texto reconocido;
  es línea introductoria, se dejó sin cita.
- id 111 (problemas del trasplante: rechazo, integración insuficiente): citaba p. 32 sin texto;
  el respaldo está en p. 29-30 ("rechazo inmunitario cuando las células son trasplantadas";
  "integración funcional de células de sustitución").
- id 82 (varios tipos de colágeno; triple hélice de tres cadenas): citaba p. 25; la afirmación
  ("unos 30 tipos", "tres cadenas polipeptídicas... triple hélice a modo de cordón") está en p. 23.
- id 87 (tipo I en matriz intersticial): p. 22 → p. 23 (tipos I, II, III y V forman fibrillas del
  tejido conjuntivo).
- id 10 (tabla de secuencias no codificantes): 2-5 → 2; las cinco clases se enumeran en p. 2.
- id 38 (tabla de orgánulos del hepatocito): 7-15 → 7; la figura con porcentajes, números y la
  columna "Función en la célula" completa está en p. 7.
- id 1 (1,5% codifica + planificación arquitectural): 1 → 1-2 (el dato del 1,5% está en p. 1 y
  la "planificación arquitectural" en p. 2).
- id 3 (miARN y ARNlnc): 5 → 4-5 (miARN descrito en p. 4, ARNlnc en p. 5).
- id 66/67 (vías de RAS y Wnt): 18 → 18-19 (figura de vías en p. 18 y desarrollo del texto en p. 19).
- id 121, 122, 124 (bloques-resumen): ajustados a 14-15, "15, 19" y 23-25 respectivamente, para
  cubrir todas las afirmaciones que mezclan páginas.
- Des-citados por ser transiciones/pure intro: 12, 19, 25, 34, 51, 56, 59, 71, 76, 78, 96, 107.

## Páginas dudosas / afirmaciones no encontradas en el OCR

- id 88 ("Tipo II: cartílago") y id 89 ("Tipo III: colágeno fino (reticulina)"): la p. 23 menciona
  los tipos I, II, III y V formando fibrillas en cartílago, vasos y cicatrización de heridas, pero
  la palabra "reticulina" y la asignación explícita tipo II=cartílago / tipo III=reticulina no
  aparecen en el OCR. La cita p. 23 es la mejor cobertura disponible; la equivalencia de
  "reticulina" proviene del conocimiento general, no del texto fuente.
- id 111 ("limitación reconocida en el texto" sobre integración/funcionalidad insuficiente): el
  OCR respalda el rechazo inmunitario (p. 29-30) y la "integración funcional de células de
  sustitución" (p. 29-30), pero la frase "limitación reconocida en el texto" es valoración del
  resumen, no cita literal.
- id 83 y 124 mencionan "lisilo oxidasa": el OCR de p. 25 dice "lisilo oxidasa" (figura 1.16) y
  "Tras la secreción, el colágeno obtiene estabilidad lateral mediante entrecruzamiento, que
  implica a la lisilo oxidasa" (p. 25), aunque en p. 23 también aparece "lisilo hidroxilasa" para
  la enzima dependiente de vitamina C. Se mantuvo la cita p. 25, que contiene ambas formas.
