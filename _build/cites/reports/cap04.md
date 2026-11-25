# Informe de revisión de citas: Capítulo 4 (pp. impresas 115-140)

## Resultado

- 297 bloques revisados (ids 0-296), todos contra el OCR de `Capitulos/ocr/Cap04.md`.
- Citas totales en la final: 301 (297 bloques, todos con cita; 7 tablas con línea `Fuente:`).
- Bloques sin cita: 0. Páginas inválidas: 0. Tablas sin fuente: 0. Texto alterado: 0. Errores: 0.
- Avisos de bajo solape restantes: 2 (bloques 112 y 114), explicados abajo.
- Audit: `python3 _build/cite_audit.py --chapter 4` -> faltan 0, inválidas 0, débiles 0, tablas sin fuente 0, texto alterado 0, errores 0.

## Correcciones importantes (37)

### Página incorrecta
- id 2: 119 -> 118-119 (los tres pasos de la hemostasia están en p. 118; los contrarreguladores, en p. 119).
- id 7: 137 -> 135-138 (definición y tipos de shock: pp. 135 y 138; tres fases: p. 137).
- id 15: 117 -> 116-117 (obstrucción linfática y elefantiasis p. 116; linfedema posmastectomía p. 117).
- id 85: 130 -> 124 (efecto fibrinolítico del endotelio normal: síntesis de t-PA, p. 124).
- id 120: 126 -> 127 (hiperestrogenismo: mayor síntesis hepática de factores y menor de anticoagulantes, p. 127).
- id 132: 128 -> 127 (diagnóstico de la TIH por anti-PF4/heparina, p. 127; la p. 128 corresponde al diagnóstico del SAA).
- id 140: 121 -> 128 (los aPL prolongan el TTP in vitro, p. 128).
- id 143: 131 -> 128 (morfolología de los trombos, "cualquier punto del aparato cardiovascular", p. 128).
- id 144: 126 -> 128 (trombos arteriales/cardiacos por turbulencia vs venosos por estasis, p. 128).
- id 149: 129 -> 128-129 (flebotrombosis arranca en p. 128; líneas de Zahn y venas afectadas, pp. 128-129).
- id 153: 119 -> 129 (propagación del trombo, p. 129).
- id 154: 132 -> 129 (embolización del trombo, p. 129).
- id 183: 126 -> 131 (cuarta parte de los émbolos sistémicos: dilatación auricular izquierda y FA, p. 131).
- id 189: 133 -> 131 (consecuencias de los émbolos sistémicos: vascularización colateral, p. 131).
- id 195: 128 -> 131 (trombocitopenia del síndrome de embolia grasa, p. 131).
- id 196: 125 -> 131 (mortalidad 5-15% del síndrome de embolia grasa, p. 131).
- id 255: 136 -> 136-137 (mecanismos procoagulantes de la sepsis: factor tisular p. 136; TFPI/trombomodulina/proteína C p. 137).
- id 256: 126 -> 137 (amortiguación de la fibrinólisis por PAI-1 en la sepsis, p. 137).
- id 273: 137 -> 138 (piel caliente y enrojecida en el shock séptico, p. 138).
- id 296: 135 -> 135-138 (bloque de síntesis del shock: tipos p. 135, fases pp. 137-138, clínica p. 138).

### Encabezados y líneas introductorias vaciados y luego recitados (audit exige 0 faltantes)
- Vaciados inicialmente como títulos de lista: 40, 48, 52, 58, 60, 72, 101, 106, 112, 114, 216, 241, 246.
- El audit de este repo exige 0 faltantes, por lo que se les asignó la página del contenido que encabezan:
  40->118, 48->120, 52->126, 58->122, 60->121, 72->122, 101->126, 106->126, 112->126, 114->127, 216->116, 241->135, 246->135.
- id 46: 119 -> 119-120 (gránulos alfa: contenido p. 120; selectina P en su membrana, p. 119).

## Avisos de bajo solape aceptados (2)

- id 112 "Primarias (genéticas):" citado p. 126: el OCR de la p. 126 usa "Primarios (genéticos)" (tabla 4.2); el resumen inflexiona distinto, por eso el solape por tokens es 0. La página es la correcta.
- id 114 "Datos adicionales:" citado p. 127: es un encabezado organizador de la guía, no una frase del libro; agrupa los bloques de repaso de la p. 127 en adelante (factor V de Leiden y demás). La primera sección que encabeza está en p. 127.

## Afirmaciones no encontradas en el OCR

- id 76 ("Dos casos tipifican este límite: en el trombocitopenia severa el corazón no puede fibrilarse (CID)..."): la frase, tal como está redactada en el resumen, no aparece en el OCR; se mantiene p. 126, que sí respalda la parte de "células endoteliales activadas sobreexpresan factores protrombóticos" (cambios procoagulantes del endotelio activado). No se toca el texto.
- id 197 (clínica de la embolia grasa, "irritabilidad e inquietud pueden progresar a síndrome confusional o coma" y el secuestro esplénico/hemólisis): el OCR de la p. 131 respalda taquipnea/disnea/taquicardia y la trombocitopenia por adhesión o secuestro esplénico; los detalles del deterioro a coma están dispersos y no se localizaron literalmente. Se mantuvo p. 131.

No se tocaron otros capítulos ni se ejecutó `cite_suggest.py`.
