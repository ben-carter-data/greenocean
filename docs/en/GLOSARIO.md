# Glossary

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Glossary |
| Version | 2.1 |
| Date | 2026-10-26 |
| Status | Current |
| Owner | The author |
| Purpose | Define once the acronyms and terms used by the panel and the documents. |
| Audience | Every reader of the panel and of the documentation. |
| Related documents | [PRD](PRD.md) · [SAD](SAD.md) · [ADR](ADR.md) · [Test and Security Plan](PLAN_PRUEBAS.md) |

## Contents

1. [In summary](#1-in-summary)
2. [Terms](#2-terms)
3. [Version history](#3-version-history)

## 1. In summary

This glossary defines once each technical word of the panel and the documents. The three diagrams show how they relate: the path of a figure, from the row ODEPA publishes to the alert of the panel; the layers the data goes through, and the actors that take part.

[[diagrama:terminos_cifra]]

[[diagrama:terminos_capas]]

[[diagrama:terminos_actores]]

## 2. Terms

The terms are ordered by theme, from what is read in the panel to the documents. The column «Where it appears» names the pages of the panel that use each term; «—» means it appears only in the documents.

| Acronym or term | Meaning | Where it appears | Theme |
|---|---|---|---|
| KPI | Key performance indicator: each figure that measures something of the business. | Weekly summary, Prices and inflation | Indicators |
| BI | Business intelligence: data analysis to take decisions; here, the panel. | — | Indicators |
| BA | Business analysis: the role that turns the data into decisions; one of the professional views of the panel. | — | Indicators |
| RN | Business rule (*regla de negocio*): each cleaning and calculation rule (RN-01 to RN-14). | Quality and audit | Indicators |
| Price alert | A weekly change that is unusual for a product and of at least 10 %. | Weekly summary | Indicators |
| Real price | A price expressed in pesos of the last published month of the CPI. | Prices and inflation | Indicators |
| Provisional week | A week of a month whose CPI is not yet published; it uses the last available month. | Prices and inflation | Indicators |
| Quality dimension | An aspect of quality that is measured: completeness, timeliness, validity, uniqueness, consistency and accuracy. | Quality and audit | Indicators |
| DAMA-DMBOK | Data management guide of DAMA International (*Data Management Body of Knowledge*); the quality dimensions come from it. | — | Indicators |
| ODEPA | Office of Agricultural Studies and Policies (*Oficina de Estudios y Políticas Agrarias*), of Chile's Ministry of Agriculture. It publishes the two price sources. | Weekly summary, Pipeline and lineage | Sources |
| INE | Chile's National Statistics Institute (*Instituto Nacional de Estadísticas*). It publishes the food CPI. | Prices and inflation, Pipeline and lineage | Sources |
| CPI (IPC) | Consumer price index (*índice de precios al consumidor*); here, the «Alimentos y bebidas no alcohólicas» (food and non-alcoholic beverages) division published by the INE. | Prices and inflation | Sources |
| CSV | Text file with comma-separated values: the format in which ODEPA publishes the prices. | Pipeline and lineage | Sources |
| SHA-256 | Function that computes the fingerprint of a file; it changes if a single byte changes. It is used to verify the downloaded files and the served database. | Quality and audit | Sources |
| JSON | Text format for structured data (*JavaScript Object Notation*); the download manifest and the original row of each rejection are stored in it. | — | Sources |
| Pipeline | The whole flow of each Tuesday, from ODEPA to the panel: download, backup ETL, build with dbt, tests, publication and report. | Pipeline and lineage, Operations center | Pipeline |
| Ingestion | The download of the ODEPA files; the ingestion agent (`agent/agent.py`) does it and checks that each file brings the expected columns. | Pipeline and lineage | Pipeline |
| ETL | Extract, transform and load. `etl/etl.py` cleans the data and applies the rules for the backup `etl/datos.db`; the same rules run in dbt for the served database. | Pipeline and lineage, Operations center | Pipeline |
| Quality gate | A check that stops the load if something does not comply: the file, each row or the database. | Quality and audit | Pipeline |
| Job, workflow | Automated task of GitHub Actions; the weekly job (`semanal.yml`) runs the pipeline every Tuesday. | Operations center | Pipeline |
| Cron | The schedule of the weekly job: every Tuesday at 12:00 UTC. | Operations center | Pipeline |
| Run | One full pass of the weekly job. | Operations center | Pipeline |
| CI, CD | Continuous integration: the tests run by themselves on each change of the code (`pruebas.yml`). Continuous delivery: what passes all the tests reaches production without manual steps. | Operations center (CI/CD) | Pipeline |
| Commit, push | Save a change in the history of the code, and upload it to GitHub. | Operations center (CI/CD) | Pipeline |
| Release | A GitHub publication that keeps files outside the history; the «base-actual» release keeps the served database and each load replaces it. | Operations center (CI/CD) | Pipeline |
| Database pointer | The `etl/datos.version` file: the fingerprint, the size and the date of the published served database. | Operations center (Deployment) | Pipeline |
| Issue | A publication on GitHub; here, the weekly report. | Operations center (Monitoring) | Pipeline |
| Landing | The `etl/raw.db` database, with the ODEPA rows as they arrive; it is not versioned. | Pipeline and lineage | Database |
| Bronze, silver, gold | The data layers: bronze (Parquet, exact copy), silver (dbt staging and intermediate: types, rules and flags) and gold (marts: the star schema the panel reads). | Pipeline and lineage | Database |
| Served database | `etl/datos.duckdb`: the database the panel reads, with the star schema; published in the «base-actual» release. | Pipeline and lineage, Data model | Database |
| Backup | `etl/datos.db`: the same prices computed without dbt, for the parity test. | Data model | Database |
| Parity | Comparison between the backup and the served database: they must give the same figures. | Quality and audit | Database |
| Data warehouse | The database ready for analysis, with the star schema. | Pipeline and lineage, Data model | Database |
| Star schema | A fact table (`weekly_price`) surrounded by its dimensions (product, region, channel, date). | Data model | Database |
| PK, FK | Primary key: the column that identifies each row of a table. Foreign key: the column that points to the primary key of another table. | Data model | Database |
| JOIN | Union of two tables by their key. | Data model, SQL queries | Database |
| SQL | Structured query language: the data of the database is read with it. | SQL queries | Database |
| dbt | dbt Core: a tool that transforms data with versioned SQL models, with tests and lineage. | Pipeline and lineage | Database |
| DuckDB | Analytical database in a single file, without a server. | Data model | Database |
| Parquet | Open, compressed, columnar file format. | Pipeline and lineage | Database |
| Git LFS | Git extension for large files (*Large File Storage*), which keeps them outside the history. | — | Database |
| ISO | International Organization for Standardization; here, the ISO week (Monday to Sunday, numbered according to ISO 8601) and the dates in YYYY-MM-DD format. | — | Database |
| Token | Credential that lets the panel query GitHub and launch the workflow; it is never shown. | Operations center | Security |
| Control code | Secret that opens the author's access in the panel. | Operations center | Security |
| OWASP | Open Worldwide Application Security Project; its Top 10 list classifies the security risks of web applications. | Security architecture | Security |
| ASCII | Basic English character set, without ñ or accents. | — | Security |
| API | Interface through which one program talks to another; the panel uses it to query GitHub. | Operations center | Connections |
| HTTPS | Encrypted web connection. | Pipeline and lineage, Operations center (Deployment) | Connections |
| URL | Address of a page or a file on the web. | — | Connections |
| UTC | Coordinated universal time; the job runs at 12:00 UTC: 09:00 in Chile in summer time and 08:00 in winter. | Operations center | Connections |
| PRD | Product Requirements Document. | — | Documents |
| SAD | Software Architecture Document. | — | Documents |
| ADR | Architecture Decision Record. | — | Documents |
| MADR | Standard format for writing an ADR (*Markdown Architectural Decision Records*). | — | Documents |
| arc42 | Standard template for software architecture documentation. | — | Documents |
| C4 | Model of architecture diagrams by levels: context, containers, components and code. | — | Documents |
| RF, RNF | Functional requirement (*requisito funcional*) and non-functional requirement (*requisito no funcional*). | — | Documents |
| ID | Identifier of a requirement, a test case or a row. | — | Documents |
| PDF | Document format for printing; the PDF of each document is its page of the panel printed by the browser. | — | Documents |
| Runbook | Operations manual: what to do about each failure, step by step. | — | Documents |

## 3. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-25 | First version as a document of its own, from the glossary of the project guide (D-279, professional documentation) |
| 2.0 | 2026-10-25 | A summary with three diagrams and the terms ordered by theme, from the indicators (D-290, documents for every reader) |
| 2.1 | 2026-10-26 | BA, one of the professional views of the panel (D-300) |
