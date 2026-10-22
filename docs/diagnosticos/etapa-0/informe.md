# Etapa 0 · Medición de las 15 páginas sobre la base D-229

Fecha: 22-10-2026. Sin ninguna corrección: solo medición. Base: `main` en `53d9cc7`, app local (`streamlit run bi/dashboard.py`).

## Método

- Playwright con Chrome en modo headless, fuera del proyecto (no se agregó ninguna dependencia). Script: `tests/medicion/medir.cjs`; tablas: `tests/medicion/tabla.py`; datos: `medicion.json` (150 mediciones).
- 15 páginas del menú (14 vistas más GitHub) × 2 temas (Vantablack, Blue Light) × 5 pantallas (1440 × 700, 1440 × 900, 1920 × 1080, 390 × 844, 844 × 390), con el menú abierto. Se navega con los enlaces reales del menú y se mide dentro de la página y de cada iframe.
- Por medición: alto natural (`stMainBlockContainer`), `scrollHeight` contra `clientHeight` de `stMain`, espacio vacío bajo el último elemento, texto menor de 11 px (con la escala real de los SVG), superposición texto × texto (30 % o más de la caja menor), texto × ícono (15 % o más), texto recortado por un ancestro con `overflow` oculto, y diagramas y tablas visibles.
- Capturas «golden»: `golden/<tema>/NN-pagina.png`, a 1440 × 900.
- Criterio de «cabe»: `scrollHeight` no mayor que `clientHeight` **y** vacío bajo el último elemento de 10 % o menos.
- En 390 × 844 la app tapa todo con «Gira tu teléfono» (D-166); las cifras de esa columna son del contenido que hay debajo y solo sirven de referencia.

## Los dos temas dan lo mismo

En las tres pantallas de escritorio, Vantablack y Blue Light miden igual en todas las páginas; por eso las tablas no separan los temas.

## Alto natural y desplazamiento (Vantablack / Blue Light si difieren)

| # | Página | 1440 × 700 | 1440 × 900 | 1920 × 1080 | Qué la hace crecer (1440 × 900) |
|--:|---|---|---|---|---|
| 1 | resumen-semanal | 1200 ✘ desplaza | 1219 ✘ desplaza | 1191 ✘ desplaza | table 3926 px; market_dashboard 1136 px |
| 2 | precios-e-inflacion | 920 ✘ desplaza | 920 ✘ desplaza | 895 ✘ vacío 21 % | ctx_main 626 px; inf_card_0 276 px |
| 3 | pipeline-y-linaje | 994 ✘ desplaza | 994 ✘ desplaza | 1175 ✘ desplaza | card_pipeline_main 705 px; svg 433 px |
| 4 | modelo-de-datos | 966 ✘ desplaza | 966 ✘ desplaza | 936 ✘ vacío 16 % | iframe 660 px; svg 627 px |
| 5 | calidad-y-auditoria | 1550 ✘ desplaza | 1550 ✘ desplaza | 1528 ✘ desplaza | iframe 830 px; div[stHorizontalBlock].st-key-qa_evidence 74 px |
| 6 | consultas-sql | 1532 ✘ desplaza | 1532 ✘ desplaza | 1510 ✘ desplaza | sqlx_studio 1031 px; sqlx_body 915 px |
| 7 | sad | 2907 ✘ desplaza | 2907 ✘ desplaza | 2885 ✘ desplaza | project_document 2323 px; svg 692 px |
| 8 | centro-de-operacion | 1255 ✘ desplaza | 1255 ✘ desplaza | 1267 ✘ desplaza | iframe 577 px; svg 571 px |
| 9 | mapa-de-seguridad | 1190 ✘ desplaza | 1190 ✘ desplaza | 1168 ✘ desplaza | iframe 590 px; svg 519 px |
| 10 | plan-de-pruebas | 3029 ✘ desplaza | 3029 ✘ desplaza | 3006 ✘ desplaza | project_document 2406 px; table 623 px |
| 11 | stack-y-evidencia | 656 ✔ | 656 ✘ vacío 30 % | 633 ✘ vacío 44 % | svg 16 px |
| 12 | prd | 3732 ✘ desplaza | 3732 ✘ desplaza | 3709 ✘ desplaza | project_document 3147 px; iframe 720 px |
| 13 | adr | 1535 ✘ desplaza | 1535 ✘ desplaza | 1512 ✘ desplaza | project_document 950 px; table 788 px |
| 14 | escalabilidad | 1147 ✘ desplaza | 1147 ✘ desplaza | 1125 ✘ desplaza | project_document 619 px; table 191 px |
| 15 | github | 1095 ✘ desplaza | 1095 ✘ desplaza | 1072 ✔ | iframe 758 px; svg.gh-hero-art 210 px |

## Texto menor de 11 px, superposiciones y recortes (peor caso de ambos temas, 3 pantallas)

| # | Página | Texto < 11 px | Texto × texto | Texto × ícono | Texto recortado | SVG fuera de la ventana |
|--:|---|--:|--:|--:|--:|---|
| 1 | resumen-semanal | 21 | 2 | 0 | 0 | — |
| 2 | precios-e-inflacion | 5 | 0 | 0 | 0 | — |
| 3 | pipeline-y-linaje | 105 | 0 | 0 | 0 | — |
| 4 | modelo-de-datos | 3 | 0 | 0 | 0 | — |
| 5 | calidad-y-auditoria | 23 | 5 | 0 | 0 | — |
| 6 | consultas-sql | 23 | 0 | 0 | 4 | — |
| 7 | sad | 171 | 0 | 0 | 0 | — |
| 8 | centro-de-operacion | 5 | 0 | 0 | 0 | — |
| 9 | mapa-de-seguridad | 1 | 0 | 0 | 0 | — |
| 10 | plan-de-pruebas | 8 | 4 | 0 | 0 | — |
| 11 | stack-y-evidencia | 0 | 0 | 0 | 0 | — |
| 12 | prd | 0 | 0 | 0 | 0 | — |
| 13 | adr | 0 | 0 | 0 | 0 | — |
| 14 | escalabilidad | 0 | 0 | 0 | 0 | — |
| 15 | github | 0 | 0 | 0 | 0 | — |

## Teléfono (Vantablack): alto natural / ventana

| # | Página | 390 × 844 | 844 × 390 |
|--:|---|---|---|
| 1 | resumen-semanal | 1694 / 844 | 1581 / 629 |
| 2 | precios-e-inflacion | 2902 / 844 | 911 / 629 |
| 3 | pipeline-y-linaje | 2073 / 844 | 2423 / 629 |
| 4 | modelo-de-datos | 1116 / 844 | 956 / 629 |
| 5 | calidad-y-auditoria | 1939 / 844 | 1540 / 629 |
| 6 | consultas-sql | 2464 / 844 | 1524 / 629 |
| 7 | sad | 2553 / 844 | 2535 / 629 |
| 8 | centro-de-operacion | 2027 / 844 | 1280 / 629 |
| 9 | mapa-de-seguridad | 1574 / 844 | 1181 / 629 |
| 10 | plan-de-pruebas | 4844 / 844 | 2975 / 629 |
| 11 | stack-y-evidencia | 1336 / 844 | 646 / 629 |
| 12 | prd | 5187 / 844 | 3632 / 629 |
| 13 | adr | 2807 / 844 | 1440 / 629 |
| 14 | escalabilidad | 1995 / 844 | 1093 / 629 |
| 15 | github | 1754 / 844 | 1565 / 629 |

## Cómo leer los incumplimientos

- **Texto × texto reales:** Resumen semanal (2), Calidad y auditoría (5: las etiquetas de los controles se montan sobre la leyenda «✓ comprobado aquí…»), Plan de pruebas (4: «prueba ↗» contra el texto del mapa de seguridad).
- **Texto × ícono: 0 reales.** La sonda marcó 9 casos en Mapa de seguridad y Plan de pruebas, pero son el «✓» dentro de su propio ícono `qa-icon`; se excluyen los glifos de uno o dos caracteres. Limitación: un ícono dibujado con trazos dentro de un SVG grande (`path`, `g`) no se detecta como ícono; esos casos se revisan a ojo con la captura.
- **Pipeline y linaje:** la sonda no encuentra etiquetas superpuestas (30 %); las que «se pegan» entre sí en Staging e Intermedio están cerca, no encima. Se revisarán en la Etapa 2 con la captura.
- **Consultas SQL, 4 «recortes»:** son líneas largas del editor (`pre.sqlx-code`), que se desplazan. Probablemente no son defecto; se confirma en la Etapa 4.
- **Texto menor de 11 px:** Pipeline y linaje (105), SAD (171), Calidad y auditoría (23), Consultas SQL (23), Resumen (21), Plan de pruebas (8), Precios e inflación (5), Centro de operación (5), Modelo de datos (3), Mapa de seguridad (1). Son recuentos de textos distintos, no de píxeles. PRD, ADR, Escalabilidad, Stack y GitHub: 0.

## Qué se toca y qué no

- **Ya cumple, no se toca:** ninguna página cumple el criterio completo en las tres pantallas. Stack y evidencia cumple a 1440 × 700 y solo falla por vacío (30 % y 44 %) en pantallas más altas; GitHub cumple solo a 1920 × 1080.
- **Pasa la regla de texto, falla solo por alto:** PRD, ADR, Escalabilidad, GitHub y Stack. Son documentos y páginas de lectura: según el prompt (regla 3) pueden desplazarse dentro de su propio panel; la decisión de cómo se encajan queda para las etapas 3 y 10.
- **Etapas que cambian:** 2 (Modelo de datos y Pipeline: textos < 11 px y que el SVG quepa), 4 (Precios, Consultas SQL; Resumen no se toca salvo el menú), 5 (Centro de operación), 6 (Calidad), 8 (Seguridad y Plan de pruebas), 9 (SAD: 171 textos menores de 11 px).

## Prueba de no regresión de vistas

`tests/test_view_regression.py` dibuja Modelo estrella, Entidad-relación y Pipeline y exige que su SVG esté abierto en la página, no dentro de un `popover`, `expander` o `dialog`. Pasa en esta base y **falla en `85ca26b`** (estrella y ER): ahí el SVG seguía en el árbol, pero escondido en un botón, y por eso una prueba que solo buscara el SVG no lo habría detectado.

## Cómo repetir la medición

```
NODE_PATH=<ruta a node_modules con playwright> node tests/medicion/medir.cjs <carpeta>
PAGES=3,4 THEMES=Vantablack node tests/medicion/medir.cjs <carpeta>   # solo algunas páginas (índice desde 0)
python tests/medicion/tabla.py <carpeta>/medicion.json
```
