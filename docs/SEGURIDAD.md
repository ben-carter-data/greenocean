# GreenOcean · Plan de pruebas de seguridad

Cómo se verifica, paso a paso, que los controles de seguridad del panel siguen cerrados. Revisión del 20-10-2026 (D-199 a D-202), actualizada el 23-10-2026 (D-249), con el OWASP Top 10 (2021) como referencia.

## 1. Objetivo y alcance

El objetivo es comprobar, con pruebas que cualquiera puede repetir, que un visitante no puede leer los secretos, cambiar los datos ni lanzar el pipeline sin la clave de control. La revisión cubre todo lo que se alcanza desde internet: el panel, el estudio de Consultas SQL (abierto a cualquier visitante, porque los datos son públicos), la clave de control y el código público. Las cuentas de GitHub y de Streamlit Cloud quedan fuera: las protege su propio inicio de sesión, que es una configuración de cada plataforma y no se puede verificar desde el repositorio.

## 2. Amenazas y controles

Las seis amenazas, el control que mitiga cada una, la prueba que lo verifica, el activo que protege y el ciclo de mejora continua que los mantiene están en [[vista:Arquitectura de seguridad]]. Aquí no se repiten: este documento dice cómo comprobarlos.

## 3. Procedimiento

[[diagrama:sop]]

Cada paso se puede repetir en cualquier computador con Python 3.11 o 3.12. En GitHub, el workflow `pruebas.yml` ejecuta las mismas pruebas en cada push y pull request.

## 4. Casos de prueba

| ID | Ataque | Resultado esperado | OWASP | Prueba |
|---|---|---|---|---|
| S-01 | 19 consultas SQL para leer secretos o escribir archivos | Rechazada; el secreto nunca aparece | A03 | `tests/test_security.py::test_the_filter_and_the_engine_stop_every_attack_on_the_server_files` |
| S-02 | 9 órdenes directas al motor | Error de permiso | A05 | `tests/test_security.py::test_the_engine_refuses_even_if_the_filter_is_bypassed` |
| S-03 | Consultas sin fin o de millones de filas | Cortada a los 10 segundos; como máximo 5.000 filas | A04 | `tests/test_sql_explorer.py::test_slow_query_is_interrupted`, `tests/test_sql_explorer.py::test_result_is_limited_and_flagged` |
| S-04 | Clave con ñ, tildes o emojis | «Clave incorrecta.», sin error | A07 | `tests/test_control.py::test_d199_the_right_code_opens_and_any_character_is_safe` |
| S-05 | Probar claves sin parar | «Clave incorrecta.» cada vez, sin bloqueo: riesgo aceptado (ver 5) | A07 | `tests/test_control.py::test_d249_there_is_no_limit_of_attempts_and_the_comparison_is_constant_time` |
| S-06 | Buscar tokens en el repositorio | Ninguno | A02 | `tests/test_security.py::test_no_secret_is_tracked_by_git` |
| S-07 | Provocar un error de GitHub | El mensaje nunca muestra el token | A09 | `tests/test_control.py::test_github_error_never_shows_the_token` |
| S-08 | Abusar de los permisos del workflow | Solo contenido e issues | A01 | `tests/test_security.py::test_the_weekly_job_has_least_privilege` |
| S-09 | Afirmar un control sin prueba | Cada control de la arquitectura de seguridad apunta a una prueba que existe | — | `tests/test_security.py::test_every_control_of_the_map_points_to_a_test_that_exists` |
| S-10 | Lanzar el pipeline sin la clave | El botón no existe antes de la clave | A01 | `tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code` |

## 5. Resultados y límites

La revisión del 20-10-2026 encontró un error de la clave de control con caracteres no ASCII, corregido en D-199, y una frase inexacta del SAD, corregida en D-200. **Sin límite de intentos de la clave:** riesgo aceptado por el autor (D-249), porque la clave solo evita que alguien pulse «Ejecutar pipeline ahora» por accidente y, con ese botón, lo máximo que se puede hacer es lanzar el workflow. Para que todo esto se sostenga, la clave de control debe ser larga, el token de GitHub debe tener solo los permisos necesarios y renovarse antes de vencer, y las cuentas de administración deben usar verificación en dos pasos; esto último lo declara el autor y no se puede comprobar desde el repositorio. Los valores secretos y los problemas aún sin corregir nunca se publican.
