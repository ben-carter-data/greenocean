# Guía del proyecto

Textos que muestra la página «El proyecto» del panel. El panel lee este archivo tal cual: para cambiar un texto de la página, se cambia aquí. Las reglas (RN), los indicadores (K) y las preguntas (P) se leen de `DISENO.md`; las cifras salen de la base en cada visita.

## Resumen

- **Problema:** quien sigue los precios de los alimentos en Chile tiene que bajar cada semana dos archivos de ODEPA, convertir unidades distintas y cruzarlos a mano.
- **Qué hace:** un pipeline semanal descarga los precios mayoristas y al consumidor, los limpia con reglas de negocio, revisa su calidad y los carga en un data warehouse.
- **Resultado:** un panel público con márgenes, diferencias por canal y región, estacionalidad, rezago y alertas, que se actualiza solo cada martes.

## Fuentes y cruces

Las dos fuentes son archivos abiertos de ODEPA (Ministerio de Agricultura), uno por año:

- **Precios mayoristas:** un precio por día hábil, mercado, producto, variedad y calidad, en la unidad en que se vende (por ejemplo `$/bandeja 18 kilos`), con el volumen vendido.
- **Precios al consumidor:** un precio por semana, región, tipo de comercio (feria, supermercado, carnicería…) y producto.

Para compararlas hay que resolver tres diferencias:

1. **Nombres:** el consumidor escribe `Tomate|Larga vida|Primera` en una sola columna; el mayorista usa tres columnas. Se separan para que ambos usen la misma clave: producto + variedad + calidad.
2. **Unidades:** el mayorista vende por caja, bandeja o malla; el consumidor compra por kilo. Si la unidad declara una cantidad, el precio se divide por ella para llegar a precio por kilo, por unidad o por litro. Si no la declara (un atado, una docena de atados), el precio se guarda sin comparar.
3. **Tiempo:** el mayorista es diario y el consumidor semanal. Los días se agrupan en su semana (lunes de inicio), con un promedio ponderado por volumen.

Solo hay margen cuando las dos fuentes coinciden en clave, región, semana y unidad. La cobertura del cruce (K7) dice cuántas claves de frutas y verduras del consumidor lo logran.

## Modelo de datos

El data warehouse (`datos.db`) es un modelo estrella: una tabla de hechos con los precios semanales al centro y tres dimensiones alrededor. Dos tablas aparte registran cada ejecución y sus rechazos.

- `weekly_price`: un precio por semana, producto, región, canal y unidad. Es la tabla de hechos que leen todos los indicadores.
- `dim_product`: cada clave de producto: grupo, producto, variedad y calidad.
- `dim_region`: las regiones con datos, con su número oficial.
- `dim_channel`: los canales; el mayorista es un canal más, así el margen compara dos canales de la misma tabla.
- `etl_run`: una línea por ejecución del ETL, con filas leídas, cargadas y rechazadas.
- `rejection`: las filas rechazadas de la última ejecución, tal como venían, con su motivo.

## KPI

| KPI | En palabras | Página | Consulta |
|---|---|---|---|
| K1 | Cuánto más paga el consumidor que el mayorista por lo mismo, en la misma semana y región. | Márgenes | k1_margin |
| K2 | Cuánto más caro o más barato es un canal que otro, para el mismo producto, semana y región. | Canales y regiones | k2_channel_gap |
| K3 | Cuánto más caro o más barato es una región que el promedio de las regiones esa semana. | Canales y regiones | k3_regional_index |
| K4 | Cuánto más caro o más barato es una semana que el promedio de su año. | Estacionalidad | k4_seasonal_index |
| K5 | Cuántas semanas tarda el precio al consumidor en moverse después del mayorista. | Márgenes | k5_weekly_variations_sql |
| K6 | Si el cambio de precio de esta semana es mucho mayor que los cambios habituales del producto. | Alertas | k6_usual_range_sql |
| K7 | Cuántas claves de frutas y verduras del consumidor tienen un precio mayorista con qué compararse. | Calidad de datos | k7_match_coverage |
| K8 | Qué parte de las filas leídas se rechazó, y por qué motivo. | Calidad de datos | k8_rejected_rows |

## Reglas de calidad

| Regla | Qué hace con la fila | Por qué | Ejemplo documentado |
|---|---|---|---|
| RN-01 | La convierte; si el texto no se puede leer, la rechaza con motivo `UNREADABLE_VALUE`. | ODEPA escribe los precios con coma decimal; sin convertirlos no se puede calcular. | El tomate Semiduro Extra del 20-04-2026 en Lo Valledor viene como `12000,0000` y se carga como 12.000. |
| RN-02 | La conserva y separa su producto en tres partes. | Así el consumidor y el mayorista usan la misma clave. | — |
| RN-03 | La conserva con su precio por kilo. | Comparar una caja de 18 kilos con un kilo exige llevar ambos al kilo. | `$/bandeja 18 kilos` a $12.000 son $666,67 por kilo. |
| RN-04 | La conserva con su precio por unidad. | Igual que RN-03, para lo que se vende por unidad. | — |
| RN-05 | La conserva sin precio comparable y la marca `UNIDAD_NO_CONVERTIBLE`. | Un atado no tiene peso declarado; inventarlo daría márgenes falsos (D-008). | — |
| RN-06 | No calcula margen si las unidades no coinciden. | Un precio por unidad no se compara con uno por kilo. | — |
| RN-07 | Junta los días de la semana en un precio, pesando más los días con más volumen. | Un día con poca venta no debe pesar lo mismo que uno con mucha. | Las 4 filas de esa semana dan (666,67 × 940 + 694,44 × 160) / 1.100 = 670,71 por kilo. |
| RN-08 | Asigna cada día a su lunes. | Es la semana del consumidor; sin ella no hay cruce. | — |
| RN-09 | Junta los precios del consumidor de la semana en un promedio por región y canal. | ODEPA publica varios puntos de venta por región. | — |
| RN-10 | Trata «Mercado Mayorista» del consumidor como un canal más. | Es un punto de venta al público, no la fuente mayorista. | — |
| RN-11 | La rechaza con su motivo y la guarda en `rejection`. | Un precio cero o una fecha imposible no se pueden usar, pero nunca se borran en silencio. | — |
| RN-12 | La conserva, la marca `ATIPICO` y la deja fuera de los indicadores. | Un precio 5 veces mayor o menor que el resto esa semana suele ser un error de digitación. | — |
| RN-13 | Le quita espacios repetidos o no separables. | Un espacio invisible distinto crea dos productos donde hay uno. | En el archivo 2026, «Pavo Pechuga s/hueso» trae un espacio no separable en 546 filas; en la base queda con un espacio normal. |
| RN-14 | Reconstruye la tabla completa en cada ejecución y revisa que no haya claves repetidas. | Ejecutar dos veces la misma semana no puede duplicar precios. | — |

## Consultas SQL

| Consulta | Qué responde | Página |
|---|---|---|
| k1_margin | ¿Cuánto más paga el consumidor que el mayorista, semana a semana? | Márgenes |
| k2_channel_gap | ¿Cuánto más caro es un canal que otro para el mismo producto? | Canales y regiones |
| k3_regional_index | ¿Qué regiones son más caras que el promedio nacional? | Canales y regiones |
| k4_seasonal_index | ¿Qué semanas del año son caras o baratas para cada producto? | Estacionalidad |
| k8_rejected_rows | ¿Cuántas filas se rechazaron en la última carga y por qué? | Calidad de datos |
| quality_runs | ¿Cómo terminaron las últimas ejecuciones del ETL? | Calidad de datos |
| quality_flag_counts | ¿Cuántos precios semanales se usan y cuántos quedaron marcados? | Calidad de datos |
| quality_outliers | ¿Qué precios se marcaron como atípicos? | Calidad de datos |
| k6_national_weekly_price | ¿Cuál es el precio nacional de cada producto y canal, semana a semana? | Alertas |
| k6_usual_range_sql | ¿Qué cambios semanales salen de su rango habitual? (versión SQL de K6) | Alertas |
| k5_weekly_variations_sql | ¿Cuánto cambió cada precio frente a la semana anterior, en las series largas? (versión SQL de K5) | Márgenes |
