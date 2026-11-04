# Documento de requisitos del producto (PRD)

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Documento de requisitos del producto (PRD) |
| Versión | 3.54 |
| Fecha | 04-11-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Explicar qué problema resuelve GreenOcean, para quién, qué preguntas responde y qué debe cumplir para que sus cifras sean confiables. |
| Audiencia | Gerencia, responsables de producto, analistas y revisores técnicos. |
| Documentos relacionados | [Documento de arquitectura de software (SAD)](../arquitectura/SAD.md) · [Registros de decisiones de arquitectura (ADR)](../arquitectura/ADR.md) · [Plan de pruebas y seguridad](../calidad/PLAN_PRUEBAS.md) · [Glosario](GLOSARIO.md) |

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

GreenOcean publica cada semana cómo se mueven los precios de los alimentos en Chile. Toma los datos oficiales de ODEPA y del INE, los revisa y los deja en un panel que cualquiera puede abrir. Nadie tiene que descargar archivos ni cruzarlos a mano.

- **Visión:** que cualquier persona en Chile sepa, con datos oficiales, cómo se mueven los precios de los alimentos.
- **Misión:** publicar cada semana precios revisados y fáciles de leer, y mejorar el proceso con cada carga.
- **Qué responde:** qué cambió esta semana, si un precio es normal para la época, cuánto paga el consumidor sobre el mayorista y qué alimentos subieron más que la inflación.
- **Para quién:** quien compra o vende alimentos, quien informa sobre precios y quien revisa cómo está hecho el proyecto.
- **Por qué fiarse:** cada cifra se puede seguir hasta el archivo original, y una carga con errores no llega al panel.

## 2. El problema

La Oficina de Estudios y Políticas Agrarias (ODEPA) publica cada semana los precios mayoristas y al consumidor de frutas, verduras y otros alimentos. El Instituto Nacional de Estadísticas (INE) publica cada mes el índice de precios al consumidor (IPC) de alimentos. Son datos abiertos y confiables, pero no se pueden comparar tal como llegan. Cada serie tiene su frecuencia, su unidad y su nivel de detalle, y ninguna descuenta la inflación. Para saber si un precio subió en términos reales, o si es alto para la época, hay que descargar y cruzar archivos a mano cada semana.

GreenOcean hace ese trabajo solo, cada martes, y deja cada paso a la vista.

[[diagrama:ciclo_semanal]]

## 3. Para quién es

### 3.1 Interesados

Cada interesado tiene una pregunta, una decisión que depende de la respuesta y una página donde la encuentra. En «Análisis», la pestaña [[vista:Insights]] responde sus preguntas con las cifras de hoy y la pestaña [[vista:Interesados]] los ubica en el mapa de interés (3.4).

| Interesado | Quién es | Qué pregunta se hace | Qué decisión le ayuda a tomar | Dónde está la respuesta |
|---|---|---|---|---|
| Personas y familias | Quien compra los alimentos de su casa | ¿Qué alimentos están subiendo? | Qué comprar antes de ir a comprar | [[vista:Semanal]] |
| Restaurantes y almacenes | Quien compra alimentos para cocinar o para vender | ¿Cuándo y dónde conviene comprar? | Cuándo y en qué canal comprar | [[vista:Semanal]] |
| Mayoristas, agricultores y feriantes | Quien vende al por mayor o en la feria | ¿Cómo está el precio mayorista frente al de consumidor? | A qué precio vender | [[vista:Semanal]] |
| Periodistas y economistas | Quien informa sobre la economía o la analiza | ¿Qué alimentos suben más que la inflación, según datos oficiales? | Qué informar, con cifras que se pueden comprobar | [[vista:Precios e inflación]] · [[vista:Insights]] |
| Equipos técnicos y reclutadores | Quien diseña sistemas de datos o evalúa a quien los construye | ¿Cómo se construye y se opera un pipeline de datos confiable? | Qué prácticas seguir o a quién contratar | [[vista:Pipeline y linaje]] · [[vista:Plan de calidad]] · [[vista:Cambios e incidentes]] |

### 3.2 Perfiles de uso

El panel tiene tres perfiles, los mismos de la ventana «Elige tu vista». Los interesados de 3.1 entran por uno de ellos.

| Perfil | Para qué lo usa |
|---|---|
| Usuario | El negocio, sin cuenta: la sección «Negocio · BA y BI», con sus dos dashboards: Semanal, guiado en cuatro pasos, y Análisis, con sus pestañas Mensual, Histórico, Precios e inflación, Insights, Interesados y Método |
| Profesional | Todo el proyecto, sin cuenta, ordenado según su rol (Data Eng, BA, BI, DevOps o Seguridad), con las Consultas SQL de solo lectura |
| Autor | Lo mismo que Profesional, más «Centro de operación», «GitHub Actions» y «Configuración», la alerta «Acción requerida», la carga manual y los enlaces al repositorio en GitHub (D-500); pide la clave de control, que nunca está en el repositorio |

La ventana «Elige tu vista» pregunta una vez por pestaña, y la vista se conserva aunque la pestaña se recargue o el servidor olvide la sesión (D-430, D-454). «Vista: … · Cambiar», debajo del logo, cambia de vista; un clic en el logo hace lo mismo (D-373). Salir de Autor cierra su sesión, y la vista Autor se cierra sola tras 30 minutos sin actividad (D-395). El autor mantiene el código y los secretos y responde consultas SQL puntuales.

### 3.3 Qué escuchamos

Usuarios reales hicieron dos revisiones: una de uso y una de arquitectura. Cada cambio que salió de ellas tiene su decisión.

| Revisión | Qué escuchamos | Qué cambió | Decisión |
|---|---|---|---|
| Revisión de uso | No sabían por dónde empezar a leer el dashboard Semanal | El dashboard Semanal se lee en tres pasos numerados; los pasos 2 y 3 esperan al anterior, con candado, en todas las vistas; la búsqueda se nota | D-352, D-372 |
| Revisión de arquitectura | Por un usuario real, sin cambios solicitados | — | — |

### 3.4 Mapa de interés

Cada interesado está en un anillo según **cuánto depende su decisión de estos datos y con qué frecuencia los usa**. El centro es GreenOcean; ODEPA y el INE, que entregan los datos, quedan en el anillo de afuera. Es el mapa de la pestaña [[vista:Interesados]] de «Análisis» (D-444, D-456):

[[diagrama:interes]]

| Interesado | Interés | Por qué | Dónde abre |
|---|---|---|---|
| Restaurantes y almacenes | Alto | Compran cada semana y el canal y la semana en que compran cambian su costo | [[vista:Semanal]] |
| Mayoristas, agricultores y feriantes | Alto | Fijan cada semana su precio de venta frente al mayorista y al consumidor | [[vista:Semanal]] |
| Periodistas y economistas | Alto | Cada nota sobre precios necesita una cifra oficial que se pueda comprobar | [[vista:Precios e inflación]] |
| Personas y familias | Medio | Les ayuda antes de comprar, pero su compra no depende solo de estos datos | [[vista:Semanal]] |
| Equipos técnicos y reclutadores | Medio | Lo revisan de vez en cuando, por cómo se construye, no por las cifras de la semana | [[vista:Pipeline y linaje]] |
| ODEPA | Bajo | Publica los precios: entrega los datos, no decide con ellos | [[vista:Semanal]] |
| INE | Bajo | Publica el IPC de alimentos: entrega los datos, no decide con ellos | [[vista:Precios e inflación]] |

## 4. Preguntas de negocio

Cada pregunta tiene la pantalla que la responde y una prueba que recalcula la respuesta por otro camino.

| ID | Pregunta | Pantalla que la responde | Evidencia |
|---|---|---|---|
| P-1 | ¿Qué precios cambiaron esta semana y cuáles son inusuales? | Semanal | `tests/test_reconciliation.py::test_k6_sql_and_python_raise_the_same_alerts`, `tests/test_data_audit.py::test_an_alert_must_be_unusual_and_material` |
| P-2 | ¿El precio de hoy es normal para la temporada? | Consultas SQL · Precio vs. época | `tests/test_sql_explorer.py::test_p2_the_price_for_the_season_query_matches_a_recomputation_in_pandas` |
| P-3 | ¿Cuánto paga el consumidor sobre el mayorista? | Consultas SQL · Brecha mayorista | `tests/test_sql_explorer.py::test_p3_the_wholesale_gap_query_matches_a_recomputation_in_pandas` |
| P-4 | ¿Qué alimentos subieron más que la inflación? | Análisis (Precios e inflación) | `tests/test_inflation_view.py::test_p4_each_family_change_and_the_ipc_match_a_recomputation_in_sql`, `tests/test_page_bar.py::test_d267_the_reading_of_a_family_is_recomputed_from_its_index` |
| P-5 | ¿Las cifras son confiables? | Controles de datos | `tests/test_data_audit.py::test_weekly_prices_rebuild_exactly_from_the_raw_rows`, `tests/test_migration_parity.py::test_every_weekly_price_has_the_same_key_flag_count_and_price` |

## 5. Requisitos

Los requisitos funcionales (RF) dicen qué hace el producto. Los no funcionales (RNF) dicen cómo debe hacerlo. Cada uno tiene un criterio medible y la prueba que lo comprueba.

[[diagrama:requisitos]]

| ID | Requisito | Criterio medible | Evidencia |
|---|---|---|---|
| RF-01 | Carga semanal automática | Un workflow corre cada martes a las 12:07 UTC, con otro intento cada 15 minutos hasta las 14:52 y cada hora hasta las 02:07 si GitHub se atrasa | `.github/workflows/semanal.yml`, `tests/test_prd_traceability.py::test_rf01_the_weekly_workflow_runs_on_tuesdays` |
| RF-02 | Ninguna fila se pierde | Filas leídas = cargadas + rechazadas: diferencia 0 en cada carga | `dbt/tests/rnf05_rows_reconcile.sql`, `tests/test_etl_run.py::test_rn11_rows_read_equal_rows_loaded_plus_rows_rejected` |
| RF-03 | Solo se publica una carga válida | Si falla una de las 31 pruebas de dbt, la carga lee menos del 90 % de la anterior, falla pytest sobre la base nueva, falta una semana en medio de los datos o una fuente lleva más de 2 semanas sin publicar, la Base DuckDB no cambia; GitHub Actions marca la ejecución como fallida y avisa al autor por correo. Se publica hasta la última semana completa en ambas fuentes, sin rellenar; las pruebas de velocidad informan y nunca bloquean | `tests/test_pipeline_gate.py::test_rf03_a_failed_dbt_build_records_the_failure_and_never_replaces_the_served_database`, `tests/test_pipeline_gate.py::test_rf03_a_load_with_far_fewer_rows_than_the_last_good_one_is_refused`, `tests/test_late_sources.py::test_d356_a_hole_in_the_middle_of_the_data_stops_the_load`, `tests/test_late_sources.py::test_d356_a_recent_week_one_source_has_not_published_does_not_stop_the_load_and_waits`, `.github/workflows/semanal.yml` |
| RF-04 | Precios reales junto a los nominales | El factor de cada semana sale del IPC del mes de su lunes; las semanas posteriores al último mes publicado se marcan como provisionales | `tests/test_ipc_audit.py::test_weekly_factor_uses_the_month_of_the_monday_and_the_last_published_month`, `tests/test_ipc_audit.py::test_only_weeks_after_the_last_published_month_are_provisional` |
| RF-05 | Alertas de precio | Una alerta exige un cambio fuera del promedio ± 2 desviaciones de sus 12 semanas previas, de al menos 10 % y con dos cotizaciones en cada semana; SQL y Python levantan las mismas. Las subidas son alzas fuertes, en rojo, y las bajadas, bajas fuertes, en verde (D-477). En «Semanal», entre el paso 2 y el paso 3, «▲ n alzas fuertes» y «▼ n bajas fuertes» de la familia elegida muestran solo esos productos en el paso 3, sin abrir ventanas; la búsqueda, al lado, busca dentro de la alerta elegida (D-489, D-491, D-492). Con una región elegida, la misma regla se aplica al precio de esa región; con todo Chile, al precio nacional (D-499) | `tests/test_data_audit.py::test_an_alert_must_be_unusual_and_material`, `tests/test_reconciliation.py::test_k6_sql_and_python_raise_the_same_alerts` |
| RF-06 | Consultas SQL abiertas y de solo lectura | Toda orden que escribe se rechaza; cada consulta devuelve como máximo 5.000 filas y se detiene a los 10 s; el motor no lee archivos ni la red | `tests/test_sql_explorer.py::test_forbidden_statements_are_rejected`, `tests/test_sql_explorer.py::test_result_is_limited_and_flagged`, `tests/test_sql_explorer.py::test_slow_query_is_interrupted`, `tests/test_sql_explorer.py::test_external_access_is_disabled_at_the_engine` |
| RF-07 | Carga manual protegida | Ninguna carga manual sin la clave de control: el botón «Ejecutar pipeline ahora» aparece solo después de ella, la clave se compara en tiempo constante y, tras 3 fallos, cada intento espera 2 s, el doble tras cada nuevo fallo, hasta 15 min. La carga se sigue en una ventana que no se cierra sola, se minimiza o se cancela, muestra el log y deja de consultar a los 20 minutos | `tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code`, `tests/test_control.py::test_d393_after_three_failures_every_door_waits_twice_as_long_up_to_fifteen_minutes`, `tests/test_dashboard.py::test_d351_the_window_cannot_be_dismissed_minimizing_does_not_cancel_and_cancel_asks_first` |
| RF-08 | Informe semanal | Cada carga publicada deja un informe con su estado y las alertas de la semana, como issue del repositorio; el anterior se cierra, así queda abierto solo el último (D-438) | `.github/workflows/semanal.yml`, `tests/test_report.py::test_report_shows_the_load_status_and_the_alert_of_the_week` |
| RF-09 | La vista se elige y la parte del autor se protege | Cada visita nueva (una pestaña nueva) pide la vista, y después solo «Vista: … · Cambiar» o el logo vuelven a abrir la ventana; ninguna dirección abre la parte del autor; toda recarga de la pestaña (abrir o imprimir un documento, cambiar el tema, un enlace, F5) conserva la vista; la del Autor, solo con un ticket que emite y comprueba el servidor y que vence con su sesión | `tests/test_actions_page.py::test_d339_a_fresh_visit_or_a_reload_never_reaches_the_author_part_whatever_the_address_says`, `tests/test_view_switch.py::test_d353_leaving_the_author_view_closes_the_author_session_and_coming_back_asks_for_the_key`, `tests/test_app_reloads.py::test_d357_a_tab_with_nothing_kept_asks_for_the_view`, `tests/test_app_reloads.py::test_d427_the_author_comes_back_after_a_reload_the_app_makes_only_with_a_ticket_the_server_issued` |
| RNF-01 | Costo cero y sin vencimientos | Ningún servicio de pago; solo planes gratuitos permanentes ([ADR-31 · No usar un data warehouse en la nube](../arquitectura/ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube)) | `docs/arquitectura/ADR.md` |
| RNF-02 | Cada cifra se puede comprobar | Los precios semanales se reconstruyen desde las filas crudas y por un segundo camino independiente, sin dbt: diferencia 0 | `tests/test_data_audit.py::test_weekly_prices_rebuild_exactly_from_the_raw_rows`, `tests/test_migration_parity.py::test_every_weekly_price_has_the_same_key_flag_count_and_price`, `tests/test_data_audit.py::test_the_panel_reproduces_the_reference_figures_of_its_week` |
| RNF-03 | Seguridad | Ningún secreto en el repositorio; el workflow semanal tiene solo los permisos que usa; el panel no puede escribir la base | `tests/test_security.py::test_no_secret_is_tracked_by_git`, `tests/test_security.py::test_the_weekly_job_has_least_privilege`, `tests/test_sql_explorer.py::test_read_only_statements_are_accepted` |
| RNF-04 | Calidad vigilada en cada cambio | pytest y la compilación de dbt corren en cada push. Los 11 indicadores de calidad de los datos se miden en cada carga, y uno fuera de su umbral cambia el veredicto. Los 14 indicadores del plan de calidad se miden cada semana ([Plan de calidad](../calidad/PLAN_DE_CALIDAD.md)) | `.github/workflows/pruebas.yml`, `tests/test_quality_audit.py::test_a_degraded_measure_turns_its_indicator_and_the_verdict_red` |
| RNF-05 | Legible en computador, tableta y teléfono | Ninguna página se desplaza a lo ancho entre 1024 × 768 y 1920 × 1080, en tableta vertical (768 × 1024) ni en teléfono horizontal (844 × 390); en vertical, el panel pide girar el teléfono. En 1024 × 768 se acepta el desplazamiento vertical, sin cortes | `tests/medicion/medir.cjs` |
| RNF-06 | Cada página principal en una pantalla | En la ventana del navegador de una pantalla de 1440 × 900 (1440 × 790 útiles), a 1280 × 800 y a 1920 × 1000, cada página principal se ve entera, sin desplazar | `tests/medicion/medir.cjs` |

## 6. Alcance

| Incluye | Por qué | Excluye | Por qué |
|---|---|---|---|
| Integración de los precios de ODEPA desde 2022 y del IPC de alimentos del INE | Son las fuentes oficiales y abiertas (ADR-01); desde 2022 hay varios años para ver la estacionalidad, y más atrás crece el riesgo de cambios de formato (D-009) | Comparación entre cadenas de supermercados o tiendas | No existe una fuente oficial de precios por cadena; la única sería leer los sitios de los supermercados, descartado en ADR-01 |
| Conversión de unidades, agregación semanal y cálculo de precios reales | Sin llevar cada precio al kilo y a la semana no hay comparación (RN-03, RN-07); el IPC del INE descuenta la inflación (ADR-33) | Predicción de precios o explicación de sus causas | Con datos semanales públicos y sin una pregunta de predicción, un modelo no aporta (D-019); los indicadores describen lo ocurrido y no atribuyen causas (sección 8) |
| Rechazo de filas inválidas con su motivo y auditoría de cada cifra | Un precio cero o una fecha imposible no se usan, pero nunca se borran en silencio (RN-11); cada cifra se reconstruye desde las filas crudas (RNF-02) | Recomendaciones de compra para el consumidor | El panel describe lo que pasó con los precios; recomendar qué comprar exige un juicio sobre cada persona que los datos públicos no dan |
| Panel de solo lectura con su documentación | Un panel público, sin cuenta ni costo (ADR-02); los documentos dejan cada decisión y cada cifra a la vista (RNF-02) | Modificación de datos por parte de los usuarios | Los datos vienen solo de las fuentes oficiales y la base se abre en solo lectura: nadie puede cambiar una cifra (RF-06, RNF-03) |
| Publicación hasta la última semana completa en ambas fuentes | El dashboard Semanal compara mayorista y consumidor en la misma semana; una semana a medias daría cifras incompletas (D-356) | Rellenar una semana que una fuente aún no publica | Una cifra inventada no se puede recalcular desde la fuente; se espera a que la fuente publique (D-356) |

Con la carga del 31-10-2026, la base tiene 821.072 precios semanales en 252 semanas (de la 3–9 ene 2022 a la 26 oct–1 nov 2026), 9 regiones, 8 canales, 1.613 claves de producto y 202 meses del IPC. Esa carga leyó 2.541.374 filas: 2.541.173 cargadas y 201 rechazadas con su motivo. La base crece cada martes; las cifras del día están en el panel.

## 7. Pantallas

Estas son seis capturas reales, del 02-11-2026, de cinco páginas principales y en los cuatro temas de color. El dashboard Semanal aparece dos veces: como lo ve el Usuario y como lo ve el Profesional. El tema oscuro es el de entrada.

- **Menú:** cinco secciones: Negocio · BA y BI, Ingeniería de datos, DevOps y seguridad, Stack y evidencia, y Calidad. La primera reúne, bajo el título «Dashboards», dos recuadros con ícono de dashboard, que siguen a la vista aunque la sección se pliegue: Semanal y Análisis (D-442, D-453, D-456, D-459, D-494). La app abre con el menú abierto; al ir a un dashboard o a una página de diagramas, el menú se pliega para darles el ancho, y el botón que lo abre palpita en verde (D-462, D-463).
- **Semanal:** se lee en cuatro pasos numerados. Primero se elige una región o todo Chile; después, si se quiere, un canal; luego una familia, y al final se miran sus productos. Cada paso se abre al completar el anterior; el canal es opcional y sin elegirlo se ven todos (D-494). Los pasos quedan siempre juntos en una sola pantalla; la tabla de productos llena el panel 4, se desplaza sola y se amplía con su propio botón (D-446, D-447). Con «Toda la canasta», la tabla dice la familia de cada producto (D-478), y la «i» de cada paso dice cómo se calcula cada cifra: frente a qué semana, con qué mediana, con qué umbral y en qué alcance (D-480).
- **Canal (paso 2 de Semanal):** cada canal con su ícono 3D en sus propios colores (D-453) y la mediana de su variación. Al elegir uno, Semanal muestra solo sus precios y su última semana publicada, aunque la otra fuente todavía no publique esa semana, y dice qué familias publica ese canal (D-404 a D-406, D-494).
- **Análisis:** seis pestañas (D-456, D-457). «Mensual» es un período, los últimos 12 meses o un año, mes a mes: cinco cifras clave (cambio de precios, frente al IPC, brecha consumidor–mayorista, alertas de precio y mayor alza mensual), tres gráficos (precio mes a mes, cambio de cada mes y alertas de precio por mes) y la tabla por familia. «Histórico» es toda la historia, de enero 2022 al último mes que publicó el INE: cinco cifras clave (cambio desde enero 2022, frente al IPC, año de mayor alza, mes más barato y alertas de precio), tres gráficos (precio desde enero 2022, cambio de cada año y temporada) y la tabla por familia. Cada gráfico dice qué meses muestra, y su lupa verde lo abre en grande, con qué mide y qué se deduce; cada cifra explica al pasar el cursor cómo se calcula. Las otras cuatro son Precios e inflación, Insights, Interesados y Método. Sobre las pestañas, un recuadro verde dice qué se está viendo, de qué mes a qué mes y por qué empieza y termina ahí; cambia con la pestaña y el período (D-458). «Mensual» e «Histórico» parten por familia, con «Toda la canasta» por defecto; el selector «Producto» baja a uno de sus productos, calculado con la regla de la familia, y la tabla muestra la familia con sus productos debajo (D-478).
- **Stack y evidencia:** dos vistas. «Herramientas» explica cada herramienta; «Flujo del sistema en vivo» muestra las piezas reales, lo que se dicen y la carga en curso (D-412).

[[diagrama:mockups]]

## 8. Supuestos, restricciones y dependencias

**Supuestos**
- El precio nacional es un promedio simple de las regiones. No se pondera por población ni por ventas, porque ninguna fuente abierta publica esos pesos. Cada variación semanal compara solo las regiones con precio en ambas semanas.
- Los indicadores describen lo que pasó. No predicen ni atribuyen causas. Que una familia suba al ritmo del IPC no prueba que la inflación la haya movido, porque el IPC de alimentos se calcula con esos mismos precios.

**Restricciones**
- Costo cero: solo planes gratuitos permanentes de GitHub y Streamlit Community Cloud.
- Ninguna cifra se inventa ni se interpola, y el histórico nunca se borra.
- El último mes del IPC puede no estar publicado: esas semanas usan el último mes disponible y se marcan como provisionales.

**Dependencias**

| Dependencia | Para qué | Si falla |
|---|---|---|
| ODEPA (datos.odepa.gob.cl) | Precios mayoristas y al consumidor | La carga no pasa sus controles y el panel conserva la última carga válida |
| INE | IPC de alimentos | Se conserva el último IPC leído; las semanas nuevas quedan provisionales |
| GitHub (repositorio, Actions, releases) | Código, ejecución de la carga y Base DuckDB | No hay carga nueva; el panel conserva la base que ya tiene |
| Streamlit Community Cloud | Publicación del panel | El panel no está disponible; los datos no se pierden |

## 9. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| ODEPA cambia el formato de sus archivos | Media | Alto | Las puertas de calidad rechazan una carga mal leída ([SAD, la carga de cada semana](../arquitectura/SAD.md#4-la-carga-de-cada-semana)) |
| Se interpreta una correlación como causa | Media | Medio | El panel y este documento lo advierten junto a cada comparación con el IPC |
| Cambian las condiciones de un plan gratuito | Baja | Alto | El pipeline corre igual en cualquier máquina con Python 3.11 o 3.12 |
| Un solo responsable de mantenimiento | Alta | Medio | Operación documentada en el [Manual de operación](../operacion/MANUAL.md) y pruebas automáticas en cada cambio |
| GitHub desactiva los workflows programados de un repositorio público tras 60 días sin actividad; su documentación no define qué cuenta como actividad ni si sirve el commit semanal del bot | Baja | Alto | Propuesta (D-439), sin implementar: no depender de esa regla. «Configuración» leería el estado de `semanal.yml` en la API de GitHub (`active` o `disabled_inactivity`), la alerta «Acción requerida» lo avisaría al Autor y un botón lo reactivaría con `GITHUB_TOKEN`; GitHub, además, avisa por correo antes de desactivarlo |
| Streamlit Community Cloud duerme la app cuando no tiene visitas, sin importar los commits; el visitante ve la pantalla de la app dormida y debe despertarla | Alta | Medio | Propuesta (D-439), sin implementar: el `README.md` y el enlace del portafolio avisan que la app puede tardar en despertar y muestran las capturas reales de `docs/img/`, para que el proyecto se vea aunque duerma. No verificado: el plazo exacto de hibernación y si una visita automática la mantiene despierta |

## 10. Criterios de aceptación

| Criterio | Cómo se verifica |
|---|---|
| Cada pregunta de negocio tiene pantalla y evidencia existentes | `tests/test_prd_traceability.py` |
| Cada requisito tiene criterio medible y evidencia existente | `tests/test_prd_traceability.py` |
| La suite completa pasa en cada push | `.github/workflows/pruebas.yml` |
| Las cifras de este documento coinciden con la Base DuckDB | `tests/test_documents.py::test_d210_the_prd_figures_match_the_served_database` |
| Cada página principal cabe en una pantalla | `tests/medicion/medir.cjs` a 1440 × 790 y 1920 × 1000 |

## 11. Próximos pasos

La incorporación del clima por región y las condiciones bajo las que se justificaría un data warehouse en la nube se describen en el [SAD, capacidad y crecimiento](../arquitectura/SAD.md#9-capacidad-y-crecimiento).

Mejora futura del flujo en vivo (D-415): que cada pieza de [[vista:Stack y evidencia]] abra su mini arquitectura, con su nivel de zoom C4. Se mostraría qué es, qué hace aquí, por qué esa herramienta, qué entra y qué sale; GitHub, la carga semanal, dbt, la app y la seguridad mostrarían su recorrido interno, por ejemplo GitHub Actions: disparador → job → pasos → resultado.

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
| 3.1 | 30-10-2026 | Visión y misión; las tres vistas y el indicador «Vista» (RF-09); fuentes retrasadas y pruebas informativas en RF-03; ventana de la carga manual en RF-07; sección Calidad, tema oscuro y Panorama en tres pasos (D-340 a D-357) |
| 3.2 | 30-10-2026 | La página «Último dato por canal» (D-365) |
| 3.3 | 31-10-2026 | Interesados (3.1) y perfiles de uso (3.2), con su página en el panel (D-376) |
| 3.4 | 31-10-2026 | Qué escuchamos (3.3), el porqué del alcance (6), el ciclo semanal (2) y la página «Análisis de negocio y sistemas» (D-377) |
| 3.5 | 31-10-2026 | El orden de lectura de la sección «Negocio · BA y BI» en el menú (7, D-378) |
| 3.6 | 31-10-2026 | Redacción revisada; cifras de la carga del 31-10-2026 (6); las tres vistas, cada una con lo que ve (3.2); la alerta de precio completa (RF-05); los indicadores de calidad de los datos y los del plan de calidad (RNF-04); capturas nuevas (7, D-392); el documento pasa a `docs/negocio/` (D-381, D-385, D-388) |
| 3.7 | 01-11-2026 | Una pantalla también a 1280 × 800 (RNF-06); a 1024 × 768 se acepta el desplazamiento vertical, sin cortes (RNF-05, D-407) |
| 3.8 | 01-11-2026 | Las mini arquitecturas del flujo en vivo, como mejora futura (11, D-415) |
| 3.9 | 01-11-2026 | La vista Autor con «Configuración» (3.2); el Panorama que pliega sus pasos, las tarjetas por canal y el flujo en vivo de «Stack y evidencia» (7, D-404 a D-417) |
| 3.10 | 01-11-2026 | RF-09: las recargas que hace la app conservan también la vista del Autor, con un ticket de un solo uso (D-427) |
| 3.11 | 01-11-2026 | RF-09: la vista se conserva también en Streamlit Community Cloud, que carga la página dos veces; el ticket del Autor vence con su sesión (D-428) |
| 3.12 | 01-11-2026 | RF-09: la vista se elige una vez por pestaña; toda recarga la conserva, también F5 y el enlace del aviso «Acción requerida» (D-430) |
| 3.13 | 01-11-2026 | RF-08: al abrir el informe semanal se cierra el anterior (D-438) |
| 3.14 | 01-11-2026 | Dos riesgos de abandono, con su mitigación propuesta: workflows desactivados por inactividad y la app dormida (9, D-439) |
| 3.15 | 02-11-2026 | «Panorama de precios» pasa a llamarse «Dashboard» y encabeza el menú (D-442) |
| 3.16 | 02-11-2026 | Mapa de interés: cada interesado en un anillo (alto, medio, bajo) con su justificación (3.4, D-444) |
| 3.17 | 02-11-2026 | Capturas nuevas de las seis pantallas, con el Dashboard y el menú actuales (7, D-445) |
| 3.18 | 02-11-2026 | El Dashboard ya no pliega los pasos 1 y 2: el panorama queda completo, y la captura M-1 lo muestra así (7, D-446) |
| 3.19 | 02-11-2026 | «Último dato por canal» es un segundo recuadro bajo el Dashboard, y cada canal se comporta igual que el Dashboard, sin plegar sus pasos (7, D-447, D-452) |
| 3.20 | 02-11-2026 | Los dos dashboards abren la sección «Negocio · BA y BI», y cada tarjeta de canal lleva su ícono 3D (7, D-453) |
| 3.21 | 02-11-2026 | Los diagramas son los de la app: el ciclo de cada semana del bloque «Proceso» de «Análisis de negocio y sistemas» (2) y el mapa de «Interesados» (3.4); se retiran «Del dato a la decisión» y los casos de uso, que nombraban perfiles que el panel no tiene; 3.2 son los tres perfiles del panel; «base servida» pasa a «Base DuckDB» (D-455) |
| 3.22 | 02-11-2026 | «Análisis» reúne en pestañas la historia de los precios, Precios e inflación, Insights, Interesados y el método; P-4 se ve en su pestaña (3.1, 3.2, 3.4, 4, 7, D-456) |
| 3.23 | 02-11-2026 | «Análisis» separa la historia de los precios en «Mensual», un período mes a mes, e «Histórico», de enero 2022 al último mes por año y temporada; cada gráfico dice sus meses y, al pasar el cursor, qué mide y qué se deduce (3.2, 7, D-457) |
| 3.24 | 02-11-2026 | Un recuadro verde sobre las pestañas de «Análisis» dice qué se ve, de qué mes a qué mes y por qué, según la pestaña y el período (7, D-458) |
| 3.25 | 02-11-2026 | Los tres dashboards de «Negocio · BA y BI» van bajo el título «Dashboards», y el primero, el de la semana, se llama «Semanal» (3.1 a 3.4, 4, 6, 7, D-459) |
| 3.26 | 02-11-2026 | En «Análisis» las tarjetas son más finas, los meses se leen en dos líneas cortas y una lupa verde abre cada gráfico en grande (7, D-460) |
| 3.27 | 02-11-2026 | Los tres dashboards abren con el menú plegado y el botón que lo abre palpita en verde (7, D-462) |
| 3.28 | 02-11-2026 | La app abre con el menú abierto; se pliega al ir a un dashboard o a una página de diagramas (7, D-463) |
| 3.29 | 03-11-2026 | El plan de calidad pasa a 14 indicadores: regiones o canales ausentes y precios atípicos de la semana (RNF-04, D-475) |
| 3.30 | 03-11-2026 | Las alertas de precio se separan en alzas fuertes y bajas fuertes (RF-05, D-477) |
| 3.31 | 03-11-2026 | Las vistas parten por familia y bajan a los productos; cada cifra dice cómo se calcula (D-478, D-480) |
| 3.32 | 03-11-2026 | La carga semanal tiene tres intentos el martes (RF-01, D-485) |
| 3.33 | 03-11-2026 | La carga semanal intenta cada 15 minutos hasta mediodía y cada hora hasta la noche del martes (RF-01, D-487) |
| 3.34 | 03-11-2026 | Las alertas de cada familia se ven en el paso 2 y se listan en el paso 3, sin ventanas (RF-05, D-489) |
| 3.35 | 03-11-2026 | «Semanal» muestra solo la semana: sale la tabla de las últimas semanas (D-490) |
| 3.36 | 03-11-2026 | Las alertas de la familia elegida, entre el paso 2 y el paso 3; el orden ya no tiene «Inusuales» (RF-05, D-491) |
| 3.37 | 03-11-2026 | El paso 3 se llama «Productos»; la búsqueda queda junto a las alertas y busca dentro de la que esté elegida (RF-05, D-492) |
| 3.38 | 03-11-2026 | Semanal tiene cuatro pasos: el canal pasa a ser el paso 2, opcional, y la sección queda con dos dashboards (D-494) |
| 3.39 | 03-11-2026 | La tabla de productos solo ordena por «Mayor cambio» o «Nombre»; el canal es el paso 2 y las alertas, sus botones (D-495) |
| 3.40 | 03-11-2026 | Una tablet horizontal ve Semanal en columnas; «Orden» recupera «Subidas» y «Bajadas» (D-496) |
| 3.41 | 03-11-2026 | «Orden» se reemplaza por un filtro junto a la búsqueda: «Todo», «Subidas» y «Bajadas» (D-497) |
| 3.42 | 03-11-2026 | Con una región elegida en Semanal, los canales, las líneas de cada familia y las alertas son de esa región (RF-05, D-499) |
| 3.43 | 03-11-2026 | Solo el Autor ve los enlaces al repositorio en GitHub (D-500) |
| 3.44 | 04-11-2026 | La vista Usuario ve solo sus dos dashboards y las fuentes: ningún enlace ni dirección lleva a otra vista (D-502) |
| 3.45 | 04-11-2026 | El modelo estrella de «Modelo de datos» es apaisado y usa su panel: dos dimensiones a cada lado de weekly_price, el IPC a la izquierda y la auditoría a la derecha (D-503) |
| 3.46 | 04-11-2026 | El menú lateral ya no se desplaza hacia un vacío: el logo, el botón de plegar y el pie quedan siempre a la vista, y se desplaza solo si el contenido no cabe (RNF-06, D-504) |
| 3.47 | 04-11-2026 | Los estilos viajan en el primer elemento de cada página, así nada se ve sin estilo al cambiar de página (RNF-06, D-505) |
| 3.48 | 04-11-2026 | «Toda la canasta» explica su mediana tras una «i»: hacia dónde se movieron más precios y los tres conteos (RF-01, D-506) |
| 3.49 | 04-11-2026 | Las tres páginas de «Calidad» se llaman «Plan de calidad», «Controles de datos» y «Cambios e incidentes», en ese orden (D-507) |
| 3.50 | 04-11-2026 | El dashboard «Análisis BA y BI» se llama «Análisis» (D-508) |
| 3.51 | 04-11-2026 | «Descargar» en el paso 4 de Semanal: todos los precios filtrados en Excel (tabla con filtro, formatos y notas) o CSV, en el idioma de la visita (RF-01, D-509) |
| 3.52 | 04-11-2026 | Las cifras que se leen de la base al abrir una página llevan la marca «en vivo», un punto verde que late (RNF-06, D-510) |
| 3.53 | 04-11-2026 | En Consultas SQL, los filtros son píldoras finas en la línea de la pestaña y el editor muestra hasta 12 líneas (RF-06, D-511) |
| 3.54 | 04-11-2026 | «Relaciones» en Consultas SQL: el diagrama entidad-relación de las vistas y cada JOIN listo para copiar (RF-06, D-515) |
