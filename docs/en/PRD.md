# Product Requirements Document (PRD)

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Product Requirements Document (PRD) |
| Version | 3.0 |
| Date | 2026-10-25 |
| Status | Current |
| Owner | The author |
| Purpose | Explain which problem GreenOcean solves, for whom, which questions it answers and what it must meet for its figures to be reliable. |
| Audience | Management, product owners, analysts and technical review. |
| Related documents | [Software Architecture Document (SAD)](SAD.md) · [Architecture Decision Records (ADR)](ADR.md) · [Test and Security Plan](PLAN_PRUEBAS.md) · [Glossary](GLOSARIO.md) |

## Contents

1. [In summary](#1-in-summary)
2. [The problem](#2-the-problem)
3. [Who it is for](#3-who-it-is-for)
4. [Business questions](#4-business-questions)
5. [Requirements](#5-requirements)
6. [Scope](#6-scope)
7. [Screens](#7-screens)
8. [Assumptions, constraints and dependencies](#8-assumptions-constraints-and-dependencies)
9. [Risks](#9-risks)
10. [Acceptance criteria](#10-acceptance-criteria)
11. [Next steps](#11-next-steps)
12. [Glossary](#12-glossary)
13. [Version history](#13-version-history)

## 1. In summary

GreenOcean turns the official food prices of Chile into clear answers, every week and without intervention.

- **What it does:** every Tuesday it downloads the ODEPA prices and the INE CPI, checks them and publishes a panel to consult them.
- **For whom:** price analysts, purchasing, management and anyone who needs to check the figures.
- **What it answers:** what changed during the week, whether a price is normal for the season, how much the consumer pays over the wholesale price, what rose more than inflation and whether the figures are reliable.
- **Why trust it:** every figure can be traced back to the original file, and a load with errors never reaches the panel.

[[diagrama:valor]]

## 2. The problem

Chile's Office of Agricultural Studies and Policies (ODEPA) publishes the wholesale and consumer prices of fruit, vegetables and other foods every week. The National Statistics Institute (INE) publishes the food consumer price index (CPI, «IPC» in Spanish) every month. Both are open and reliable data, but they are not ready to be compared: each series has its own frequency, unit of sale and level of detail, and none of them discounts inflation. Answering whether a price rose in real terms, or whether it is high for the time of year, means downloading the files and crossing them by hand every week.

GreenOcean does that work automatically and leaves each step in view.

## 3. Who it is for

| Profile | What they use it for |
|---|---|
| Pricing analyst | Know whether today's price is normal for the season and which foods rose more than inflation, in today's pesos |
| Purchasing and supply | See how much the consumer pays over the wholesale price of the same product |
| Management | Review what moved during the week and what is out of the ordinary |
| Technical reviewer | Check that the figures are reliable: quality, tests, lineage and documentation |

[[diagrama:casos]]

The panel is read-only and needs no account. On entry the reader chooses a view: the user view shows the business (the dashboard, the weekly summary and prices against inflation) and the professional view, the whole project in order of importance; one click goes from one to the other. The administrator, the author of the project, maintains the code and the secrets, answers ad hoc SQL queries and can launch a manual load with the control code.

## 4. Business questions

Each question names the screen that answers it and the test that recomputes its answer along an independent path.

| ID | Question | Screen that answers it | Evidence |
|---|---|---|---|
| P-1 | Which prices changed this week, and which are unusual? | Weekly summary | `tests/test_reconciliation.py::test_k6_sql_and_python_raise_the_same_alerts`, `tests/test_data_audit.py::test_an_alert_must_be_unusual_and_material` |
| P-2 | Is today's price normal for the season? | SQL queries · Price vs. season | `tests/test_sql_explorer.py::test_p2_the_price_for_the_season_query_matches_a_recomputation_in_pandas` |
| P-3 | How much does the consumer pay over the wholesale price? | SQL queries · Wholesale gap | `tests/test_sql_explorer.py::test_p3_the_wholesale_gap_query_matches_a_recomputation_in_pandas` |
| P-4 | Which foods rose more than inflation? | Prices and inflation | `tests/test_inflation_view.py::test_p4_each_family_change_and_the_ipc_match_a_recomputation_in_sql`, `tests/test_page_bar.py::test_d267_the_reading_of_a_family_is_recomputed_from_its_index` |
| P-5 | Are the figures reliable? | Quality and audit | `tests/test_data_audit.py::test_weekly_prices_rebuild_exactly_from_the_raw_rows`, `tests/test_migration_parity.py::test_every_weekly_price_has_the_same_key_flag_count_and_price` |

## 5. Requirements

Functional requirements (RF) define what the product does; non-functional requirements (RNF), with which qualities. Each one has a measurable criterion and the test that checks it.

[[diagrama:requisitos]]

| ID | Requirement | Measurable criterion | Evidence |
|---|---|---|---|
| RF-01 | Automatic weekly load | A workflow runs every Tuesday at 12:00 UTC (`0 12 * * 2`) | `.github/workflows/semanal.yml`, `tests/test_prd_traceability.py::test_rf01_the_weekly_workflow_runs_on_tuesdays` |
| RF-02 | No row is lost | Rows read = loaded + rejected: difference 0 in every load | `dbt/tests/rnf05_rows_reconcile.sql`, `tests/test_etl_run.py::test_rn11_rows_read_equal_rows_loaded_plus_rows_rejected` |
| RF-03 | Only a valid load is published | If one of the 31 dbt tests fails, the load reads less than 90 % of the previous one or pytest fails on the new database, the served database does not change; GitHub Actions marks the run as failed and emails the author | `tests/test_pipeline_gate.py::test_rf03_a_failed_dbt_build_records_the_failure_and_never_replaces_the_served_database`, `tests/test_pipeline_gate.py::test_rf03_a_load_with_far_fewer_rows_than_the_last_good_one_is_refused`, `.github/workflows/semanal.yml` |
| RF-04 | Real prices next to nominal ones | The factor of each week comes from the CPI of the month of its Monday; the weeks after the last published month are marked as provisional | `tests/test_ipc_audit.py::test_weekly_factor_uses_the_month_of_the_monday_and_the_last_published_month`, `tests/test_ipc_audit.py::test_only_weeks_after_the_last_published_month_are_provisional` |
| RF-05 | Price alerts | An alert needs a change that is unusual for that product and of at least 10 %; SQL and Python raise the same ones | `tests/test_data_audit.py::test_an_alert_must_be_unusual_and_material`, `tests/test_reconciliation.py::test_k6_sql_and_python_raise_the_same_alerts` |
| RF-06 | Open, read-only SQL queries | Every statement that writes is rejected; each query returns at most 5,000 rows and stops after 10 s; the engine reads no files and no network | `tests/test_sql_explorer.py::test_forbidden_statements_are_rejected`, `tests/test_sql_explorer.py::test_result_is_limited_and_flagged`, `tests/test_sql_explorer.py::test_slow_query_is_interrupted`, `tests/test_sql_explorer.py::test_external_access_is_disabled_at_the_engine` |
| RF-07 | Protected manual load | No manual load without the control code: the «Run pipeline now» button appears only after it, and the code is compared in constant time | `tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code`, `tests/test_control.py::test_d249_there_is_no_limit_of_attempts_and_the_comparison_is_constant_time` |
| RF-08 | Weekly report | Each published load leaves a report with its status and the alerts of the week, as an issue of the repository | `.github/workflows/semanal.yml`, `tests/test_report.py::test_report_shows_the_load_status_and_the_alert_of_the_week` |
| RNF-01 | Zero cost and no expiry | No paid service; only permanent free plans ([ADR-31 · Do not use a cloud data warehouse](ADR.md#adr-31--do-not-use-a-cloud-data-warehouse)) | `docs/ADR.md` |
| RNF-02 | Every figure can be checked | Weekly prices are rebuilt from the raw rows and along a second, independent path without dbt: difference 0 | `tests/test_data_audit.py::test_weekly_prices_rebuild_exactly_from_the_raw_rows`, `tests/test_migration_parity.py::test_every_weekly_price_has_the_same_key_flag_count_and_price`, `tests/test_data_audit.py::test_the_panel_reproduces_the_reference_figures_of_its_week` |
| RNF-03 | Security | No secret in the repository; the weekly workflow has only the permissions it uses; the panel cannot write to the database | `tests/test_security.py::test_no_secret_is_tracked_by_git`, `tests/test_security.py::test_the_weekly_job_has_least_privilege`, `tests/test_dashboard.py::test_c03_every_result_is_read_only_and_runs_only_stored_queries` |
| RNF-04 | Quality watched on every change | pytest and the dbt compilation run on every push; the 11 quality indicators are measured on every load, and one outside its threshold changes the verdict | `.github/workflows/pruebas.yml`, `tests/test_quality_audit.py::test_a_degraded_measure_turns_its_indicator_and_the_verdict_red` |
| RNF-05 | Readable on computer, tablet and phone | No page scrolls sideways between 1024 × 768 and 1920 × 1080, on a portrait tablet (768 × 1024) or on a landscape phone (844 × 390); in portrait, the panel asks to turn the phone | `tests/medicion/medir.cjs` |
| RNF-06 | Each main page on one screen | In the browser window of a 1440 × 900 screen (1440 × 790 usable) and at 1920 × 1000, each main page is seen whole, without scrolling | `tests/medicion/medir.cjs` |

## 6. Scope

| Includes | Excludes |
|---|---|
| Integration of ODEPA prices since 2022 and of the INE food CPI | Comparison between supermarket chains or stores |
| Unit conversion, weekly aggregation and real-price calculation | Price forecasting or explanation of its causes |
| Rejection of invalid rows with their reason, and an audit of every figure | Purchase recommendations for consumers |
| Read-only panel with its documentation | Data changes by the users |

Today the database holds 814,610 weekly prices over 250 weeks (2022-01-03 to 2026-10-12), 9 regions, 8 channels, 1,609 product keys and 202 months of the CPI. The last load read 2,521,012 rows: 2,520,811 loaded and 201 rejected with their reason.

## 7. Screens

Real captures of the panel, one per color theme.

[[diagrama:mockups]]

## 8. Assumptions, constraints and dependencies

**Assumptions**
- The national price is a simple average of the regions, not weighted by population or sales, because no open source publishes those weights. Each weekly change compares only the regions with a price in both weeks.
- The indicators describe what happened; they do not forecast or attribute causes. A family rising with the CPI does not prove that inflation moved it: the food CPI is computed from those same prices.

**Constraints**
- Zero cost: only the permanent free plans of GitHub and Streamlit Community Cloud.
- No figure is invented or interpolated, and the history is never deleted.
- The last month of the CPI may not be published yet: those weeks use the last available month and are marked as provisional.

**Dependencies**

| Dependency | What for | If it fails |
|---|---|---|
| ODEPA (datos.odepa.gob.cl) | Wholesale and consumer prices | The load does not pass its checks and the panel keeps the last valid load |
| INE | Food CPI | The last CPI read is kept; the new weeks stay provisional |
| GitHub (repository, Actions, releases) | Code, execution of the load and served database | There is no new load; the panel keeps the database it already has |
| Streamlit Community Cloud | Publication of the panel | The panel is not available; no data is lost |

## 9. Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| ODEPA changes the format of its files | Medium | High | The quality gates reject a load that was read wrongly ([SAD, the load of each week](SAD.md#4-the-load-of-each-week)) |
| A correlation is read as a cause | Medium | Medium | The panel and this document warn about it next to each comparison with the CPI |
| The terms of a free plan change | Low | High | The pipeline runs the same on any machine with Python 3.11 or 3.12 |
| A single maintainer | High | Medium | Operation documented in the [Operations Runbook](MANUAL.md) and automated tests on every change |

## 10. Acceptance criteria

| Criterion | How it is verified |
|---|---|
| Each business question has an existing screen and evidence | `tests/test_prd_traceability.py` |
| Each requirement has a measurable criterion and existing evidence | `tests/test_prd_traceability.py` |
| The full suite passes on every push | `.github/workflows/pruebas.yml` |
| The figures of this document match the served database | `tests/test_documents.py::test_d210_the_prd_figures_match_the_served_database` |
| Each main page fits one screen | `tests/medicion/medir.cjs` at 1440 × 790 and 1920 × 1000 |

## 11. Next steps

Adding the weather by region, and the conditions under which a cloud data warehouse would be justified, are described in the [SAD, capacity and growth](SAD.md#9-capacity-and-growth).

## 12. Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## 13. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-18 | First version: the project documentation becomes the PRD, the SAD and the ADR (D-151, documentation in three documents) |
| 1.1 | 2026-10-19 | Planned evolution towards dbt, DuckDB, Parquet and the CPI (D-152, stack evolution); alerts with two quotes per week (D-158, price alerts) |
| 1.2 | 2026-10-20 | Figures aligned with the database of the week of 2026-10-12; own diagrams (D-205, document diagrams); «Technical reviewer» profile (D-208) |
| 1.3 | 2026-10-21 | Engineering-document wording and bounded length (D-210, D-214 and D-217, document wording) |
| 1.4 | 2026-10-23 | Use cases and requirements traceability (D-240); question P-4 (D-244); RF-03 with its test (D-245); the download is the printed page (D-248) |
| 1.5 | 2026-10-24 | Consistency review (D-252); objectives, question P-5, fourteen requirements and assumptions (D-269, documents reviewed against the product) |
| 2.0 | 2026-10-25 | Standard structure: header, contents, constraints and dependencies, risks, acceptance criteria, glossary and history; screen measure corrected to 1440 × 790 usable (D-279, professional documentation) |
| 3.0 | 2026-10-25 | Reading from the most important to the least: summary, problem, users, questions and requirements first; diagrams of the value and of the requirements (D-290, documents for every reader) |
