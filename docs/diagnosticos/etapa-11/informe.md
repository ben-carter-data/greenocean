# Etapa 11 · Revisión global de la optimización

Fecha: 24-10-2026. Punto de partida: D-229 (commit `53d9cc7`, el último publicado en GitHub). Resultado: D-230 a D-251, en commits locales que esperan la revisión del autor antes del push.

## 1. Qué cambió, etapa por etapa

| Etapa | Decisiones | Qué cambió |
|---|---|---|
| 0 · Medición | D-230 | Medición de las 15 páginas (`tests/medicion/medir.cjs`), capturas de referencia y prueba de no regresión de vistas. |
| 1 · Menú | D-231 | Menú lateral plano por tipo de lector, con ícono pequeño al plegarse. |
| 2 · Diagramas de ingeniería de datos | D-232, D-236 a D-239 | Estrella, entidad-relación y pipeline a todo el ancho con zoom; «Dónde viven los datos» como arquitectura de almacenamiento; «Cruces entre bases» como bases en capas con líneas entre tablas. |
| 3 · Análisis de negocio y PRD | D-240, D-244 | Casos de uso, trazabilidad y requisitos medibles; P-4 en el PRD; cada respuesta recalculada por otro camino; sin código muerto. |
| 4 · BI | D-233 a D-235 | Precios e inflación, Consultas SQL, Centro de operación y Calidad y auditoría caben en la ventana. |
| Calidad y auditoría | D-241 | Sin huecos, aviso preciso de las huellas y toda la evidencia a la vista. |
| SAD · contexto | D-242 | El SAD abre con el diagrama de contexto del sistema (C4, nivel 1). |
| 5 · DevOps | D-243 | Diagrama de CI/CD con su definición, desde los workflows reales. |
| 6 · Calidad de datos | D-245 | Puertas de calidad sobre el recorrido; RF-03 con su prueba. |
| 7 · Orquestación | D-246 | La orquestación del workflow semanal, dentro del diagrama de CI/CD. |
| 8 · Seguridad y monitoreo | D-249 | Arquitectura de seguridad como proceso (amenaza, mitigación, verificación, activo y mejora continua), procedimiento de pruebas, pestaña Monitoreo, clave sin límite de intentos por decisión del autor. |
| 9 · SAD | D-247 | El SAD por vistas, con contenedores (C4, nivel 2), sin copiar diagramas. |
| 10 · Documentos | D-248 | ADR al formato estándar; el PDF es la página impresa. |
| 11 · Revisión global | D-250 | Esta revisión; la ruta de cada página y su pie siguen al menú. |

Los datos no cambiaron: `etl/`, `agent/` y `dbt/` están igual que en D-229. En `.github/workflows/semanal.yml` cambió solo un comentario (la hora de Chile).

## 2. Medición final

Las 15 páginas del menú, en Vantablack y Blue Light, a 1440 × 700, 1440 × 900 y 1920 × 1080, más teléfono en vertical (390 × 844) y en horizontal (844 × 390). Capturas a 1440 × 900 en `capturas/<tema>/`; datos completos en `medicion.json`.

### Alto natural y desplazamiento (Vantablack / Blue Light si difieren)

| # | Página | 1440 × 700 | 1440 × 900 | 1920 × 1080 | Qué la hace crecer (1440 × 900) |
|--:|---|---|---|---|---|
| 1 | resumen-semanal | 1200 ✘ desplaza | 1219 ✘ desplaza | 1191 ✘ desplaza | table 3926 px; market_dashboard 1136 px |
| 2 | precios-e-inflacion | 699 ✔ | 895 ✔ | 1049 ✔ | ctx_main 600 px; inf_card_0 263 px |
| 3 | pipeline-y-linaje | 720 ✘ desplaza | 893 ✔ | 1080 ✔ | card_pipeline_main 661 px; svg 433 px |
| 4 | modelo-de-datos | 659 ✔ | 856 ✔ | 1039 ✔ | architecture_diagram 600 px; svg 537 px |
| 5 | calidad-y-auditoria | 1220 ✘ desplaza | 1220 ✘ desplaza | 1167 ✘ desplaza | iframe 600 px; div[stHorizontalBlock].st-key-qa_evidence 150 px |
| 6 | consultas-sql | 809 ✘ desplaza | 1009 ✘ desplaza | 1174 ✘ desplaza | sqlx_studio 726 px; sqlx_body 610 px |
| 7 | sad | 3133 ✘ desplaza | 3133 ✘ desplaza | 3110 ✘ desplaza | project_document 2540 px; iframe 650 px |
| 8 | centro-de-operacion | 819 ✘ desplaza | 819 ✘ vacío 12 % | 1013 ✔ | svg 428 px; compact_footer 97 px |
| 9 | mapa-de-seguridad | 941 ✘ desplaza | 941 ✘ desplaza | 926 ✘ vacío 17 % | iframe 620 px; svg 608 px |
| 10 | plan-de-pruebas | 2737 ✘ desplaza | 2737 ✘ desplaza | 2714 ✘ desplaza | project_document 2144 px; table 831 px |
| 11 | stack-y-evidencia | 577 ✘ vacío 21 % | 577 ✘ vacío 39 % | 562 ✘ vacío 50 % | compact_footer 97 px |
| 12 | prd | 4405 ✘ desplaza | 4405 ✘ desplaza | 4383 ✘ desplaza | project_document 3813 px; iframe 720 px |
| 13 | adr | 3709 ✘ desplaza | 3709 ✘ desplaza | 3686 ✘ desplaza | project_document 3116 px |
| 14 | escalabilidad | 1200 ✘ desplaza | 1200 ✘ desplaza | 1178 ✘ desplaza | project_document 639 px; table 191 px |
| 15 | github | 1095 ✘ desplaza | 1095 ✘ desplaza | 1072 ✔ | iframe 758 px; svg.gh-hero-art 210 px |

### Texto menor de 11 px, superposiciones y recortes (peor caso de ambos temas, 3 pantallas)

| # | Página | Texto < 11 px | Texto × texto | Texto × ícono | Texto recortado | SVG fuera de la ventana |
|--:|---|--:|--:|--:|--:|---|
| 1 | resumen-semanal | 21 | 2 | 0 | 0 | — |
| 2 | precios-e-inflacion | 5 | 0 | 0 | 0 | — |
| 3 | pipeline-y-linaje | 105 | 0 | 0 | 0 | — |
| 4 | modelo-de-datos | 43 | 0 | 0 | 0 | — |
| 5 | calidad-y-auditoria | 58 | 5 | 0 | 0 | — |
| 6 | consultas-sql | 23 | 20 | 0 | 94 | — |
| 7 | sad | 0 | 0 | 0 | 0 | — |
| 8 | centro-de-operacion | 62 | 0 | 0 | 0 | — |
| 9 | mapa-de-seguridad | 0 | 0 | 0 | 0 | — |
| 10 | plan-de-pruebas | 0 | 0 | 0 | 0 | — |
| 11 | stack-y-evidencia | 0 | 0 | 0 | 0 | — |
| 12 | prd | 0 | 0 | 0 | 0 | — |
| 13 | adr | 0 | 0 | 0 | 0 | — |
| 14 | escalabilidad | 0 | 0 | 0 | 0 | — |
| 15 | github | 0 | 0 | 0 | 0 | — |

### Teléfono (Vantablack): alto natural / ventana

| # | Página | 390 × 844 | 844 × 390 |
|--:|---|---|---|
| 1 | resumen-semanal | 1748 / 844 | 1581 / 629 |
| 2 | precios-e-inflacion | 2615 / 844 | 689 / 629 |
| 3 | pipeline-y-linaje | 2021 / 844 | 2307 / 629 |
| 4 | modelo-de-datos | 844 / 844 | 629 / 629 |
| 5 | calidad-y-auditoria | 1883 / 844 | 1195 / 629 |
| 6 | consultas-sql | 1729 / 844 | 741 / 629 |
| 7 | sad | 4455 / 844 | 2954 / 629 |
| 8 | centro-de-operacion | 844 / 844 | 816 / 629 |
| 9 | mapa-de-seguridad | 1224 / 844 | 917 / 629 |
| 10 | plan-de-pruebas | 6088 / 844 | 2597 / 629 |
| 11 | stack-y-evidencia | 1271 / 844 | 629 / 629 |
| 12 | prd | 8317 / 844 | 4223 / 629 |
| 13 | adr | 6668 / 844 | 3555 / 629 |
| 14 | escalabilidad | 2099 / 844 | 1126 / 629 |
| 15 | github | 1792 / 844 | 1565 / 629 |

## 3. Frente a la Etapa 0

| Página | Texto < 11 px (Etapa 0 → hoy) | Superposiciones de texto (Etapa 0 → hoy) | Causa |
|---|---|---|---|
| SAD | 171 → 0 | 0 → 0 | Diagramas a todo el ancho y texto a tamaño real (D-247). |
| Arquitectura de seguridad | 1 → 0 | 0 → 0 | Nuevo diagrama (D-249). |
| Plan de pruebas de seguridad | 8 → 0 | 4 → 0 | Ya no copia el mapa; enlaza a la página (D-249). |
| PRD | 0 → 0 | 0 → 0 | Casos de uso a 11,2 px (D-250); llegó a 17 entre medio. |
| Modelo de datos | 3 → 3 a 1440 × 900 | 0 → 0 | A 1440 × 700 la estrella se reduce para caber y llega a 43. |
| Calidad y auditoría | 23 → 58 | 5 → 5 | La franja de puertas de calidad (D-245) usa textos de 9,5 a 10,4 px. Las 5 superposiciones son la parte oculta de nombres cortados con «…»: en pantalla no se tocan. |
| Centro de operación | 5 → 62 | 0 → 0 | La pestaña Despliegue, que se abre primero, muestra ahora solo el diagrama de despliegue (D-249); sus textos son de 9,7 px y menos. A 1920 × 1080 queda en 1. |
| Consultas SQL | 23 → 23 | 0 → 20 | El explorador de objetos es una lista con desplazamiento propio (610 px visibles de 915 a 1440 × 900); lo que la medición cuenta como superpuesto o recortado está fuera de su área visible. No es un defecto. |
| Pipeline y linaje | 105 → 105 | 0 → 0 | Sin cambios: diagrama denso con zoom. |
| Resumen semanal | 21 → 21 | 2 → 2 | Referencia fija; no se toca. |

## 4. Resumen semanal frente a su captura de referencia

Idéntico en los dos temas salvo la línea de la ruta, que dice «Negocio · BI › Resumen semanal» en vez de «Dashboard › Resumen semanal» (D-250). Todos los píxeles distintos están dentro de esa franja (alto de 4 a 44 px de la zona principal).

## 5. Documentos impresos

`tests/medicion/imprimir.cjs` imprime con Chrome el PRD, el SAD, el ADR, el Plan de pruebas de seguridad y Escalabilidad, y compara títulos y diagramas con la página y con su `.md`. Los cinco dan OK.

## 6. Pruebas

pytest: 589 pasan y 1 se omite, en unos 46 segundos. GitHub Actions (consultado el 24-10-2026 en la API pública): la última carga semanal programada (martes 20-10-2026) terminó bien, y también la última ejecución de `pruebas.yml` tras un push (`53d9cc7`). Los commits D-230 a D-250 aún no se suben, así que el CI no los ha corrido. `dbt parse` no corrió en este computador: el entorno `.venv-dbt` apunta a la carpeta antigua del proyecto; el CI lo corre en cada push.

## 7. Lo que queda abierto

| Tema | Estado | Qué haría falta |
|---|---|---|
| Diagramas densos: Pipeline y linaje (8,7 a 10,9 px), Despliegue (9,7 px y menos) y la franja de puertas de Calidad y auditoría (9,5 a 10,4 px) | Se leen con su zoom (+ y −). | Rediseñarlos con menos texto por caja o en más de una vista; subir la letra sin rediseñar desborda las cajas. Es el lugar natural para el diagrama global de arquitectura que propuso el autor. |
| Textos de 10 a 10,9 px en el Resumen (21), Precios e inflación (5, números del eje) y Consultas SQL (23) | A medio punto del mínimo. | El Resumen es la referencia fija; los otros dos son ajustes pequeños. |
| Modelo de datos a 1440 × 700 | Resuelto en D-251: la estrella vuelve a su tamaño de D-229 y la página se desplaza. | Nada. |
| Once vistas antiguas sin enlace desde el menú: Datos, Esta semana, Brecha de precio, Canales y regiones, Alertas, Portada, Definición del proyecto, Reglas de calidad, Manual, Glosario y la antigua DevOps y seguridad | Se abren solo desde direcciones guardadas (D-065). Usan 27 funciones (369 líneas) que ninguna página del menú usa. «Indicadores explicados» y «Documentación» sí tienen enlaces desde el Resumen y se mantienen. | Retirarlas y llevar sus direcciones a la página del menú más cercana. Cambia adónde llegan esos enlaces antiguos, así que lo decide el autor. |
| Teléfono en vertical | Las superposiciones medidas son con el aviso «Gira tu teléfono», que tapa la app a propósito (D-166). | Nada. |

## 8. Límites de esta revisión

La medición corre en Chrome sin ventana, en macOS, contra el panel local con la base del 20-10-2026; otro sistema puede tener otras fuentes y medir distinto. La app publicada en Streamlit Community Cloud no se midió: tendrá estos cambios cuando el autor los revise y los suba.

## 9. Después del informe: D-251

El autor pidió que el pipeline, el modelo estrella y el Centro de operación volvieran a como estaban en D-229. Se restauraron y se comprobaron contra D-229 (ver D-251). Por eso, en las tablas de arriba cambian tres filas: Pipeline y linaje vuelve a desplazarse a 1440 × 900 (como en D-229); el Centro de operación abre en «Operación», sin el texto chico del diagrama de despliegue en la primera vista; y la estrella vuelve a su tamaño de D-229, con la página que se desplaza para verla completa.
