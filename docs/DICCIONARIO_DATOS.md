# Diccionario de datos

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Diccionario de datos |
| Versión | 1.0 |
| Fecha | 25-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Describir cada tabla y cada columna de la base servida: su tipo, sus claves y su significado. |
| Audiencia | Análisis de datos, ingeniería de datos y revisión técnica. |
| Documentos relacionados | [Documento de arquitectura de software (SAD)](SAD.md) · [Registros de decisiones de arquitectura (ADR)](ADR.md) · [Glosario](GLOSARIO.md) |

## Índice

1. [Alcance](#1-alcance)
2. [Tablas](#2-tablas)
3. [Hechos y dimensiones](#3-hechos-y-dimensiones)
4. [IPC](#4-ipc)
5. [Auditoría y linaje](#5-auditoría-y-linaje)
6. [Glosario](#6-glosario)
7. [Historial de versiones](#7-historial-de-versiones)

## 1. Alcance

Describe la base servida, `etl/datos.duckdb`, la que lee el panel. Las fechas se guardan como texto ISO (`AAAA-MM-DD`). El modelo y sus relaciones se ven en la página «Modelo de datos» del panel.

## 2. Tablas

| Tabla | Función | Contenido |
|---|---|---|
| `weekly_price` | Hechos | Un precio por semana, producto, región, canal y unidad |
| `dim_product` | Dimensión | Producto, variedad, calidad y familia |
| `dim_region` | Dimensión | Regiones con precios |
| `dim_channel` | Dimensión | Canales de venta y su fuente |
| `dim_date` | Dimensión | Una fila por semana, sin huecos |
| `ipc_monthly` | IPC | IPC de alimentos mensual como una sola serie |
| `ipc_weekly` | IPC | Deflactor de cada semana |
| `ine_ipc_source` | IPC | Filas del IPC tal como se leyeron del INE |
| `etl_run` | Auditoría | Una fila por carga publicada |
| `rejection` | Auditoría | Filas rechazadas por la última carga, con su motivo |
| `dbt_node` | Linaje | Modelos, fuentes y pruebas del último `dbt build` |
| `dbt_result` | Linaje | Resultado de cada modelo y prueba del último `dbt build` |

## 3. Hechos y dimensiones

### weekly_price

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `week_start` | VARCHAR | FK → `dim_date` | Lunes de la semana |
| `product_id` | BIGINT | FK → `dim_product` | Producto, variedad y calidad |
| `region_id` | INTEGER | FK → `dim_region` | Región |
| `channel_id` | BIGINT | FK → `dim_channel` | Canal de venta |
| `normalized_unit` | VARCHAR | | Unidad normalizada: `kilo`, `litro` o `unidad`; vacía si no se puede convertir |
| `price` | DOUBLE | | Precio semanal en pesos nominales, por unidad normalizada |
| `volume` | DOUBLE | | Volumen informado por la fuente, cuando existe |
| `observation_count` | BIGINT | | Número de cotizaciones que forman el precio de la semana |
| `flag` | VARCHAR | | Vacía si el precio entra en los indicadores; `ATIPICO` o `UNIDAD_NO_CONVERTIBLE` si queda fuera de ellos |

### dim_product

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `product_id` | BIGINT | PK | Identificador del producto |
| `product_group` | VARCHAR | | Familia de alimentos |
| `product` | VARCHAR | | Producto |
| `variety` | VARCHAR | | Variedad |
| `quality` | VARCHAR | | Calidad |

### dim_region

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `region_id` | INTEGER | PK | Identificador de la región |
| `region` | VARCHAR | | Nombre de la región |

### dim_channel

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `channel_id` | BIGINT | PK | Identificador del canal |
| `channel` | VARCHAR | | Canal de venta, por ejemplo «Supermercado» o «Feria libre» |
| `source` | VARCHAR | | Fuente de ODEPA: `wholesale` (mayorista) o `consumer` (consumidor) |

### dim_date

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `week_start` | VARCHAR | PK | Lunes de la semana |
| `iso_year` | BIGINT | | Año ISO de la semana |
| `iso_week` | BIGINT | | Número de semana ISO |
| `month` | BIGINT | | Mes del lunes |
| `month_name` | VARCHAR | | Nombre del mes |
| `year` | BIGINT | | Año del lunes |
| `season` | VARCHAR | | Estación en Chile: `verano`, `otoño`, `invierno` o `primavera` |

## 4. IPC

### ipc_monthly

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `year` | INTEGER | PK (con `month`) | Año |
| `month` | INTEGER | PK (con `year`) | Mes |
| `food_index` | DOUBLE | | IPC de alimentos, base 2023 = 100 |
| `origin` | VARCHAR | | Serie de origen: la base 2023 o la serie empalmada, enlazada en enero de 2024 |

### ipc_weekly

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `week_start` | VARCHAR | PK, FK → `dim_date` | Lunes de la semana |
| `ipc_year` | INTEGER | | Año del IPC usado para esa semana |
| `ipc_month` | INTEGER | | Mes del IPC usado para esa semana |
| `food_index` | DOUBLE | | IPC de alimentos de ese mes |
| `reference_year` | INTEGER | | Año del último mes publicado, al que se llevan los precios |
| `reference_month` | INTEGER | | Último mes publicado |
| `real_factor` | DOUBLE | | Factor que convierte un precio nominal de la semana en pesos del mes de referencia |
| `provisional` | BOOLEAN | | Verdadero si la semana es posterior al último mes publicado |

### ine_ipc_source

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `file` | VARCHAR | | Archivo del INE de origen |
| `year` | VARCHAR | | Año, como lo publica el INE |
| `month` | VARCHAR | | Mes, como lo publica el INE |
| `index_value` | VARCHAR | | Valor del índice, como lo publica el INE |
| `monthly_change` | VARCHAR | | Variación mensual, como la publica el INE |

## 5. Auditoría y linaje

### etl_run

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `run_id` | INTEGER | PK | Número de la carga |
| `started_at` | VARCHAR | | Inicio de la carga, en UTC |
| `status` | VARCHAR | | Estado: `LOADED` para una carga publicada |
| `rows_read` | INTEGER | | Filas leídas de ODEPA |
| `rows_loaded` | INTEGER | | Filas cargadas |
| `rows_rejected` | INTEGER | | Filas rechazadas; leídas = cargadas + rechazadas |
| `message` | VARCHAR | | Mensaje de la carga, si lo hay |

### rejection

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `run_id` | INTEGER | FK → `etl_run` | Carga que rechazó la fila |
| `source` | VARCHAR | | Fuente: `wholesale` o `consumer` |
| `reason` | VARCHAR | | Motivo del rechazo, por ejemplo `NON_POSITIVE_PRICE` (precio cero o negativo) |
| `original_row` | JSON | | La fila tal como llegó |

### dbt_node

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `unique_id` | VARCHAR | PK | Identificador del nodo en dbt |
| `name` | VARCHAR | | Nombre del modelo, la fuente o la prueba |
| `resource_type` | VARCHAR | | `model`, `source` o `test` |
| `layer` | VARCHAR | | Capa: `bronze`, `staging`, `intermediate` o `marts`; vacía para las pruebas |
| `materialized` | VARCHAR | | Cómo se materializa el modelo |
| `depends_on` | VARCHAR | | Nodos de los que depende |
| `test_type` | VARCHAR | | Tipo de prueba, para las pruebas |
| `column_name` | VARCHAR | | Columna que prueba, si aplica |
| `description` | VARCHAR | | Descripción del nodo en el proyecto dbt |

### dbt_result

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `unique_id` | VARCHAR | FK → `dbt_node` | Nodo ejecutado |
| `status` | VARCHAR | | Resultado: `success` para un modelo construido, `pass` para una prueba superada |
| `execution_time` | DOUBLE | | Duración en segundos |
| `failures` | INTEGER | | Filas que no cumplen la prueba |
| `generated_at` | VARCHAR | | Fecha del `dbt build` |

## 6. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](GLOSARIO.md).

## 7. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 25-10-2026 | Primera versión (D-279, documentación profesional) |
