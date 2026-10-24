# GreenOcean · Documento de requisitos del producto (PRD)

Versión del 24-10-2026. El registro completo de decisiones está en `docs/DECISIONES.md`.

## 1. Contexto

Cada semana, ODEPA publica los precios mayoristas y al consumidor de frutas, verduras y otros alimentos en Chile, y el INE publica cada mes el IPC de alimentos. Son datos abiertos y confiables, pero no están hechos para compararse: cada serie trae su propia frecuencia, su unidad de venta y su nivel de detalle, y ninguna descuenta la inflación. Quien quiere saber si un precio subió de verdad, o si está caro para la época, tiene que descargar los archivos y cruzarlos a mano, semana tras semana.

GreenOcean hace ese trabajo una sola vez y de forma automática: cada martes descarga las fuentes, las ordena, revisa su calidad y publica un panel donde cada cifra se puede rastrear hasta el archivo original.

## 2. Objetivos

- **Responder en minutos** las preguntas de negocio de la sección 5, que hoy toman horas de planilla.
- **Que cada cifra se pueda comprobar:** todo número del panel se recalcula desde la fuente en las pruebas automáticas.
- **Que funcione solo:** la carga corre cada martes sin intervención, y una carga con problemas nunca llega al panel.
- **Costo cero y sin vencimientos:** solo servicios gratuitos permanentes, para que el proyecto siga funcionando sin que nadie pague ni renueve nada.

## 3. Alcance

| Hace | No hace |
|---|---|
| Integra los precios de ODEPA desde 2022 y el IPC de alimentos del INE | Comparar cadenas de supermercados o tiendas |
| Convierte unidades, agrega por semana y calcula precios reales | Predecir precios o explicar sus causas |
| Rechaza filas inválidas con su motivo y audita cada cifra | Orientar al consumidor sobre dónde comprar |
| Publica un panel de solo lectura con su documentación | Permitir que los usuarios modifiquen datos |

Hoy la base tiene 814.610 precios semanales en 250 semanas (03-01-2022 a 12-10-2026), 9 regiones, 8 canales, 1.609 claves de producto y 202 meses del IPC. La última carga leyó 2.521.012 filas: 2.520.811 cargadas y 201 rechazadas con su motivo.

## 4. Usuarios

| Perfil | Para qué lo usa |
|---|---|
| Analista de pricing | Saber si el precio de hoy es normal para la época y qué alimentos subieron más que la inflación, en pesos de hoy |
| Compras y abastecimiento | Ver cuánto paga el consumidor sobre el precio mayorista del mismo producto |
| Gerencia | Revisar qué se movió en la semana y qué está fuera de lo habitual |
| Revisor técnico | Comprobar que las cifras son confiables: la calidad, las pruebas, el linaje y la documentación |

[[diagrama:casos]]

El panel es de consulta: nadie necesita cuenta para leerlo. El administrador mantiene el código y los secretos, responde consultas SQL puntuales y puede lanzar una carga manual con la clave de control.

## 5. Preguntas de negocio

Cada pregunta apunta a la pantalla que la responde y a la prueba que recalcula su respuesta por otro camino.

| ID | Pregunta | Pantalla que la responde | Evidencia |
|---|---|---|---|
| P-1 | ¿Qué precios cambiaron esta semana y cuáles son inusuales? | Resumen semanal | `tests/test_reconciliation.py::test_k6_sql_and_python_raise_the_same_alerts`, `tests/test_data_audit.py::test_an_alert_must_be_unusual_and_material` |
| P-2 | ¿El precio de hoy es normal para la temporada? | Consultas SQL · Precio vs. época | `tests/test_sql_explorer.py::test_p2_the_price_for_the_season_query_matches_a_recomputation_in_pandas` |
| P-3 | ¿Cuánto paga el consumidor sobre el mayorista? | Consultas SQL · Brecha mayorista | `tests/test_sql_explorer.py::test_p3_the_wholesale_gap_query_matches_a_recomputation_in_pandas` |
| P-4 | ¿Qué alimentos subieron más que la inflación? | Precios e inflación | `tests/test_inflation_view.py::test_p4_each_family_change_and_the_ipc_match_a_recomputation_in_sql`, `tests/test_page_bar.py::test_d267_the_reading_of_a_family_is_recomputed_from_its_index` |
| P-5 | ¿Puedo confiar en estas cifras? | Calidad y auditoría | `tests/test_data_audit.py::test_weekly_prices_rebuild_exactly_from_the_raw_rows`, `tests/test_migration_parity.py::test_every_weekly_price_has_the_same_key_flag_count_and_price` |

## 6. Requisitos

Cada requisito tiene un criterio que se puede medir y la evidencia que lo comprueba. Los funcionales (RF) dicen qué hace el producto; los no funcionales (RNF), cómo debe hacerlo.

| ID | Requisito | Criterio medible | Evidencia |
|---|---|---|---|
| RF-01 | Carga semanal automática | Un workflow corre cada martes a las 12:00 UTC (`0 12 * * 2`) | `.github/workflows/semanal.yml`, `tests/test_prd_traceability.py::test_rf01_the_weekly_workflow_runs_on_tuesdays` |
| RF-02 | Ninguna fila se pierde | Filas leídas = cargadas + rechazadas: diferencia 0 en cada carga | `dbt/tests/rnf05_rows_reconcile.sql`, `tests/test_etl_run.py::test_rn11_rows_read_equal_rows_loaded_plus_rows_rejected` |
| RF-03 | Solo se publica una carga válida | Si falla una de las 31 pruebas de dbt, la carga lee menos del 90 % de la anterior o falla pytest sobre la base nueva, la base publicada no cambia; el workflow queda en rojo en GitHub Actions, que avisa al autor por correo | `tests/test_pipeline_gate.py::test_rf03_a_failed_dbt_build_records_the_failure_and_never_replaces_the_served_database`, `tests/test_pipeline_gate.py::test_rf03_a_load_with_far_fewer_rows_than_the_last_good_one_is_refused`, `.github/workflows/semanal.yml` |
| RF-04 | Precios reales junto a los nominales | El factor de cada semana sale del IPC del mes del lunes; las semanas posteriores al último mes publicado se marcan provisionales | `tests/test_ipc_audit.py::test_weekly_factor_uses_the_month_of_the_monday_and_the_last_published_month`, `tests/test_ipc_audit.py::test_only_weeks_after_the_last_published_month_are_provisional` |
| RF-05 | Alertas de precio | Una alerta exige un cambio inusual para ese producto y de al menos 10 %; SQL y Python levantan las mismas | `tests/test_data_audit.py::test_an_alert_must_be_unusual_and_material`, `tests/test_reconciliation.py::test_k6_sql_and_python_raise_the_same_alerts` |
| RF-06 | Consultas SQL abiertas y de solo lectura | Solo lectura: toda orden que escribe se rechaza; cada consulta devuelve como máximo 5.000 filas y se detiene a los 10 s; el motor no lee archivos ni la red | `tests/test_sql_explorer.py::test_forbidden_statements_are_rejected`, `tests/test_sql_explorer.py::test_result_is_limited_and_flagged`, `tests/test_sql_explorer.py::test_slow_query_is_interrupted`, `tests/test_sql_explorer.py::test_external_access_is_disabled_at_the_engine` |
| RF-07 | Carga manual protegida | Ninguna carga manual sin la clave de control: el botón «Ejecutar pipeline ahora» aparece solo después de ella, y la clave se compara en tiempo constante | `tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code`, `tests/test_control.py::test_d249_there_is_no_limit_of_attempts_and_the_comparison_is_constant_time` |
| RF-08 | Informe semanal | Cada carga publicada deja un informe con su estado y las alertas de la semana, como issue del repositorio | `.github/workflows/semanal.yml`, `tests/test_report.py::test_report_shows_the_load_status_and_the_alert_of_the_week` |
| RNF-01 | Costo cero y sin vencimientos | Ningún servicio de pago; solo planes gratuitos permanentes (ADR-31) | `docs/ADR.md` |
| RNF-02 | Cada cifra se puede comprobar | Los precios semanales se reconstruyen desde las filas crudas y por un segundo camino independiente, sin dbt: diferencia 0 | `tests/test_data_audit.py::test_weekly_prices_rebuild_exactly_from_the_raw_rows`, `tests/test_migration_parity.py::test_every_weekly_price_has_the_same_key_flag_count_and_price`, `tests/test_data_audit.py::test_the_panel_reproduces_the_reference_figures_of_its_week` |
| RNF-03 | Seguridad | Ningún secreto en el repositorio; el workflow semanal tiene solo los permisos que usa; el panel no puede escribir la base | `tests/test_security.py::test_no_secret_is_tracked_by_git`, `tests/test_security.py::test_the_weekly_job_has_least_privilege`, `tests/test_dashboard.py::test_c03_every_result_is_read_only_and_runs_only_stored_queries` |
| RNF-04 | Calidad vigilada en cada cambio | pytest y la compilación de dbt corren en cada push; los 11 indicadores de calidad se miden en cada carga y uno fuera de su umbral pone el veredicto en rojo | `.github/workflows/pruebas.yml`, `tests/test_quality_audit.py::test_a_degraded_measure_turns_its_indicator_and_the_verdict_red` |
| RNF-05 | Se lee en computador, tableta y teléfono | Ninguna página se desplaza a lo ancho entre 1024 × 768 y 1920 × 1080, en tableta vertical (768 × 1024) ni en teléfono horizontal (844 × 390); en vertical, el panel pide girar el teléfono (D-166) | `tests/medicion/medir.cjs` |
| RNF-06 | Cada página principal en una pantalla | A 1440 × 900, cada página principal se ve entera, sin desplazar, en su vista inicial (D-264, D-267) | `tests/medicion/medir.cjs` |

## 7. Supuestos y límites

- **El precio nacional es un promedio simple de las regiones**, sin ponderar por población ni por ventas, porque ninguna fuente abierta publica esos pesos. Cada variación semanal compara solo las regiones con precio en ambas semanas.
- **Los indicadores describen lo que pasó; no predicen** ni atribuyen causas. Que una familia suba con el IPC no prueba que la inflación la haya movido: el IPC de alimentos se calcula con esos mismos precios.
- **El último mes del IPC puede faltar:** el INE publica con algunas semanas de retraso. Esas semanas usan el último mes publicado y se marcan provisionales; nunca se inventa un índice.
- **Las fuentes mandan:** si ODEPA cambia el formato de sus archivos o deja de publicar, una carga incompleta o mal leída no pasa los controles de RF-03 y el panel sigue mostrando la última carga válida hasta que se ajuste el agente.
- **Lo mantiene una sola persona** y depende de planes gratuitos de GitHub y Streamlit; los riesgos técnicos y cómo crecería están en el SAD y en [[vista:Escalabilidad]].

## 8. Pantallas

Capturas reales del panel, una por tema de color.

[[diagrama:mockups]]
