# Plan de pruebas y seguridad

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Plan de pruebas y de seguridad |
| Versión | 3.0 |
| Fecha | 25-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Explicar cómo se comprueba que cada cifra es correcta, que una carga con errores nunca se publica y que nadie puede leer los secretos, cambiar los datos ni lanzar la carga sin permiso. |
| Audiencia | Gerencia, calidad, seguridad, operación y revisión técnica. |
| Documentos relacionados | [Documento de requisitos del producto (PRD)](PRD.md) · [Documento de arquitectura de software (SAD)](SAD.md) · [Manual de operación](MANUAL.md) · [Glosario](GLOSARIO.md) |

## Índice

1. [En resumen](#1-en-resumen)
2. [Qué se prueba](#2-qué-se-prueba)
3. [Quién participa en la seguridad](#3-quién-participa-en-la-seguridad)
4. [Amenazas y controles](#4-amenazas-y-controles)
5. [Casos de seguridad](#5-casos-de-seguridad)
6. [Procedimiento](#6-procedimiento)
7. [Una carga manual, paso a paso](#7-una-carga-manual-paso-a-paso)
8. [Un cambio de código, paso a paso](#8-un-cambio-de-código-paso-a-paso)
9. [Entorno y ejecución](#9-entorno-y-ejecución)
10. [Criterios de aceptación](#10-criterios-de-aceptación)
11. [Riesgos aceptados y límites](#11-riesgos-aceptados-y-límites)
12. [Trazabilidad](#12-trazabilidad)
13. [Glosario](#13-glosario)
14. [Historial de versiones](#14-historial-de-versiones)

## 1. En resumen

Las pruebas de GreenOcean responden tres preguntas, siempre de forma automática:

- **¿Las cifras son correctas?** Cada precio se recalcula desde los archivos de ODEPA y por un segundo camino independiente; el resultado debe coincidir.
- **¿Una carga con errores puede llegar al panel?** No: si una prueba falla, la carga se detiene y el panel conserva la última base válida.
- **¿Alguien puede abusar del sistema?** Diez ataques (S-01 a S-10) se repiten en cada cambio del código: leer secretos, colgar el panel, lanzar la carga sin la clave o robar el token.

[[diagrama:niveles]]

## 2. Qué se prueba

| Nivel | Qué verifica | Herramienta | Dónde |
|---|---|---|---|
| Pruebas de datos de dbt | Unicidad, valores aceptados, relaciones entre tablas y conciliación de filas en cada modelo | dbt Core | `dbt/tests/`, modelos de `dbt/models/` |
| Auditoría de cifras | Los precios semanales se reconstruyen desde las filas crudas; las cifras de referencia del panel se reproducen | pytest | `tests/test_data_audit.py`, `tests/test_reconciliation.py` |
| Paridad | El ETL en Python y dbt producen los mismos precios, dimensiones y rechazos | pytest | `tests/test_migration_parity.py` |
| Puerta de publicación | Una carga con pruebas fallidas o con muchas menos filas no reemplaza la base servida | pytest | `tests/test_pipeline_gate.py` |
| IPC y precios reales | El factor semanal, el mes de referencia y las semanas provisionales | pytest | `tests/test_ipc_audit.py` |
| Panel | Cada página se dibuja sin errores y muestra lo que su decisión exige | pytest con AppTest de Streamlit | `tests/test_dashboard.py` y las pruebas de cada vista |
| Diagramas | Cada pieza dibujada existe en el código, el workflow o la base | pytest | `tests/test_devops.py`, `tests/test_monitoring.py`, `tests/test_stack_page.py` y afines |
| Documentos | Trazabilidad de requisitos, cifras contra la base, estructura y redacción | pytest | `tests/test_documents.py`, `tests/test_prd_traceability.py` |
| Medición de pantallas | Desborde horizontal y altura de cada página en varios tamaños de ventana | Playwright, externo al proyecto | `tests/medicion/medir.cjs` |

## 3. Quién participa en la seguridad

[[diagrama:actores]]

La seguridad no depende de esconder el código, que es público, sino de cuatro actores y de lo que cada uno puede hacer:

- **El visitante** lee el panel y usa el estudio SQL sin cuenta: los datos son públicos, y la base está en solo lectura.
- **El autor** mantiene el código y los secretos; con la clave de control abre el botón «Ejecutar pipeline ahora». Entra a GitHub y a Streamlit con su propia cuenta, con verificación en dos pasos.
- **Streamlit Community Cloud** guarda los secretos del panel (el token de GitHub y la clave de control), fuera del repositorio, y publica el panel desde `main`.
- **GitHub** guarda el código, sin ningún secreto, y ejecuta el workflow semanal con los permisos mínimos: escribir contenido y crear issues.

## 4. Amenazas y controles

Las amenazas y los casos se clasifican según el OWASP Top 10 (2021), la lista de riesgos de seguridad de aplicaciones web del Open Worldwide Application Security Project (OWASP).

| Amenaza | Descripción | OWASP | Controles que la mitigan |
|---|---|---|---|
| T1 | Leer secretos o archivos del servidor con SQL | A03 · A05 | SQL público con límites, Base en solo lectura |
| T2 | Colgar el panel con consultas pesadas | A04 | SQL público con límites |
| T3 | Lanzar el pipeline sin permiso | A01 · A07 | Clave de control |
| T4 | Robar el token o la clave | A02 · A09 | Token protegido, Ningún secreto en Git |
| T5 | Abusar de los permisos del workflow | A01 | Privilegio mínimo del job |
| T6 | Tomar la administración de GitHub o Streamlit | A07 | Inicio de sesión externo |

| Control | En qué consiste | Dónde está |
|---|---|---|
| SQL público con límites | Una sola sentencia de lectura, sin archivos ni direcciones web; se corta a los 10 s, devuelve como máximo 5.000 filas y usa como máximo 1 GB de memoria | `bi/sql_explorer.py` |
| Base en solo lectura | Motor sin acceso externo y con la configuración bloqueada | `bi/queries.py`, `bi/sql_explorer.py` |
| Clave de control | Evita ejecuciones accidentales; se compara en tiempo constante | `bi/control.py`, `bi/dashboard.py` |
| Token protegido | Nunca aparece en pantalla ni en los mensajes de error; el panel avisa antes de su vencimiento | `bi/control.py` |
| Ningún secreto en Git | El repositorio es público; los secretos viven en la plataforma del panel | `.gitignore` |
| Privilegio mínimo del job | El workflow semanal solo puede escribir contenido y crear issues | `.github/workflows/semanal.yml` |
| Inicio de sesión externo | Declarado por el autor; no verificable desde el repositorio | Configuración de GitHub y Streamlit |

La representación gráfica de las zonas de confianza, los controles y las amenazas está en [[vista:Arquitectura de seguridad]].

## 5. Casos de seguridad

Precondición común: el entorno de la sección 9, sin el secreto real.

| Caso | Nombre | Pasos | Resultado esperado | OWASP | Prueba |
|---|---|---|---|---|---|
| S-01 | SQL que lee secretos | 19 consultas SQL para leer secretos o escribir archivos | Rechazada; el secreto nunca aparece | A03 | `tests/test_security.py::test_the_filter_and_the_engine_stop_every_attack_on_the_server_files` |
| S-02 | Órdenes directas al motor | 9 órdenes directas al motor | Error de permiso | A05 | `tests/test_security.py::test_the_engine_refuses_even_if_the_filter_is_bypassed` |
| S-03 | Consultas sin fin | Consultas sin fin o de millones de filas | Cortada a los 10 segundos; como máximo 5.000 filas | A04 | `tests/test_sql_explorer.py::test_slow_query_is_interrupted`, `tests/test_sql_explorer.py::test_result_is_limited_and_flagged` |
| S-04 | Clave con ñ o emojis | Clave con ñ, tildes o emojis | «Clave incorrecta.», sin error | A07 | `tests/test_control.py::test_d199_the_right_code_opens_and_any_character_is_safe` |
| S-05 | Probar claves sin parar | Probar claves sin parar | «Clave incorrecta.» cada vez, sin bloqueo (riesgo aceptado, sección 11) | A07 | `tests/test_control.py::test_d249_there_is_no_limit_of_attempts_and_the_comparison_is_constant_time` |
| S-06 | Tokens en el repositorio | Buscar tokens en el repositorio | Ninguno | A02 | `tests/test_security.py::test_no_secret_is_tracked_by_git` |
| S-07 | Error de GitHub | Provocar un error de GitHub | El mensaje nunca muestra el token | A09 | `tests/test_control.py::test_github_error_never_shows_the_token` |
| S-08 | Permisos del workflow | Abusar de los permisos del workflow | Solo contenido e issues | A01 | `tests/test_security.py::test_the_weekly_job_has_least_privilege` |
| S-09 | Control sin prueba | Afirmar un control sin prueba | Cada control de la arquitectura de seguridad apunta a una prueba que existe | — | `tests/test_security.py::test_every_control_of_the_map_points_to_a_test_that_exists` |
| S-10 | Pipeline sin la clave | Lanzar el pipeline sin la clave | El botón no existe antes de la clave | A01 | `tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code` |

**Resultado obtenido:** cada caso se ejecuta en cada push; un caso que no cumple su resultado esperado hace fallar `pruebas.yml`. La revisión del 20-10-2026 encontró un error de la clave de control con caracteres no ASCII, corregido en D-199 (clave con cualquier carácter), y una frase inexacta del SAD, corregida en D-200.

El esquema interactivo de los casos, con cada caso sobre la tecnología que ataca, acompaña esta tabla:

[[diagrama:pruebas]]

## 6. Procedimiento

[[diagrama:sop]]

| Paso | Acción | Detalle |
|---|---|---|
| 1 | Preparar | Clonar el repositorio e instalar `requirements.txt`; las pruebas crean un secreto ficticio |
| 2 | Ejecutar | `python -m pytest -q tests/test_security.py tests/test_control.py tests/test_sql_explorer.py tests/test_dashboard.py` |
| 3 | Comprobar | Cada caso compara su resultado con el esperado y falla si no se cumple |
| 4 | Registrar | La salida de pytest en local y, en GitHub, el resultado de `pruebas.yml` junto al commit; toda corrección se registra en `docs/DECISIONES.md` |
| 5 | Decidir | Si pasa, el cambio queda verificado; si falla, se corrige y se vuelve al paso 2 |

## 7. Una carga manual, paso a paso

[[diagrama:secuencia_manual]]

El botón «Ejecutar pipeline ahora» no existe hasta que el autor escribe la clave de control. La clave se compara en tiempo constante y el token, que nunca aparece en pantalla ni en los mensajes de error, solo sirve para lanzar el workflow.

## 8. Un cambio de código, paso a paso

[[diagrama:secuencia_ci]]

Cada cambio corre las mismas pruebas en una máquina limpia de GitHub. Su resultado queda junto al commit; Streamlit publica `main` sin esperarlo, un riesgo aceptado y descrito en la sección 11.

## 9. Entorno y ejecución

| Elemento | Valor |
|---|---|
| Sistema | Cualquier computador con Python 3.11 o 3.12, o una máquina de GitHub Actions (Ubuntu); el panel y las pruebas también corren en versiones más recientes |
| Dependencias | `requirements.txt` (panel y pruebas) y `requirements-pipeline.txt` (dbt) |
| Base | La base servida, descargada con `python bi/served_database.py` |
| Datos crudos | `etl/raw.db`, solo en el computador del autor y en la máquina de cada carga; sin ella, las pruebas que reconstruyen desde las filas crudas se omiten |
| Secretos | Las pruebas crean su propio secreto ficticio y nunca usan el real |
| Ejecución local | `python -m pytest -q` |
| Ejecución continua | `pruebas.yml` en cada push y pull request: compila dbt (`dbt parse`) y ejecuta pytest |
| Antes de publicar | `semanal.yml` ejecuta pytest sobre la base nueva, incluida la paridad |

## 10. Criterios de aceptación

| Momento | Criterio | Verificación |
|---|---|---|
| Entrada | El cambio compila y la base servida está disponible | `dbt parse` |
| Salida de un cambio | La suite completa pasa, incluidos los diez casos de seguridad | `pruebas.yml` en verde |
| Salida de una carga | Pasan las pruebas de dbt, la carga lee al menos el 90 % de las filas de la anterior y pytest pasa sobre la base nueva | `semanal.yml` |
| Seguridad | Cada control apunta a una prueba que existe y ningún secreto está en el repositorio | Casos S-09 y S-06 |
| Cambio de comportamiento | Tiene su entrada en `docs/DECISIONES.md` y sus pruebas | Revisión del autor |

## 11. Riesgos aceptados y límites

| Riesgo o límite | Decisión o mitigación |
|---|---|
| Sin `etl/raw.db`, la reconstrucción desde filas crudas no corre en `pruebas.yml` | Corre en el computador del autor y en cada carga semanal, donde los datos crudos existen |
| Las pruebas que consultan enlaces públicos dependen de la red | Un resultado fallido se repite antes de tratarlo como un defecto del código |
| La medición de pantallas no forma parte de la suite | Se ejecuta antes de cada cambio visual |
| Sin límite de intentos de la clave de control | Riesgo aceptado por el autor (D-249): la clave solo evita pulsar «Ejecutar pipeline ahora» por accidente, lo máximo que permite es lanzar el workflow, y debe ser larga |
| Token de GitHub del panel | Permisos mínimos y renovación antes del vencimiento; el panel avisa cuando faltan menos de 14 días |
| Streamlit publica `main` sin esperar a `pruebas.yml` | El autor revisa en local antes de cada push |
| Verificación en dos pasos de las cuentas | Declarada por el autor; no verificable desde el repositorio |

Los valores secretos y los problemas aún sin corregir no se publican.

## 12. Trazabilidad

Cada pregunta de negocio y cada requisito del [PRD](PRD.md#5-requisitos) nombra la prueba que lo verifica, y `tests/test_prd_traceability.py` exige que cada una exista.

## 13. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](GLOSARIO.md).

## 14. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 20-10-2026 | Primera versión: sección de seguridad con su vista y su plan (D-201, D-202, D-204, D-205) |
| 1.1 | 21-10-2026 | Redacción de documento de ingeniería (D-210, D-214, D-217, D-218) |
| 1.2 | 23-10-2026 | Seguridad como proceso, procedimiento y riesgos aceptados (D-249) |
| 1.3 | 24-10-2026 | Los diez casos en un esquema y el procedimiento como ciclo (D-258) |
| 2.0 | 25-10-2026 | Documento autónomo: referencia, modelo de amenazas, controles, entorno, casos con su prueba y criterios de aceptación (D-279, documentación profesional) |
| 2.1 | 25-10-2026 | El Plan de pruebas, versión 1.0, nace como documento aparte (D-279) |
| 3.0 | 25-10-2026 | Un solo documento para las pruebas y la seguridad: qué se prueba, quién participa, amenazas, casos, procedimiento y las secuencias de una carga manual y de un cambio de código (D-290, documentos para todo lector) |
