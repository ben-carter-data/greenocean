# Software Quality Assurance Plan (SQAP)

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Software Quality Assurance Plan (SQAP) |
| Version | 1.10 |
| Date | 2026-11-02 |
| Status | Current |
| Owner | The author |
| Purpose | Say which quality GreenOcean looks after, how it measures it, who decides and what happens when something fails. |
| Audience | Management, analysts, technical reviewers and anyone who wants to know why to trust the figures. |
| Related documents | [Product Requirements Document (PRD)](../negocio/PRD.md) · [Software Architecture Document (SAD)](../arquitectura/SAD.md) · [Test and Security Plan](PLAN_PRUEBAS.md) · [Operations Manual](../operacion/MANUAL.md) · [Glossary](../negocio/GLOSARIO.md) |

## Contents

1. [Why this plan exists](#1-why-this-plan-exists)
2. [Vision and mission](#2-vision-and-mission)
3. [What we measure and why](#3-what-we-measure-and-why)
4. [How we measure it](#4-how-we-measure-it)
5. [What we do not measure and why](#5-what-we-do-not-measure-and-why)
6. [How an indicator reads](#6-how-an-indicator-reads)
7. [Tests that block and tests that inform](#7-tests-that-block-and-tests-that-inform)
8. [Quality reports](#8-quality-reports)
9. [Failure register](#9-failure-register)
10. [Incidents of the data sources](#10-incidents-of-the-data-sources)
11. [Who decides what](#11-who-decides-what)
12. [A self-assessment, not a certificate](#12-a-self-assessment-not-a-certificate)
13. [Glossary](#13-glossary)
14. [Version history](#14-version-history)

## 1. Why this plan exists

This plan says which quality the project looks after, how it measures it and who decides. That way quality does not depend on anyone's memory. It follows the structure of the IEEE 730 standard, adapted to a project with a single author.

## 2. Vision and mission

- **Vision:** that anyone in Chile knows, with official data, how food prices move.
- **Mission:** publish checked, easy-to-read prices every week, and improve the process with every load.

## 3. What we measure and why

We measure two qualities. The first is that of the data we publish, following the ISO/IEC 25012 standard: nobody should see a corrupt, late or badly compared price without knowing it. The second is that of the code that treats the data, following the ISO/IEC 25010 standard: it must be tested, tidy and secure.

[[diagrama:calidades]]

They are the 12 indicators of the quality plan: 8 of the code and 4 of the data. Each one has written down what it measures, why it matters, how it is measured and what to do if it fails. All of that lives in `docs/calidad/metas.json`, and the page «Method and quality» shows it.

They are not the 11 data quality indicators, which are measured on every load on the published database and shown in «Quality and audit». Those protect each publication; the plan's indicators measure the project week by week.

This is how the 11 data indicators look in [[vista:Quality and audit]], each one under the pipeline stop where it is watched:

[[diagrama:calidad]]

## 4. How we measure it

Automated tests measure it: programs that check the work with no one stepping in. They run in the CI, GitHub's server that tests every change, and in every Tuesday load. Each indicator has a threshold, a limit the author set. A threshold is never lowered to let a test pass, and a test is never skipped: the cause is fixed.

## 5. What we do not measure and why

- **Response time:** GitHub's server is shared and its speed changes from one day to the next, so it is no good for measuring. The speed tests keep running on the author's computer as informative (D-341).
- **Browsers:** they left the measurement because the plan measures the minimum that proves quality: the data and the code (D-330). The quality workflow no longer installs browsers.
- **Accessibility:** it was reviewed once and came out with no failures (D-323). It left the weekly measurement for the same reason (D-330).

## 6. How an indicator reads

Each indicator has a goal (the wanted value), an acceptable (the worst value tolerated) and a critical margin (how far past the acceptable it may go before acting at once). With those three values, an indicator is in one of four states.

[[diagrama:estados_calidad]]

The values of each indicator are in `docs/calidad/metas.json`, and the names of the states, in `docs/calidad/politica.json`.

The acceptable of a data indicator is calibrated with the history of the source, not by eye: it marks what is rare in those data. The one of the prices with a valid comparison is 81 %, the 5th percentile of 251 weeks, the same as its goal ([ADR-36](../arquitectura/ADR.md#adr-36--calibrate-the-acceptable-of-the-comparable-prices-with-the-history-of-the-data), D-433). A change of acceptable holds from the next report: the reports already written keep the acceptable they were measured with.

## 7. Tests that block and tests that inform

A test that blocks stops publication if it fails. That is how dbt's data tests and the tests of the dashboard figures work. A test that informs only warns: it must never stop publication.

The weekly load runs only the tests that block for the data: the data and pipeline tests. The screen tests (pages, translations, documents) run in the CI of every push; a screen failure never stops the publication of data (D-366).

The example is F-10 of the failure register. A speed test, which was informative, blocked the weekly load, and the data stopped being updated. The test left the load and the CI, and it stays local as informative (D-341).

## 8. Quality reports

There is only one numbered report: the weekly quality report, one per data week (D-431). The quality workflow makes it only when the weekly load ended in green, with its tests passed and the database published, and proposes it as a pull request (D-363). It measures the 3 data indicators of each load: dbt data tests passed, prices with a valid comparison and rejected rows. The 8 code indicators are checked by the CI of every push: they pass or fail in GitHub Actions, with no report. The days since the last load are shown in the dashboard, not in the report.

The report has four pages: the cover, with the version of this plan it was measured by; the results; the comparison with another report, which warns when the two do not measure the same indicators; and one table of non-conformities and incidents, with the open ones and the ones of that week. The method lives only in this plan. A report is never edited afterwards: if something changes, the next report comes out. If the code indicators are within their acceptable, the pull request is merged by itself and the dashboard shows the report; otherwise it stays open and the author reviews it; if it is still open the week after, the new report replaces it with the same number (D-436). In the dashboard, each report opens as a presentation and downloads as a PDF (D-333, D-347).

A non-conformity of the weekly series closes by itself when a later report brings its indicator back within the acceptable, with the state «resolved automatically, report No. x»; the cause and the action the author wrote stay (D-437).

Reports C-1 to C-7, from 26 to 31 October 2026, are the construction series: they mix code and data, were measured on every push and are never edited. The dashboard shows them apart and does not compare them with the weekly series.


## 9. Failure register

The register, `docs/calidad/plan_mitigacion.json`, keeps every failure the project went through and how it was solved. It helps not to repeat mistakes and shows how each one is corrected.

Each failure has a category (data, code or operation), a station of the git flow (the path of a change, from the idea to the deployment) and its occurrences. What fails in GitHub, the CI or the deployment is in the operation category.

Each occurrence is written in one line per field and in plain language: what happened, the cause, what was done and a comment. The detailed analysis lives in its decision D-xxx (D-354). The Professional view shows what happened and how it was solved; only the Author sees the diagnosis (D-345). Each diagnosed failure is recorded before the change that fixes it is published (D-342).

## 10. Incidents of the data sources

An external incident is a failure of the data sources: ODEPA or the INE. For example, a week that is not published or a file that changes its format. Faced with an incident, the load does not pass its checks and the dashboard keeps the last valid load, with its date in sight. Incidents are recorded in `docs/calidad/incidentes_externos.json`, and their response awaits the author's approval (D-334).

**Late sources (D-356).** We publish up to the last week complete in both sources, filling in nothing. That is how the Dashboard and the indicators read it. The page «Latest data by channel» shows each source's latest week, labelled (D-365). A recent week a source has not published yet does not block the load: it stays as an external incident and the app shows a quiet notice. The load stops only if a week is missing in the middle of the data, or if the source has gone more than 2 weeks without publishing. In that case the Author also gets an urgent alert.

## 11. Who decides what

- **The author:** sets the goals, the acceptables and the margins; approves the report that is not merged by itself; decides each change and each publication.
- **The tools:** measure, compare and propose. They never publish or change a threshold on their own.

## 12. A self-assessment, not a certificate

This plan and its reports are a self-assessment by the author. No external body audits them, and they do not replace a certification. Their value is that every number can be checked against the code and the data.

## 13. Glossary

The acronyms and terms of this document are defined in the [Glossary](../negocio/GLOSARIO.md).

## 14. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-30 | First version of the software quality assurance plan (D-355) |
| 1.1 | 2026-10-30 | Rule for late sources (D-356) |
| 1.2 | 2026-10-30 | The page «Latest data by channel» shows each source's latest week (D-365) |
| 1.3 | 2026-10-30 | The weekly load runs only the data and pipeline tests (D-366) |
| 1.4 | 2026-10-31 | The 12 indicators of the quality plan, apart from the 11 data quality indicators (3); the report is proposed as a pull request after each load (8); vision and mission as in the PRD; the document moves to `docs/calidad/` (D-381, D-384, D-388) |
| 1.5 | 2026-11-01 | One numbered report only, the weekly one of the data, in four pages and only after a load in green; the code is checked by the CI; the construction series C-1 to C-7 (8, D-431) |
| 1.6 | 2026-11-01 | The acceptable and the goal of the comparable prices are calibrated to the 5th percentile of the history, 81 % (6, ADR-36, D-433) |
| 1.7 | 2026-11-01 | The report's pull request is merged by itself if the code is within its acceptable; an open one is replaced by the next report (8, 11, D-436) |
| 1.8 | 2026-11-01 | A non-conformity of the weekly series closes by itself when its indicator is back within the acceptable (8, D-437) |
| 1.9 | 2026-11-02 | «Price overview» is renamed «Dashboard» and leads the menu (D-442) |
| 1.10 | 2026-11-02 | The 11 data indicators are drawn with the flow of «Quality and audit» (3), instead of «The cycle of each week» (D-455) |
