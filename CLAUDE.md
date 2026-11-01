# CLAUDE.md · GreenOcean

Guía para trabajar en este repositorio, también desde una sesión en la nube que lo clona desde GitHub.

**Cómo se trabaja:** lee `REGLAS_DE_TRABAJO.md` (solo lo necesario, aviso antes de lo pesado, lo liviano en paralelo, un párrafo al terminar).

## Qué es

GreenOcean es un proyecto de portafolio de ingeniería de datos: un pipeline semanal y un panel de BI sobre los precios de alimentos de Chile.

- **Fuentes:** ODEPA (precios mayoristas y al consumidor, CSV públicos) y el IPC de alimentos del INE (para precios reales).
- **Pipeline:** ingesta en Python → aterrizaje `etl/raw.db` (SQLite) → bronce en Parquet → dbt Core sobre DuckDB (staging → intermedio → marts, 31 pruebas) → base servida `etl/datos.duckdb`, publicada en el release «base-actual» de GitHub, que cada carga reemplaza; git guarda solo su puntero `etl/datos.version` (D-270, ADR-35).
- **Panel:** Streamlit (`bi/dashboard.py`), que lee `etl/datos.duckdb` en solo lectura.
- **Orquestación:** GitHub Actions, cada martes (`.github/workflows/semanal.yml`).
- **Documentos del proyecto**, en cuatro carpetas de `docs/` y de `docs/en/` (D-381): `negocio/` (`PRD.md`, `GLOSARIO.md`), `arquitectura/` (`SAD.md` con la capacidad y el diccionario de datos, `ADR.md`, `INDICE_DECISIONES.md`), `calidad/` (`PLAN_DE_CALIDAD.md`, `PLAN_PRUEBAS.md` con el plan de pruebas y seguridad; la carpeta guarda también los datos del plan de calidad) y `operacion/` (`MANUAL.md`, el runbook), todos con portada, índice, resumen, al menos tres diagramas (cinco el SAD), glosario e historial de versiones (D-279, D-290). Todas las decisiones están en `docs/DECISIONES.md` (desde D-001, una por cambio); `docs/arquitectura/INDICE_DECISIONES.md` reúne las principales por tema. La historia del proyecto (hitos y backlog) está en `docs/archivo/`; no es documentación de lectura.

## Cómo responderme

1. Primero la respuesta: la idea principal en una o dos frases, sin introducción.
2. Que lo entienda alguien de 12 años: palabras simples y frases cortas; si usas un término técnico, explícalo en la misma frase.
3. Profesional, no infantil: usa los nombres correctos (commit, CI, SQAP), pero di qué son en palabras normales.
4. Una idea, una frase. Un tema, un párrafo.
5. Detalle solo si lo pido; no anticipes dudas.
6. Sin vueltas: nada de hipótesis largas, repeticiones ni resúmenes de lo ya dicho.
7. Si no sabes algo, dilo en una línea y di cómo averiguarlo.
8. Prompts y comandos, listos para copiar, en un bloque aparte.

Ejemplo: «Los documentos viven en un .md. La app lo usa para generar un PDF formal, con portada e índice, que es lo que ve el visitante.»

Estas reglas valen también para los briefings.

## Instalar y ejecutar

| Para qué | Comando |
|---|---|
| Panel y pruebas | `pip install -r requirements.txt` |
| Pipeline con dbt | `pip install -r requirements-pipeline.txt` (dbt no se instala en Python 3.14: usar 3.11 o 3.12) |
| Abrir el panel | `streamlit run bi/dashboard.py` |
| Descargar la base de la última carga | `python bi/served_database.py` (el panel lo hace solo al arrancar) |
| Pruebas | `python -m pytest -q` (unas 1.290, alrededor de dos minutos y medio) |
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
| `bi/` | Panel: `dashboard.py` (páginas y navegación), `queries.sql` y `queries.py` (SQL), diagramas (`architecture.py` pipeline y despliegue, `lineage.py`, `star_model.py`, `er_diagram.py`, `storage_map.py` dónde viven los datos, `database_crossings.py` cruces entre bases, `deployment.py` despliegue, `devops.py` CI/CD y orquestación, `monitoring.py` monitoreo, `security_map.py` arquitectura de seguridad, `doc_views.py` contexto, contenedores, casos de uso y procedimiento de los documentos), vistas (`home_mockup.py`, `quality_live.py`, `quality_view.py`, `github_page.py`, `git_workflow.py` el mapa del ciclo git y su registro de incidentes, D-344), `page_bar.py` (la barra de encabezado de las páginas principales, D-267), `tech_glossary.py`, `buttons.py` (el componente único de botones y enlaces, D-281), `documents_folder.py` (la carpeta «Documentos», D-282), `i18n.py` y `i18n_en.py` (español e inglés, D-283 y D-284), `app_map.py` (el mapa de la app, D-285), `zoom.py` (zoom y explicaciones al pasar el cursor), `weeks.py` (las semanas como rango de lunes a domingo, D-374), `business_analysis.py` (lee del PRD y del SQAP, en el idioma de la visita, las páginas «Interesados» y «Análisis de negocio y sistemas», D-376 y D-377), `data_terms.py` (las palabras de los datos en el idioma de la visita, D-403), `configuration.py` (la consola «Configuración» del Autor, leída del MANUAL, D-409), `live_flow.py` (el flujo del sistema en vivo, su ventana de la carga y su imagen del SAD, D-412 a D-414) |
| `tests/` | pytest: auditoría de cifras (`test_data_audit.py`), paridad SQLite ↔ DuckDB, IPC, linaje, diagramas, documentos y su trazabilidad (`test_prd_traceability.py`), puerta de publicación (`test_pipeline_gate.py`) y panel (AppTest). `tests/medicion/`: medición del diseño con Playwright (`medir.cjs`) y comparación de cada documento impreso con su página (`imprimir.cjs`), que corren con Playwright instalado fuera del proyecto |
| `docs/` | Cuatro carpetas de documentos (`negocio/`, `arquitectura/`, `calidad/`, `operacion/`, y la misma estructura en `en/`), `DECISIONES.md`, `DISENO.md` y `PROYECTO.md`; `calidad/` guarda también los datos del plan de calidad. Una ruta de documento se resuelve con `i18n.document_path`, nunca a mano |
| `.github/workflows/` | `semanal.yml` (carga semanal), `pruebas.yml` (pytest + dbt parse en cada push) |

## Convenciones

- **Idioma:** todo en español (panel, documentos, decisiones y mensajes de commit). El código y sus comentarios, en inglés. En inglés solo el «About» de GitHub y `README.en.md`; no se mezclan dos idiomas en un archivo (D-338). Desde D-283 el panel se lee también en inglés (`?lang=en`): los textos del marco pasan por `tr` de `bi/i18n.py` (diccionario `EN`) y los de las páginas se traducen al dibujarse, con su inglés en `bi/i18n_en.py` (D-284): un texto nuevo en una página necesita su entrada, o `tests/i18n_audit.py` lo lista; y cada documento de `docs/` tiene su versión en `docs/en/` con la misma estructura, los mismos identificadores y las mismas cifras; `tests/test_i18n.py` lo verifica.
- **Vocabulario:** pipeline, workflow, ingesta, ETL, staging, data warehouse. Nunca «robot».
- **Autoría:** «el autor». Ningún nombre personal en el panel ni en los documentos, y nada inventado sobre él.
- **Datos:** nunca inventar una cifra ni interpolar un precio; nunca borrar histórico. Cada cifra del panel debe poder recalcularse desde la fuente; las pruebas lo verifican.
- **Fuentes retrasadas (D-356):** se publica hasta la última semana completa en ambas fuentes, sin rellenar nada. El Panorama y los indicadores publican hasta esa semana común; la página «Último dato por canal» muestra la última semana de cada fuente, rotulada (D-365). Una semana reciente que una fuente aún no publica no bloquea la carga: se registra como incidente externo y la app muestra un aviso discreto («ODEPA aún no publica la semana X»). Bloquea solo si falta una semana en medio de los datos, o si la fuente lleva más de 2 semanas sin publicar (y entonces hay aviso urgente al Autor).
- **Encabezado (D-398):** el encabezado es solo para ubicarse y navegar: volver (a la página anterior de la visita, con su estado, sin recargar; sin página anterior, «Elige tu vista», D-423), la ruta de la página, la semana mostrada como rango (con «Próxima semana» en letra pequeña donde aplique) y la fecha de los datos. La información (preguntas, cifras, avisos, botones y selectores) va en el contenido, en la fila bajo el encabezado, y los enlaces a otras páginas, en el menú. `tests/test_page_bar.py` lo verifica en cada página y en los dos idiomas.
- **Cada cambio de comportamiento** lleva su entrada `## D-xxx · título` en `docs/DECISIONES.md`, con sus pruebas en verde.
- **Acceso (D-420, D-421):** las secciones de operación y seguridad interna se muestran solo al perfil administrador (el Autor), con control de acceso en el servidor: la sesión se comprueba antes de dibujar cada página y antes de cada acción, no solo en el menú. Hay una sola clave, la de entrar como Autor.
- **Commits (desde D-323):** Conventional Commits en español, `tipo(alcance): descripción (D-xxx)`; ver `CONTRIBUTING.md`. Ruff, mypy y la cobertura mínima (90 %) se revisan en el CI.
- **Documentos:** sin bloques de código. Diagramas con marcadores `[[diagrama:nombre]]` en su propia línea: las vistas de `bi/doc_views.py` (`contexto`, `contenedores`, `casos`, `sop` y `mockups`) y las figuras de `bi/doc_figures.py` (secuencias, columnas, líneas de tiempo, árboles; D-289). Para no copiar una vista, un documento enlaza a su página con `[[vista:Página del menú]]`. Los mockups son seis capturas reales de cinco páginas actuales (el Panorama en las vistas Usuario y Profesional) en `docs/img/` y `docs/img/en/`, en los cuatro temas; se toman sin el respaldo local `etl/datos.db`, para que la calidad se vea como en producción (D-392). El PDF de un documento es la página misma impresa por el navegador (botón «Imprimir o guardar como PDF», D-248).
- **Dependencias:** no agregar ninguna sin acuerdo del autor. Solo herramientas gratuitas y sin vencimiento; no hay nube de pago (ADR-31).
- **Commits libres; push solo después de que el autor revise la app en local.**
- **Qué prueba la carga (D-366):** la carga semanal solo corre las pruebas de datos y del pipeline (`pytest -m datos`, la lista vive en `tests/conftest.py`); las de pantalla (traducciones, páginas, AppTest, documentos) corren en el CI de cada push. Una falla de pantalla nunca bloquea la publicación de datos.
- **Registro de fallas (D-342):** cada falla diagnosticada y resuelta se anota en `docs/calidad/plan_mitigacion.json` (fecha, ocurrencia, diagnóstico, solución, comentario, estación y estado) antes del push. No se anotan secretos ni datos sensibles: el repositorio es público. Cada ocurrencia va en una línea por campo y en lenguaje simple: la ocurrencia dice qué pasó; el diagnóstico, la causa en una frase; la solución, qué se hizo en una frase. El análisis largo va en la decisión (D-xxx), no en el registro (D-354).

## Nombres oficiales en diagramas y documentos

Valen en todo diagrama, tabla o texto de `docs/` y del panel.

1. **Nunca un nombre genérico solo** («la base», «el pipeline», «el panel», «el workflow», «el token», «el informe»). Siempre el nombre oficial:
   - **Datos:** Base DuckDB · `etl/datos.duckdb` (publicada en el release «base-actual», puntero `etl/datos.version` en main; antes «base servida», D-426); aterrizaje `etl/raw.db` (SQLite, solo local); bronce (Parquet, `etl/bronze/`); respaldo `etl/datos.db` (SQLite); registro de cargas `etl_run`; `agent/downloads/manifest.json`.
   - **Carga:** carga semanal (`semanal.yml`), con dbt Core en tres capas: staging, intermedio y marts.
   - **Workflows, por archivo:** `semanal.yml` (carga semanal), `calidad.yml` (medición e informe de calidad), `pruebas.yml` (pruebas de cada push).
   - **Secretos, por nombre:** `GITHUB_TOKEN` (lanza y cancela `semanal.yml`), `GITHUB_READ_TOKEN` (solo lectura; en GitHub se llama `greenocean-read`), `CONTROL_CODE` (la clave del Autor).
   - **Perfiles:** Usuario, Profesional (roles Data Eng, BA, BI, DevOps y Seguridad, que solo ordenan el menú) y Autor. GitHub Actions no es un perfil.
   - **Panel web** (Streamlit Community Cloud), con el nombre exacto del menú:
     - Negocio · BA y BI: «Interesados», «Análisis de negocio y sistemas», «Panorama de precios», «Último dato por canal», «Precios e inflación», «Insights».
     - Ingeniería de datos: «Pipeline y linaje», «Modelo de datos», «Consultas SQL».
     - DevOps y seguridad (solo el Autor): «Centro de operación», «GitHub Actions», «Configuración».
     - Stack y evidencia: «Stack y evidencia» (con el «Flujo del sistema en vivo»), «Mapa de la app», «Arquitectura de seguridad».
     - Calidad: «Calidad y auditoría», «Método y calidad», «Git workflow».
     - Pie del menú: «Documentos» (carpeta), «Fuentes», «Apariencia», ES/EN, GitHub.
     - Ventanas, botones y avisos: «Elige tu vista», «Vista: … · Cambiar», «Ver todo el proyecto», «Volver», «Ejecutar pipeline ahora», «Recargar datos», «Cerrar acceso», «Acción requerida», «La carga del … falló».
   - **Fuentes:** ODEPA (precios mayoristas y al consumidor) e INE (IPC de alimentos).
   - **Documentos:** PRD, SAD, ADR, Índice de decisiones, SQAP (plan de calidad), Plan de pruebas y seguridad, MANUAL (manual de operación), Glosario; las decisiones, en `docs/DECISIONES.md` (D-xxx).
   - **Informes y registros:** «Informe semanal» (issue de `semanal.yml`), informe semanal de calidad N° x (pull request «Actualizar medición de calidad» de `calidad.yml`, solo tras una carga en verde; los 7 primeros son la serie de construcción C-1 a C-7, D-431), `plan_mitigacion.json` (fallas F-xx), `no_conformidades.json`, `incidentes_externos.json`.
2. **Con su ID del PRD** cuando lo tiene: P-1 a P-5, RF-01 a RF-09, RNF-01 a RNF-06 (por ejemplo, «Consultas SQL» P-2 · P-3 · RF-06). Si no lo tiene, no se inventa.
3. **Si un nombre oficial no existe todavía,** se propone y se pregunta al autor antes de usarlo. Un genérico nunca es la solución.
4. **Antes de entregar un diagrama,** se revisa que cada caja, flecha y etiqueta cumpla 1 y 2, y el resumen lista los nombres usados.

## Trampas conocidas del panel

- `st.html` ejecuta solo el primer `<script>` de un bloque y descarta los scripts cuyos textos JavaScript contienen etiquetas HTML. Construir el DOM con APIs (`createElement`, `textContent`) y escribir los scripts como cadenas crudas de Python (`r"""…"""`).
- Streamlit (React) es dueño del DOM que dibuja: un script puede cambiar atributos y clases, pero nunca mover ni borrar nodos. Si no, al cambiar de vista aparece `NotFoundError: removeChild`.
- `st.markdown` sanitiza SVG complejos (gradientes, filtros, botones). Por eso la página GitHub se dibuja en `st.iframe` con su propio HTML.
- `streamlit run` guarda en memoria los módulos importados y el vigilante de archivos está apagado en `.streamlit/config.toml`; desde D-172 el panel recarga en cada ejecución los `bi/*.py` que cambiaron (las fechas viven en el paquete `bi`, porque `bi/dashboard.py` se ejecuta desde cero cada vez), así que basta con volver a cargar la página. En la práctica, un cambio en `bi/dashboard.py` mismo no siempre se ve hasta reiniciar `streamlit run`: si una página no cambia, reiniciar el servidor antes de medir.
- El contenedor de `st.markdown` lleva `margin-bottom: -1rem` para compensar el párrafo final. Un bloque HTML que termina en `div` no trae ese margen y el elemento siguiente se le monta encima: anular el margen del contenedor o cerrar con un párrafo (D-173).
- El respaldo `etl/datos.db` nunca se renombra ni se mueve (D-402): para correr la suite como el CI, sin respaldo, se usa una copia aparte del repositorio (`git worktree add <carpeta> HEAD`, más una copia de `etl/datos.duckdb`).
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
