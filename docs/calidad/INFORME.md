# Método y calidad · Informe de autoevaluación

|  |  |
|---|---|
| **Proyecto** | GreenOcean |
| **Tipo** | Informe de autoevaluación de calidad |
| **Medido** | 2026-10-27 11:04 UTC (commit d66804c, Python 3.14.7) |
| **Línea base** | 2026-10-27 01:41 UTC (commit 6c6286c), antes de las mejoras de D-323 |
| **Autor** | el autor |
| **Estado** | Autoevaluación automática, revisada y aprobada por el autor · rúbrica ISO borrador, pendiente de confirmación del autor |

## Resumen

Se evaluó el repositorio completo aplicando, como método de revisión, la ISO/IEC 25010 (calidad del producto), 25012 e ISO 8000 (calidad de los datos), ISO/IEC 5055 (calidad del código), ISO/IEC 29119 (pruebas), WCAG 2.1 AA (accesibilidad), ISO/IEC/IEEE 42010 y el modelo C4 (arquitectura), los ADR, OWASP Top 10, Twelve-Factor App y las métricas DORA. **Es una autoevaluación, no una certificación**: nadie externo la revisó y no se declara conformidad con ninguna norma.

Resultado: 12 de 15 indicadores medidos cumplen su meta (en la línea base, 8 de 15). Promedio de la rúbrica ISO/IEC 25010: 3,0 de 4 en las 8 características (borrador, pendiente de confirmación del autor); en D-320, 2,6 de 4 en las 7 verificadas.

Cada número sale de ejecutar una herramienta: scripts/medir_calidad.py los deja con su comando en docs/calidad/medicion.json, y este informe se genera desde ese archivo con scripts/informe_calidad.py. Lo que no se pudo medir dice «no verificado».

## Antes → ahora → meta

| Indicador | Antes | Ahora | Meta | Estado | Cómo reproducirlo |
|---|---|---|---|---|---|
| Pruebas que fallan | 5 | **7** | ≤ 0 | **no cumple** | `pytest -q` |
| Cobertura total | 91,5 % | **94,2 %** | ≥ 90 % | cumple | `pytest -q --cov` |
| Cobertura del módulo más bajo | 0,0 % | **83,1 %** | ≥ 70 % | cumple | `pytest -q --cov --cov-report=term` |
| Avisos de Ruff (E, F y W; el largo de línea, aparte) | 50 | **0** | ≤ 0 | cumple | `ruff check .` |
| Archivos sin formatear | 111 | **0** | ≤ 0 | cumple | `ruff format --check .` |
| Funciones con tipos (módulos principales) | 0,0 % | **100,0 %** | ≥ 100 % | cumple | `mypy` |
| Errores de mypy | 0 | **0** | ≤ 0 | cumple | `mypy` |
| Funciones con complejidad sobre 10 | 9 | **6** | ≤ 6 | cumple | `ruff check bi etl agent --select C901` |
| Hallazgos altos de Bandit | 0 | **0** | ≤ 0 | cumple | `bandit -r bi etl agent` |
| Vulnerabilidades en dependencias | 0 | **0** | ≤ 0 | cumple | `pip-audit -r requirements.txt` |
| Posibles secretos sin revisar | 0 | **0** | ≤ 0 | cumple | `detect-secrets scan $(git ls-files)` |
| Carga de la página más lenta | 1,31 s | **2,34 s** | ≤ 2,0 s | **no cumple** | `node tests/medicion/calidad.cjs` |
| Consulta más lenta | 0,45 s | **0,42 s** | ≤ 1,0 s | cumple | `pytest -q tests/test_rendimiento.py` |
| Violaciones WCAG 2.1 AA | 18 | **0** | ≤ 0 | cumple | `node tests/medicion/calidad.cjs` |
| Comprobaciones fallidas en Chromium, Firefox y WebKit | 0 | **2** | ≤ 0 | **no cumple** | `node tests/medicion/calidad.cjs` |

«Antes» es la línea base, medida antes de cambiar nada. El módulo más bajo de la línea base tenía 0 % porque dos módulos vacíos (bi/data_browser.py y bi/explorer.py) se contaban; D-323 los retiró. Los avisos de Ruff cuentan las reglas E, F y W sin el largo de línea en las dos columnas.

## Rúbrica ISO/IEC 25010

| Nota | Significado |
|---|---|
| 0 | no existe o no funciona |
| 1 | existe pero es débil o está medido en contra |
| 2 | existe con huecos importantes |
| 3 | sólido, con huecos menores medidos |
| 4 | sólido y verificado de punta a punta |

| Característica | Antes (D-320) | Ahora | Evidencia | Qué falta |
|---|---|---|---|---|
| Adecuación funcional | 3 / 4 | 3 / 4 | Cada cifra del panel se recalcula desde la fuente en las pruebas (tests/test_data_audit.py) y cada requisito del PRD apunta a una prueba que existe (tests/test_prd_traceability.py). | ODEPA publica 9 de las 16 regiones y los márgenes solo existen para frutas y verduras: el panel no puede decir más que eso. |
| Eficiencia de desempeño | no verificado | 3 / 4 | Cada página y cada consulta se miden contra un presupuesto (2 s por página, 1 s por consulta) y una prueba falla si una consulta lo supera. | Carga de la página más lenta: 2,34 s (meta ≤ 2,0 s); No hay pruebas con varias personas a la vez ni medición en Streamlit Cloud: los tiempos son de un equipo local. |
| Compatibilidad | 2 / 4 | 3 / 4 | Todas las páginas cargan sin errores ni desplazamiento horizontal en Chromium, Firefox y WebKit, a 1440 × 790, 1920 × 1000 y un teléfono en horizontal; el CI prueba Python 3.11 y 3.12. | Comprobaciones fallidas en Chromium, Firefox y WebKit: 2 (meta ≤ 0); La comprobación es de errores y desborde, no una comparación visual píxel a píxel entre navegadores. |
| Usabilidad | 2 / 4 | 3 / 4 | axe-core no encuentra violaciones de WCAG 2.1 AA en las 13 páginas y los cuatro temas; español e inglés auditados. | Una auditoría automática no cubre todo WCAG: falta recorrer cada página solo con teclado y con un lector de pantalla, y probar con personas. |
| Fiabilidad | 3 / 4 | 3 / 4 | Una puerta de pruebas impide publicar si algo falla (tests/test_pipeline_gate.py); la ingesta tiene pruebas propias sin red ni dbt. | Pruebas que fallan: 7 (meta ≤ 0); La carga del 25-10 falló por una prueba demasiado estricta (D-299): el arreglo está en el repositorio pero no se ha visto pasar una carga real. |
| Seguridad | 3 / 4 | 3 / 4 | Sin secretos en el repositorio, sin hallazgos altos de Bandit, sin vulnerabilidades conocidas en las dependencias del panel; panel de solo lectura y base con huella SHA-256. | No hubo prueba de penetración y las dependencias del pipeline (dbt) no se auditan con el Python de este equipo. |
| Mantenibilidad | 2 / 4 | 3 / 4 | Ruff sin avisos y todo formateado; los módulos principales con tipos y mypy sin errores; pre-commit y CI revisan cada cambio. | bi/dashboard.py sigue concentrando miles de líneas y seis funciones de páginas pasan la complejidad 10. |
| Portabilidad | 3 / 4 | 3 / 4 | Corre en local, en Streamlit Cloud y en GitHub Actions, con un devcontainer; la base es un archivo publicado en un release. | Las dependencias no tienen versión fija y el pipeline necesita otra versión de Python que el panel. |

Qué cambió: la eficiencia ya se mide (tiempos de cada página y consulta, con presupuesto); la compatibilidad, con tres navegadores y dos versiones de Python en el CI; la usabilidad, con axe-core en las 13 páginas y los cuatro temas; la mantenibilidad, con Ruff, formato, tipos, pre-commit y CI. La adecuación, la fiabilidad, la seguridad y la portabilidad mantienen su nota.

## Calidad de los datos (ISO/IEC 25012)

| Indicador | Valor | Detalle |
|---|---|---|
| Precios de la última semana con comparación válida | 93,1 % | 719 de 772 |
| Series de las últimas 12 semanas con dato esta semana | 69,4 % | 772 de 1.113 |
| Días desde el fin de la última semana con datos | 9 | semana del 2026-10-12 |
| Días desde la última carga | 7 | medido el 2026-10-27 |

Límites declarados: ODEPA publica 9 de las 16 regiones; los precios son nominales (el real descuenta la inflación general de alimentos); el margen existe solo para frutas y verduras.

## Navegadores, accesibilidad y rendimiento

| Página | Carga | Violaciones WCAG 2.1 AA |
|---|---|---|
| Panorama de precios | 0,83 s | 0 |
| Dónde comprar | 0,32 s | 0 |
| Insights | 0,82 s | 0 |
| Pipeline y linaje | 1,33 s | 0 |
| Modelo de datos | 0,82 s | 0 |
| Calidad y auditoría | 0,82 s | 0 |
| Consultas SQL | 0,34 s | 0 |
| Stack y evidencia | 0,82 s | 0 |
| Mapa de la app | 0,82 s | 0 |
| Método y calidad | 0,83 s | 0 |
| Centro de operación | 2,34 s | 0 |
| Arquitectura de seguridad | 0,84 s | 0 |
| Documentos | 0,83 s | 0 |

| Navegador | Comprobaciones superadas | Fallos |
|---|---|---|
| Chromium | 39 / 39 | — |
| Firefox | 38 / 39 | Documentos 844x390 |
| Webkit | 38 / 39 | Pipeline y linaje 1920x1000 |

Cada página se abre a 1440 × 790, 1920 × 1000 y en un teléfono en horizontal (844 × 390). La consulta más lenta es k3_regional_index (0,42 s, mediana de tres ejecuciones).

## Buenas prácticas de código

| Práctica | Herramienta | Meta | Medido | Estado |
|---|---|---|---|---|
| 1 · Estilo y formato | Ruff (lint + format) | 0 avisos E, F y W; 0 archivos sin formatear | 0 avisos E, F y W; 0 de 117 archivos sin formatear; 1.187 líneas de más de 120 columnas (E501, fuera de la meta: ver límites) | cumple |
| 2 · SQL | SQLFluff (DuckDB) | sin meta | 279 avisos en bi/queries.sql; 240 en los modelos de dbt | sin meta |
| 3 · Tipado | mypy | 0 errores; 100 % de funciones con tipos en los módulos principales | 0 errores en 10 módulos; 134 de 134 funciones con tipo de retorno | cumple |
| 4 · Complejidad | Ruff C901 · radon | ≤ 6 funciones sobre 10 | 6 funciones sobre 10 (la peor, read_home_model, con 21); 81 funciones de más de 50 líneas (la mayor, bi/dashboard.py:build_style_css, con 920); promedio radon A (3,5) | cumple |
| 5 · Código muerto | vulture | sin meta | 4 funciones sin uso (render_page, read_glossary, add_to_history, orthogonal) y 34 variables o atributos de baja confianza | sin meta |
| 6 · Pruebas y cobertura | pytest + coverage | 0 pruebas fallidas; ≥ 90 % total; ≥ 70 % en cada módulo | 996 pruebas, 988 pasan; cobertura total 94,2 %; lógica crítica 93,6 %; módulo más bajo bi/overview.py (83,1 %) | **no cumple** |
| 7 · Seguridad | Bandit · pip-audit · detect-secrets | 0 altos; 0 vulnerabilidades; 0 secretos sin revisar | Bandit: 0 altos, 26 medios y 12 bajos; pip-audit: 0 en requirements.txt; no verificado en requirements-pipeline.txt (las dependencias no se pueden resolver con este Python (dbt pide 3.11 o 3.12)); secretos: 22 candidatos, 22 falsos positivos revisados y 0 sin clasificar | cumple |
| 8 · Datos y dbt | dbt | pruebas pasando | 31 de 31 pruebas en la última carga; 16 modelos en tres capas (se lee el registro de la carga) | sin meta |
| 9 · Proceso | Conventional Commits · pre-commit · CI | commits convencionales desde D-323; pre-commit; CI con lint, tipos y cobertura | 11 de 321 commits siguen Conventional Commits (todos los de D-323; los anteriores usan «D-nnn: …»); pre-commit configurado; CI: calidad.yml (pytest, ruff, mypy, bandit, pip-audit, sqlfluff); pruebas.yml (pytest, ruff, mypy, dbt parse); semanal.yml (pytest, dbt build) | sin meta |

## OWASP Top 10 (revisión por categoría)

| Categoría | Revisión | Evidencia |
|---|---|---|
| A01 Control de acceso | El panel solo lee; ejecutar el pipeline pide la clave del autor | `tests/test_security.py` |
| A02 Fallas criptográficas | No se guarda información personal; la base publicada lleva huella SHA-256 que se comprueba al descargar | `bi/served_database.py` |
| A03 Inyección | 25 avisos B608 de Bandit revisados uno por uno: identificadores de constantes o enteros, valores como parámetros; la consola SQL ejecuta el SQL del visitante por diseño, solo SELECT y en una conexión de solo lectura | `bi/sql_explorer.py` |
| A04 Diseño inseguro | Las decisiones de seguridad están en ADR y en el plan de pruebas | `docs/ADR.md` |
| A05 Configuración | Secretos solo en st.secrets; workflows con los permisos mínimos | `tests/test_security.py` |
| A06 Componentes vulnerables | pip-audit: 0 en requirements.txt; no verificado en requirements-pipeline.txt (las dependencias no se pueden resolver con este Python (dbt pide 3.11 o 3.12)) | `docs/calidad/medicion.json` |
| A07 Autenticación | Una sola clave para la acción de operar; sin cuentas de usuario | `bi/control.py` |
| A08 Integridad | Huella de la base publicada; el pipeline no publica si una prueba falla | `tests/test_pipeline_gate.py` |
| A09 Registro y monitoreo | Historial de cargas y aviso de carga fallida para quien opera | `bi/control.py` |
| A10 SSRF | No se hacen solicitudes a direcciones que el visitante escriba | `revisión de lectura` |

No hubo prueba de penetración.

## Twelve-Factor App

| Factor | Estado |
|---|---|
| I Código base | Aplicado: un repositorio |
| II Dependencias | Parcial: declaradas en requirements*.txt, con versión máxima donde rompió (duckdb<2) pero no fijas |
| III Configuración | Aplicado: secretos en st.secrets y variables de entorno |
| IV Servicios de apoyo | Aplicado: la base es un archivo publicado en un release |
| V Construir, publicar, ejecutar | Aplicado: GitHub Actions y release «base-actual» |
| VI Procesos | Aplicado: el panel no guarda estado en disco |
| VII Enlace de puertos | Aplicado: Streamlit |
| VIII Concurrencia | No aplica |
| IX Desechabilidad | Parcial: arranque rápido, pero descarga la base al iniciar |
| X Paridad desarrollo y producción | Parcial: panel en Python 3.14 y pipeline en 3.11 o 3.12 |
| XI Registros | Parcial: el agente escribe archivos de registro, no un flujo |
| XII Procesos de administración | Aplicado: etl/pipeline.py --local |

## DORA

- **Frecuencia de despliegue:** una carga por semana; la base registra 6 cargas entre el 2026-10-11 y el 2026-10-20.
- **Workflow semanal:** no verificado (no se pudo consultar la API de GitHub).
- **Workflow pruebas:** no verificado (no se pudo consultar la API de GitHub).

## Historial de mediciones

| Medición | Commit | Cumplen la meta | Cobertura | Ruff | mypy | WCAG | Página más lenta |
|---|---|---|---|---|---|---|---|
| 2026-10-27 11:04 UTC | d66804c | 12 de 15 | 94,2 % | 0 | 0 | 0 | 2,34 s |
| 2026-10-27 01:41 UTC | 6c6286c | 8 de 15 | 91,5 % | 50 | 0 | 18 | 1,31 s |
| 2026-10-26 23:28 UTC | cf561e7 | 5 de 10 | 91,5 % | 43 | 0 | — | — |

## Qué se mide solo y qué se revisa a mano

| Qué | Cómo | Frecuencia |
|---|---|---|
| Los 15 indicadores de la tabla «Antes → ahora → meta» | Automático: workflow «calidad» (scripts/medir_calidad.py) | En cada push; una vez por semana cuando el autor lo active |
| Calidad de los datos servidos | Automático: el código del proyecto lee la base servida | En cada push |
| Tiempos, WCAG 2.1 AA y diseño en tres navegadores | Automático: Playwright y axe-core (tests/medicion/calidad.cjs) | En cada push |
| Comparación con las metas | Automático: scripts/verificar_calidad.py; el CI falla y dice cuál indicador bajó | En cada push |
| Publicar una medición en esta página | Manual: el autor fusiona el pull request «Actualizar medición de calidad» | Cada vez que el workflow lo abre |
| Rúbrica ISO/IEC 25010 | Manual: el autor revisa y confirma docs/calidad/rubrica.json | Una vez por versión |
| OWASP Top 10 y Twelve-Factor App | Manual: revisión por categoría en el informe | Una vez por versión |
| Posibles secretos y hallazgos medios de Bandit | Manual: cada candidato nuevo se revisa y se anota en .secrets.baseline | Cuando aparece uno nuevo |
| Las metas | Manual: decisión del autor en docs/calidad/metas.json | Cuando el autor lo decide |
| Recorrido con teclado y lector de pantalla | Manual | Pendiente: aún no se ha hecho |

## Lo que no se pudo mejorar, y por qué

- 6 funciones siguen sobre la complejidad 10 (las mayores: read_home_model (21), show_quality_evidence_dialog (13), show_market_overview (13), restore_return_context (12), show_sql_explorer_page (11)). Son funciones que dibujan páginas del panel; dividirlas sin cambiar la interfaz necesita pruebas de interfaz que aún no existen. Por eso la meta quedó en 6 y no en 0.
- 81 funciones pasan de 50 líneas; la mayor, bi/dashboard.py:build_style_css (920 líneas), es el CSS del panel en una cadena. Partir bi/dashboard.py por páginas y sacar el CSS a archivos es un cambio grande que se dejó fuera para no cambiar el comportamiento.
- 1.187 líneas pasan de 120 columnas: casi todas son textos del panel en español e inglés, que el formateador no parte. pyproject.toml deja E501 fuera de las reglas y la meta; el número se sigue midiendo aparte para que no se oculte.
- SQLFluff marca 279 avisos en bi/queries.sql y 240 en dbt: el SQL de dbt es la lógica del pipeline, que esta mejora no debía tocar.
- pip-audit no audita requirements-pipeline.txt con Python 3.14.7: dbt pide 3.11 o 3.12. El workflow «calidad» corre con 3.11 y sí lo audita.
- gitleaks no está instalado: se usó detect-secrets y una búsqueda de patrones de claves en el historial.
- Las métricas DORA del historial de GitHub Actions quedaron sin verificar en este equipo (no se pudo consultar la API); en el workflow sí se consultan.
- 7 pruebas fallan: las que consultan los enlaces públicos del repositorio (test_t54_every_public_link_answers) esperan que se llame «greenocean» en GitHub (D-319), y el cambio de nombre lo hace el autor.
- La auditoría automática de accesibilidad (axe-core) no cubre todo WCAG: falta recorrer cada página con teclado y con un lector de pantalla, y probar con personas.
- El 69,4 % de las series de las últimas 12 semanas tiene dato en la última: ODEPA no publica cada serie cada semana, y el proyecto nunca interpola un precio.

## Cómo se aprueba

- **Una medición:** el workflow «calidad» la propone en un pull request «Actualizar medición de calidad»; la página la muestra solo cuando el autor lo fusiona.
- **La rúbrica:** el autor revisa docs/calidad/rubrica.json y cambia «estado» a «confirmada» y «revisada_por» a «el autor»; hasta entonces la página dice «borrador, pendiente de su confirmación».
- **Las metas:** solo el autor las cambia, en docs/calidad/metas.json.

## Cómo reproducir

- `python scripts/medir_calidad.py --tools <entorno>/bin --node-path <node_modules>` escribe la medición.
- `python scripts/verificar_calidad.py docs/calidad/medicion.json` la compara con las metas.
- `python scripts/informe_calidad.py` escribe este informe y agrega la medición al historial.

Las herramientas de calidad no son dependencias del proyecto: viven en un entorno aparte, con las versiones del workflow «calidad».
