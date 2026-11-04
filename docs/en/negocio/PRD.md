# Product Requirements Document (PRD)

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Product Requirements Document (PRD) |
| Version | 3.43 |
| Date | 2026-11-03 |
| Status | Current |
| Owner | The author |
| Purpose | Explain which problem GreenOcean solves, for whom, which questions it answers and what it must meet for its figures to be reliable. |
| Audience | Management, product owners, analysts and technical reviewers. |
| Related documents | [Software Architecture Document (SAD)](../arquitectura/SAD.md) · [Architecture Decision Records (ADR)](../arquitectura/ADR.md) · [Test and Security Plan](../calidad/PLAN_PRUEBAS.md) · [Glossary](GLOSARIO.md) |

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

GreenOcean publishes every week how food prices move in Chile. It takes the official data of ODEPA and the INE, checks it and puts it in a panel anyone can open. Nobody has to download files or cross them by hand.

- **Vision:** that anyone in Chile knows, with official data, how food prices move.
- **Mission:** publish checked, easy-to-read prices every week, and improve the process with every load.
- **What it answers:** what changed this week, whether a price is normal for the season, how much the consumer pays over the wholesale price and which foods rose more than inflation.
- **For whom:** whoever buys or sells food, whoever reports on prices and whoever reviews how the project is built.
- **Why trust it:** every figure can be traced back to the original file, and a load with errors does not reach the panel.

## 2. The problem

Chile's Office of Agricultural Studies and Policies (ODEPA) publishes the wholesale and consumer prices of fruit, vegetables and other foods every week. The National Statistics Institute (INE) publishes the food consumer price index (CPI, «IPC» in Spanish) every month. Both are open and reliable data, but they cannot be compared as they arrive. Each series has its own frequency, unit and level of detail, and none of them discounts inflation. To know whether a price rose in real terms, or whether it is high for the time of year, someone has to download the files and cross them by hand every week.

GreenOcean does that work by itself, every Tuesday, and leaves each step in view.

[[diagrama:ciclo_semanal]]

## 3. Who it is for

### 3.1 Stakeholders

Each stakeholder has a question, a decision that depends on the answer and a page where they find it. In «BA and BI analysis», the tab [[vista:Insights]] answers their questions with today's figures and the tab [[vista:Stakeholders]] places them on the interest map (3.4).

| Stakeholder | Who they are | What they ask | What decision it helps them make | Where the answer is |
|---|---|---|---|---|
| People and families | Whoever buys the food for their home | Which foods are going up? | What to buy before going shopping | [[vista:Weekly]] |
| Restaurants and grocery stores | Whoever buys food to cook or to sell | When and where is it best to buy? | When and in which channel to buy | [[vista:Weekly]] |
| Wholesalers, farmers and market vendors | Whoever sells wholesale or at the street market | How does the wholesale price compare with the consumer price? | At what price to sell | [[vista:Weekly]] |
| Journalists and economists | Whoever reports on the economy or analyzes it | Which foods rise more than inflation, according to official data? | What to report, with figures that can be checked | [[vista:Prices and inflation]] · [[vista:Insights]] |
| Technical teams and recruiters | Whoever designs data systems or evaluates who builds them | How is a reliable data pipeline built and operated? | Which practices to follow or whom to hire | [[vista:Pipeline and lineage]] · [[vista:Method and quality]] · [[vista:Git workflow]] |

### 3.2 Usage profiles

The panel has three profiles, the same as the window that asks for the view on entry. The stakeholders of 3.1 come in through one of them.

| Profile | What they use it for |
|---|---|
| User | The business, with no account: the section «Business · BA and BI», with its two dashboards: Weekly, guided in four steps, and BA and BI analysis, with its tabs Monthly, Historical, Prices and inflation, Insights, Stakeholders and Method |
| Professional | The whole project, with no account, ordered by its role (Data Eng, BA, BI, DevOps or Security), with the read-only SQL queries |
| Author | The same as Professional, plus «Operations center», «GitHub Actions» and «Settings», the «Action required» alert, the manual load and the links to the GitHub repository (D-500); it asks for the control code, which is never in the repository |

That window asks once per tab, and the view stays even if the tab reloads or the server forgets the session (D-430, D-454). «View: … · Change», under the logo, changes the view; a click on the logo does the same (D-373). Leaving Author closes its session, and the Author view closes by itself after 30 minutes without activity (D-395). The author maintains the code and the secrets and answers ad hoc SQL queries.

### 3.3 What we heard

Real users made two reviews: one of usability and one of architecture. Each change that came out of them has its decision.

| Review | What we heard | What changed | Decision |
|---|---|---|---|
| Usability review | They did not know where to start reading the Weekly dashboard | The Weekly dashboard reads in three numbered steps; steps 2 and 3 wait for the one before, with a padlock, in every view; the search stands out | D-352, D-372 |
| Architecture review | By a real user, no changes requested | — | — |

### 3.4 Interest map

Each stakeholder sits on a ring according to **how much their decision depends on these data and how often they use them**. GreenOcean is the center; ODEPA and the INE, which provide the data, sit on the outer ring. It is the map of the tab [[vista:Stakeholders]] of «BA and BI analysis» (D-444, D-456):

[[diagrama:interes]]

| Stakeholder | Interest | Why | Opens |
|---|---|---|---|
| Restaurants and grocery stores | High | They buy every week, and the channel and the week they buy in change their cost | [[vista:Weekly]] |
| Wholesalers, farmers and market vendors | High | Every week they set their selling price against the wholesale and the consumer price | [[vista:Weekly]] |
| Journalists and economists | High | Every story on prices needs an official figure that can be checked | [[vista:Prices and inflation]] |
| People and families | Medium | It helps them before they shop, but what they buy does not depend on these data alone | [[vista:Weekly]] |
| Technical teams and recruiters | Medium | They review it now and then, for how it is built, not for the week's figures | [[vista:Pipeline and lineage]] |
| ODEPA | Low | It publishes the prices: it provides the data, it does not decide with them | [[vista:Weekly]] |
| INE | Low | It publishes the food CPI: it provides the data, it does not decide with them | [[vista:Prices and inflation]] |

## 4. Business questions

Each question has the screen that answers it and a test that recomputes the answer along another path.

| ID | Question | Screen that answers it | Evidence |
|---|---|---|---|
| P-1 | Which prices changed this week, and which are unusual? | Weekly | `tests/test_reconciliation.py::test_k6_sql_and_python_raise_the_same_alerts`, `tests/test_data_audit.py::test_an_alert_must_be_unusual_and_material` |
| P-2 | Is today's price normal for the season? | SQL queries · Price vs. season | `tests/test_sql_explorer.py::test_p2_the_price_for_the_season_query_matches_a_recomputation_in_pandas` |
| P-3 | How much does the consumer pay over the wholesale price? | SQL queries · Wholesale gap | `tests/test_sql_explorer.py::test_p3_the_wholesale_gap_query_matches_a_recomputation_in_pandas` |
| P-4 | Which foods rose more than inflation? | BA and BI analysis (Prices and inflation) | `tests/test_inflation_view.py::test_p4_each_family_change_and_the_ipc_match_a_recomputation_in_sql`, `tests/test_page_bar.py::test_d267_the_reading_of_a_family_is_recomputed_from_its_index` |
| P-5 | Are the figures reliable? | Quality and audit | `tests/test_data_audit.py::test_weekly_prices_rebuild_exactly_from_the_raw_rows`, `tests/test_migration_parity.py::test_every_weekly_price_has_the_same_key_flag_count_and_price` |

## 5. Requirements

Functional requirements (RF) say what the product does. Non-functional requirements (RNF) say how it must do it. Each one has a measurable criterion and the test that checks it.

[[diagrama:requisitos]]

| ID | Requirement | Measurable criterion | Evidence |
|---|---|---|---|
| RF-01 | Automatic weekly load | A workflow runs every Tuesday at 12:07 UTC, with another attempt every 15 minutes until 14:52 and every hour until 02:07 if GitHub is late | `.github/workflows/semanal.yml`, `tests/test_prd_traceability.py::test_rf01_the_weekly_workflow_runs_on_tuesdays` |
| RF-02 | No row is lost | Rows read = loaded + rejected: difference 0 in every load | `dbt/tests/rnf05_rows_reconcile.sql`, `tests/test_etl_run.py::test_rn11_rows_read_equal_rows_loaded_plus_rows_rejected` |
| RF-03 | Only a valid load is published | If one of the 31 dbt tests fails, the load reads less than 90 % of the previous one, pytest fails on the new database, a week is missing in the middle of the data or a source has gone more than 2 weeks without publishing, the DuckDB database does not change; GitHub Actions marks the run as failed and emails the author. Publication goes up to the last week complete in both sources, filling nothing in; the speed tests inform and never block | `tests/test_pipeline_gate.py::test_rf03_a_failed_dbt_build_records_the_failure_and_never_replaces_the_served_database`, `tests/test_pipeline_gate.py::test_rf03_a_load_with_far_fewer_rows_than_the_last_good_one_is_refused`, `.github/workflows/semanal.yml`, `tests/test_late_sources.py::test_d356_a_hole_in_the_middle_of_the_data_stops_the_load`, `tests/test_late_sources.py::test_d356_a_recent_week_one_source_has_not_published_does_not_stop_the_load_and_waits` |
| RF-04 | Real prices next to nominal ones | The factor of each week comes from the CPI of the month of its Monday; the weeks after the last published month are marked as provisional | `tests/test_ipc_audit.py::test_weekly_factor_uses_the_month_of_the_monday_and_the_last_published_month`, `tests/test_ipc_audit.py::test_only_weeks_after_the_last_published_month_are_provisional` |
| RF-05 | Price alerts | An alert needs a change outside the average ± 2 deviations of its previous 12 weeks, of at least 10 % and with two quotes in each week; SQL and Python raise the same ones. Rises are sharp rises, in red, and drops are sharp drops, in green (D-477). In «Semanal», between step 2 and step 3, «▲ n sharp rises» and «▼ n sharp drops» of the chosen family show only those products in step 3, without opening windows; the search, beside them, looks within the alert chosen (D-489, D-491, D-492). With a region chosen, the same rule applies to the price of that region; with all of Chile, to the national price (D-499) | `tests/test_data_audit.py::test_an_alert_must_be_unusual_and_material`, `tests/test_reconciliation.py::test_k6_sql_and_python_raise_the_same_alerts` |
| RF-06 | Open, read-only SQL queries | Every statement that writes is rejected; each query returns at most 5,000 rows and stops after 10 s; the engine reads no files and no network | `tests/test_sql_explorer.py::test_forbidden_statements_are_rejected`, `tests/test_sql_explorer.py::test_result_is_limited_and_flagged`, `tests/test_sql_explorer.py::test_slow_query_is_interrupted`, `tests/test_sql_explorer.py::test_external_access_is_disabled_at_the_engine` |
| RF-07 | Protected manual load | No manual load without the control code: the «Run pipeline now» button appears only after it, the code is compared in constant time and, after 3 failures, each try waits 2 s, twice as long after each new failure, up to 15 min. The load is followed in a window that does not close by itself, can be minimized or cancelled, shows the log and stops asking after 20 minutes | `tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code`, `tests/test_control.py::test_d393_after_three_failures_every_door_waits_twice_as_long_up_to_fifteen_minutes`, `tests/test_dashboard.py::test_d351_the_window_cannot_be_dismissed_minimizing_does_not_cancel_and_cancel_asks_first` |
| RF-08 | Weekly report | Each published load leaves a report with its status and the alerts of the week, as an issue of the repository; the previous one is closed, so only the latest stays open (D-438) | `.github/workflows/semanal.yml`, `tests/test_report.py::test_report_shows_the_load_status_and_the_alert_of_the_week` |
| RF-09 | The view is chosen and the author's part is protected | Every new visit (a new tab) asks for the view, and after that only «View: … · Change» or the logo open the window again; no address opens the author's part; every reload of the tab (opening or printing a document, changing the theme, a link, F5) keeps the view; the Author's, only with a ticket the server issues and checks and that expires with the Author's session | `tests/test_actions_page.py::test_d339_a_fresh_visit_or_a_reload_never_reaches_the_author_part_whatever_the_address_says`, `tests/test_view_switch.py::test_d353_leaving_the_author_view_closes_the_author_session_and_coming_back_asks_for_the_key`, `tests/test_app_reloads.py::test_d357_a_tab_with_nothing_kept_asks_for_the_view`, `tests/test_app_reloads.py::test_d427_the_author_comes_back_after_a_reload_the_app_makes_only_with_a_ticket_the_server_issued` |
| RNF-01 | Zero cost and no expiry | No paid service; only permanent free plans ([ADR-31 · Do not use a cloud data warehouse](../arquitectura/ADR.md#adr-31--do-not-use-a-cloud-data-warehouse)) | `docs/arquitectura/ADR.md` |
| RNF-02 | Every figure can be checked | Weekly prices are rebuilt from the raw rows and along a second, independent path without dbt: difference 0 | `tests/test_data_audit.py::test_weekly_prices_rebuild_exactly_from_the_raw_rows`, `tests/test_migration_parity.py::test_every_weekly_price_has_the_same_key_flag_count_and_price`, `tests/test_data_audit.py::test_the_panel_reproduces_the_reference_figures_of_its_week` |
| RNF-03 | Security | No secret in the repository; the weekly workflow has only the permissions it uses; the panel cannot write to the database | `tests/test_security.py::test_no_secret_is_tracked_by_git`, `tests/test_security.py::test_the_weekly_job_has_least_privilege`, `tests/test_sql_explorer.py::test_read_only_statements_are_accepted` |
| RNF-04 | Quality watched on every change | pytest and the dbt compilation run on every push. The 11 data quality indicators are measured on every load, and one outside its threshold changes the verdict. The 14 indicators of the quality plan are measured every week ([Quality plan](../calidad/PLAN_DE_CALIDAD.md)) | `.github/workflows/pruebas.yml`, `tests/test_quality_audit.py::test_a_degraded_measure_turns_its_indicator_and_the_verdict_red` |
| RNF-05 | Readable on computer, tablet and phone | No page scrolls sideways between 1024 × 768 and 1920 × 1080, on a portrait tablet (768 × 1024) or on a landscape phone (844 × 390); in portrait, the panel asks to turn the phone. At 1024 × 768 vertical scrolling is accepted, without cuts | `tests/medicion/medir.cjs` |
| RNF-06 | Each main page on one screen | In the browser window of a 1440 × 900 screen (1440 × 790 usable), at 1280 × 800 and at 1920 × 1000, each main page is seen whole, without scrolling | `tests/medicion/medir.cjs` |

## 6. Scope

| Includes | Why | Excludes | Why |
|---|---|---|---|
| Integration of ODEPA prices since 2022 and of the INE food CPI | They are the official, open sources (ADR-01); since 2022 there are several years to see seasonality, and further back the risk of format changes grows (D-009) | Comparison between supermarket chains or stores | There is no official source of prices by chain; the only one would be reading the supermarkets' sites, discarded in ADR-01 |
| Unit conversion, weekly aggregation and real-price calculation | Without bringing each price to the kilo and to the week there is no comparison (RN-03, RN-07); the INE CPI discounts inflation (ADR-33) | Price forecasting or explanation of its causes | With public weekly data and no forecasting question, a model adds nothing (D-019); the indicators describe what happened and attribute no causes (section 8) |
| Rejection of invalid rows with their reason, and an audit of every figure | A zero price or an impossible date is not used, but never deleted in silence (RN-11); every figure is rebuilt from the raw rows (RNF-02) | Purchase recommendations for consumers | The panel describes what happened to prices; recommending what to buy demands a judgement about each person that public data does not give |
| Read-only panel with its documentation | A public panel, with no account and no cost (ADR-02); the documents leave every decision and every figure in view (RNF-02) | Data changes by the users | The data comes only from the official sources and the database opens read-only: nobody can change a figure (RF-06, RNF-03) |
| Publication up to the last week complete in both sources | The Weekly dashboard compares wholesale and consumer in the same week; a half week would give incomplete figures (D-356) | Filling in a week a source has not published yet | An invented figure cannot be recomputed from the source; the load waits for the source to publish (D-356) |

With the load of 2026-10-31, the database holds 821,072 weekly prices over 252 weeks (from Jan 3–9, 2022 to Oct 26–Nov 1, 2026), 9 regions, 8 channels, 1,613 product keys and 202 months of the CPI. That load read 2,541,374 rows: 2,541,173 loaded and 201 rejected with their reason. The database grows every Tuesday; the figures of the day are in the panel.

## 7. Screens

These are six real captures, of 2026-11-02, of five main pages and in the four color themes. The Weekly dashboard appears twice: as the User sees it and as the Professional sees it. The dark theme is the one on entry.

- **Menu:** five sections: Business · BA and BI, Data engineering, DevOps and security, Stack and evidence, and Quality. The first gathers, under the title «Dashboards», two tiles with a dashboard icon, which stay in sight even when the section folds: Weekly and BA and BI analysis (D-442, D-453, D-456, D-459, D-494). The app opens with the menu open; on going to a dashboard or a page of diagrams the menu folds to give them the width, and the button that opens it beats in green (D-462, D-463).
- **Weekly:** it reads in four numbered steps. First a region or all of Chile is chosen; then, if wished, a channel; then a family, and last its products are shown. Each step opens when the one before is done; the channel is optional and without it every channel is shown (D-494). The steps always stay together on one screen; the products table fills panel 4, scrolls by itself and is enlarged with its own button (D-446, D-447). With «The whole basket», the table names each product's family (D-478), and the «i» of each step says how each figure is computed: against which week, with which median, with which threshold and in which scope (D-480).
- **Channel (step 2 of Weekly):** each channel with its 3D icon in its own colours (D-453) and the median of its change. On choosing one, Weekly shows only its prices and its latest published week, even if the other source has not published that week yet, and says which families that channel publishes (D-404 to D-406, D-494).
- **BA and BI analysis:** six tabs (D-456, D-457). «Monthly» is one period, the last 12 months or one year, month by month: five key figures (price change, against the CPI, consumer–wholesale gap, price alerts and biggest monthly rise), three charts (price month by month, change of each month and price alerts by month) and the table by family. «Historical» is the whole history, from January 2022 to the last month the INE published: five key figures (change since January 2022, against the CPI, year of the biggest rise, cheapest month and price alerts), three charts (price since January 2022, change of each year and season) and the table by family. Each chart says which months it shows, and its green magnifier opens it large, with what it measures and what follows from it; each figure explains on hover how it is computed. The other four are Prices and inflation, Insights, Stakeholders and Method. Above the tabs, a green panel says what is being shown, from which month to which and why it starts and ends there; it follows the tab and the period (D-458). «Monthly» and «Historical» start by family, with «The whole basket» by default; the «Product» selector goes down to one of its products, computed with the family's rule, and the table shows the family with its products under it (D-478).
- **Stack and evidence:** two views. «Tools» explains each tool; «Live system flow» shows the real pieces, what they say to each other and the running load (D-412).

[[diagrama:mockups]]

## 8. Assumptions, constraints and dependencies

**Assumptions**
- The national price is a simple average of the regions. It is not weighted by population or sales, because no open source publishes those weights. Each weekly change compares only the regions with a price in both weeks.
- The indicators describe what happened. They do not forecast or attribute causes. A family rising in step with the CPI does not prove that inflation moved it, because the food CPI is computed from those same prices.

**Constraints**
- Zero cost: only the permanent free plans of GitHub and Streamlit Community Cloud.
- No figure is invented or interpolated, and the history is never deleted.
- The last month of the CPI may not be published yet: those weeks use the last available month and are marked as provisional.

**Dependencies**

| Dependency | What for | If it fails |
|---|---|---|
| ODEPA (datos.odepa.gob.cl) | Wholesale and consumer prices | The load does not pass its checks and the panel keeps the last valid load |
| INE | Food CPI | The last CPI read is kept; the new weeks stay provisional |
| GitHub (repository, Actions, releases) | Code, execution of the load and DuckDB database | There is no new load; the panel keeps the database it already has |
| Streamlit Community Cloud | Publication of the panel | The panel is not available; no data is lost |

## 9. Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| ODEPA changes the format of its files | Medium | High | The quality gates reject a load that was read wrongly ([SAD, the load of each week](../arquitectura/SAD.md#4-the-load-of-each-week)) |
| A correlation is read as a cause | Medium | Medium | The panel and this document warn about it next to each comparison with the CPI |
| The terms of a free plan change | Low | High | The pipeline runs the same on any machine with Python 3.11 or 3.12 |
| A single maintainer | High | Medium | Operation documented in the [Operations Runbook](../operacion/MANUAL.md) and automated tests on every change |
| GitHub disables the scheduled workflows of a public repository after 60 days without activity; its documentation does not define what counts as activity nor whether the bot's weekly commit does | Low | High | Proposal (D-439), not implemented: not depending on that rule. «Settings» would read the state of `semanal.yml` from the GitHub API (`active` or `disabled_inactivity`), the «Action required» alert would warn the Author and a button would enable it again with `GITHUB_TOKEN`; GitHub also warns by email before disabling it |
| Streamlit Community Cloud puts the app to sleep when it has no visits, whatever the commits; the visitor sees the sleeping app's screen and has to wake it up | High | Medium | Proposal (D-439), not implemented: `README.md` and the portfolio link warn that the app may take a moment to wake up and show the real captures of `docs/img/`, so the project shows even while it sleeps. Not verified: the exact sleep delay and whether an automatic visit keeps it awake |

## 10. Acceptance criteria

| Criterion | How it is verified |
|---|---|
| Each business question has an existing screen and evidence | `tests/test_prd_traceability.py` |
| Each requirement has a measurable criterion and existing evidence | `tests/test_prd_traceability.py` |
| The full suite passes on every push | `.github/workflows/pruebas.yml` |
| The figures of this document match the DuckDB database | `tests/test_documents.py::test_d210_the_prd_figures_match_the_served_database` |
| Each main page fits one screen | `tests/medicion/medir.cjs` at 1440 × 790 and 1920 × 1000 |

## 11. Next steps

Adding the weather by region, and the conditions under which a cloud data warehouse would be justified, are described in the [SAD, capacity and growth](../arquitectura/SAD.md#9-capacity-and-growth).

A future improvement of the live flow (D-415): each piece of [[vista:Stack and evidence]] would open its mini architecture, at its C4 zoom level. It would show what it is, what it does here, why that tool, what goes in and what comes out; GitHub, the weekly load, dbt, the app and security would show their inner path, for example GitHub Actions: trigger → job → steps → result.

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
| 3.1 | 2026-10-30 | Vision and mission; the three views and the «Vista» indicator (RF-09); late sources and informative tests in RF-03; the manual load window in RF-07; the Quality section, dark theme and the overview in three steps (D-340 to D-357) |
| 3.2 | 2026-10-30 | The page «Latest data by channel» (D-365) |
| 3.3 | 2026-10-31 | Stakeholders (3.1) and usage profiles (3.2), with their page in the panel (D-376) |
| 3.4 | 2026-10-31 | What we heard (3.3), the why of the scope (6), the weekly cycle (2) and the page «Business and systems analysis» (D-377) |
| 3.5 | 2026-10-31 | The reading order of the section «Business · BA and BI» in the menu (7, D-378) |
| 3.6 | 2026-10-31 | Wording reviewed; figures of the load of 2026-10-31 (6); the three views, each with what it sees (3.2); the full price alert (RF-05); the data quality indicators and those of the quality plan (RNF-04); new captures (7, D-392); the document moves to `docs/negocio/` (D-381, D-385, D-388) |
| 3.7 | 2026-11-01 | One screen also at 1280 × 800 (RNF-06); at 1024 × 768 vertical scrolling is accepted, without cuts (RNF-05, D-407) |
| 3.8 | 2026-11-01 | The mini architectures of the live flow, as a future improvement (11, D-415) |
| 3.9 | 2026-11-01 | The Author view with «Settings» (3.2); the Overview that folds its steps, the channel cards and the live flow of «Stack and evidence» (7, D-404 to D-417) |
| 3.10 | 2026-11-01 | RF-09: the reloads the app makes also keep the Author's view, with a one-time ticket (D-427) |
| 3.11 | 2026-11-01 | RF-09: the view is kept on Streamlit Community Cloud too, which loads the page twice; the Author's ticket expires with the session (D-428) |
| 3.12 | 2026-11-01 | RF-09: the view is chosen once per tab; every reload keeps it, F5 and the link of the «Action required» alert too (D-430) |
| 3.13 | 2026-11-01 | RF-08: opening the weekly report closes the previous one (D-438) |
| 3.14 | 2026-11-01 | Two abandonment risks, with their proposed mitigation: workflows disabled for inactivity and the sleeping app (9, D-439) |
| 3.15 | 2026-11-02 | «Price overview» is renamed «Dashboard» and leads the menu (D-442) |
| 3.16 | 2026-11-02 | Interest map: each stakeholder on a ring (high, medium, low) with its reason (3.4, D-444) |
| 3.17 | 2026-11-02 | New captures of the six screens, with the current Dashboard and menu (7, D-445) |
| 3.18 | 2026-11-02 | The Dashboard no longer folds steps 1 and 2: the overview stays whole, and capture M-1 shows it that way (7, D-446) |
| 3.19 | 2026-11-02 | «Latest data by channel» is a second tile under the Dashboard, and each channel behaves exactly like the Dashboard, without folding its steps (7, D-447, D-452) |
| 3.20 | 2026-11-02 | The two dashboards open the section «Business · BA and BI», and each channel card carries its 3D icon (7, D-453) |
| 3.21 | 2026-11-02 | The diagrams are the app's: the weekly cycle of the «Process» block of «Business and systems analysis» (2) and the map of «Stakeholders» (3.4); «From data to decision» and the use cases, which named profiles the panel does not have, are retired; 3.2 is the panel's three profiles; «served database» becomes «DuckDB database» (D-455) |
| 3.22 | 2026-11-02 | «BA and BI analysis» gathers in tabs the history of prices, Prices and inflation, Insights, Stakeholders and the method; P-4 is seen in its tab (3.1, 3.2, 3.4, 4, 7, D-456) |
| 3.23 | 2026-11-02 | «BA and BI analysis» splits the history of prices into «Monthly», one period month by month, and «Historical», from January 2022 to the last month by year and season; each chart says its months and, on hover, what it measures and what follows from it (3.2, 7, D-457) |
| 3.24 | 2026-11-02 | A green panel above the tabs of «BA and BI analysis» says what is shown, from which month to which and why, by tab and period (7, D-458) |
| 3.25 | 2026-11-02 | The three dashboards of «Business · BA and BI» go under the title «Dashboards», and the first, the week's, is called «Weekly» (3.1 to 3.4, 4, 6, 7, D-459) |
| 3.26 | 2026-11-02 | In «BA and BI analysis» the cards are thinner, the months read in two short lines and a green magnifier opens each chart large (7, D-460) |
| 3.27 | 2026-11-02 | The three dashboards open with the menu folded and the button that opens it beats in green (7, D-462) |
| 3.28 | 2026-11-02 | The app opens with the menu open; it folds on going to a dashboard or a page of diagrams (7, D-463) |
| 3.29 | 2026-11-03 | The quality plan grows to 14 indicators: missing regions or channels and atypical prices of the week (RNF-04, D-475) |
| 3.30 | 2026-11-03 | Price alerts split into sharp rises and sharp drops (RF-05, D-477) |
| 3.31 | 2026-11-03 | The views start by family and go down to the products; each figure says how it is computed (D-478, D-480) |
| 3.32 | 2026-11-03 | The weekly load has three attempts on Tuesday (RF-01, D-485) |
| 3.33 | 2026-11-03 | The weekly load tries every 15 minutes until noon and every hour until Tuesday night (RF-01, D-487) |
| 3.34 | 2026-11-03 | Each family's alerts show in step 2 and are listed in step 3, without windows (RF-05, D-489) |
| 3.35 | 2026-11-03 | «Semanal» shows only the week: the table of the last weeks leaves (D-490) |
| 3.36 | 2026-11-03 | The chosen family's alerts, between step 2 and step 3; the order no longer has «Inusuales» (RF-05, D-491) |
| 3.37 | 2026-11-03 | Step 3 is called «Productos»; the search sits by the alerts and looks within the one chosen (RF-05, D-492) |
| 3.38 | 2026-11-03 | Weekly has four steps: the channel becomes step 2, optional, and the section keeps two dashboards (D-494) |
| 3.39 | 2026-11-03 | The products table only orders by «Mayor cambio» or «Nombre»; the channel is step 2 and the alerts, their buttons (D-495) |
| 3.40 | 2026-11-03 | A landscape tablet sees Weekly in columns; «Orden» gets «Subidas» and «Bajadas» back (D-496) |
| 3.41 | 2026-11-03 | «Orden» is replaced by a filter beside the search: «Todo», «Subidas» and «Bajadas» (D-497) |
| 3.42 | 2026-11-03 | With a region chosen in Weekly, the channels, the small line of each family and the alerts are of that region (RF-05, D-499) |
| 3.43 | 2026-11-03 | Only the Author sees the links to the GitHub repository (D-500) |
