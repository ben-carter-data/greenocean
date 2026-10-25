# Software Architecture Document (SAD)

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Software Architecture Document (SAD), arc42 structure with C4 views |
| Version | 2.0 |
| Date | 2026-10-25 |
| Status | Current |
| Owner | The author |
| Purpose | Describe how the system is built, view by view, and why it has that shape. |
| Audience | Architecture, data engineering, operations and technical review. |
| Related documents | [Product Requirements Document (PRD)](PRD.md) · [Architecture Decision Records (ADR)](ADR.md) · [Data Dictionary](DICCIONARIO_DATOS.md) · [Security Test Plan](SEGURIDAD.md) · [Glossary](GLOSARIO.md) |

## Contents

1. [Introduction and goals](#1-introduction-and-goals)
2. [Constraints](#2-constraints)
3. [Context and scope](#3-context-and-scope)
4. [Solution strategy](#4-solution-strategy)
5. [Building block view](#5-building-block-view)
6. [Runtime view](#6-runtime-view)
7. [Deployment view](#7-deployment-view)
8. [Crosscutting concepts](#8-crosscutting-concepts)
9. [Architecture decisions](#9-architecture-decisions)
10. [Quality requirements](#10-quality-requirements)
11. [Risks and technical debt](#11-risks-and-technical-debt)
12. [Glossary](#12-glossary)
13. [Version history](#13-version-history)

## 1. Introduction and goals

GreenOcean is a weekly pipeline and a read-only panel on food prices in Chile. The requirements are in the [PRD](PRD.md). This document focuses on how they are met. The quality goals that weigh most on the architecture are three:

| Priority | Quality goal | What it means here |
|---|---|---|
| 1 | Accuracy and traceability | Every figure of the panel can be recomputed from the original file |
| 2 | Reliability of publication | A load with errors never replaces the served database |
| 3 | Zero cost and minimal maintenance | Only permanent free services and no servers of its own |

## 2. Constraints

| Constraint | Origin |
|---|---|
| Only free services without expiry | [ADR-02 · Orchestrate with GitHub Actions and publish on Streamlit Community Cloud](ADR.md#adr-02--orchestrate-with-github-actions-and-publish-on-streamlit-community-cloud) and [ADR-31 · Do not use a cloud data warehouse](ADR.md#adr-31--do-not-use-a-cloud-data-warehouse) |
| Only official, open sources | [ADR-01 · Use only the official files of ODEPA and the INE](ADR.md#adr-01--use-only-the-official-files-of-odepa-and-the-ine) |
| No figure is invented or interpolated, and the history is not deleted | Project rule |
| Python 3.11 or 3.12 for the pipeline with dbt | dbt Core compatibility |
| Public repository | Open portfolio; security depends on the secrets, not on hidden code |

## 3. Context and scope

[[diagrama:contexto]]

The system reads two public sources, ODEPA and the INE, and relies on two free services: GitHub keeps the code and the served database and runs the load; Streamlit Community Cloud publishes the panel. The visitor only reads the panel. The administrator maintains the code and the secrets.

## 4. Solution strategy

| Principle | How it is applied | Decision |
|---|---|---|
| Rebuild everything on each load | Every Tuesday the whole history is recomputed from the official files; repeating a load never duplicates data | [ADR-10](ADR.md#adr-10--rebuild-everything-on-each-load) |
| Publish only what is validated | The served database changes only if all the tests pass | [ADR-11](ADR.md#adr-11--publish-only-if-the-tests-pass) |
| Check along a second path | A Python ETL, independent of dbt, computes the same prices | [ADR-34](ADR.md#adr-34--separate-the-dbt-working-database-the-database-the-panel-reads-and-the-backup) |
| Declarative, tested layers | Bronze in Parquet; staging, intermediate and marts in dbt Core on DuckDB | [ADR-30](ADR.md#adr-30--parquet-dbt-core-and-duckdb) |
| A single published copy | The served database lives in a release that each load replaces | [ADR-35](ADR.md#adr-35--publish-the-served-database-in-a-release-that-each-load-replaces) |

## 5. Building block view

[[diagrama:contenedores]]

The system has two applications and three data stores:

| Container | Technology | Responsibility |
|---|---|---|
| Weekly load | Python, dbt Core, DuckDB | Downloads the CSV files, keeps them unchanged, transforms and tests them, and replaces the served database only if everything passes. The agent, the ETL and dbt run in the same job |
| Working files | SQLite, Parquet, DuckDB | Landing, bronze and the dbt working database; rebuilt on each load and not versioned |
| Served database | DuckDB (`etl/datos.duckdb`) | The tables the panel reads; published in the «base-actual» release |
| Backup | SQLite (`etl/datos.db`) | The same prices computed without dbt, for the parity test; rebuilt on the machine of each load and not published |
| Web panel | Streamlit, Python | Shows the indicators and the documents, and offers the SQL studio; reads the served database read-only and, with the control code, launches the load through the GitHub API |

The component view (level 3 of the C4 model) is omitted: the modules of `bi/` are not deployed separately, and the load is already described step by step in section 6 and in the dbt lineage.

## 6. Runtime view

Each step of the weekly load starts only if the previous one ended well:

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

If a step fails, the following ones do not run and the served database does not change ([ADR-11 · Publish only if the tests pass](ADR.md#adr-11--publish-only-if-the-tests-pass)). The run and its steps can be followed in the «Operations» tab of [[vista:Operations center]]; the administrator can also launch the load from the panel, with the control code.

## 7. Deployment view

| Piece | Where it runs | Detail |
|---|---|---|
| Weekly load and the tests of each change | GitHub Actions machines (Ubuntu, Python 3.11) | Created and discarded on each run; the CSV files of closed years stay in the Actions cache |
| Code and database pointer | GitHub repository, `main` branch | |
| Served database | «base-actual» release of the repository | A single copy, replaced by each load |
| Panel | Streamlit Community Cloud, from `main` | Keeps the secrets: the GitHub token and the control code |
| Landing (`etl/raw.db`) | The author's computer and the machine of each load | Not versioned |

The deployment diagram, with the live status of each piece, is in the «Deployment» tab of [[vista:Operations center]]; the path of a change to production, in its «CI/CD» tab.

## 8. Crosscutting concepts

**Data layers.** Landing keeps the rows as they arrive; bronze is their literal copy in Parquet, by source and year; staging normalizes types and text; intermediate applies the business rules (units, weeks, rejections); the marts form the star schema the panel reads. The journey and the lineage are in [[vista:Pipeline and lineage]]; the tables and their keys, in [[vista:Data model]] and in the [Data Dictionary](DICCIONARIO_DATOS.md).

**Real prices.** Each week takes the food CPI of the month of its Monday; real prices are expressed in pesos of the last published month ([ADR-33 · Compute real prices with the INE food CPI](ADR.md#adr-33--compute-real-prices-with-the-ine-food-cpi)).

**Quality.** Three gates: the file (did it arrive complete and on time?), each row (is it valid?) and the database (is it consistent, and did it pass its tests?). Eleven indicators, in five dimensions, are measured on each load against their threshold; accuracy, the sixth dimension, is measured with four controls that compare the figures with the source. The detail is in [[vista:Quality and audit]].

**Observability.** Each load leaves a trace in four places: `etl_run` (rows read, loaded and rejected by each published load), `dbt_result` (the result of each model and test), the GitHub Actions log (each step, including the ones that fail) and the email GitHub sends the author if the load fails. The «Monitoring» tab of [[vista:Operations center]] brings them together.

**Security.** The threats, their controls and the tests that verify them are in [[vista:Security architecture]]; the verification procedure, in the [Security Test Plan](SEGURIDAD.md).

## 9. Architecture decisions

The decisions that shape this architecture, with their context, their alternatives and their consequences, are in the [Architecture Decision Records (ADR)](ADR.md).

## 10. Quality requirements

| Attribute | Scenario | Expected response |
|---|---|---|
| Accuracy | A business rule changes by mistake | The parity with the backup or the rebuild from raw rows fails in pytest and the load is not published |
| Reliability | ODEPA publishes a truncated file | The load reads less than 90 % of the previous one and stops; the panel keeps the last valid database |
| Availability | GitHub does not respond when the panel opens | The panel keeps the database it already has, and says so if it has none |
| Security | A visitor tries to read server files with SQL | The query is rejected and the engine has no access to files or to the network |
| Usability | A 1440 × 900 screen | Each main page is seen whole in the browser window (1440 × 790) |

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
