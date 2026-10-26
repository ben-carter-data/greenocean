# Software Architecture Document (SAD)

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Software Architecture Document (SAD), arc42 structure with C4 views |
| Version | 3.1 |
| Date | 2026-10-26 |
| Status | Current |
| Owner | The author |
| Purpose | Explain how GreenOcean is built, how it runs each week, where its data lives and why it has that shape. |
| Audience | Architecture, data engineering, operations, management and technical review. |
| Related documents | [Product Requirements Document (PRD)](PRD.md) · [Architecture Decision Records (ADR)](ADR.md) · [Test and Security Plan](PLAN_PRUEBAS.md) · [Glossary](GLOSARIO.md) |

## Contents

1. [In summary](#1-in-summary)
2. [Context](#2-context)
3. [Containers](#3-containers)
4. [The load of each week](#4-the-load-of-each-week)
5. [The panel when it opens](#5-the-panel-when-it-opens)
6. [The data](#6-the-data)
7. [Deployment](#7-deployment)
8. [Quality, security and observability](#8-quality-security-and-observability)
9. [Capacity and growth](#9-capacity-and-growth)
10. [Constraints and decisions](#10-constraints-and-decisions)
11. [Risks and technical debt](#11-risks-and-technical-debt)
12. [Glossary](#12-glossary)
13. [Version history](#13-version-history)

## 1. In summary

GreenOcean is a weekly pipeline and a read-only panel on food prices in Chile. Its architecture pursues three goals, in this order:

| Priority | Quality goal | What it means here |
|---|---|---|
| 1 | Accuracy and traceability | Every figure of the panel can be recomputed from the original file |
| 2 | Reliability of publication | A load with errors never replaces the served database |
| 3 | Zero cost and minimal maintenance | Only permanent free services and no servers of its own |

To reach them, the load rebuilds the whole history every Tuesday from the official files, checks it along two independent paths and only then replaces the database the panel reads. Everything runs on free services, with no servers of its own.

## 2. Context

[[diagrama:contexto]]

The system reads two public sources, ODEPA and the INE, and relies on two free services: GitHub keeps the code and the served database and runs the load; Streamlit Community Cloud publishes the panel. The visitor only reads the panel. The administrator, the author of the project, maintains the code and the secrets.

### 2.1 Key scenarios

[[diagrama:escenarios]]

Each scenario goes through the architecture end to end; sections 4 and 5 show them step by step.

## 3. Containers

[[diagrama:contenedores]]

The system has two applications and three data stores:

| Container | Technology | Responsibility |
|---|---|---|
| Weekly load | Python, dbt Core, DuckDB | Downloads the CSV files, keeps them unchanged, transforms and tests them, and replaces the served database only if everything passes. The agent, the ETL and dbt run in the same job |
| Working files | SQLite, Parquet, DuckDB | Landing, bronze and the dbt working database; rebuilt on each load and not versioned |
| Served database | DuckDB (`etl/datos.duckdb`) | The tables the panel reads; published in the «base-actual» release |
| Backup | SQLite (`etl/datos.db`) | The same prices computed without dbt, for the parity test; rebuilt on the machine of each load and not published |
| Web panel | Streamlit, Python | Shows the indicators and the documents, and offers the SQL studio; reads the served database read-only and, with the control code, launches the load through the GitHub API |

### 3.1 Components of the weekly load

[[diagrama:componentes_carga]]

Each component is a file of the repository and runs as a step of `semanal.yml`; if one fails, the following ones do not run.

### 3.2 Components of the panel

[[diagrama:componentes_panel]]

`bi/dashboard.py` builds the navigation and each page with its views; the queries go through `bi/queries.py` and the database is opened read-only. `bi/control.py` is the only piece that talks to the GitHub API.

## 4. The load of each week

[[diagrama:secuencia_carga]]

Each step starts only if the previous one ended well:

| Step | What happens |
|---|---|
| 1 | At 12:00 UTC, GitHub Actions creates a new machine and restores the CSV files of the closed years from its cache |
| 2 | It downloads the served database of the previous week from the «base-actual» release and verifies its fingerprint; the load history and the comparison of step 6 come from it |
| 3 | The agent downloads from ODEPA the file of the current year and any missing ones, and records the SHA-256 fingerprint of each in `manifest.json` |
| 4 | The Python ETL computes the prices on its own and writes the backup `etl/datos.db` |
| 5 | `etl/pipeline.py` stores the rows in the landing database, copies them to bronze together with the INE CPI and runs `dbt build`, which builds and tests each model in the working database |
| 6 | Publication gate: if a dbt test fails or the load reads less than 90 % of the rows of the last good load, the process stops; if everything passes, the panel tables are copied to a new file that replaces `etl/datos.duckdb` |
| 7 | pytest runs on the new database, including the parity between the backup and DuckDB |
| 8 | The machine replaces the database in the release and pushes its pointer, `etl/datos.version`, to the `main` branch; the panel detects the new pointer, downloads the database and verifies its fingerprint before using it |
| 9 | The weekly report is published as an issue of the repository |

If a step fails, the following ones do not run and the served database does not change ([ADR-11 · Publish only if the tests pass](ADR.md#adr-11--publish-only-if-the-tests-pass)). The run and its steps can be followed in the «Operations» tab of [[vista:Operations center]].

## 5. The panel when it opens

[[diagrama:secuencia_panel]]

When it opens, the panel compares its database with the pointer of the `main` branch. If its copy is older, it downloads the database from the «base-actual» release and uses it only if its SHA-256 fingerprint matches. Then it opens the database read-only: no page can change a value. If GitHub does not respond, the panel carries on with the database it already has.

The first time, the reader chooses a view: the user view shows the business (the Price overview, Where to buy, Insights and Prices and inflation) and the professional view, the whole project, ordered by the profile chosen (Data Eng, BA, BI, DevOps or Security); the user view opens the rest only with the app's code. If the last load failed, a red notice above the menu says so on every page, with a link to the step that failed. The panel reads in Spanish and in English.

## 6. The data

[[diagrama:capas]]

Landing keeps the rows as they arrive; bronze is their literal copy in Parquet, by source and year; staging normalizes types and text; intermediate applies the business rules (units, weeks, rejections); the marts form the star schema the panel reads. The journey and the lineage are in [[vista:Pipeline and lineage]], and the model, in [[vista:Data model]]. Dates are stored as ISO text (`YYYY-MM-DD`).

### 6.1 Tables of the served database

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

### 6.2 Facts and dimensions

### weekly_price

| Column | Type | Key | Description |
|---|---|---|---|
| `week_start` | VARCHAR | FK → `dim_date` | Monday of the week |
| `product_id` | BIGINT | FK → `dim_product` | Product, variety and quality |
| `region_id` | INTEGER | FK → `dim_region` | Region |
| `channel_id` | BIGINT | FK → `dim_channel` | Sales channel |
| `normalized_unit` | VARCHAR | | Normalized unit: `kilo`, `litro` or `unidad`; empty if it cannot be converted |
| `price` | DOUBLE | | Weekly price in nominal pesos, per normalized unit; empty when the unit cannot be converted (flag `UNIDAD_NO_CONVERTIBLE`) |
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

### 6.3 CPI

**Real prices.** Each week takes the food CPI of the month of its Monday; real prices are expressed in pesos of the last published month ([ADR-33 · Compute real prices with the INE food CPI](ADR.md#adr-33--compute-real-prices-with-the-ine-food-cpi)).

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

### 6.4 Audit and lineage

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

## 7. Deployment

[[diagrama:despliegue]]

| Piece | Where it runs | Detail |
|---|---|---|
| Weekly load and the tests of each change | GitHub Actions machines (Ubuntu, Python 3.11) | Created and discarded on each run; the CSV files of closed years stay in the Actions cache |
| Code and database pointer | GitHub repository, `main` branch | |
| Served database | «base-actual» release of the repository | A single copy, replaced by each load |
| Panel | Streamlit Community Cloud, from `main` | Keeps the secrets: the GitHub token and the control code |
| Landing (`etl/raw.db`) | The author's computer and the machine of each load | Not versioned |

The diagram with the live status of each piece is in the «Deployment» tab of [[vista:Operations center]]; the path of a change to production, in its «CI/CD» tab.

## 8. Quality, security and observability

**Quality.** Three gates: the file (did it arrive complete and on time?), each row (is it valid?) and the database (is it consistent, and did it pass its tests?). Eleven indicators, in five dimensions, are measured on each load against their threshold; accuracy, the sixth dimension, is measured with four controls that compare the figures with the source. The detail is in [[vista:Quality and audit]].

**Observability.** Each load leaves a trace in four places: `etl_run` (rows read, loaded and rejected by each published load), `dbt_result` (the result of each model and test), the GitHub Actions log (each step, including the ones that fail) and the email GitHub sends the author if the load fails. The «Monitoring» tab of [[vista:Operations center]] brings them together.

**Security.** The threats, their controls and the tests that verify them are in [[vista:Security architecture]]; the verification procedure, in the [Test and Security Plan](PLAN_PRUEBAS.md).

**Quality requirements**

| Attribute | Scenario | Expected response |
|---|---|---|
| Accuracy | A business rule changes by mistake | The parity with the backup or the rebuild from raw rows fails in pytest and the load is not published |
| Reliability | ODEPA publishes a truncated file | The load reads less than 90 % of the previous one and stops; the panel keeps the last valid database |
| Availability | GitHub does not respond when the panel opens | The panel keeps the database it already has, and says so if it has none |
| Security | A visitor tries to read server files with SQL | The query is rejected and the engine has no access to files or to the network |
| Usability | A 1440 × 900 screen | Each main page is seen whole in the browser window (1440 × 790) |

## 9. Capacity and growth

### 9.1 Current capacity

| Measure | Value | Origin |
|---|---|---|
| Served database | About 14 MB in the served database | Size of `etl/datos.duckdb` |
| Data | Volume and coverage of the last load | [PRD, section 6](PRD.md#6-scope) |
| Frequency | One load per week | [RF-01](PRD.md#5-requirements) |
| Users | One public, read-only panel | [PRD, section 3](PRD.md#3-who-it-is-for) |

### 9.2 What gives way first

| Limit | Current situation | Planned response |
|---|---|---|
| Size of the served database | A single copy in a release, replaced by each load ([ADR-35](ADR.md#adr-35--publish-the-served-database-in-a-release-that-each-load-replaces)); the Git history no longer grows with the data | A release file can hold up to 2 GB; long before that, the option of section 9.4 would be advisable |
| Duration of the load | Each load rebuilds the whole history since 2022 ([ADR-10](ADR.md#adr-10--rebuild-everything-on-each-load)) and takes a little longer every year | Incremental loads when the duration justifies them |
| Simultaneous visitors | A free Streamlit app that reads a small file read-only | If several teams used it daily, the free plan would not be enough: it is one of the thresholds of section 9.4 |

### 9.3 Growth options

A new source is added like the current ones: a folder in bronze and its dbt models, without changing the existing ones.

| Extension | Status | How it would be added |
|---|---|---|
| Weather by region and week | Planned; official source to be defined | A staging model and a mart by week and region, next to the price alerts, without claiming that the weather causes a price |
| Cloud data warehouse | Not adopted ([ADR-31](ADR.md#adr-31--do-not-use-a-cloud-data-warehouse)) | A new target in the dbt configuration, with the same models and the same audit |

### 9.4 When a cloud would be justified

With public, weekly and small data, read by a single panel, a cloud data warehouse would add cost, secrets and expiry risks with no benefit ([ADR-31](ADR.md#adr-31--do-not-use-a-cloud-data-warehouse)). It would be justified if a company added its own data:

| Criterion | Today | Threshold |
|---|---|---|
| Volume | About 14 MB | Several GB: sales by store and day, costs, inventory |
| Users | One read-only panel | Several teams or BI tools on the same data |
| Access | Public | Permissions per person or sensitive data |
| Freshness | Weekly | Several loads a day or real time |

## 10. Constraints and decisions

| Constraint | Origin |
|---|---|
| Only free services without expiry | [ADR-02 · Orchestrate with GitHub Actions and publish on Streamlit Community Cloud](ADR.md#adr-02--orchestrate-with-github-actions-and-publish-on-streamlit-community-cloud) and [ADR-31 · Do not use a cloud data warehouse](ADR.md#adr-31--do-not-use-a-cloud-data-warehouse) |
| Only official, open sources | [ADR-01 · Use only the official files of ODEPA and the INE](ADR.md#adr-01--use-only-the-official-files-of-odepa-and-the-ine) |
| No figure is invented or interpolated, and the history is not deleted | Project rule |
| Python 3.11 or 3.12 for the pipeline with dbt | dbt Core compatibility |
| Public repository | Open portfolio; security depends on the secrets, not on hidden code |

**Solution strategy**

| Principle | How it is applied | Decision |
|---|---|---|
| Rebuild everything on each load | Every Tuesday the whole history is recomputed from the official files; repeating a load never duplicates data | [ADR-10](ADR.md#adr-10--rebuild-everything-on-each-load) |
| Publish only what is validated | The served database changes only if all the tests pass | [ADR-11](ADR.md#adr-11--publish-only-if-the-tests-pass) |
| Check along a second path | A Python ETL, independent of dbt, computes the same prices | [ADR-34](ADR.md#adr-34--separate-the-dbt-working-database-the-database-the-panel-reads-and-the-backup) |
| Declarative, tested layers | Bronze in Parquet; staging, intermediate and marts in dbt Core on DuckDB | [ADR-30](ADR.md#adr-30--parquet-dbt-core-and-duckdb) |
| A single published copy | The served database lives in a release that each load replaces | [ADR-35](ADR.md#adr-35--publish-the-served-database-in-a-release-that-each-load-replaces) |

The decisions that shape this architecture, with their context, their alternatives and their consequences, are in the [Architecture Decision Records (ADR)](ADR.md).

## 11. Risks and technical debt

| Risk or debt | Effect | Current mitigation |
|---|---|---|
| ODEPA changes the format of its files | A load that was read wrongly | The publication gate rejects it and the panel keeps the last valid load |
| A dependency changes without notice | A slow or broken load with no change in the code; it happened with DuckDB 2 (D-227, DuckDB with a maximum version) and with certifi, which removed the root of ODEPA's certificate (D-164, emSign root in the agent) | DuckDB has a maximum version in `requirements.txt`; ODEPA's root travels with the agent, without disabling verification |
| The database cannot be downloaded from the release | The panel does not get the database of the last load | The panel keeps the database it already has; the weekly load stops before building |
| The terms of the free plans change | The load or the panel would have to move | The pipeline runs on any machine with Python 3.11 or 3.12 |
| Legacy views in `bi/dashboard.py` | Code reachable only through old addresses, which reads `docs/DISENO.md` | Pending removal |
| Earlier versions of the database in the Git history | The repository weighed 309 MB on 2026-10-24; since ADR-35 the database is no longer added to the history | Kept; deleting them would require rewriting the history |

## 12. Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## 13. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-18 | First version (D-151, documentation in three documents) |
| 1.1 | 2026-10-19 | Architecture with dbt, DuckDB and Parquet (D-152, D-154); rationale for each tool |
| 1.2 | 2026-10-20 | Security corrected (D-200); own diagrams (D-205); figures of the week of 2026-10-12 |
| 1.3 | 2026-10-21 | Engineering-document wording (D-210, D-214, D-217); CPI straight to Parquet (D-218) |
| 1.4 | 2026-10-23 | Context diagram (D-242); C4 views without copying diagrams (D-247); download as the printed page (D-248); security as a process (D-249) |
| 1.5 | 2026-10-24 | Principles, runtime view, quality and observability, risks (D-269); served database in a release (D-270) |
| 2.0 | 2026-10-25 | Complete arc42 structure: constraints, solution strategy, crosscutting concepts, quality requirements, technical debt, glossary and history (D-279, professional documentation) |
| 3.0 | 2026-10-25 | From the most important to the least: summary, context, containers, the load and the panel as sequences, the data with its dictionary, deployment, quality and security, capacity and growth (formerly documents of their own); six diagrams (D-290, documents for every reader) |
| 3.1 | 2026-10-26 | Key scenarios and components of the load and of the panel (C4, level 3); the views, the Dashboard and the failed-load notice in the panel (D-300) |
