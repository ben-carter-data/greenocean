# Decision Index

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Decision Index |
| Version | 2.2 |
| Date | 2026-11-01 |
| Status | Current |
| Owner | The author |
| Purpose | Gather, by theme, the decisions that change the architecture, the data, the security or the operations. |
| Audience | Architects, management and technical reviewers. |
| Related documents | [Architecture Decision Records (ADR)](ADR.md) · [Software Architecture Document (SAD)](SAD.md) · [Glossary](../negocio/GLOSARIO.md) |

## Contents

1. [In summary](#1-in-summary)
2. [Sources and ingestion](#2-sources-and-ingestion)
3. [Data model and rules](#3-data-model-and-rules)
4. [Pipeline and publication](#4-pipeline-and-publication)
5. [Quality and audit](#5-quality-and-audit)
6. [Security](#6-security)
7. [Operations and observability](#7-operations-and-observability)
8. [Panel](#8-panel)
9. [Documentation](#9-documentation)
10. [Version history](#10-version-history)

## 1. In summary

GreenOcean records each change of behavior as a decision with its date, its reason and its tests. This index gathers the 98 that weigh most, grouped in eight themes, so they can be read without going through the full log. Each row says first what was decided. If the decision gave rise to an architecture record, the second column links it. The D-xxx code finds it in `docs/DECISIONES.md` (in Spanish), which keeps them all in chronological order.

[[diagrama:temas]]

[[diagrama:mapa_temas]]

[[diagrama:adr_decisiones]]

## 2. Sources and ingestion

What is downloaded, from where, and how the download is protected.

| What was decided | Architecture record | Code |
|---|---|---|
| The data comes from ODEPA's official files, not from copying web pages | [Use only the official files of ODEPA and the INE](ADR.md#adr-01--use-only-the-official-files-of-odepa-and-the-ine) | D-001 |
| Start with two sources: wholesale and consumer prices | — | D-002 |
| A product is identified by its name, variety and quality, never mixed | — | D-007 |
| The raw files are not committed to the repository | [Do not commit the raw data to the repository](ADR.md#adr-04--do-not-commit-the-raw-data-to-the-repository) | D-020 |
| The week of 2022-05-02, missing at ODEPA, is recorded as a known gap | — | D-042 |
| Closed years are not downloaded again: they are kept in GitHub's cache | — | D-047 |
| The download keeps working although certifi removed ODEPA's certificate | — | D-164 |

## 3. Data model and rules

How each price is computed and what counts as a valid figure.

| What was decided | Architecture record | Code |
|---|---|---|
| Wholesale and consumer prices are compared week by week | — | D-006 |
| A price whose unit cannot be converted is kept, but without a margin | — | D-008 |
| Tables and columns named in English, and one schema per database | [Star schema with a gapless date dimension](ADR.md#adr-19--star-schema-with-a-gapless-date-dimension) | D-023 |
| Each load recomputes every weekly price from scratch | [Rebuild everything on each load](ADR.md#adr-10--rebuild-everything-on-each-load) | D-024 |
| Units are converted by reading the text exactly as ODEPA writes it | — | D-026 |
| A price more than five times above or below the median of its week is flagged as an outlier and stays out of the indicators | — | D-028 |
| A gapless calendar of weeks to join every date | [Star schema with a gapless date dimension](ADR.md#adr-19--star-schema-with-a-gapless-date-dimension) | D-095 |
| The national change is always measured over the same regions | — | D-144 |
| Price alerts also compare the same regions | — | D-145 |
| The panel shows only conclusions the data supports | — | D-146 |
| Every page shows the same price for a product and a week | — | D-153 |
| Real prices remove inflation with the INE food CPI | [Compute real prices with the INE food CPI](ADR.md#adr-33--compute-real-prices-with-the-ine-food-cpi) | D-155 |
| An alert needs at least two quotes in each compared week | — | D-158 |
| Weeks read as a range from Monday to Sunday | — | D-374 |

## 4. Pipeline and publication

Which tools build the database and when it is published.

| What was decided | Architecture record | Code |
|---|---|---|
| The project runs on free tools: SQLite, GitHub Actions and Streamlit | [Orchestrate with GitHub Actions and publish on Streamlit Community Cloud](ADR.md#adr-02--orchestrate-with-github-actions-and-publish-on-streamlit-community-cloud) | D-012 |
| The data is checked before it is loaded | [Publish only if the tests pass](ADR.md#adr-11--publish-only-if-the-tests-pass) | D-029 |
| If a step of the weekly load fails, nothing is saved | — | D-034 |
| The growth plan: dbt, DuckDB and Parquet first; a cloud only with company data | [Do not use a cloud data warehouse](ADR.md#adr-31--do-not-use-a-cloud-data-warehouse) | D-152 |
| The data warehouse moves to dbt, DuckDB and Parquet with exactly the same results | [Parquet, dbt Core and DuckDB](ADR.md#adr-30--parquet-dbt-core-and-duckdb) | D-154 |
| The two builds of the database are compared without ambiguity, the CPI included | — | D-194 |
| DuckDB 2.0 waits until a slow query is reviewed | — | D-227 |
| The published database lives in a GitHub release; the repository keeps only its pointer | [Publish the served database in a release that each load replaces](ADR.md#adr-35--publish-the-served-database-in-a-release-that-each-load-replaces) | D-270 |
| The performance tests leave the CI and stay local | — | D-341 |
| Publication goes up to the last week complete in both sources, filling nothing in; a late source does not block the load | [Publish only if the tests pass](ADR.md#adr-11--publish-only-if-the-tests-pass) | D-356 |
| The weekly load runs only the data and pipeline tests; the screen tests run on every push | — | D-366 |

## 5. Quality and audit

What stops a load and how each figure is proven.

| What was decided | Architecture record | Code |
|---|---|---|
| The tests and quality checks are visible in the panel from the first version | — | D-016 |
| A finding is published only if it can be reproduced | — | D-018 |
| The indicators computed in SQL are checked against a computation in Python | — | D-049 |
| Quality is explained with the six dimensions of the DAMA-DMBOK standard | — | D-176 |
| Each quality figure is a real measurement and shows its origin | — | D-196 |
| The quality gates are drawn over the journey of the load | — | D-245 |
| Quality in one view: six dimensions and three gates | — | D-256 |
| In Quality, each piece of the diagram opens its detail | — | D-257 |
| Quality is drawn as a data-quality pipeline | — | D-273 |
| Quality is measured in two parts: the data that is published and the code that treats it | — | D-330 |
| The quality reports are numbered and never modified | — | D-331 |
| Each diagnosed failure goes into a register, with its category and its station of the git flow | — | D-342 |
| A software quality assurance plan (SQAP) says what is measured, how and who decides | — | D-355 |
| The 11 indicators of the load and the 12 of the quality plan have different names | — | D-384 |

## 6. Security

Who can do what, and how it is checked.

| What was decided | Architecture record | Code |
|---|---|---|
| The repository is public, with no secret in it | — | D-013 |
| The control code resists guessing and accepts any character | — | D-199 |
| Each attack is shown with its barrier and its test | — | D-200 |
| The button that launches the load appears only after the author's code | — | D-202 |
| The control code is no longer a browser password field | — | D-207 |
| Security is handled as a process, with its procedure and monitoring | — | D-249 |
| The security architecture is drawn by trust zones | — | D-254 |
| The «GitHub Actions» page is read-only and only the Author sees it | — | D-339 |
| The address does not choose the view: the window to choose it always opens | — | D-340 |
| The key's doors share a limit of attempts, kept on the server | — | D-393 |
| The Author's alert warns of each token at 15 days or fewer from its expiry | — | D-410 |

## 7. Operations and observability

How we know what happened in each load, and what to do.

| What was decided | Architecture record | Code |
|---|---|---|
| The weekly report and the warnings use GitHub's own tools | — | D-017 |
| The load is watched from a control center inside the panel | — | D-038 |
| The manual run is a visible button that shows its result | — | D-149 |
| The Operations center follows the journey of each Tuesday | — | D-165 |
| The CI/CD diagram is drawn from the real workflows | — | D-243 |
| The Tuesday orchestration lives inside the CI/CD diagram | — | D-246 |
| Deployment is drawn as a standard deployment diagram | — | D-255 |
| The monitoring signals hang from the weekly load | — | D-275 |
| The manual load is followed in a window that does not close by itself, and it can be minimized or cancelled | — | D-351 |
| The quality report is weekly and proposed as a pull request; a push only measures | — | D-363 |
| The deployment shows the two reports: the weekly one as an issue and the quality one as a pull request | — | D-383 |
| The console «Settings» gathers the state, what to do in each case and the maintenance | — | D-409 |
| The live system flow shows the real pieces, their messages and the running load | — | D-412 |
| The manual load's window shows the flow focused on the run | — | D-413 |

## 8. Panel

How the panel reads on a single screen and in two languages.

| What was decided | Architecture record | Code |
|---|---|---|
| Navigation is a single side menu, without tabs | — | D-096 |
| On a phone, the panel is read in landscape | — | D-166 |
| The Price overview has a single header bar | — | D-264 |
| Each main page has a single header bar | — | D-267 |
| Each page fits a real window of 1440 × 790 | — | D-274 |
| Buttons and links share a single component | — | D-281 |
| The panel and the documents exist in Spanish and English | — | D-283 |
| Each page is translated into English as it is drawn | — | D-284 |
| An app map shows the whole system in one view | — | D-285 |
| The dark theme is the default | — | D-349 |
| The page «Latest data by channel» shows the latest week of each source | — | D-365 |
| The Price overview reads in three steps that open in order | — | D-372 |
| The header only places the reader; the information goes in the content | — | D-398 |
| Each channel opens with the Overview's steps, in its own latest week | — | D-405 |
| Each main page also fits 1280 × 800 | — | D-407 |
| Once the family is chosen, steps 1 and 2 fold and the products table takes the screen | — | D-408 |

## 9. Documentation

How the project is explained.

| What was decided | Architecture record | Code |
|---|---|---|
| The documentation follows the PRD, SAD and ADR standard | — | D-151 |
| Short, direct documents | — | D-210 |
| A document's PDF is the same page, printed | — | D-248 |
| The documents are reviewed against the real product | — | D-269 |
| The documentation is separated from the history of the project | — | D-278 |
| Each document has a cover, contents, glossary and history | — | D-279 |
| Diagrams without a background, and the PDF always on a white sheet | — | D-280 |
| Every document in a single folder of the menu | — | D-282 |
| The documents go from the most important to the least, for every reader | — | D-290 |
| The documents are sorted into four folders by subject | — | D-381 |
| The SAD carries the fixed picture of the system flow | — | D-414 |

## 10. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-25 | First version (D-279, professional documentation) |
| 2.0 | 2026-10-25 | A summary with three diagrams; each row says first what was decided and links its architecture record by its name (D-290, documents for every reader) |
| 2.1 | 2026-10-31 | The major decisions since D-290: late sources, quality in two parts, the three views, the manual load window, the two reports and the four folders of documents; wording reviewed (D-381, D-388) |
| 2.2 | 2026-11-01 | The major decisions of the final part: the limit of attempts, «Settings» and its token warning, the live flow and its picture in the SAD, the header, the channels and one screen at 1280 × 800 (D-393 to D-414) |
