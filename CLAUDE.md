# CLAUDE.md · GreenOcean

Guía para trabajar en este repositorio, también desde una sesión en la nube que lo clona desde GitHub.

## Qué es

GreenOcean es un proyecto de portafolio de ingeniería de datos: un pipeline semanal y un panel de BI sobre los precios de alimentos de Chile.

- **Fuentes:** ODEPA (precios mayoristas y al consumidor, CSV públicos) y el IPC de alimentos del INE (para precios reales).
- **Pipeline:** ingesta en Python → aterrizaje `etl/raw.db` (SQLite) → bronce en Parquet → dbt Core sobre DuckDB (staging → intermedio → marts, 31 pruebas) → base servida `etl/datos.duckdb`.
- **Panel:** Streamlit (`bi/dashboard.py`), que lee `etl/datos.duckdb` en solo lectura.
- **Orquestación:** GitHub Actions, cada martes (`.github/workflows/semanal.yml`).
- **Documentos del proyecto:** `docs/PRD.md`, `docs/SAD.md`, `docs/ADR.md` y `docs/SEGURIDAD.md` (plan de pruebas de seguridad). Todas las decisiones están en `docs/DECISIONES.md` (D-001 … D-220). `docs/PROMPT_EVOLUCION.md` es el plan de la refonte (pasos 0 a 7, hechos).

## Instalar y ejecutar

| Para qué | Comando |
|---|---|
| Panel y pruebas | `pip install -r requirements.txt` |
| Pipeline con dbt | `pip install -r requirements-pipeline.txt` (dbt no se instala en Python 3.14: usar 3.11 o 3.12) |
| Abrir el panel | `streamlit run bi/dashboard.py` |
| Pruebas | `python -m pytest -q` (unas 640, entre 2 y 4 minutos) |
| Compilar el proyecto dbt | `dbt parse --project-dir dbt --profiles-dir dbt` |
| Descargar ODEPA | `python agent/agent.py` |
| ETL de respaldo (SQLite) | `python etl/etl.py` |
| Construir el data warehouse | `python etl/pipeline.py` (registra una carga en `etl_run`) |
| Reconstruir en local sin registrar carga | `python etl/pipeline.py --local` |

En el computador del autor, dbt corre en un entorno aparte: `DBT_BIN=$PWD/.venv-dbt/bin/dbt python etl/pipeline.py --local`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `agent/` | Descarga de ODEPA (`agent.py`, `input.csv`, `downloads/manifest.json`) |
| `etl/` | `etl.py` (respaldo SQLite), `bronze.py` (Parquet), `ine.py` (IPC), `pipeline.py` (dbt build y publicación), `datos.duckdb` (base servida), `datos.db` (respaldo) |
| `dbt/` | Proyecto dbt: `models/staging`, `models/intermediate`, `models/marts`, `tests/`, `macros/`, `profiles.yml` |
| `bi/` | Panel: `dashboard.py` (páginas y navegación), `queries.sql` y `queries.py` (SQL), diagramas SVG (`architecture.py`, `lineage.py`, `star_model.py`, `doc_diagrams.py`, `devops.py`), vistas (`home_mockup.py`, `quality_view.py`, `github_page.py`), `tech_glossary.py`, `zoom.py` (zoom y explicaciones al pasar el cursor), `document_pdf.py` (PDF de los documentos) |
| `tests/` | pytest: auditoría de cifras (`test_data_audit.py`), paridad SQLite ↔ DuckDB, IPC, linaje, diagramas, documentos y panel (AppTest) |
| `docs/` | PRD, SAD, ADR, DECISIONES, MANUAL, plan de evolución |
| `.github/workflows/` | `semanal.yml` (carga semanal), `pruebas.yml` (pytest + dbt parse en cada push) |

## Convenciones

- **Idioma:** todo en español (panel, documentos, decisiones y mensajes de commit). El código y sus comentarios, en inglés.
- **Vocabulario:** pipeline, workflow, ingesta, ETL, staging, data warehouse. Nunca «robot».
- **Autoría:** «el autor». Ningún nombre personal en el panel ni en los documentos, y nada inventado sobre él.
- **Datos:** nunca inventar una cifra ni interpolar un precio; nunca borrar histórico. Cada cifra del panel debe poder recalcularse desde la fuente; las pruebas lo verifican.
- **Cada cambio de comportamiento** lleva su entrada `## D-xxx · título` en `docs/DECISIONES.md`, con sus pruebas en verde.
- **Documentos:** sin bloques de código. Diagramas con marcadores `[[diagrama:nombre]]` en su propia línea: las vistas de `bi/doc_views.py` (actores y mockups, con el estilo del pipeline) o los diagramas vivos `plataforma`, `pipeline`, `modelo` y `seguridad`. Los mockups son capturas reales en `docs/img/`.
- **Dependencias:** no agregar ninguna sin acuerdo del autor. Solo herramientas gratuitas y sin vencimiento; no hay nube de pago (ADR-31).
- **Commits libres; push solo después de que el autor revise la app en local.**

## Trampas conocidas del panel

- `st.html` ejecuta solo el primer `<script>` de un bloque y descarta los scripts cuyos textos JavaScript contienen etiquetas HTML. Construir el DOM con APIs (`createElement`, `textContent`) y escribir los scripts como cadenas crudas de Python (`r"""…"""`).
- Streamlit (React) es dueño del DOM que dibuja: un script puede cambiar atributos y clases, pero nunca mover ni borrar nodos. Si no, al cambiar de vista aparece `NotFoundError: removeChild`.
- `st.markdown` sanitiza SVG complejos (gradientes, filtros, botones). Por eso la página GitHub se dibuja en `st.iframe` con su propio HTML.
- `streamlit run` guarda en memoria los módulos importados y el vigilante de archivos está apagado en `.streamlit/config.toml`; desde D-172 el panel recarga en cada ejecución los `bi/*.py` que cambiaron (las fechas viven en el paquete `bi`, porque `bi/dashboard.py` se ejecuta desde cero cada vez), así que basta con volver a cargar la página.
- El contenedor de `st.markdown` lleva `margin-bottom: -1rem` para compensar el párrafo final. Un bloque HTML que termina en `div` no trae ese margen y el elemento siguiente se le monta encima: anular el margen del contenedor o cerrar con un párrafo (D-173).
- El historial de cargas (`etl_run`) solo guarda ejecuciones reales. Una reconstrucción local debe usar `--local` para no agregar una carga falsa.

- Los teléfonos (D-166): en vertical, `PHONE_LAYOUT_HTML` tapa la app con «Gira tu teléfono»; en horizontal (alto de 500 px o menos) `.stApp` se dibuja más ancho y se reduce con `transform: scale(.62)`, y los contenedores que Streamlit mide con la altura de la pantalla crecen con la escala. Revisar los dos casos en 390 × 844 y 844 × 390.
- Una dependencia sin versión máxima puede romper el martes: certifi 2026.10.18 retiró la raíz de ODEPA (D-164).

## Lo que la sesión en la nube NO tendrá

| Falta | Consecuencia | Qué hacer |
|---|---|---|
| `etl/raw.db` (unos 665 MB, fuera de git, D-020) | Las pruebas que recalculan precios desde las filas crudas se saltan (skip) | Normal; el resto de la auditoría corre con `datos.duckdb` |
| `agent/downloads/*.csv` | No hay CSV de ODEPA locales | `python agent/agent.py` los descarga, si hay red hacia datos.odepa.gob.cl |
| `etl/bronze/` y `etl/warehouse_build.duckdb` | No se puede correr `dbt build` de inmediato | Necesita `raw.db` (ingesta) más `pip install -r requirements-pipeline.txt` |
| `.venv` y `.venv-dbt` | Sin entornos | Crear uno nuevo con Python 3.11 o 3.12 e instalar los requirements |
| `.streamlit/secrets.toml` (`GITHUB_TOKEN`, `CONTROL_CODE`) | El Centro de operación lee GitHub sin clave (60 consultas por hora) y el botón «Ejecutar pipeline ahora» queda inactivo | Esperado; nunca crear ni subir secretos |
| `docs/privado/` | Notas privadas del autor, ignoradas por git | Ninguna |
| Chrome con depuración en el puerto 9333 | No hay capturas de pantalla automáticas | Revisar con AppTest y con las pruebas |

Sí están en el repositorio: `etl/datos.duckdb` (la base servida, unos 14 MB), `etl/datos.db` (respaldo SQLite) y `agent/downloads/manifest.json`. Con ellos el panel y casi todas las pruebas funcionan sin red.
