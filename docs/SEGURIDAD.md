# Plan de pruebas de seguridad

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Plan de pruebas de seguridad |
| Versión | 2.0 |
| Fecha | 25-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Definir cómo se verifica, con pruebas repetibles, que los controles de seguridad del sistema siguen vigentes. |
| Audiencia | Seguridad, arquitectura, operación y revisión técnica. |
| Documentos relacionados | [Documento de arquitectura de software (SAD)](SAD.md) · [Plan de pruebas](PLAN_PRUEBAS.md) · [Manual de operación](MANUAL.md) · [Glosario](GLOSARIO.md) |

## Índice

1. [Objetivo y alcance](#1-objetivo-y-alcance)
2. [Referencia](#2-referencia)
3. [Modelo de amenazas](#3-modelo-de-amenazas)
4. [Entorno de prueba](#4-entorno-de-prueba)
5. [Procedimiento](#5-procedimiento)
6. [Casos de prueba](#6-casos-de-prueba)
7. [Criterios de aceptación](#7-criterios-de-aceptación)
8. [Riesgos aceptados y límites](#8-riesgos-aceptados-y-límites)
9. [Glosario](#9-glosario)
10. [Historial de versiones](#10-historial-de-versiones)

## 1. Objetivo y alcance

**Objetivo:** comprobar que un visitante no puede leer los secretos, modificar los datos ni lanzar el pipeline sin la clave de control.

**Alcance:** todo lo que se alcanza desde internet: el panel, el estudio de Consultas SQL (abierto a cualquier visitante, porque los datos son públicos), la clave de control y el código público del repositorio.

**Fuera de alcance:** las cuentas de GitHub y de Streamlit Community Cloud. Las protege su propio inicio de sesión, una configuración de cada plataforma que no se puede verificar desde el repositorio.

## 2. Referencia

Las amenazas y los casos se clasifican según el OWASP Top 10 (2021), la lista de riesgos de seguridad de aplicaciones web del Open Worldwide Application Security Project (OWASP).

## 3. Modelo de amenazas

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

## 4. Entorno de prueba

| Elemento | Valor |
|---|---|
| Sistema | Cualquier computador con Python 3.11 o 3.12, o una máquina de GitHub Actions (Ubuntu) |
| Dependencias | `requirements.txt` |
| Datos | La base servida (`python bi/served_database.py`); las pruebas crean su propio secreto ficticio y nunca usan el real |
| Herramienta | pytest |
| Ejecución continua | El workflow `pruebas.yml` ejecuta las mismas pruebas en cada push y pull request |

## 5. Procedimiento

[[diagrama:sop]]

| Paso | Acción | Detalle |
|---|---|---|
| 1 | Preparar | Clonar el repositorio e instalar `requirements.txt`; las pruebas crean un secreto ficticio |
| 2 | Ejecutar | `python -m pytest -q tests/test_security.py tests/test_control.py tests/test_sql_explorer.py tests/test_dashboard.py` |
| 3 | Comprobar | Cada caso compara su resultado con el esperado y falla si no se cumple |
| 4 | Registrar | La salida de pytest en local y, en GitHub, el resultado de `pruebas.yml` junto al commit; toda corrección se registra en `docs/DECISIONES.md` |
| 5 | Decidir | Si pasa, el cambio queda verificado; si falla, se corrige y se vuelve al paso 2 |

## 6. Casos de prueba

Precondición común: entorno de la sección 4, sin el secreto real.

| Caso | Nombre | Pasos | Resultado esperado | OWASP | Prueba |
|---|---|---|---|---|---|
| S-01 | SQL que lee secretos | 19 consultas SQL para leer secretos o escribir archivos | Rechazada; el secreto nunca aparece | A03 | `tests/test_security.py::test_the_filter_and_the_engine_stop_every_attack_on_the_server_files` |
| S-02 | Órdenes directas al motor | 9 órdenes directas al motor | Error de permiso | A05 | `tests/test_security.py::test_the_engine_refuses_even_if_the_filter_is_bypassed` |
| S-03 | Consultas sin fin | Consultas sin fin o de millones de filas | Cortada a los 10 segundos; como máximo 5.000 filas | A04 | `tests/test_sql_explorer.py::test_slow_query_is_interrupted`, `tests/test_sql_explorer.py::test_result_is_limited_and_flagged` |
| S-04 | Clave con ñ o emojis | Clave con ñ, tildes o emojis | «Clave incorrecta.», sin error | A07 | `tests/test_control.py::test_d199_the_right_code_opens_and_any_character_is_safe` |
| S-05 | Probar claves sin parar | Probar claves sin parar | «Clave incorrecta.» cada vez, sin bloqueo (riesgo aceptado, sección 8) | A07 | `tests/test_control.py::test_d249_there_is_no_limit_of_attempts_and_the_comparison_is_constant_time` |
| S-06 | Tokens en el repositorio | Buscar tokens en el repositorio | Ninguno | A02 | `tests/test_security.py::test_no_secret_is_tracked_by_git` |
| S-07 | Error de GitHub | Provocar un error de GitHub | El mensaje nunca muestra el token | A09 | `tests/test_control.py::test_github_error_never_shows_the_token` |
| S-08 | Permisos del workflow | Abusar de los permisos del workflow | Solo contenido e issues | A01 | `tests/test_security.py::test_the_weekly_job_has_least_privilege` |
| S-09 | Control sin prueba | Afirmar un control sin prueba | Cada control de la arquitectura de seguridad apunta a una prueba que existe | — | `tests/test_security.py::test_every_control_of_the_map_points_to_a_test_that_exists` |
| S-10 | Pipeline sin la clave | Lanzar el pipeline sin la clave | El botón no existe antes de la clave | A01 | `tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code` |

**Resultado obtenido:** cada caso se ejecuta en cada push; un caso que no cumple su resultado esperado hace fallar `pruebas.yml`. La revisión del 20-10-2026 encontró un error de la clave de control con caracteres no ASCII, corregido en D-199 (clave con cualquier carácter), y una frase inexacta del SAD, corregida en D-200.

El esquema interactivo de los casos, con cada caso sobre la tecnología que ataca, acompaña esta tabla:

[[diagrama:pruebas]]

## 7. Criterios de aceptación

| Criterio | Verificación |
|---|---|
| Los diez casos cumplen su resultado esperado | pytest en verde en local y en `pruebas.yml` |
| Cada control apunta a una prueba que existe | Caso S-09 |
| Ningún secreto en el repositorio | Caso S-06 |

## 8. Riesgos aceptados y límites

| Riesgo o límite | Decisión | Condición |
|---|---|---|
| Sin límite de intentos de la clave de control | Riesgo aceptado por el autor (D-249, seguridad como proceso): la clave solo evita pulsar «Ejecutar pipeline ahora» por accidente, y lo máximo que permite es lanzar el workflow | La clave debe ser larga |
| Token de GitHub del panel | Permisos mínimos y renovación antes del vencimiento | El panel avisa cuando faltan menos de 14 días |
| Verificación en dos pasos de las cuentas | Declarada por el autor; no verificable desde el repositorio | Fuera de alcance (sección 1) |

Los valores secretos y los problemas aún sin corregir no se publican.

## 9. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](GLOSARIO.md).

## 10. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 20-10-2026 | Primera versión: sección de seguridad con su vista y su plan (D-201, D-202, D-204, D-205) |
| 1.1 | 21-10-2026 | Redacción de documento de ingeniería (D-210, D-214, D-217, D-218) |
| 1.2 | 23-10-2026 | Seguridad como proceso, procedimiento y riesgos aceptados (D-249) |
| 1.3 | 24-10-2026 | Los diez casos en un esquema y el procedimiento como ciclo (D-258) |
| 2.0 | 25-10-2026 | Documento autónomo: referencia, modelo de amenazas, controles, entorno, casos con su prueba y criterios de aceptación (D-279, documentación profesional) |
