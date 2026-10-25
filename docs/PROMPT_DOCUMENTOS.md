# Prompt · Documentos de verdad, carpeta de documentos y mapa completo de la app

Prompt para una sesión de Claude Code en el repositorio GreenOcean. Léelo entero antes de empezar; trabaja por etapas, con un commit y una entrada D-xxx por etapa.

## 0. Antes de tocar nada

1. Lee `CLAUDE.md` (reglas del proyecto) y la memoria del proyecto. Las reglas que más pesan aquí:
   - **Coherencia primero:** ninguna contradicción entre páginas, documentos y código; cada cifra se lee de la base o del repositorio y una prueba la recalcula. Nunca inventar una cifra, un historial ni una alternativa «evaluada».
   - **Una pantalla:** cada página principal se ve entera sin desplazar a **1440 × 790** (la ventana real del navegador en una pantalla de 1440 × 900) y a 1920 × 1000. Nunca medir a 1440 × 900.
   - **Mínimo texto en pantalla:** lo largo va al pasar el cursor. Respuestas al autor, breves.
   - **No tocar lo aprobado:** el pipeline (D-229), el modelo estrella y la pestaña Operación conservan su dibujo.
   - **Sin dependencias nuevas** sin acuerdo del autor; solo herramientas gratuitas y sin vencimiento.
   - **Cada cambio de comportamiento** lleva su `## D-xxx · título` en `docs/DECISIONES.md` y sus pruebas en verde (`python -m pytest -q`).
   - **Commits libres; push solo cuando el autor revise en local.**
2. Mide el estado actual antes de cambiar (tamaños, alturas, rutas). La herramienta: Playwright de fuera del proyecto (`NODE_PATH=/Users/carter/.npm/_npx/e41f203b7505f1fb/node_modules`) y `tests/medicion/medir.cjs`.

## 1. Cómo está hoy (verifícalo, no lo supongas)

- **Menú** (`MENU_BLOCKS` en `bi/dashboard.py`): los documentos están repartidos. El SAD está en «Ingeniería de datos»; PRD, ADR y Escalabilidad, en «Análisis de negocio · BA»; el Plan de pruebas de seguridad, en «DevOps y seguridad».
- **Páginas de documentos:** `PROJECT_DOCUMENTS` y `show_project_document` dibujan `docs/PRD.md`, `docs/SAD.md`, `docs/ADR.md` y `docs/SEGURIDAD.md`. Escalabilidad sale de la sección `### Escalabilidad` de `docs/DECISIONES.md` (`show_scalability_page`). Los diagramas entran con marcadores `[[diagrama:nombre]]` (vistas de `bi/doc_views.py`) y los enlaces a páginas con `[[vista:Página del menú]]`. Desde D-269 no tienen fila de ruta ni «Volver».
- **Descarga:** el botón «Imprimir o guardar como PDF» imprime la página misma (D-248, `PRINT_DOCUMENT_CSS`, `PRINT_BUTTON_HTML`). Hay que conservarlo.
- **Otros documentos del repositorio:** `MANUAL.md` (operación), `PROYECTO.md` (guía y glosario; el panel lee partes de él), `DECISIONES.md` (registro D-001 en adelante), `DISENO.md`, `BACKLOG.md`, `hito-1..4.md` y `PROMPT_EVOLUCION.md` (historia del proyecto).
- **Pruebas que los vigilan:** `tests/test_documents.py`, `tests/test_prd_traceability.py`, `tests/test_doc_diagrams.py`, `tests/test_documents.py::test_d248_*` (impresión).
- **Incoherencia conocida:** el subtítulo del ADR en `PROJECT_DOCUMENTS` dice «Las diez decisiones», pero desde D-270 son once (ADR-35). Corrígela y haz que el número se cuente, no se escriba.

## 2. Etapa A · Una sola carpeta «Documentos»

**Objetivo:** todos los documentos en un solo lugar del menú, y solo documentos, presentados como una carpeta (Finder de macOS o árbol de archivos de GitHub).

1. Crea el bloque de menú **«Documentos»** con una sola entrada que abre la carpeta. Saca de los otros bloques el SAD, el PRD, el ADR, Escalabilidad y el Plan de pruebas de seguridad. Si un bloque queda vacío (por ejemplo, «Análisis de negocio · BA»), retíralo y ajusta `MENU_ORDER`, los pies «Anterior / Siguiente» (D-250) y las pruebas del menú.
2. **La página carpeta:**
   - Una cuadrícula (o lista, con un selector entre las dos vistas, como en Finder) de «archivos». Cada archivo muestra un ícono de documento por tipo (requisitos, arquitectura, decisiones, seguridad, operación, crecimiento), su nombre, una línea de qué contiene, su versión y fecha (leídas del propio archivo), y su tiempo de lectura o número de secciones (calculados).
   - Acciones finas en cada archivo: **Abrir**, **PDF** (la impresión de D-248) y **GitHub** (el archivo en el repositorio).
   - Encabezado tipo ruta de carpeta: `GreenOcean / docs`, con el número de documentos y la fecha del último cambio.
   - Al pasar el cursor, una vista previa: el índice de secciones del documento.
3. **Al abrir un documento:** su página actual, con una ruta fina «Documentos / PRD» que vuelve a la carpeta (esta relación sí justifica un regreso) y, al pie, el anterior y el siguiente dentro de la carpeta.
4. **Qué documentos entran:** PRD, SAD, ADR, Escalabilidad, Plan de pruebas de seguridad, Manual de operación y Registro de decisiones (este último con un índice navegable de sus D-xxx, no como un muro de texto). Escalabilidad pasa a su propio archivo `docs/ESCALABILIDAD.md` (hoy es una sección de DECISIONES.md); actualiza las pruebas que leen esa sección. `DISENO.md`, `BACKLOG.md`, `hito-*.md` y los prompts quedan en el repositorio, fuera de la carpeta: pregunta al autor si quiere una subcarpeta «Historia del proyecto» con ellos.
5. **Las direcciones antiguas** de cada documento siguen funcionando y llevan a su nueva ubicación.
6. **Pruebas:** cada documento de la carpeta existe en `docs/`, abre su página y tiene su PDF; ninguna página de documento queda fuera de la carpeta; ningún documento queda en otro bloque del menú; la versión y la fecha mostradas son las del archivo.

## 3. Etapa B · Documentos de verdad

**Objetivo:** que cada documento resista la lectura de un revisor exigente (dirección técnica, gerencia, reclutador senior): completo, riguroso, coherente con el código y escrito para personas.

Para **cada** documento:

1. **Ficha inicial** en una tabla corta: propósito, audiencia, alcance, estado, versión, fecha, responsable («el autor»; ningún nombre personal) y documentos relacionados.
2. **Historial de versiones** al final: versión, fecha y qué cambió, con enlaces a las D-xxx correspondientes.
3. **Estructura estándar de su tipo**, adaptada sin relleno:
   - PRD: problema, objetivos y métricas de éxito, usuarios, alcance, preguntas de negocio, requisitos funcionales y no funcionales trazables, supuestos y límites, pantallas, próximos pasos.
   - SAD: arc42 con vistas C4 (contexto, contenedores; componentes solo si aportan), principios, ejecución, despliegue, calidad y observabilidad, seguridad, riesgos y deuda técnica, glosario.
   - ADR: formato de Nygard o MADR, un registro por decisión, con estado, contexto, decisión, alternativas reales y consecuencias; un índice al inicio.
   - Plan de pruebas de seguridad: objetivo y alcance, amenazas (enlazadas a la vista), procedimiento, casos con resultado esperado y obtenido, criterios de aceptación, límites y riesgos aceptados.
   - Manual de operación: qué hacer en cada falla, paso a paso (*runbook*), cómo se recupera, a quién avisa.
   - Escalabilidad: qué se agregaría, qué cede primero, umbrales medibles, y cuándo valdría una nube (ADR-31).
4. **Cada afirmación verificable:** si dice una cifra, una prueba la compara con la base o el repositorio; si nombra un archivo, una prueba exige que exista; si dice que algo pasa (por ejemplo, dónde queda una carga fallida), el código debe hacerlo. Revisa en especial lo que cambió en D-264 a D-277 (barras de encabezado, release «base-actual», Calidad como pipeline, Monitoreo, CI/CD, ventana de 1440 × 790).
5. **Tono:** humano, claro y profesional, en español; frases cortas; sin jerga sin explicar; sin bloques de código; los diagramas por marcador.
6. **Pruebas:** amplía `tests/test_documents.py` para la ficha, el historial y la estructura de cada tipo, y mantén las de trazabilidad.

## 4. Etapa C · Enlaces y botones finos, modernos

**Objetivo:** un solo componente de enlace y botón para todo el panel, fino y de aire futurista, en lugar de los estilos dispersos de hoy (acciones de documento, «Anterior / Siguiente», enlaces a GitHub, «Imprimir o guardar como PDF», enlaces de las barras).

- Borde de 1 px, esquinas suaves, fondo casi transparente con un leve brillo de vidrio, ícono fino a la izquierda, y al pasar el cursor el borde y un halo en el color de acento del tema; foco visible con el teclado.
- Variantes: principal, secundario y de texto. Tamaños: compacto para barras, normal para páginas.
- Igual de legible en los cuatro temas (Corporativo, Vantablack, Blue Light, Dark Grey); contraste AA.
- Definido una sola vez (por ejemplo, en `bi/premium.css` o en un módulo pequeño) y usado en todas partes; una prueba comprueba que las páginas lo usan y no quedan estilos de enlace sueltos.

## 5. Etapa D · Mapa completo de la app, de punta a punta

**Objetivo:** una página propia, **«Mapa de la app»**, con todo el sistema en una sola vista interactiva que se explica sola, hasta la tecnología más pequeña.

1. **Qué muestra, de izquierda a derecha:** fuentes (ODEPA, INE) → ingesta (agente, `requests`, la raíz emSign de D-164, el manifiesto SHA-256) → aterrizaje (SQLite) → bronce (Parquet, `pyarrow`) → transformación (dbt Core: staging, intermedio, marts, pruebas) → data warehouse (DuckDB) → publicación (release «base-actual», puntero `etl/datos.version`, D-270) → panel (Streamlit, Altair, cada página principal) → lectores (visitante, autor). Arriba, la orquestación: GitHub Actions (cron del martes, carga manual con la clave de control, caché), y la CI (pytest, dbt parse). Abajo, lo que vigila: las tres puertas de calidad, la paridad SQLite ↔ DuckDB, la seguridad (controles de `bi/security_map.py`), la observabilidad (señales de `bi/monitoring.py`) y los documentos.
2. **Cada tecnología es un nodo**, por mínima que sea (por ejemplo `hmac.compare_digest`, `certifi`, Playwright para la medición). Al pasar el cursor dice qué es, su rol en GreenOcean, cuándo actúa y con qué se conecta; esa última lista se lee de las conexiones mismas, como en Stack y evidencia (D-266), para que el texto y el dibujo no se contradigan. Un clic abre la página del panel donde está en uso.
3. **Interacción:** filtros por capa o por tema (datos, orquestación, calidad, seguridad, observabilidad) que atenúan el resto; resaltar el camino de un nodo (sus entradas y salidas) al pasar el cursor; leyenda de los tipos de línea.
4. **Una pantalla:** cabe a 1440 × 790 sin desplazar; HTML y CSS con letras de al menos 11 px, no un SVG que se encoge; bajo 760 px de ancho se apila. Sin dependencias nuevas.
5. **Lugar en el menú:** junto a Stack y evidencia. Stack queda como el resumen de las nueve herramientas principales y enlaza al mapa, que es el detalle; evita repetir la misma vista en dos lugares.
6. **Pruebas:** toda librería de `requirements*.txt` y todo módulo de `bi/`, `etl/` y `agent/` que el mapa nombra existe; cada conexión une nodos que existen; cada archivo citado existe; cada página a la que lleva un clic está en el menú; los textos al pasar el cursor tienen las cuatro partes.

## 6. Cómo trabajar y cuándo terminar

- Orden: A, B, C, D. Al final de cada etapa: pruebas en verde, medición a 1440 × 790 y 1920 × 1000 en los cuatro temas, capturas revisadas, entrada D-xxx y commit. No hagas push.
- Pregunta al autor antes de borrar archivos, retirar vistas antiguas o cambiar algo aprobado.
- **Terminado cuando:** hay una sola carpeta «Documentos» con todos los documentos y nada más; cada documento tiene ficha, historial y estructura de su tipo, y sus afirmaciones están probadas; todos los enlaces y botones usan el mismo componente; el mapa de la app cabe en una pantalla y explica cada tecnología; la suite completa pasa.
- Informe final para el autor: corto, con lo que cambió, lo que queda pendiente y lo que necesita su decisión.
