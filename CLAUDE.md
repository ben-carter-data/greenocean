# CLAUDE.md · GreenOcean

Guía para trabajar en este repositorio, también desde una sesión en la nube que lo clona desde GitHub.

## Qué es

GreenOcean es un proyecto de portafolio de ingeniería de datos: un pipeline semanal y un panel de BI sobre los precios de alimentos de Chile.

- **Fuentes:** ODEPA (precios mayoristas y al consumidor, CSV públicos) y el IPC de alimentos del INE (para precios reales).
- **Pipeline:** ingesta en Python → aterrizaje `etl/raw.db` (SQLite) → bronce en Parquet → dbt Core sobre DuckDB (staging → intermedio → marts, 31 pruebas) → base servida `etl/datos.duckdb`, publicada en el release «base-actual» de GitHub, que cada carga reemplaza; git guarda solo su puntero `etl/datos.version` (D-270, ADR-35).
- **Panel:** Streamlit (`bi/dashboard.py`), que lee `etl/datos.duckdb` en solo lectura.
- **Orquestación:** GitHub Actions, cada martes (`.github/workflows/semanal.yml`).
- **Documentos del proyecto:** `docs/PRD.md`, `docs/SAD.md`, `docs/ADR.md`, `docs/SEGURIDAD.md` (plan de pruebas de seguridad), `docs/MANUAL.md` (runbook), `docs/ESCALABILIDAD.md`, `docs/PLAN_PRUEBAS.md`, `docs/DICCIONARIO_DATOS.md` y `docs/GLOSARIO.md`, todos con encabezado, índice, glosario e historial de versiones (D-279). Todas las decisiones están en `docs/DECISIONES.md` (D-001 … D-280); `docs/INDICE_DECISIONES.md` reúne las principales por tema. La historia del proyecto (hitos y backlog) está en `docs/historia/`; no es documentación de lectura.

## Instalar y ejecutar

| Para qué | Comando |
|---|---|
| Panel y pruebas | `pip install -r requirements.txt` |
| Pipeline con dbt | `pip install -r requirements-pipeline.txt` (dbt no se instala en Python 3.14: usar 3.11 o 3.12) |
| Abrir el panel | `streamlit run bi/dashboard.py` |
| Descargar la base de la última carga | `python bi/served_database.py` (el panel lo hace solo al arrancar) |
| Pruebas | `python -m pytest -q` (unas 630, alrededor de un minuto) |
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
| `etl/` | `etl.py` (respaldo SQLite), `bronze.py` (Parquet), `ine.py` (IPC), `pipeline.py` (dbt build y publicación), `datos.version` (puntero de la base publicada); `datos.duckdb` (base servida) y `datos.db` (respaldo) no se suben a git |
| `dbt/` | Proyecto dbt: `models/staging`, `models/intermediate`, `models/marts`, `tests/`, `macros/`, `profiles.yml` |
| `bi/` | Panel: `dashboard.py` (páginas y navegación), `queries.sql` y `queries.py` (SQL), diagramas (`architecture.py` pipeline y despliegue, `lineage.py`, `star_model.py`, `er_diagram.py`, `storage_map.py` dónde viven los datos, `database_crossings.py` cruces entre bases, `deployment.py` despliegue, `devops.py` CI/CD y orquestación, `monitoring.py` monitoreo, `security_map.py` arquitectura de seguridad, `doc_views.py` contexto, contenedores, casos de uso y procedimiento de los documentos), vistas (`home_mockup.py`, `quality_live.py`, `quality_view.py`, `github_page.py`), `page_bar.py` (la barra de encabezado de las páginas principales, D-267), `tech_glossary.py`, `zoom.py` (zoom y explicaciones al pasar el cursor) |
| `tests/` | pytest: auditoría de cifras (`test_data_audit.py`), paridad SQLite ↔ DuckDB, IPC, linaje, diagramas, documentos y su trazabilidad (`test_prd_traceability.py`), puerta de publicación (`test_pipeline_gate.py`) y panel (AppTest). `tests/medicion/`: medición del diseño con Playwright (`medir.cjs`) y comparación de cada documento impreso con su página (`imprimir.cjs`), que corren con Playwright instalado fuera del proyecto |
| `docs/` | PRD, SAD, ADR, DECISIONES, MANUAL, plan de evolución |
| `.github/workflows/` | `semanal.yml` (carga semanal), `pruebas.yml` (pytest + dbt parse en cada push) |

## Convenciones

- **Idioma:** todo en español (panel, documentos, decisiones y mensajes de commit). El código y sus comentarios, en inglés.
- **Vocabulario:** pipeline, workflow, ingesta, ETL, staging, data warehouse. Nunca «robot».
- **Autoría:** «el autor». Ningún nombre personal en el panel ni en los documentos, y nada inventado sobre él.
- **Datos:** nunca inventar una cifra ni interpolar un precio; nunca borrar histórico. Cada cifra del panel debe poder recalcularse desde la fuente; las pruebas lo verifican.
- **Cada cambio de comportamiento** lleva su entrada `## D-xxx · título` en `docs/DECISIONES.md`, con sus pruebas en verde.
- **Documentos:** sin bloques de código. Diagramas con marcadores `[[diagrama:nombre]]` en su propia línea: las vistas de `bi/doc_views.py` (`contexto`, `contenedores`, `casos`, `sop` y `mockups`). Para no copiar una vista, un documento enlaza a su página con `[[vista:Página del menú]]`. Los mockups son capturas reales de las páginas actuales en `docs/img/`, una por tema. El PDF de un documento es la página misma impresa por el navegador (botón «Imprimir o guardar como PDF», D-248).
- **Dependencias:** no agregar ninguna sin acuerdo del autor. Solo herramientas gratuitas y sin vencimiento; no hay nube de pago (ADR-31).
- **Commits libres; push solo después de que el autor revise la app en local.**

## Trampas conocidas del panel

- `st.html` ejecuta solo el primer `<script>` de un bloque y descarta los scripts cuyos textos JavaScript contienen etiquetas HTML. Construir el DOM con APIs (`createElement`, `textContent`) y escribir los scripts como cadenas crudas de Python (`r"""…"""`).
- Streamlit (React) es dueño del DOM que dibuja: un script puede cambiar atributos y clases, pero nunca mover ni borrar nodos. Si no, al cambiar de vista aparece `NotFoundError: removeChild`.
- `st.markdown` sanitiza SVG complejos (gradientes, filtros, botones). Por eso la página GitHub se dibuja en `st.iframe` con su propio HTML.
- `streamlit run` guarda en memoria los módulos importados y el vigilante de archivos está apagado en `.streamlit/config.toml`; desde D-172 el panel recarga en cada ejecución los `bi/*.py` que cambiaron (las fechas viven en el paquete `bi`, porque `bi/dashboard.py` se ejecuta desde cero cada vez), así que basta con volver a cargar la página. En la práctica, un cambio en `bi/dashboard.py` mismo no siempre se ve hasta reiniciar `streamlit run`: si una página no cambia, reiniciar el servidor antes de medir.
- El contenedor de `st.markdown` lleva `margin-bottom: -1rem` para compensar el párrafo final. Un bloque HTML que termina en `div` no trae ese margen y el elemento siguiente se le monta encima: anular el margen del contenedor o cerrar con un párrafo (D-173).
- El historial de cargas (`etl_run`) solo guarda ejecuciones reales. Una reconstrucción local debe usar `--local` para no agregar una carga falsa.

- Los teléfonos (D-166): en vertical, `PHONE_LAYOUT_HTML` tapa la app con «Gira tu teléfono»; en horizontal (alto de 500 px o menos) `.stApp` se dibuja más ancho y se reduce con `transform: scale(.62)`, y los contenedores que Streamlit mide con la altura de la pantalla crecen con la escala. Revisar los dos casos en 390 × 844 y 844 × 390.
- Una dependencia sin versión máxima puede romper el martes: certifi 2026.10.18 retiró la raíz de ODEPA (D-164); DuckDB 2.0.0 volvió `k2_channel_gap` de 0,1 s a más de 60 s, por eso `requirements.txt` pide `duckdb<2` (D-227). Con DuckDB 2 una relación (`connection.sql`) ya no tiene `fetchone()`: usar `connection.execute(...)`.

## Lo que la sesión en la nube NO tendrá

| Falta | Consecuencia | Qué hacer |
|---|---|---|
| `etl/datos.duckdb` (fuera de git, D-270) | El panel la descarga solo al arrancar; las pruebas que la leen se saltan hasta que exista | `python bi/served_database.py` (necesita red hacia github.com) |
| `etl/raw.db` (unos 665 MB, fuera de git, D-020) | Las pruebas que recalculan precios desde las filas crudas se saltan (skip) | Normal; el resto de la auditoría corre con `datos.duckdb` |
| `agent/downloads/*.csv` | No hay CSV de ODEPA locales | `python agent/agent.py` los descarga, si hay red hacia datos.odepa.gob.cl |
| `etl/bronze/` y `etl/warehouse_build.duckdb` | No se puede correr `dbt build` de inmediato | Necesita `raw.db` (ingesta) más `pip install -r requirements-pipeline.txt` |
| `.venv` y `.venv-dbt` | Sin entornos | Crear uno nuevo con Python 3.11 o 3.12 e instalar los requirements |
| `.streamlit/secrets.toml` (`GITHUB_TOKEN`, `CONTROL_CODE`) | El Centro de operación lee GitHub sin clave (60 consultas por hora) y el botón «Ejecutar pipeline ahora» queda inactivo | Esperado; nunca crear ni subir secretos |
| `docs/privado/` | Notas privadas del autor, ignoradas por git | Ninguna |
| Chrome con depuración en el puerto 9333 | No hay capturas de pantalla automáticas | Revisar con AppTest y con las pruebas |

Sí están en el repositorio: `etl/datos.version` (el puntero de la base publicada) y `agent/downloads/manifest.json`. La base servida (`etl/datos.duckdb`, unos 14 MB) no está en git: `python bi/served_database.py` la descarga del release «base-actual» y comprueba su huella; con ella el panel y casi todas las pruebas funcionan. El respaldo `etl/datos.db` tampoco está: lo construye `python etl/etl.py` (necesita `raw.db`), y sin él las pruebas de paridad se saltan.
