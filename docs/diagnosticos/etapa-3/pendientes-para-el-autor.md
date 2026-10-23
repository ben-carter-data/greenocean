# Etapa 3 · Lo que el PRD no cubre y necesita al autor

El PRD no se rellena con lo que falta: se lista aquí.

## 1. «Precios e inflación» no responde ninguna pregunta del PRD

Desde D-163 esa página responde «¿Qué alimentos subieron más que la inflación?». El PRD decía que ahí se respondían P-2 («¿El precio de hoy es normal para la temporada?») y P-3 («¿Cuánto paga el consumidor sobre el mayorista?»). Eso ya no es cierto.

- **Qué se hizo:** P-2 y P-3 apuntan a donde hoy se responden de verdad: las consultas de ejemplo «Precio vs. época» y «Brecha mayorista» del estudio SQL (cada una la ejecuta `tests/test_sql_explorer.py`).
- **Falta decidir:** la pregunta que sí responde «Precios e inflación» no está en el PRD. No se agregó una P-4 porque sería inventar un requisito: ¿la agregas tú?
- **Falta decidir:** `bi/dashboard.py` conserva `read_context_model` (rango habitual y brecha por canal, de la antigua página de contexto) sin ninguna pantalla que lo use. ¿Se retira o se vuelve a mostrar en alguna página?

## 2. Requisitos sin prueba automática

| Requisito | Qué falta |
|---|---|
| RNF-01 · Costo cero y sin vencimientos | Solo lo respalda ADR-31; no hay una comprobación automática. |
| RNF-02 · Cada vista en una pantalla de 1440 × 900 | Se mide con `tests/medicion/medir.cjs`, que no es pytest. Varias vistas se siguen desplazando (los documentos largos, el Resumen semanal y Consultas SQL con resultados, entre otras); la medición completa está en `docs/diagnosticos/etapa-0/informe.md`, hecha antes de las etapas 1 a 6, y se repite en la Etapa 11. |

## 3. Un caso de uso que no es una pantalla del panel

«Mantener el código y los secretos» (del administrador) ocurre en GitHub y en Streamlit Cloud, no en el panel. El diagrama lo dice («GitHub, fuera del panel»).

## 4. El PRD pasa de 2 a 3 páginas en el PDF

La regla de D-210 es de dos páginas como máximo. Las tablas de trazabilidad y de requisitos medibles añaden una página y ningún recorte de una sola sección la devuelve a dos. Se permite 3 solo para el PRD hasta que el PDF sea una impresión de la página (Etapa 10). Se retiró «Visión y misión», que no es problema, usuarios ni requisitos. Las cuatro capturas de pantallas siguen en el PRD: salen o se quedan cuando apruebes la tabla de la Etapa 10.

## Resuelto después

- RF-03 ya tiene prueba: `tests/test_pipeline_gate.py` (D-245).
- P-4 entró al PRD y el código sin pantalla se borró (D-244).
