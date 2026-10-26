# Documento de requisitos del producto (PRD)

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Documento de requisitos del producto (PRD) |
| Versión | 3.0 |
| Fecha | 25-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Explicar qué problema resuelve GreenOcean, para quién, qué preguntas responde y qué debe cumplir para que sus cifras sean confiables. |
| Audiencia | Gerencia, responsables de producto, analistas y revisión técnica. |
| Documentos relacionados | [Documento de arquitectura de software (SAD)](SAD.md) · [Registros de decisiones de arquitectura (ADR)](ADR.md) · [Plan de pruebas y seguridad](PLAN_PRUEBAS.md) · [Glosario](GLOSARIO.md) |

## Índice

1. [En resumen](#1-en-resumen)
2. [El problema](#2-el-problema)
3. [Para quién es](#3-para-quién-es)
4. [Preguntas de negocio](#4-preguntas-de-negocio)
5. [Requisitos](#5-requisitos)
6. [Alcance](#6-alcance)
7. [Pantallas](#7-pantallas)
8. [Supuestos, restricciones y dependencias](#8-supuestos-restricciones-y-dependencias)
9. [Riesgos](#9-riesgos)
10. [Criterios de aceptación](#10-criterios-de-aceptación)
11. [Próximos pasos](#11-próximos-pasos)
12. [Glosario](#12-glosario)
13. [Historial de versiones](#13-historial-de-versiones)

## 1. En resumen

GreenOcean convierte los precios oficiales de los alimentos en Chile en respuestas claras, cada semana y sin intervención.

- **Qué hace:** cada martes descarga los precios de ODEPA y el IPC del INE, los revisa y publica un panel de consulta.
- **Para quién:** analistas de precios, compras, gerencia y quien necesite comprobar las cifras.
- **Qué responde:** qué cambió en la semana, si un precio es normal para la época, cuánto paga el consumidor sobre el mayorista, qué subió más que la inflación y si las cifras son confiables.
- **Por qué confiar:** cada cifra se puede seguir hasta el archivo original, y una carga con errores nunca llega al panel.

[[diagrama:valor]]

## 2. El problema

La Oficina de Estudios y Políticas Agrarias (ODEPA) publica cada semana los precios mayoristas y al consumidor de frutas, verduras y otros alimentos. El Instituto Nacional de Estadísticas (INE) publica cada mes el índice de precios al consumidor (IPC) de alimentos. Son datos abiertos y confiables, pero no están listos para compararse: cada serie trae su propia frecuencia, unidad y nivel de detalle, y ninguna descuenta la inflación. Responder si un precio subió en términos reales, o si es alto para la época, exige descargar y cruzar archivos a mano cada semana.

GreenOcean hace ese trabajo de forma automática y deja cada paso a la vista.

## 3. Para quién es

| Perfil | Para qué lo usa |
|---|---|
| Analista de pricing | Saber si el precio de hoy es normal para la época y qué alimentos subieron más que la inflación, en pesos de hoy |
| Compras y abastecimiento | Ver cuánto paga el consumidor sobre el precio mayorista del mismo producto |
| Gerencia | Revisar qué se movió en la semana y qué está fuera de lo habitual |
| Revisor técnico | Comprobar que las cifras son confiables: la calidad, las pruebas, el linaje y la documentación |

[[diagrama:casos]]

El panel es de consulta y no pide cuenta. Al entrar se elige una vista: la de usuario muestra el negocio (el dashboard, el resumen semanal y los precios frente a la inflación) y la profesional, todo el proyecto en orden de importancia; un clic pasa de una a otra. El administrador, el autor del proyecto, mantiene el código y los secretos, responde consultas SQL puntuales y puede lanzar una carga manual con la clave de control.

## 4. Preguntas de negocio

Cada pregunta tiene la pantalla que la responde y la prueba que recalcula su respuesta por un camino independiente.

| ID | Pregunta | Pantalla que la responde | Evidencia |
|---|---|---|---|
| P-1 | ¿Qué precios cambiaron esta semana y cuáles son inusuales? | Resumen semanal | `tests/test_reconciliation.py::test_k6_sql_and_python_raise_the_same_alerts`, `tests/test_data_audit.py::test_an_alert_must_be_unusual_and_material` |
| P-2 | ¿El precio de hoy es normal para la temporada? | Consultas SQL · Precio vs. época | `tests/test_sql_explorer.py::test_p2_the_price_for_the_season_query_matches_a_recomputation_in_pandas` |
| P-3 | ¿Cuánto paga el consumidor sobre el mayorista? | Consultas SQL · Brecha mayorista | `tests/test_sql_explorer.py::test_p3_the_wholesale_gap_query_matches_a_recomputation_in_pandas` |
| P-4 | ¿Qué alimentos subieron más que la inflación? | Precios e inflación | `tests/test_inflation_view.py::test_p4_each_family_change_and_the_ipc_match_a_recomputation_in_sql`, `tests/test_page_bar.py::test_d267_the_reading_of_a_family_is_recomputed_from_its_index` |
| P-5 | ¿Las cifras son confiables? | Calidad y auditoría | `tests/test_data_audit.py::test_weekly_prices_rebuild_exactly_from_the_raw_rows`, `tests/test_migration_parity.py::test_every_weekly_price_has_the_same_key_flag_count_and_price` |

## 5. Requisitos

Los requisitos funcionales (RF) dicen qué hace el producto; los no funcionales (RNF), con qué cualidades. Cada uno tiene un criterio medible y la prueba que lo comprueba.

[[diagrama:requisitos]]

| ID | Requisito | Criterio medible | Evidencia |
|---|---|---|---|
| RF-01 | Carga semanal automática | Un workflow corre cada martes a las 12:00 UTC (`0 12 * * 2`) | `.github/workflows/semanal.yml`, `tests/test_prd_traceability.py::test_rf01_the_weekly_workflow_runs_on_tuesdays` |
| RF-02 | Ninguna fila se pierde | Filas leídas = cargadas + rechazadas: diferencia 0 en cada carga | `dbt/tests/rnf05_rows_reconcile.sql`, `tests/test_etl_run.py::test_rn11_rows_read_equal_rows_loaded_plus_rows_rejected` |
| RF-03 | Solo se publica una carga válida | Si falla una de las 31 pruebas de dbt, la carga lee menos del 90 % de la anterior o falla pytest sobre la base nueva, la base servida no cambia; GitHub Actions marca la ejecución como fallida y avisa al autor por correo | `tests/test_pipeline_gate.py::test_rf03_a_failed_dbt_build_records_the_failure_and_never_replaces_the_served_database`, `tests/test_pipeline_gate.py::test_rf03_a_load_with_far_fewer_rows_than_the_last_good_one_is_refused`, `.github/workflows/semanal.yml` |
| RF-04 | Precios reales junto a los nominales | El factor de cada semana sale del IPC del mes de su lunes; las semanas posteriores al último mes publicado se marcan como provisionales | `tests/test_ipc_audit.py::test_weekly_factor_uses_the_month_of_the_monday_and_the_last_published_month`, `tests/test_ipc_audit.py::test_only_weeks_after_the_last_published_month_are_provisional` |
| RF-05 | Alertas de precio | Una alerta exige un cambio inusual para ese producto y de al menos 10 %; SQL y Python levantan las mismas | `tests/test_data_audit.py::test_an_alert_must_be_unusual_and_material`, `tests/test_reconciliation.py::test_k6_sql_and_python_raise_the_same_alerts` |
| RF-06 | Consultas SQL abiertas y de solo lectura | Toda orden que escribe se rechaza; cada consulta devuelve como máximo 5.000 filas y se detiene a los 10 s; el motor no lee archivos ni la red | `tests/test_sql_explorer.py::test_forbidden_statements_are_rejected`, `tests/test_sql_explorer.py::test_result_is_limited_and_flagged`, `tests/test_sql_explorer.py::test_slow_query_is_interrupted`, `tests/test_sql_explorer.py::test_external_access_is_disabled_at_the_engine` |
| RF-07 | Carga manual protegida | Ninguna carga manual sin la clave de control: el botón «Ejecutar pipeline ahora» aparece solo después de ella, y la clave se compara en tiempo constante | `tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code`, `tests/test_control.py::test_d249_there_is_no_limit_of_attempts_and_the_comparison_is_constant_time` |
| RF-08 | Informe semanal | Cada carga publicada deja un informe con su estado y las alertas de la semana, como issue del repositorio | `.github/workflows/semanal.yml`, `tests/test_report.py::test_report_shows_the_load_status_and_the_alert_of_the_week` |
| RNF-01 | Costo cero y sin vencimientos | Ningún servicio de pago; solo planes gratuitos permanentes ([ADR-31 · No usar un data warehouse en la nube](ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube)) | `docs/ADR.md` |
| RNF-02 | Cada cifra se puede comprobar | Los precios semanales se reconstruyen desde las filas crudas y por un segundo camino independiente, sin dbt: diferencia 0 | `tests/test_data_audit.py::test_weekly_prices_rebuild_exactly_from_the_raw_rows`, `tests/test_migration_parity.py::test_every_weekly_price_has_the_same_key_flag_count_and_price`, `tests/test_data_audit.py::test_the_panel_reproduces_the_reference_figures_of_its_week` |
| RNF-03 | Seguridad | Ningún secreto en el repositorio; el workflow semanal tiene solo los permisos que usa; el panel no puede escribir la base | `tests/test_security.py::test_no_secret_is_tracked_by_git`, `tests/test_security.py::test_the_weekly_job_has_least_privilege`, `tests/test_dashboard.py::test_c03_every_result_is_read_only_and_runs_only_stored_queries` |
| RNF-04 | Calidad vigilada en cada cambio | pytest y la compilación de dbt corren en cada push; los 11 indicadores de calidad se miden en cada carga y uno fuera de su umbral cambia el veredicto | `.github/workflows/pruebas.yml`, `tests/test_quality_audit.py::test_a_degraded_measure_turns_its_indicator_and_the_verdict_red` |
| RNF-05 | Legible en computador, tableta y teléfono | Ninguna página se desplaza a lo ancho entre 1024 × 768 y 1920 × 1080, en tableta vertical (768 × 1024) ni en teléfono horizontal (844 × 390); en vertical, el panel pide girar el teléfono | `tests/medicion/medir.cjs` |
| RNF-06 | Cada página principal en una pantalla | En la ventana del navegador de una pantalla de 1440 × 900 (1440 × 790 útiles) y a 1920 × 1000, cada página principal se ve entera, sin desplazar | `tests/medicion/medir.cjs` |

## 6. Alcance

| Incluye | Excluye |
|---|---|
| Integración de los precios de ODEPA desde 2022 y del IPC de alimentos del INE | Comparación entre cadenas de supermercados o tiendas |
| Conversión de unidades, agregación semanal y cálculo de precios reales | Predicción de precios o explicación de sus causas |
| Rechazo de filas inválidas con su motivo y auditoría de cada cifra | Recomendaciones de compra para el consumidor |
| Panel de solo lectura con su documentación | Modificación de datos por parte de los usuarios |

Con la carga del 20-10-2026, la base tiene 814.610 precios semanales en 250 semanas (03-01-2022 a 12-10-2026), 9 regiones, 8 canales, 1.609 claves de producto y 202 meses del IPC. Esa carga leyó 2.521.012 filas: 2.520.811 cargadas y 201 rechazadas con su motivo. Cada martes la base crece; las cifras del día están en el panel.

## 7. Pantallas

Capturas reales de las páginas principales, en los cuatro temas de color.

[[diagrama:mockups]]

## 8. Supuestos, restricciones y dependencias

**Supuestos**
- El precio nacional es un promedio simple de las regiones, sin ponderar por población ni por ventas, porque ninguna fuente abierta publica esos pesos. Cada variación semanal compara solo las regiones con precio en ambas semanas.
- Los indicadores describen lo ocurrido; no predicen ni atribuyen causas. Que una familia suba con el IPC no prueba que la inflación la haya movido: el IPC de alimentos se calcula con esos mismos precios.

**Restricciones**
- Costo cero: solo planes gratuitos permanentes de GitHub y Streamlit Community Cloud.
- Ninguna cifra se inventa ni se interpola, y el histórico nunca se borra.
- El último mes del IPC puede no estar publicado: esas semanas usan el último mes disponible y se marcan como provisionales.

**Dependencias**

| Dependencia | Para qué | Si falla |
|---|---|---|
| ODEPA (datos.odepa.gob.cl) | Precios mayoristas y al consumidor | La carga no pasa sus controles y el panel conserva la última carga válida |
| INE | IPC de alimentos | Se conserva el último IPC leído; las semanas nuevas quedan provisionales |
| GitHub (repositorio, Actions, releases) | Código, ejecución de la carga y base servida | No hay carga nueva; el panel conserva la base que ya tiene |
| Streamlit Community Cloud | Publicación del panel | El panel no está disponible; los datos no se pierden |

## 9. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| ODEPA cambia el formato de sus archivos | Media | Alto | Las puertas de calidad rechazan una carga mal leída ([SAD, la carga de cada semana](SAD.md#4-la-carga-de-cada-semana)) |
| Se interpreta una correlación como causa | Media | Medio | El panel y este documento lo advierten junto a cada comparación con el IPC |
| Cambian las condiciones de un plan gratuito | Baja | Alto | El pipeline corre igual en cualquier máquina con Python 3.11 o 3.12 |
| Un solo responsable de mantenimiento | Alta | Medio | Operación documentada en el [Manual de operación](MANUAL.md) y pruebas automáticas en cada cambio |

## 10. Criterios de aceptación

| Criterio | Cómo se verifica |
|---|---|
| Cada pregunta de negocio tiene pantalla y evidencia existentes | `tests/test_prd_traceability.py` |
| Cada requisito tiene criterio medible y evidencia existente | `tests/test_prd_traceability.py` |
| La suite completa pasa en cada push | `.github/workflows/pruebas.yml` |
| Las cifras de este documento coinciden con la base servida | `tests/test_documents.py::test_d210_the_prd_figures_match_the_served_database` |
| Cada página principal cabe en una pantalla | `tests/medicion/medir.cjs` a 1440 × 790 y 1920 × 1000 |

## 11. Próximos pasos

La incorporación del clima por región y las condiciones bajo las que se justificaría un data warehouse en la nube se describen en el [SAD, capacidad y crecimiento](SAD.md#9-capacidad-y-crecimiento).

## 12. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](GLOSARIO.md).

## 13. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 18-10-2026 | Primera versión: la documentación del proyecto pasa a ser el PRD, el SAD y el ADR (D-151, documentación en tres documentos) |
| 1.1 | 19-10-2026 | Evolución prevista hacia dbt, DuckDB, Parquet y el IPC (D-152, evolución del stack); alertas con dos cotizaciones por semana (D-158, alertas de precio) |
| 1.2 | 20-10-2026 | Cifras alineadas con la base de la semana del 12-10-2026; diagramas propios (D-205, diagramas de los documentos); perfil «Revisor técnico» (D-208) |
| 1.3 | 21-10-2026 | Redacción de documento de ingeniería y extensión acotada (D-210, D-214 y D-217, redacción de los documentos) |
| 1.4 | 23-10-2026 | Casos de uso y trazabilidad de requisitos (D-240); pregunta P-4 (D-244); RF-03 con su prueba (D-245); la descarga es la página impresa (D-248) |
| 1.5 | 24-10-2026 | Revisión de coherencia (D-252); objetivos, pregunta P-5, catorce requisitos y supuestos (D-269, documentos revisados contra el producto) |
| 2.0 | 25-10-2026 | Estructura estándar: cabecera, índice, restricciones y dependencias, riesgos, criterios de aceptación, glosario e historial; medida de pantalla corregida a 1440 × 790 útiles (D-279, documentación profesional) |
| 3.0 | 25-10-2026 | Lectura de lo más importante a lo menos: resumen, problema, usuarios, preguntas y requisitos primero; diagramas del valor y de los requisitos (D-290, documentos para todo lector) |
