# Data Dictionary

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Data Dictionary |
| Version | 1.0 |
| Date | 2026-10-25 |
| Status | Current |
| Owner | The author |
| Purpose | Describe each table and each column of the served database: its type, its keys and its meaning. |
| Audience | Data analysis, data engineering and technical review. |
| Related documents | [Software Architecture Document (SAD)](SAD.md) · [Architecture Decision Records (ADR)](ADR.md) · [Glossary](GLOSARIO.md) |

## Contents

1. [Scope](#1-scope)
2. [Tables](#2-tables)
3. [Facts and dimensions](#3-facts-and-dimensions)
4. [CPI](#4-cpi)
5. [Audit and lineage](#5-audit-and-lineage)
6. [Glossary](#6-glossary)
7. [Version history](#7-version-history)

## 1. Scope

It describes the served database, `etl/datos.duckdb`, the one the panel reads. Dates are stored as ISO text (`YYYY-MM-DD`). The model and its relationships are shown on the «Data model» page of the panel.

## 2. Tables

| Table | Role | Content |
|---|---|---|
| `weekly_price` | Facts | One price per week, product, region, channel and unit |
| `dim_product` | Dimension | Product, variety, quality and family |
| `dim_region` | Dimension | Regions with prices |
| `dim_channel` | Dimension | Sales channels and their source |
| `dim_date` | Dimension | One row per week, with no gaps |
| `ipc_monthly` | CPI | Monthly food CPI as a single series |
| `ipc_weekly` | CPI | Deflator of each week |
| `ine_ipc_source` | CPI | CPI rows as they were read from the INE |
| `etl_run` | Audit | One row per published load |
| `rejection` | Audit | Rows rejected by the last load, with their reason |
| `dbt_node` | Lineage | Models, sources and tests of the last `dbt build` |
| `dbt_result` | Lineage | Result of each model and test of the last `dbt build` |

## 3. Facts and dimensions

### weekly_price

| Column | Type | Key | Description |
|---|---|---|---|
| `week_start` | VARCHAR | FK → `dim_date` | Monday of the week |
| `product_id` | BIGINT | FK → `dim_product` | Product, variety and quality |
| `region_id` | INTEGER | FK → `dim_region` | Region |
| `channel_id` | BIGINT | FK → `dim_channel` | Sales channel |
| `normalized_unit` | VARCHAR | | Normalized unit: `kilo`, `litro` or `unidad`; empty if it cannot be converted |
| `price` | DOUBLE | | Weekly price in nominal pesos, per normalized unit |
| `volume` | DOUBLE | | Volume reported by the source, when it exists |
| `observation_count` | BIGINT | | Number of quotes that make up the price of the week |
| `flag` | VARCHAR | | Empty if the price enters the indicators; `ATIPICO` (outlier) or `UNIDAD_NO_CONVERTIBLE` (unit that cannot be converted) if it stays out of them |

### dim_product

| Column | Type | Key | Description |
|---|---|---|---|
| `product_id` | BIGINT | PK | Product identifier |
| `product_group` | VARCHAR | | Food family |
| `product` | VARCHAR | | Product |
| `variety` | VARCHAR | | Variety |
| `quality` | VARCHAR | | Quality |

### dim_region

| Column | Type | Key | Description |
|---|---|---|---|
| `region_id` | INTEGER | PK | Region identifier |
| `region` | VARCHAR | | Name of the region |

### dim_channel

| Column | Type | Key | Description |
|---|---|---|---|
| `channel_id` | BIGINT | PK | Channel identifier |
| `channel` | VARCHAR | | Sales channel, for example «Supermercado» or «Feria libre» |
| `source` | VARCHAR | | ODEPA source: `wholesale` or `consumer` |

### dim_date

| Column | Type | Key | Description |
|---|---|---|---|
| `week_start` | VARCHAR | PK | Monday of the week |
| `iso_year` | BIGINT | | ISO year of the week |
| `iso_week` | BIGINT | | ISO week number |
| `month` | BIGINT | | Month of the Monday |
| `month_name` | VARCHAR | | Name of the month, in Spanish |
| `year` | BIGINT | | Year of the Monday |
| `season` | VARCHAR | | Season in Chile: `verano`, `otoño`, `invierno` or `primavera` (summer, autumn, winter or spring) |

## 4. CPI

### ipc_monthly

| Column | Type | Key | Description |
|---|---|---|---|
| `year` | INTEGER | PK (with `month`) | Year |
| `month` | INTEGER | PK (with `year`) | Month |
| `food_index` | DOUBLE | | Food CPI, base 2023 = 100 |
| `origin` | VARCHAR | | Series of origin: the 2023 base or the spliced series, linked in January 2024 |

### ipc_weekly

| Column | Type | Key | Description |
|---|---|---|---|
| `week_start` | VARCHAR | PK, FK → `dim_date` | Monday of the week |
| `ipc_year` | INTEGER | | Year of the CPI used for that week |
| `ipc_month` | INTEGER | | Month of the CPI used for that week |
| `food_index` | DOUBLE | | Food CPI of that month |
| `reference_year` | INTEGER | | Year of the last published month, to which prices are brought |
| `reference_month` | INTEGER | | Last published month |
| `real_factor` | DOUBLE | | Factor that turns a nominal price of the week into pesos of the reference month |
| `provisional` | BOOLEAN | | True if the week is after the last published month |

### ine_ipc_source

| Column | Type | Key | Description |
|---|---|---|---|
| `file` | VARCHAR | | INE file of origin |
| `year` | VARCHAR | | Year, as the INE publishes it |
| `month` | VARCHAR | | Month, as the INE publishes it |
| `index_value` | VARCHAR | | Index value, as the INE publishes it |
| `monthly_change` | VARCHAR | | Monthly change, as the INE publishes it |

## 5. Audit and lineage

### etl_run

| Column | Type | Key | Description |
|---|---|---|---|
| `run_id` | INTEGER | PK | Number of the load |
| `started_at` | VARCHAR | | Start of the load, in UTC |
| `status` | VARCHAR | | Status: `LOADED` for a published load |
| `rows_read` | INTEGER | | Rows read from ODEPA |
| `rows_loaded` | INTEGER | | Rows loaded |
| `rows_rejected` | INTEGER | | Rows rejected; read = loaded + rejected |
| `message` | VARCHAR | | Message of the load, if any |

### rejection

| Column | Type | Key | Description |
|---|---|---|---|
| `run_id` | INTEGER | FK → `etl_run` | Load that rejected the row |
| `source` | VARCHAR | | Source: `wholesale` or `consumer` |
| `reason` | VARCHAR | | Reason for the rejection, for example `NON_POSITIVE_PRICE` (zero or negative price) |
| `original_row` | JSON | | The row as it arrived |

### dbt_node

| Column | Type | Key | Description |
|---|---|---|---|
| `unique_id` | VARCHAR | PK | Identifier of the node in dbt |
| `name` | VARCHAR | | Name of the model, the source or the test |
| `resource_type` | VARCHAR | | `model`, `source` or `test` |
| `layer` | VARCHAR | | Layer: `bronze`, `staging`, `intermediate` or `marts`; empty for the tests |
| `materialized` | VARCHAR | | How the model is materialized |
| `depends_on` | VARCHAR | | Nodes it depends on |
| `test_type` | VARCHAR | | Type of test, for the tests |
| `column_name` | VARCHAR | | Column it tests, if any |
| `description` | VARCHAR | | Description of the node in the dbt project |

### dbt_result

| Column | Type | Key | Description |
|---|---|---|---|
| `unique_id` | VARCHAR | FK → `dbt_node` | Node executed |
| `status` | VARCHAR | | Result: `success` for a model built, `pass` for a test passed |
| `execution_time` | DOUBLE | | Duration in seconds |
| `failures` | INTEGER | | Rows that do not meet the test |
| `generated_at` | VARCHAR | | Date of the `dbt build` |

## 6. Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## 7. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-25 | First version (D-279, professional documentation) |
