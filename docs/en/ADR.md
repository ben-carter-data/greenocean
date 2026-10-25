# Architecture Decision Records (ADR)

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Architecture Decision Records (ADR), MADR format |
| Version | 3.0 |
| Date | 2026-10-25 |
| Status | Current |
| Owner | The author |
| Purpose | Explain the eleven decisions that weigh most on the architecture of GreenOcean: why they were taken, which alternatives there were and what consequences they have. |
| Audience | Architecture, engineering, management and technical review. |
| Related documents | [Software Architecture Document (SAD)](SAD.md) · [Decision Index](INDICE_DECISIONES.md) · [Glossary](GLOSARIO.md) |

Each record keeps its original number, which is why the numbering is not consecutive. The minor decisions are in the [Decision Index](INDICE_DECISIONES.md) and in the full log, `docs/DECISIONES.md`. The options considered are only those recorded in that log or in the history of the repository.

## Contents

| Decision | Record | Status | Date |
|---|---|---|---|
| [Use only the official files of ODEPA and the INE](#adr-01--use-only-the-official-files-of-odepa-and-the-ine) | ADR-01 | Accepted | 2026-10-11 |
| [Orchestrate with GitHub Actions and publish on Streamlit Community Cloud](#adr-02--orchestrate-with-github-actions-and-publish-on-streamlit-community-cloud) | ADR-02 | Accepted | 2026-10-11 |
| [Do not commit the raw data to the repository](#adr-04--do-not-commit-the-raw-data-to-the-repository) | ADR-04 | Accepted, amended by ADR-35 | 2026-10-11 |
| [Rebuild everything on each load](#adr-10--rebuild-everything-on-each-load) | ADR-10 | Accepted | 2026-10-11 |
| [Publish only if the tests pass](#adr-11--publish-only-if-the-tests-pass) | ADR-11 | Accepted | 2026-10-11 |
| [Star schema with a gapless date dimension](#adr-19--star-schema-with-a-gapless-date-dimension) | ADR-19 | Accepted | 2026-10-11 |
| [Parquet, dbt Core and DuckDB](#adr-30--parquet-dbt-core-and-duckdb) | ADR-30 | Accepted | 2026-10-19 |
| [Do not use a cloud data warehouse](#adr-31--do-not-use-a-cloud-data-warehouse) | ADR-31 | Accepted | 2026-10-19 |
| [Compute real prices with the INE food CPI](#adr-33--compute-real-prices-with-the-ine-food-cpi) | ADR-33 | Accepted | 2026-10-19 |
| [Separate the dbt working database, the database the panel reads and the backup](#adr-34--separate-the-dbt-working-database-the-database-the-panel-reads-and-the-backup) | ADR-34 | Accepted | 2026-10-19 |
| [Publish the served database in a release that each load replaces](#adr-35--publish-the-served-database-in-a-release-that-each-load-replaces) | ADR-35 | Accepted | 2026-10-24 |

## In summary

Each decision of this document answers a concrete question: where the data comes from, how it is loaded, how it is stored, when it is published and how much it costs. Three ideas join them:

- **Only official data, recomputed from scratch.** Nothing is interpolated, and repeating a load never duplicates data.
- **Nothing is published without tests.** A load with errors stops before it reaches the panel.
- **Zero cost and no expiry.** Permanent free services and a single published copy of the database.

[[diagrama:mapa_adr]]

[[diagrama:tiempo_adr]]

## ADR-01 · Use only the official files of ODEPA and the INE

- **Status:** accepted (D-001, official sources).
- **Date:** 2026-10-11.
- **Context:** the prices the project needs are already published as CSV files on open-data portals, with licenses that allow their reuse.
- **Decision:** download the official CSV files of ODEPA (prices) and of the INE (food CPI), without changing any value.
- **Considered options:** extracting prices from supermarket websites (*scraping*); public health records.
- **Consequences:** the source is stable, verifiable and independent of the design of a web page. Supermarket chains cannot be compared, because there is no official source for that.

## ADR-02 · Orchestrate with GitHub Actions and publish on Streamlit Community Cloud

- **Status:** accepted (D-012, orchestration and publication).
- **Date:** 2026-10-11.
- **Context:** a public project, with a weekly load and a read-only panel, with no cost and no servers to maintain.
- **Decision:** GitHub Actions runs the weekly load and the tests of each change; Streamlit Community Cloud publishes the panel from the `main` branch.
- **Considered options:** a server of its own; Power BI, which requires a license to share a dashboard.
- **Consequences:** the panel opens from a public link and the project can be cloned. Concurrency and volume are limited by the free plans, which are enough for weekly data of this size.

## ADR-04 · Do not commit the raw data to the repository

- **Status:** accepted (D-020, raw data out of the repository); the served database and the backup left the repository in D-270 ([ADR-35](#adr-35--publish-the-served-database-in-a-release-that-each-load-replaces)).
- **Date:** 2026-10-11.
- **Context:** each yearly ODEPA CSV file weighs up to about 65 MB and the raw database of all years, hundreds of MB. GitHub rejects files over 100 MB and the repository would grow with each load.
- **Decision:** the CSV files and the landing database (`etl/raw.db`) are rebuilt on each load and stay out of the repository. The download log (`manifest.json`) is versioned, with the SHA-256 fingerprint of each file.
- **Considered options:** versioning all the data; using large-file storage.
- **Consequences:** the repository does not carry the raw data and each downloaded file can be verified against its fingerprint. A new copy of the project must run the agent to get the raw data; the database of the indicators is downloaded with one command ([ADR-35](#adr-35--publish-the-served-database-in-a-release-that-each-load-replaces)).

## ADR-10 · Rebuild everything on each load

- **Status:** accepted (D-024, full rebuild).
- **Date:** 2026-10-11.
- **Context:** the raw database is already rebuilt on each load, and a week that crosses two years gathers rows from two files.
- **Decision:** each load recomputes all the weekly prices from the raw rows, instead of adding only the new week.
- **Considered options:** incremental loads, week by week, with keys.
- **Consequences:** repeating a load never duplicates rows and the change of year needs no special logic. The rejection table keeps only those of the last load; of the earlier ones, their count stays in `etl_run`. The duration of the load grows with each year of data.

## ADR-11 · Publish only if the tests pass

- **Status:** accepted (D-029, row threshold; D-154, build with dbt).
- **Date:** 2026-10-11.
- **Context:** a truncated file or a broken rule must never reach the panel.
- **Decision:** the served database is replaced only if all the dbt tests pass, if the load reads at least 90 % of the rows of the last good load and if pytest passes on the new database. If something fails, the workflow stops before publishing, GitHub Actions marks the run as failed and emails the author.
- **Considered options:** fixed row limits per week.
- **Consequences:** the panel always shows the last valid load. `etl_run` keeps only the published loads; the failed ones stay in the GitHub Actions history, visible in «Operations center». The first load has nothing to compare with, and a duplicated file is not detected by counting: the uniqueness tests detect it.

## ADR-19 · Star schema with a gapless date dimension

- **Status:** accepted (D-023, star schema; D-095, date dimension).
- **Date:** 2026-10-11.
- **Context:** comparing a price with the same season of other years requires knowing, for each week, its ISO week, its month and its season, even when that week has no prices.
- **Decision:** a star schema with `weekly_price` at the center and the product, region, channel and date dimensions; `dim_date` has one row per week, with no gaps, from the first to the last.
- **Considered options:** no alternative options were recorded when the decision was taken.
- **Consequences:** the calculations by season and the weekly CPI join on `week_start` with a real foreign key. Tables and columns are in English, so the model does not match the names of the original design literally.

## ADR-30 · Parquet, dbt Core and DuckDB

- **Status:** accepted (D-154, data warehouse with dbt Core and DuckDB).
- **Date:** 2026-10-19.
- **Context:** the business rules lived in a Python ETL without layers or declarative tests, and the project had to stay free and portable.
- **Decision:** bronze in Parquet, the transformations and their tests in dbt Core (staging, intermediate and marts) and DuckDB as the engine.
- **Considered options:** BigQuery in *sandbox* mode, whose tables expire after 60 days; Snowflake and Redshift, available only in trial periods; Databricks, oversized for this volume; free PostgreSQL, with plans that pause inactive projects (recorded on 2026-10-19, in the planned stack evolution, D-152).
- **Consequences:** each layer has its tests and the engine can be changed from the dbt configuration. The Python ETL is kept as an independent backup to check parity.

## ADR-31 · Do not use a cloud data warehouse

- **Status:** accepted (D-152, planned stack evolution).
- **Date:** 2026-10-19.
- **Context:** public, weekly data of a few megabytes, read by a single panel.
- **Decision:** the served database is a DuckDB file; there is no cloud data warehouse.
- **Considered options:** BigQuery as a second dbt target, declared as an option and never as a dependency of the panel.
- **Consequences:** there is no cost, no cloud secrets and no expiry. It would be reconsidered only if a company added its own data; the thresholds are in the [SAD, capacity and growth](SAD.md#9-capacity-and-growth).

## ADR-33 · Compute real prices with the INE food CPI

- **Status:** accepted (D-155, real prices with the CPI).
- **Date:** 2026-10-19.
- **Context:** without discounting inflation, a current price looks high only because everything rose.
- **Decision:** use the «Alimentos y bebidas no alcohólicas» (food and non-alcoholic beverages) division of the INE CPI, linking its two series with the official change of January 2024; each week takes the CPI of the month of its Monday.
- **Considered options:** joining the two INE series without linking them, which produces a false jump of −33.7 %.
- **Consequences:** real prices are expressed in pesos of the last published month. A week of a month not yet published uses that last month and is marked as provisional; an index is never estimated.

## ADR-34 · Separate the dbt working database, the database the panel reads and the backup

- **Status:** accepted (D-154, data warehouse with dbt Core and DuckDB).
- **Date:** 2026-10-19.
- **Context:** the panel must never read a half-built database.
- **Decision:** dbt builds in a working database that is not versioned (`etl/warehouse_build.duckdb`); at the end of a valid load, the panel tables are copied to a new, compact file that replaces `etl/datos.duckdb` at once. The Python ETL writes the backup `etl/datos.db` separately.
- **Considered options:** letting the panel read the dbt working database directly.
- **Consequences:** the panel reads a light file that is always complete, and the backup makes it possible to check that two independent paths produce the same figures.

## ADR-35 · Publish the served database in a release that each load replaces

- **Status:** accepted (D-270, served database in a release).
- **Date:** 2026-10-24.
- **Context:** each load committed the served database and the backup, about 48 MB. Git keeps every version of a file: the history grew by about 1 GB per year with copies nobody reads, because each new database already contains the whole history ([ADR-10](#adr-10--rebuild-everything-on-each-load)). Measurements of 2026-10-24.

[[diagrama:antes_despues]]

- **Decision:** the served database is published as a file of the «base-actual» GitHub release, replaced by each load. Git keeps only its pointer, `etl/datos.version`, with the SHA-256 fingerprint, the size and the date of the published database. The panel, the tests of each push and a new copy of the project download the file when it is missing or older, and use it only if its fingerprint matches. The SQLite backup is rebuilt on the machine of each load, where the parity test runs, and is not published.
- **Considered options:** no longer versioning only the backup, which reduced the growth to about 300 MB per year without stopping it; large-file storage (Git LFS), which also keeps every version and has a limited free quota; rewriting the history periodically, which invalidates the copies already cloned.
- **Consequences:** the history stops growing with the data and there is a single published copy. The panel depends on being able to download the database when it starts; if it cannot, it keeps the one it has. The earlier versions stay in the history. A local rebuild newer than the pointer is kept.

## Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-18 | First version (D-151, documentation in three documents) |
| 1.1 | 2026-10-19 | Decisions on dbt, DuckDB, Parquet and the CPI (D-152, D-154) |
| 1.2 | 2026-10-20 | Figures aligned with the database of the week of 2026-10-12 |
| 1.3 | 2026-10-21 | Engineering-document wording (D-210, D-214, D-218) |
| 1.4 | 2026-10-23 | The ten decisions with their standard parts (D-248) |
| 1.5 | 2026-10-24 | ADR-11 corrected and alternatives of ADR-19 (D-269); ADR-35 (D-270) |
| 2.0 | 2026-10-25 | MADR format with date and options considered, contents first, ADR-30 options completed from the history, ADR-19 without unrecorded alternatives (D-279, professional documentation) |
| 3.0 | 2026-10-25 | Summary in plain language, map of where each decision acts, timeline and the before and after of ADR-35; index by the name of each decision (D-290, documents for every reader) |
