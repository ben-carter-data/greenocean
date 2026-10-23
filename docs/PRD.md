# GreenOcean · Documento de requisitos del producto (PRD)

Versión del 20-10-2026. El registro completo de decisiones está en `docs/DECISIONES.md`.

## 1. Contexto

ODEPA publica cada semana los precios mayoristas y al consumidor de frutas, verduras y otros alimentos, y el INE publica el IPC de alimentos. Los datos son abiertos, pero cada serie viene en su propia frecuencia, unidad de venta y nivel de detalle, y ninguna descuenta la inflación. Para compararlos hay que cruzarlos a mano todas las semanas.

## 2. Alcance

| Hace | No hace |
|---|---|
| Integra los precios de ODEPA desde 2022 y el IPC de alimentos del INE | Comparar cadenas de supermercados o tiendas |
| Convierte unidades, agrega por semana y calcula precios reales | Predecir precios o explicar sus causas |
| Rechaza filas inválidas con su motivo y audita cada cifra | Orientar al consumidor sobre dónde comprar |
| Publica un panel de solo lectura con su documentación | Permitir que los usuarios modifiquen datos |

Hoy la base tiene 814.610 precios semanales en 250 semanas (03-01-2022 a 12-10-2026), 9 regiones, 8 canales, 1.609 claves de producto y 202 meses del IPC. La última carga leyó 2.521.012 filas: 2.520.811 cargadas y 201 rechazadas con su motivo.

## 3. Usuarios

| Perfil | Para qué lo usa |
|---|---|
| Analista de pricing | Saber si el precio de hoy es normal para la época, en pesos de hoy |
| Compras y abastecimiento | Ver cuánto paga el consumidor sobre el precio mayorista, por canal |
| Gerencia | Revisar qué se movió en la semana y qué está fuera de lo habitual |
| Revisor técnico | Comprobar la calidad, las pruebas, el linaje y la documentación |

[[diagrama:casos]]

El panel es de consulta. El administrador mantiene el código y los secretos, responde consultas SQL puntuales y puede lanzar una carga manual con la clave de control.

## 4. Preguntas de negocio

Cada pregunta apunta a la pantalla que la responde y a la prueba que lo respalda.

| ID | Pregunta | Pantalla que la responde | Evidencia |
|---|---|---|---|
| P-1 | ¿Qué precios cambiaron esta semana y cuáles son inusuales? | Resumen semanal | `tests/test_home_mockup.py::test_dashboard_alerts_follow_week_and_family_and_keep_severity_order`, `tests/test_data_audit.py::test_an_alert_must_be_unusual_and_material` |
| P-2 | ¿El precio de hoy es normal para la temporada? | Consultas SQL · Precio vs. época | `tests/test_sql_explorer.py::test_every_example_query_returns_rows`, `tests/test_price_context.py::test_price_state_against_p25_and_p75` |
| P-3 | ¿Cuánto paga el consumidor sobre el mayorista? | Consultas SQL · Brecha mayorista | `tests/test_sql_explorer.py::test_every_example_query_returns_rows`, `tests/test_price_context.py::test_gap_is_supermarket_over_street_market_on_common_weeks` |

## 5. Requisitos

Cada requisito tiene un criterio que se puede medir y la evidencia que lo comprueba.

| ID | Requisito | Criterio medible | Evidencia |
|---|---|---|---|
| RF-01 | Carga semanal automática | Un workflow corre cada martes a las 12:00 UTC (`0 12 * * 2`) | `.github/workflows/semanal.yml`, `tests/test_prd_traceability.py::test_rf01_the_weekly_workflow_runs_on_tuesdays` |
| RF-02 | Ninguna fila se pierde | Filas leídas = cargadas + rechazadas: diferencia 0 en cada carga | `dbt/tests/rnf05_rows_reconcile.sql`, `tests/test_etl_run.py::test_rn11_rows_read_equal_rows_loaded_plus_rows_rejected` |
| RF-03 | Solo se publica una carga válida | 31 de 31 pruebas de dbt superadas antes de reemplazar la base | `etl/pipeline.py`, `.github/workflows/semanal.yml` |
| RF-04 | Precios reales junto a los nominales | El factor de cada semana sale del IPC del mes del lunes; las semanas posteriores al último mes publicado se marcan provisionales | `tests/test_ipc_audit.py::test_weekly_factor_uses_the_month_of_the_monday_and_the_last_published_month`, `tests/test_ipc_audit.py::test_only_weeks_after_the_last_published_month_are_provisional` |
| RNF-01 | Costo cero y sin vencimientos | Ningún servicio de pago; solo planes gratuitos permanentes (ADR-31) | `docs/ADR.md` |
| RNF-02 | Cada vista se lee en una pantalla de 1440 × 900 | El contenido de la vista no supera el alto de la ventana a 1440 × 900 | `tests/medicion/medir.cjs` |

## 6. Pantallas

[[diagrama:mockups]]
