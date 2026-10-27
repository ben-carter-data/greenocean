# Método y calidad · Informe de autoevaluación

| | |
|---|---|
| **Proyecto** | GreenOcean |
| **Tipo** | Informe de autoevaluación de calidad |
| **Medido** | 2026-10-26 (commit cf561e7) |
| **Autor** | el autor |
| **Estado** | Para aprobación: ninguna mejora se ha aplicado |

## Resumen

Se evaluó el repositorio completo de GreenOcean aplicando, como método de revisión, el marco de la ISO/IEC 25010 (calidad del producto), 25012 e ISO 8000 (calidad de los datos), ISO/IEC 5055 (calidad del código), ISO/IEC 29119 (pruebas), ISO/IEC/IEEE 42010 y el modelo C4 (arquitectura), los ADR, OWASP Top 10, Twelve-Factor App y las métricas DORA. **Es una autoevaluación, no una certificación**: nadie externo la revisó y no se declara conformidad con ninguna norma.

Resultado en una línea: producto bien probado (947 pruebas, cobertura 91,5 %) y con datos trazables, pero con la mantenibilidad del código por debajo de lo deseable; el promedio de las 7 características de la ISO/IEC 25010 verificadas es 2,6 de 4.

Cada número sale de ejecutar una herramienta real; `scripts/medir_calidad.py` los deja con su comando en `docs/calidad/medicion.json`. Lo que no se pudo medir se marca «no verificado».

## Escala

| Nota | Significado |
|---|---|
| 0 | no existe o no funciona |
| 1 | existe pero es débil o está medido en contra |
| 2 | existe con huecos importantes |
| 3 | sólido, con huecos menores medidos |
| 4 | sólido y verificado de punta a punta |

## Características de la ISO/IEC 25010

| Característica | Nota | Evidencia | Qué falta |
|---|---|---|---|
| Adecuación funcional | 3 / 4 | 947 pruebas; cada cifra del panel se recalcula en tests/test_data_audit.py; requisitos trazados a pruebas (tests/test_prd_traceability.py) | ODEPA publica 9 de las 16 regiones; los márgenes sólo existen para frutas y verduras |
| Eficiencia de desempeño | no verificado | Sin pruebas de carga ni de tiempos: sólo hay un incidente conocido (DuckDB 2 volvió una consulta de 0,1 s a más de 60 s, D-227) y la versión quedó acotada | Medir tiempos de carga de cada página y de cada consulta, y fijarlos como umbral |
| Compatibilidad | 2 / 4 | El panel corre en Python 3.14 y el pipeline con dbt, sólo en 3.11 o 3.12; español e inglés; sólo se midió el diseño en Chromium | Probar en Firefox y Safari y en una matriz de versiones de Python en el CI |
| Usabilidad | 2 / 4 | Cada página se mide a 1440 × 790 y 1920 × 1000 con Playwright (tests/medicion); español e inglés auditados; no hay auditoría de accesibilidad (WCAG) ni pruebas con personas | Auditar contraste y teclado, y probar con personas reales |
| Fiabilidad | 3 / 4 | Una puerta de pruebas impide publicar si algo falla (tests/test_pipeline_gate.py); 31 de 31 pruebas dbt; la carga del 25-10 falló por una prueba demasiado estricta (D-299) y se corrigió | Tres módulos de ingesta con poca cobertura (bronce 36,4 %, INE 30,8 %, pipeline 43,2 %) |
| Seguridad | 3 / 4 | Sin secretos en el árbol ni en el historial (21 candidatos de detect-secrets, 21 falsos positivos revisados); Bandit 0 altos; pip-audit sin hallazgos en requirements.txt; panel de sólo lectura; hash de la base publicada | Sin prueba de penetración; dependencias del pipeline sin auditar; gitleaks no instalado |
| Mantenibilidad | 2 / 4 | Complejidad media A (3,5) y 947 pruebas, pero bi/dashboard.py concentra miles de líneas, 40 funciones pasan de 50 líneas (la mayor, build_style_css, con 917), 109 de 115 archivos sin formatear y 1.776 líneas largas | Partir el panel por páginas, sacar el CSS a archivos y aplicar un formateador |
| Portabilidad | 3 / 4 | Corre en local, en Streamlit Cloud y en GitHub Actions; hay un devcontainer; la base es un archivo; un script de macOS queda en scripts/ | Dependencias sin versión fija y dos versiones de Python según el uso |

## Buenas prácticas de código

| Práctica | Herramienta | Umbral | Medido | Estado | Respalda a |
|---|---|---|---|---|---|
| 1 · Estilo y formato | Ruff (lint + format) | 0 errores | 1.819 avisos (1.776 de largo de línea; 43 otros, entre ellos 15 claves repetidas en diccionarios); 109 de 115 archivos sin formatear | Fuera del umbral | 25010/5055 · mantenibilidad |
| 2 · SQL | SQLFluff (DuckDB) | 0 errores | 279 avisos en bi/queries.sql; 240 en los modelos de dbt, de los cuales 21 son errores de plantilla que impiden analizar el archivo | Fuera del umbral | 25010 · mantenibilidad |
| 3 · Tipado | mypy | módulos principales sin errores | 0 errores, pero sólo porque el código no tiene anotaciones (0 de 123 funciones con tipo de retorno); al revisar también los cuerpos sin tipos, 3 errores | Parcial | 5055 · fiabilidad |
| 4 · Complejidad | Ruff C901 · radon | ≤ 10 por función; ≤ 50 líneas | 9 funciones sobre 10 (la peor, read_home_model, con 21); 40 funciones sobre 50 líneas (la mayor, build_style_css, con 917: CSS en una cadena); promedio A (3,5) | Parcial | 25010/5055 · mantenibilidad |
| 5 · Duplicación y código muerto | vulture | sin código muerto | 3 funciones sin uso (puntos de entrada de pruebas y un auxiliar de diagramas, a propósito) y 42 variables o atributos que vulture marca con baja confianza, sin revisar uno por uno; la duplicación (DRY) no se midió con herramienta | Parcial | 5055 · mantenibilidad |
| 6 · Pruebas y cobertura | pytest + coverage | ≥ 70 % en lógica de negocio y transformaciones | 947 pruebas; cobertura total 91,5 %; lógica crítica 83,8 %; bajo el umbral: bronce 36,4 %, INE 30,8 % y pipeline 43,2 % | Parcial | 29119 · pruebas |
| 7 · Seguridad | Bandit · pip-audit · detect-secrets | 0 hallazgos altos | Bandit: 0 altos, 25 medios (24 de SQL armado, revisados uno por uno: identificadores de constantes o enteros, valores con parámetros; uno ejecuta el SQL del visitante por diseño, en una conexión de sólo lectura) y 12 bajos; pip-audit: 0 en requirements.txt y no verificado en el pipeline; secretos: 21 candidatos, 21 falsos positivos revisados y 0 sin clasificar | Dentro del umbral | OWASP / 27034 · seguridad |
| 8 · Datos y dbt | dbt | pruebas pasando; staging, intermediate y marts | 31 de 31 pruebas superadas en la última carga; 16 modelos en tres capas. Esta revisión no ejecutó dbt: lee el registro de la última carga | Dentro del umbral | 25012 · datos |
| 9 · Principios de diseño | Lista de control | nombres claros, una responsabilidad, pocos parámetros | Nombres con prefijos que dicen lo que hacen (build_, read_, show_); pero bi/dashboard.py mezcla páginas, estilos y consultas, 50 funciones tienen más de 5 parámetros (build_lineage_node, 12) y esta revisión retiró unas 4.000 líneas de vistas sin uso (D-318), señal de deuda YAGNI | Parcial | 25010 · mantenibilidad |
| 10 · Proceso | Conventional Commits · pre-commit · CI | commits convencionales; pre-commit; CI con los puntos 1 a 8 | 0 de 307 commits siguen Conventional Commits (usan el formato «D-nnn: …»); no hay .pre-commit-config.yaml; el CI corre pytest y dbt parse, sin lint, tipos ni auditoría | Fuera del umbral | DORA · mantenibilidad |

## Calidad de los datos (ISO/IEC 25012)

Los indicadores se calculan en vivo desde la base servida y se muestran en la pestaña «Datos» de la página; sus notas por dimensión son: exactitud 3, completitud 2, consistencia 3, vigencia 3 y trazabilidad 3, con la evidencia que cita la página. Límites declarados: ODEPA publica 9 de las 16 regiones; los precios son nominales (el real descuenta la inflación general de alimentos); el margen existe sólo para frutas y verduras.

## OWASP Top 10 (revisión por categoría)

| Categoría | Revisión | Evidencia |
|---|---|---|
| A01 Control de acceso | El panel sólo lee; ejecutar el pipeline pide la clave del autor | `tests/test_security.py`, `docs/PLAN_PRUEBAS.md` |
| A02 Fallas criptográficas | No se guarda información personal; la base publicada lleva huella SHA-256 que se comprueba al descargar | `bi/served_database.py` |
| A03 Inyección | 24 avisos B608 de Bandit revisados uno por uno: identificadores de constantes o enteros, valores como parámetros; la consola SQL ejecuta el SQL del visitante por diseño, sólo SELECT y en una conexión de sólo lectura | `bi/sql_explorer.py`, `tests/test_sql_explorer.py` |
| A04 Diseño inseguro | Las decisiones de seguridad están en ADR y en el plan de pruebas | `docs/ADR.md` |
| A05 Configuración | Secretos sólo en `st.secrets`; workflow con los permisos mínimos | `tests/test_security.py` |
| A06 Componentes vulnerables | pip-audit: 0 en `requirements.txt`; **no verificado** en `requirements-pipeline.txt` (no se resuelve con este Python) | `docs/calidad/medicion.json` |
| A07 Autenticación | Una sola clave para la acción de operar; sin cuentas de usuario | `bi/control.py` |
| A08 Integridad | Huella de la base publicada; el pipeline no publica si una prueba falla | `tests/test_pipeline_gate.py` |
| A09 Registro y monitoreo | Historial de cargas y aviso de carga fallida visible sólo para quien opera | `bi/control.py` |
| A10 SSRF | No se hacen solicitudes a direcciones que el visitante escriba | revisión de lectura |

No hubo prueba de penetración.

## Twelve-Factor App

| Factor | Estado |
|---|---|
| I Código base | Aplicado: un repositorio |
| II Dependencias | Parcial: declaradas en `requirements*.txt`, sin versiones fijas |
| III Configuración | Aplicado: secretos en `st.secrets` y variables de entorno |
| IV Servicios de apoyo | Aplicado: la base es un archivo publicado en un release |
| V Construir, publicar, ejecutar | Aplicado: GitHub Actions y release «base-actual» |
| VI Procesos | Aplicado: el panel no guarda estado en disco |
| VII Enlace de puertos | Aplicado: Streamlit |
| VIII Concurrencia | No aplica |
| IX Desechabilidad | Parcial: arranque rápido, pero descarga la base al iniciar |
| X Paridad desarrollo y producción | Parcial: panel en Python 3.14 y pipeline en 3.11 o 3.12 |
| XI Registros | Parcial: el agente escribe archivos de registro, no un flujo |
| XII Procesos de administración | Aplicado: `etl/pipeline.py --local` |

Total: 7 aplicados, 4 parciales y 1 que no aplica.

## DORA

- **Frecuencia de despliegue:** una carga por semana; la base registra 6 cargas entre el 2026-10-11 y el 2026-10-20.
- **Tiempo de entrega, tasa de fallos de cambios y tiempo de recuperación:** no verificado (la consulta a la API de GitHub no pudo completarse desde este equipo).

## Limitaciones

- Autoevaluación del autor: las notas son un juicio apoyado en evidencia y pueden discutirse.
- No se midieron el rendimiento, la accesibilidad (WCAG), la duplicación con una herramienta, la tasa de fallos de cambios ni el tiempo de recuperación.
- Las dependencias del pipeline no se pudieron auditar; gitleaks no está instalado (se usó detect-secrets y una búsqueda de patrones en el historial).
- Cinco pruebas de enlaces públicos del repositorio dependen de que exista en GitHub con el nombre nuevo.
- dbt no se ejecutó en esta revisión: sus resultados se leen del registro de la última carga.

## Mejoras, por prioridad

| Prioridad | Mejora |
|---|---|
| Alta | Correr en el CI Ruff, Bandit, pip-audit y detect-secrets, y fallar con hallazgos altos |
| Alta | Partir `bi/dashboard.py` por páginas y sacar a archivos el CSS de `build_style_css` |
| Alta | Cubrir la ingesta con pruebas (bronce, INE y pipeline están bajo el 70 %) |
| Media | Revisar las 15 claves repetidas en diccionarios (en `bi/i18n_en.py`) |
| Media | Aplicar un formateador a todo el repositorio y fijar el largo de línea |
| Media | Anotar tipos en los módulos críticos y activar mypy en el CI |
| Media | Configurar pre-commit y Conventional Commits |
| Media | Bajar a 10 o menos la complejidad de las 9 funciones que la superan |
| Baja | SQLFluff con la plantilla de dbt para analizar los modelos |
| Baja | Medir tiempos de las páginas, fijarlos como umbral y auditar la accesibilidad |

Ninguna de estas mejoras se ha aplicado: esperan la aprobación del autor.

## Cómo reproducir

- `python scripts/medir_calidad.py --tools /ruta/al/entorno/bin` (escribe `docs/calidad/medicion.json`)
- `ruff check bi etl agent tests --select E,F,W --line-length 120`
- `ruff format --check bi etl agent tests --line-length 120`
- `vulture bi etl agent --min-confidence 60`
- `pytest -q --cov=bi --cov=etl --cov=agent`
- `bandit -r bi etl agent` y `pip-audit -r requirements.txt`
- `detect-secrets scan $(git ls-files)`

Las herramientas de calidad no son dependencias del proyecto: viven en un entorno aparte.
