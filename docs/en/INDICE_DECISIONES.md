# Decision Index

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Decision Index |
| Version | 1.0 |
| Date | 2026-10-25 |
| Status | Current |
| Owner | The author |
| Purpose | Gather, by theme, the decisions that change the architecture, the data, the security or the operations. |
| Audience | Architecture, management and technical review. |
| Related documents | [Architecture Decision Records (ADR)](ADR.md) · [Software Architecture Document (SAD)](SAD.md) · [Glossary](GLOSARIO.md) |

The full log, with every decision in chronological order, is `docs/DECISIONES.md` (in Spanish). This index gathers only those that change the architecture, the data, the security or the operations; the architecture decisions that weigh most also have their record in the [ADR](ADR.md).

## Contents

1. [Sources and ingestion](#1-sources-and-ingestion)
2. [Data model and rules](#2-data-model-and-rules)
3. [Pipeline and publication](#3-pipeline-and-publication)
4. [Quality and audit](#4-quality-and-audit)
5. [Security](#5-security)
6. [Operations and observability](#6-operations-and-observability)
7. [Panel](#7-panel)
8. [Documentation](#8-documentation)
9. [Version history](#9-version-history)

## 1. Sources and ingestion

| Decision | Title | ADR |
|---|---|---|
| D-001 | Download official files instead of scraping | [ADR-01](ADR.md#adr-01--use-only-the-official-files-of-odepa-and-the-ine) |
| D-002 | Two sources in stage 1 | — |
| D-007 | Exact key product + variety + quality | — |
| D-020 | The raw data is not committed to the repository | [ADR-04](ADR.md#adr-04--do-not-commit-the-raw-data-to-the-repository) |
| D-042 | The week of 2022-05-02 is missing at the source and is recorded as a known gap | — |
| D-047 | The files of closed years are kept in the GitHub Actions cache | — |
| D-164 | The ODEPA download trusts the emSign root that certifi removed | — |

## 2. Data model and rules

| Decision | Title | ADR |
|---|---|---|
| D-006 | Crossing by week | — |
| D-008 | Units that cannot be converted are kept, without a margin | — |
| D-023 | Tables and columns in English; one schema per database | [ADR-19](ADR.md#adr-19--star-schema-with-a-gapless-date-dimension) |
| D-024 | Weekly prices are rebuilt in full on each run | [ADR-10](ADR.md#adr-10--rebuild-everything-on-each-load) |
| D-026 | Unit conversion by literal reading of the text | — |
| D-028 | RN-12: median by product, unit, week and source, with a factor of 5 | — |
| D-095 | Date dimension dim_date | [ADR-19](ADR.md#adr-19--star-schema-with-a-gapless-date-dimension) |
| D-144 | Data audit and national change over the same regions | — |
| D-145 | The K6 alerts measure the change over the same regions | — |
| D-146 | Relevance review: only conclusions that hold | — |
| D-153 | Audit across pages: a single price per product and week | — |
| D-155 | Real prices with the INE food CPI | [ADR-33](ADR.md#adr-33--compute-real-prices-with-the-ine-food-cpi) |
| D-158 | An alert needs at least two quotes in each week | — |

## 3. Pipeline and publication

| Decision | Title | ADR |
|---|---|---|
| D-012 | SQLite, GitHub Actions and Streamlit Community Cloud | [ADR-02](ADR.md#adr-02--orchestrate-with-github-actions-and-publish-on-streamlit-community-cloud) |
| D-029 | Quality checks before loading | [ADR-11](ADR.md#adr-11--publish-only-if-the-tests-pass) |
| D-034 | Weekly job: nothing is saved if a step fails | — |
| D-152 | Planned evolution: dbt, DuckDB, Parquet, CPI and weather; the cloud only with company data | [ADR-31](ADR.md#adr-31--do-not-use-a-cloud-data-warehouse) |
| D-154 | The data warehouse moves to dbt Core, DuckDB and Parquet, with exact parity | [ADR-30](ADR.md#adr-30--parquet-dbt-core-and-duckdb) |
| D-194 | Unambiguous parity, and the CPI that does not go through SQLite | — |
| D-227 | DuckDB 2.0 stays out until the gap-between-channels query is reviewed | — |
| D-270 | The served database lives in a release that each load replaces; git keeps only its pointer | [ADR-35](ADR.md#adr-35--publish-the-served-database-in-a-release-that-each-load-replaces) |

## 4. Quality and audit

| Decision | Title | ADR |
|---|---|---|
| D-016 | Tests and quality checks visible from the first version | — |
| D-018 | Findings are published only if they can be reproduced | — |
| D-049 | SQL versions of K6 and K5 verified against Python; K4 without a double version | — |
| D-176 | Quality and audit tells the story with a method: the six dimensions of the DAMA-DMBOK | — |
| D-196 | Quality and audit rebuilt: real measurement and the origin of each figure | — |
| D-245 | Stage 6: the quality gates on the journey, and RF-03 with its test | — |
| D-256 | Quality and audit rebuilt: six dimensions, three gates, and text of normal size | — |
| D-257 | Quality and audit: the diagram is the page, and each piece opens its detail | — |
| D-273 | Quality: the diagram becomes a data-quality pipeline, with the same behavior | — |

## 5. Security

| Decision | Title | ADR |
|---|---|---|
| D-013 | Public repository | — |
| D-199 | The control code resists being guessed | — |
| D-200 | Security tab: each attack, its barrier and its test | — |
| D-202 | A single author gate: the pipeline button appears only after the code | — |
| D-207 | The control code is no longer a password field | — |
| D-249 | Stage 8: security as a process, its procedure and monitoring | — |
| D-254 | Security architecture as a diagram of trust zones | — |

## 6. Operations and observability

| Decision | Title | ADR |
|---|---|---|
| D-017 | Weekly report and warnings with GitHub's own tools | — |
| D-038 | Pipeline control center inside the panel | — |
| D-149 | The manual run is a visible button, with its result | — |
| D-165 | Operations center: the Tuesday journey is its own guide | — |
| D-243 | Stage 5: CI/CD diagram with its definition, from the real workflows | — |
| D-246 | Stage 7: the orchestration of the weekly workflow, inside the CI/CD diagram | — |
| D-255 | Deployment as a real deployment diagram, and first in the Operations center | — |
| D-275 | Monitoring: the signals hang from the weekly load, not from eight identical chains | — |

## 7. Panel

| Decision | Title | ADR |
|---|---|---|
| D-096 | Single navigation through a side menu, without tabs | — |
| D-166 | The panel is read in landscape on phones | — |
| D-264 | Weekly summary: the header is a single bar | — |
| D-267 | The main pages with a single header bar; Prices and inflation with its reading | — |
| D-274 | The measure is the real browser window (1440 × 790); Quality and audit fits in it | — |
| D-281 | A single component for buttons and links | — |
| D-283 | Spanish and English: the language is chosen like the theme, and the documents exist in both languages | — |
| D-284 | Spanish and English, second layer: each page is translated as it is drawn | — |
| D-285 | The app map: the whole system in one view | — |

## 8. Documentation

| Decision | Title | ADR |
|---|---|---|
| D-151 | The documentation is the PRD, the SAD and the ADR | — |
| D-210 | Documents of at most two pages | — |
| D-248 | Stage 10: documents to standard, and the PDF is the printed page | — |
| D-269 | The documents, reviewed against the product: PRD, SAD, ADR and Scalability | — |
| D-278 | The documentation is separated from the history of the project | — |
| D-279 | Professional documentation: header, contents, glossary and history in each document | — |
| D-280 | Diagrams and logos of the documents without a background; the PDF always on a white sheet | — |
| D-282 | A single «Documents» folder in the menu | — |

## 9. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-25 | First version (D-279, professional documentation) |
