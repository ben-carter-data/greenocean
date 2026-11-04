# Glossary

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Glossary |
| Version | 2.17 |
| Date | 2026-11-03 |
| Status | Current |
| Owner | The author |
| Purpose | Define once the acronyms and terms used by the panel and the documents. |
| Audience | Every reader of the panel and of the documentation. |
| Related documents | [PRD](PRD.md) · [SAD](../arquitectura/SAD.md) · [ADR](../arquitectura/ADR.md) · [Test and Security Plan](../calidad/PLAN_PRUEBAS.md) |

## Contents

1. [In summary](#1-in-summary)
2. [Terms](#2-terms)
3. [Version history](#3-version-history)

## 1. In summary

This glossary defines once each technical word of the panel and the documents. Three diagrams show how they relate: the path of a figure, from the row ODEPA publishes to the alert of the panel; the layers the data goes through; and the actors that take part.

[[diagrama:terminos_cifra]]

[[diagrama:terminos_capas]]

[[diagrama:terminos_actores]]

## 2. Terms

The terms are ordered by theme, from what is read in the panel to the documents. The column «Where it appears» says on which pages of the panel each term is used. A «—» means it appears only in the documents.

| Acronym or term | Meaning | Where it appears | Theme |
|---|---|---|---|
| KPI | Key performance indicator: each figure that measures something of the business. The technical indicators are numbered K1 to K8. | Weekly, BA and BI analysis (Monthly), BA and BI analysis (Historical), BA and BI analysis (Method) | Indicators |
| BI | Business intelligence: data analysis to take decisions; here, the panel. | — | Indicators |
| BA | Business analysis: the role that turns the data into decisions; one of the professional views of the panel. | BA and BI analysis (Stakeholders) | Indicators |
| BSA | Business systems analysis: the role that decides how the system meets what the business asks: what is measured, what blocks publication and what warns. | BA and BI analysis (Method) | Indicators |
| RN | Business rule (*regla de negocio*): each cleaning and calculation rule (RN-01 to RN-14). | Quality and audit | Indicators |
| Price alert | A weekly change outside the average ± 2 deviations of its previous 12 weeks, of at least 10 % and with two quotes in each week (K6). It splits into sharp rises and sharp drops (D-477). In Weekly, with a region chosen, it is calculated with the price of that region (D-499). | Weekly | Indicators |
| Sharp rise | A price alert for a rise, in red. Its level says how unusual it was: Extreme rise (4 deviations or more), Very sharp rise (3 or more) or Sharp rise (more than 2) (D-478, D-479). | Weekly | Indicators |
| Sharp drop | A price alert for a drop, in green: good news for whoever buys. Its level: Extreme drop (4 deviations or more), Very sharp drop (3 or more) or Sharp drop (more than 2) (D-478, D-479). | Weekly | Indicators |
| Real price | A price expressed in pesos of the last published month of the CPI. | BA and BI analysis (Prices and inflation) | Indicators |
| Provisional week | A week of a month whose CPI is not yet published; it uses the last available month. | BA and BI analysis (Prices and inflation) | Indicators |
| Data quality indicator | Each of the 11 indicators measured on every load on the published database, in five dimensions. | Quality and audit | Indicators |
| Quality plan indicator | Each of the 14 indicators of the SQAP (8 of code and 6 of data) that the quality workflow measures every week. | Method and quality | Indicators |
| Quality dimension | An aspect of quality that is measured: completeness, timeliness, validity, uniqueness, consistency and accuracy. | Quality and audit | Indicators |
| DAMA-DMBOK | Data management guide of DAMA International (*Data Management Body of Knowledge*); the quality dimensions come from it. | — | Indicators |
| ODEPA | Office of Agricultural Studies and Policies (*Oficina de Estudios y Políticas Agrarias*), of Chile's Ministry of Agriculture. It publishes the two price sources. | Weekly, Pipeline and lineage | Sources |
| INE | Chile's National Statistics Institute (*Instituto Nacional de Estadísticas*). It publishes the food CPI. | BA and BI analysis (Prices and inflation), Pipeline and lineage | Sources |
| CPI (IPC) | Consumer price index (*índice de precios al consumidor*); here, the «Alimentos y bebidas no alcohólicas» (food and non-alcoholic beverages) division published by the INE. | BA and BI analysis (Prices and inflation) | Sources |
| CSV | Text file with comma-separated values: the format in which ODEPA publishes the prices. | Pipeline and lineage | Sources |
| SHA-256 | Function that computes the fingerprint of a file; it changes if a single byte changes. It is used to verify the downloaded files and the DuckDB database. | Quality and audit | Sources |
| JSON | Text format for structured data (*JavaScript Object Notation*); the download manifest and the original row of each rejection are stored in it. | — | Sources |
| Pipeline | The whole flow of each Tuesday, from ODEPA to the panel: download, backup ETL, build with dbt, tests, publication and report. | Pipeline and lineage, Operations center | Pipeline |
| Ingestion | The download of the ODEPA files; the ingestion agent (`agent/agent.py`) does it and checks that each file brings the expected columns. | Pipeline and lineage | Pipeline |
| ETL | Extract, transform and load. `etl/etl.py` cleans the data and applies the rules for the backup `etl/datos.db`; the same rules run in dbt for the DuckDB database. | Pipeline and lineage, Operations center | Pipeline |
| Quality gate | A check that stops the load if something does not comply: the file, each row or the database. | Quality and audit | Pipeline |
| Job, workflow | Automated task of GitHub Actions; the weekly job (`semanal.yml`) runs the pipeline every Tuesday. | Operations center | Pipeline |
| Cron | The schedule of the weekly job: every Tuesday at 12:07 UTC, with another attempt every 15 minutes until 14:52 and every hour until 02:07 if GitHub is late (D-485). | Operations center | Pipeline |
| Run | One full pass of the weekly job. | Operations center | Pipeline |
| CI, CD | Continuous integration: the tests run by themselves on each change of the code (`pruebas.yml`). Continuous delivery: what passes all the tests reaches production without manual steps. | Operations center (CI/CD) | Pipeline |
| Commit, push | Save a change in the history of the code, and upload it to GitHub. | Operations center (CI/CD) | Pipeline |
| Release | A GitHub publication that keeps files outside the history; the «base-actual» release keeps the DuckDB database and each load replaces it. | Operations center (CI/CD) | Pipeline |
| Database pointer | The `etl/datos.version` file: the fingerprint, the size and the date of the published DuckDB database. | Operations center (Deployment) | Pipeline |
| Issue | A publication on GitHub; here, the weekly report each load leaves. | Operations center (Monitoring) | Pipeline |
| Pull request | A proposed change on GitHub that the author reviews before accepting it; here, the quality report of each week. | Method and quality | Pipeline |
| Landing | The `etl/raw.db` database, with the ODEPA rows as they arrive; it is not versioned. | Pipeline and lineage | Database |
| Bronze, silver, gold | The data layers: bronze (Parquet, exact copy), silver (dbt staging and intermediate: types, rules and flags) and gold (marts: the star schema the panel reads). | Pipeline and lineage | Database |
| DuckDB database | `etl/datos.duckdb`: the database the panel reads, with the star schema; published in the «base-actual» release. It was called «DuckDB database» before (D-426). | Pipeline and lineage, Data model | Database |
| Backup | `etl/datos.db`: the same prices computed without dbt, for the parity test. | Data model | Database |
| Parity | Comparison between the backup and the DuckDB database: they must give the same figures. | Quality and audit | Database |
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
| Token | Credential with which the panel starts the load, reads its state and logs, and cancels it; it is never shown. | Operations center | Security |
| Control code | Secret that opens the Author view in the panel. | Operations center | Security |
| View | What the panel shows depending on who reads it: User (the business), Professional (the whole project) or Author (the same, plus what only the author sees, with the control code). | App map, Security architecture | Security |
| OWASP | Open Worldwide Application Security Project; its Top 10 list classifies the security risks of web applications. | Security architecture | Security |
| ASCII | Basic English character set, without ñ or accents. | — | Security |
| API | Interface through which one program talks to another. The panel uses GitHub's to start the load, read its state and logs, and cancel it. | Operations center | Connections |
| HTTPS | Encrypted web connection. | Pipeline and lineage, Operations center (Deployment) | Connections |
| URL | Address of a page or a file on the web. | — | Connections |
| UTC | Coordinated universal time; the job runs at 12:07 UTC: 09:07 in Chile in summer time and 08:07 in winter. | Operations center | Connections |
| PRD | Product Requirements Document. | — | Documents |
| SAD | Software Architecture Document. | — | Documents |
| SQAP | Software Quality Assurance Plan: which quality is looked after, how it is measured and who decides. | Method and quality | Documents |
| IEEE | Institute of Electrical and Electronics Engineers; it publishes the IEEE 730 standard, which gives the structure of the SQAP. | — | Documents |
| IEC | International Electrotechnical Commission; with the ISO it signs the standards ISO/IEC 25010 (software quality) and ISO/IEC 25012 (data quality). | Method and quality | Documents |
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
| 2.2 | 2026-10-30 | SQAP, IEEE and IEC, from the software quality assurance plan (D-355) |
| 2.3 | 2026-10-31 | BSA, from the pages «Stakeholders» and «Business and systems analysis» (D-376, D-377) |
| 2.4 | 2026-10-31 | Wording reviewed; the three views; the data quality indicators and those of the quality plan; the pull request of the quality report; the full price alert; the document moves to `docs/negocio/` (D-381 to D-385, D-388) |
| 2.5 | 2026-11-01 | «Served database» becomes «DuckDB database» (D-426) |
| 2.6 | 2026-11-02 | «Price overview» is renamed «Dashboard» and leads the menu (D-442) |
| 2.7 | 2026-11-02 | «Served database» becomes «DuckDB database» in the definitions too, which still used the former name (D-455) |
| 2.8 | 2026-11-02 | The pages that became tabs of «BA and BI analysis» are named «BA and BI analysis (tab)» (D-456) |
| 2.9 | 2026-11-02 | The «Trends» tab of «BA and BI analysis» becomes «Monthly» and «Historical» (D-457) |
| 2.10 | 2026-11-02 | The week's dashboard is called «Weekly» (D-459) |
| 2.11 | 2026-11-03 | The quality plan has 14 indicators (D-475) |
| 2.12 | 2026-11-03 | Sharp rise and sharp drop, the two kinds of price alert (D-477) |
| 2.13 | 2026-11-03 | The levels of an alert, all at least «sharp» (D-478) |
| 2.14 | 2026-11-03 | The bounds of each level, as the alert window shows them: 4 or more, 3 or more, more than 2 (D-479) |
| 2.15 | 2026-11-03 | The load's cron: 12:17 UTC and two more attempts (D-485) |
| 2.16 | 2026-11-03 | The load's cron: 12:07 UTC, an attempt every 15 minutes until 14:52 and every hour until 02:07 (D-487) |
| 2.17 | 2026-11-03 | The price alert in Weekly, with the price of the chosen region (D-499) |
