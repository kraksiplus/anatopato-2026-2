# Reporte de revisión de citas: Capítulo 6

Revisión bloque a bloque (0–204) contra el OCR (`Capitulos/ocr/Cap06.md`), páginas impresas
189–266. Se usó `cite_review.py` (completo + `--low`) y verificación directa del OCR para los
bloques dudosos. No se modificó el texto del resumen.

## Cifras

- Bloques: 205 (0–204), más 12 tablas con línea `Fuente:`.
- Citas aplicadas: 191 bloques citados (193 citas contadas por el audit, incluye rangos).
- Bloques sin cita: 14, todos intencionales (frases de transición, títulos de lista o líneas
  introductorias, según la regla del flujo): ids 12, 56, 61, 71, 74, 81, 84, 89, 98, 107,
  112, 131, 136, 170.
- Audit final: páginas inválidas 0, débiles 0, tablas sin fuente 0, texto alterado 0, errores 0.
  Faltan 14 (los bloques intencionales sin cita; mismo criterio aceptado en el capítulo 1).
- Bajo solape: 1 (id 52, falso positivo — ver abajo).
- Cobertura de páginas: todas las citas quedan entre 189 y 266. La p. 189 es el índice del
  capítulo más el párrafo introductorio; ninguna cita usa páginas fuera de rango.

## Correcciones importantes

- id 18 (mastocitos, células epiteliales y endoteliales como fuentes de citocinas): citaba
  p. 205 (hipersensibilidad); el pasaje ("Sus principales fuentes son los macrófagos, las DC,
  ILC y los linfocitos NK, pero las células endoteliales y las epiteliales...") está en p. 199.
- id 36 (linfocitos B: 10%–20% de los linfocitos sanguíneos): citaba p. 196; el dato está en
  p. 195.
- id 50 (citocinas de la inmunidad innata: TNF, IL-1, IL-12, IFN, quimiocinas): citaba p. 190
  (índice de sección); el listado está en p. 199.
- id 52 (citocinas limitadoras: TGF-beta e IL-10): citaba p. 202 (figura de subgrupos Th); el
  pasaje ("citocinas que limitan y terminan las respuestas... TGF-β y la IL-10") está en p. 200.
- id 57 (IL-2 y receptores de alta afinidad, expansión clonal): citaba p. 202; el pasaje ("una
  de las primeras respuestas de los linfocitos T CD4+ colaboradores es la secreción de la
  citocina IL-2 y la expresión de receptores de afinidad alta") está en p. 200.
- id 93 (inflamación por anticuerpos contra matriz/membrana basal, necrosis fibrinoide):
  citaba p. 236 (rechazo de injerto); el mecanismo de hipersensibilidad tipo II está en
  p. 209-210.
- id 96 (tabla 6.4, enfermedades por inmunocomplejos): citaba "211-229"; la tabla completa
  está en p. 211.
- id 102 (tabla 6.5, enfermedades mediadas por linfocitos T): citaba "213-214"; la tabla está
  en p. 213.
- id 145 (LES, pulmones: pleuritis, fibrosis intersticial, hipertensión pulmonar): citaba
  p. 232 (esclerosis sistémica); el pasaje del LES está en p. 228.
- id 148 (definición de Sjögren: sequedad ocular y oral, glándulas lagrimales y salivales):
  citaba p. 230 (patogenia); la definición está en p. 229.
- id 150 (Sjögren: factor reumatoide, ANA, anti-SS-A/SS-B como marcadores serológicos):
  citaba p. 222 (tabla de otra sección); el respaldo está en p. 230.
- id 160 (panarteritis nudosa y otras vasculitis): citaba p. 211 (tabla 6.4); la sección
  dedicada está en p. 234.
- id 170 ("Defectos de la inmunidad adaptativa"): citaba p. 189 (índice del capítulo); es
  título de lista, se dejó sin cita.
- id 185 (patogenia de la amiloidosis: plegamiento anómalo, producción excesiva, degradación
  defectuosa): citaba p. 264 (clínica); "Patogenia y clasificación de la amiloidosis" está en
  p. 260.
- id 196 (resumen de los cuatro tipos de hipersensibilidad): citaba p. 205 (solo tipo III);
  la clasificación (tabla 6.1) está en p. 204.

## Ajustes de rango (bloques que mezclan páginas)

- id 16 (ILC y grupos 1/2/3): 190 → "190-191".
- id 24 (linfocitos NK completo: CD16/CCDA, inhibidores, IFN-gamma): 192 → "192-193".
- id 80 (eosinófilos, Charcot-Leyden y corticoesteroides en fase tardía): 207 → "207-208".
- id 154 (esclerodermia difusa + anti-Scl-70): 233 → "231, 233" (definición p. 231,
  anticuerpo p. 233).
- id 155 (esclerodermia limitada, CREST + anticentroméricos): 231 → "231, 234"
  (anticentromérico en p. 234).
- id 197 (resumen de autotolerancia central y periférica): 217 → "216-217".
- id 199 (resumen LES: anti-Sm, nefritis clases, Libman-Sacks, mariposa): 228 →
  "221, 226-228".
- id 200 (resumen Sjögren, incluido linfoma 40x): 230 → "230-231".
- id 201 (resumen esclerosis sistémica: formas, anticuerpos, crisis renal): 233 → "231-234".

## Avisos de bajo solape o débiles restantes

- id 52, bajo solape 0.00: falso positivo. El único término sin cubrir es "limitadoras",
  palabra acuñada por el resumen; el OCR p. 200 dice textualmente "algunas citocinas sirven,
  sobre todo, para limitar y terminar las respuestas inmunitarias; entre ellas están el
  TGF-β y la IL-10". La página es correcta.

## Afirmaciones no encontradas en el OCR

Ninguna. Todos los bloques citados tienen respaldo textual en las páginas indicadas. Dos
observaciones menores:

- id 189 (resumen "dos tipos de inmunidad") y otros bloques de resumen final (ids 189-204)
  condensan contenido repartido; se citó la página con el respaldo más directo.
- id 0 se mantiene en p. 189: el párrafo introductorio del capítulo ("El sistema inmunitario
  es vital para la supervivencia... alergia y... autoinmunidad") está en esa página, junto al
  índice.
