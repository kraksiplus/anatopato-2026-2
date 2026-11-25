# Reporte de revisión de citas: Capítulo 8

Revisión de los 109 bloques (ids 0–108) contra el OCR (`Capitulos/ocr/Cap08.md`), páginas
impresas 339–404. Se usó `cite_review --low` (39 bloques de bajo solape) y lectura directa
del OCR para cada corrección. No se modificó el texto del resumen. No se ejecutó `cite_suggest.py`.

## Cifras

- Bloques: 109 (0–108), más 4 tablas con línea `Fuente:`.
- Citas aplicadas: 106 bloques citados; 3 sin cita intencionales.
- Audit final (`cite_apply` + `cite_audit`): 169 citas, faltan 3 (los bloques sin cita
  intencionales), páginas inválidas 0, débiles 0, bajo solape 0, tablas sin fuente 0,
  texto alterado 0, errores 0.
- Cobertura de páginas: todas las citas entre 339 y 404. Las 66 páginas tienen texto
  extraíble en el OCR; no hubo páginas sin texto reconocible.

## Bloques sin cita (intencionales)

- id 23: `**Virales** (fig. 8.3):` — anuncio de lista.
- id 27: `**Bacterianos**:` — anuncio de lista.
- id 32: `El patrón morfológico orienta el tipo de agente:` — línea introductoria de la
  tabla siguiente (que lleva `Fuente: [p. 348]`).

## Correcciones importantes

Bloques cuyo contenido citaba una página equivocada o cubría solo una parte:

- id 23/27/32: citaban p. 383/348/373 por palabra suelta (con underlines de figure); son
  introductorias, se dejó sin cita.
- id 31 (bacterias intracelulares, receptores de opsoninas): p. 345 → p. 346
  ("M. tuberculosis usa receptores del huésped para opsoninas...").
- id 33 (tabla de patrones inflamatorios): "348-349" → 348; la Tabla 8.3 completa está en p. 348.
- id 35 (tabla de virus agudos): "350-352" → 350-354; la fila de COVID-19 está en p. 354.
- id 37 (VHS): 354 → 354-355 (Cowdry A en 354; encefalitis y queratitis en 355).
- id 38 (VZV): 355 → 355-356 (vacunación >50 en 355; neumonía/encefalitis/vasculopatía en 356).
- id 41 (VEB): 358 → 357-359 (mononucleosis 357; heterófilos/Monospot 358; Duncan/SH2D1A 359).
- id 42 (S. aureus): 360 → 359-360 (lesiones y shock tóxico 359; exfoliativas/SST 360).
- id 45 (listeriosis): 362 → 362-363 (meningitis/granulomatosis 362; listeriolisina O y ActA 363).
- id 52 (chancroide y granuloma inguinal): 368 → 367-368.
- id 60 (sífilis): 377 → 376-379 (TprK y fases 376-377; serología 378; congénita 377-379).
- id 61 (Lyme): 379 → 379-380 (eritema migratorio 379; VlsE 380).
- id 63 (clostridios): 380 → 380-381 (tétanos/botulismo 380-381; C. difficile y trasplante fecal 381).
- id 64 (Chlamydia): 382 → 381-382 (cuerpo elemental/reticular 381; LGV serotipos L 382).
- id 65 (rickettsias): 383 → 382-383 (Montañas Rocosas 382; nódulos tifoideos 383).
- id 67 (candidiasis): 384 → 384-385 (Th17/neutrófilos 384; muguet y esofagitis 385).
- id 68 (C. auris): 385 → 385-386 (patógeno emergente 385; mortalidad hasta 50% 386).
- id 71 (aspergilosis): 388 → 387-388 (conidios/hifas 387; aflatoxina 388).
- id 72 (mucormicosis): 388 → 388-389 (hifas sin septos 388; forma rinocerebral 389).
- id 73 (paludismo): 390 → 389-391 (hipnozoitos 389; PfEMP1/marginación 390; hemozoína 391).
- id 75 (leishmaniosis): 392 → 391-392 (flebótomos/cinetoplasto 391; promastigoto/amastigoto y kala-azar 392).
- id 78 (toxoplasmosis): 395 → 394-395 (sección empieza en 394; vías de infección 395).
- id 79 (estrongiloidosis): 395 → 395-396 (penetración cutánea 395; hiperinfección con sepsis 396).
- id 80 (cisticercosis/hidatidosis): 396 → 396-397.
- id 81 (triquinosis): 397 → 397-398 (eosinofilia y edema periorbitario 397; larvas en músculo, fig. 8.54, 398).
- id 82 (esquistosomiasis): 398 → 397-399 (cañería 398; S. haematobium/vejiga 399).
- id 85 (ITS): 401 → 400-401 (contacto directo 400; tabla 8.7 401).
- id 86 (emergentes): 401 → 401-402 (sección 401; tabla 8.8 y ejemplos 402).
- id 88 (diagnóstico, métodos de referencia): 402 correcto (sección "Técnicas especiales" abre en p. 402).
- id 89 (tabla de tinciones): "386-403" → 403 (Tabla 8.9 completa en p. 403).
- id 90 (serología/PCR/secuenciación): 402 → 402-403 (secuenciación masiva ADNr 16S/ITS en 403).

Bloques "Puntos de examen" (resúmenes que mezclan contenido de varias páginas), ajustados a rangos:
- id 91: 342 → 340-342; id 92: 343 → 343-344; id 93: 348 → 348-349;
- id 95: 356 → 354-356; id 96: 358 → 357-358; id 97: 360 → 359-361; id 98: 363 → 362-363;
- id 99 (TB): 372 → 369-373 (patogenia y TNF/anti-TNF 369-370; complejo de Ghon 372; miliar, Pott y escrófula 373);
- id 101 (sífilis): 377 → 376-379; id 102 (Lyme): 379 → 379-380; id 103: 380 → 380-381;
- id 104: 382 → 381-382; id 105 (hongos): 388 → 384-389; id 106: 390 → 389-391;
- id 107 (parásitos): 399 → 392-399 (kala-azar 392, enfermedad del sueño 393, Chagas 394, toxoplasmosis 394-395, esquistosomiasis 397-398, filariasis 399);
- id 108 (diagnóstico): 371 → 403 (tinciones según Tabla 8.9).

Otros bloques de bajo solape revisados y confirmados como correctos: id 0 (p. 339, cierre de
"Principios generales": mayores, inmunodeprimidos y países de bajos ingresos), id 4 (p. 344,
destrucción de hepatocitos por respuesta inmunitaria), id 17 (p. 343), id 18 (p. 343-344,
Tabla 8.2), id 19 (p. 344, agotamiento de linfocitos T vía PD-1), id 20/22 (p. 344, fiebre
reumática/inmunocomplejos y drepanocitosis/fibrosis quística), id 26 (p. 346), id 34 (p. 349),
id 47 (p. 364), id 55 (p. 370, cavitación y contagio), id 74 (p. 391, cruz de Malta), id 83
(p. 399, Wuchereria/Brugia y Wolbachia), id 94 (p. 350, Koplik y Warthin-Finkeldey),
id 100 (p. 375, Th1/Th2 en lepra).

## Afirmaciones no encontradas en el OCR

- "granulomas de Dürck" (id 73): no aparece en el OCR de las pp. 389-391 (posible error de
  OCR del nombre propio); el resto del bloque paludismo está verificado.
- "granulomatosis infantiséptica" y "meningitis exudativa" (id 45): texto OCR de p. 362
  confirma el cuadro neonatal diseminado; el término exacto coincide con el OCR
  ("granulomatosis infantiséptica del neonato").
- Ningún bloque cita páginas fuera de 339-404 ni texto alterado tras `cite_audit`.
