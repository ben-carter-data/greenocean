# Software Quality Assurance Plan (SQAP)

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Software Quality Assurance Plan (SQAP) |
| Version | 1.3 |
| Date | 2026-10-30 |
| Status | Current |
| Owner | The author |
| Purpose | Say which quality GreenOcean looks after, how it measures it, who decides and what happens when something fails. |
| Audience | Management, analysts, technical review and anyone who wants to know why to trust the figures. |
| Related documents | [Product Requirements Document (PRD)](PRD.md) · [Software Architecture Document (SAD)](SAD.md) · [Test and Security Plan](PLAN_PRUEBAS.md) · [Operations Manual](MANUAL.md) · [Glossary](GLOSARIO.md) |

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

- **Vision:** That anyone in Chile knows, with official and reliable data, how food prices move.
- **Mission:** Publish verified, clear and easy-to-read prices every week, and improve the process continuously.

## 3. What we measure and why

We measure two qualities. The first is that of the data we publish, following the ISO/IEC 25012 standard: nobody should see a corrupt, late or badly compared price without knowing it. The second is that of the code that treats the data, following the ISO/IEC 25010 standard: it must be tested, tidy and secure.

Each indicator has written down what it measures, why it matters, how it is measured and what to do if it fails. All of that lives in `docs/calidad/metas.json`, and the page «Method and quality» shows it.

[[diagrama:calidades]]

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

## 7. Tests that block and tests that inform

A test that blocks stops publication if it fails. That is how dbt's data tests and the tests of the dashboard figures work. A test that informs only warns: it must never stop publication.

The weekly load runs only the tests that block for the data: the data and pipeline tests. The screen tests (pages, translations, documents) run in the CI of every push; a screen failure never stops the publication of data (D-366).

The example is F-10 of the failure register. A speed test, which was informative, blocked the weekly load, and the data stopped being updated. The test left the load and the CI, and it stays local as informative (D-341).

## 8. Quality reports

Every week everything is measured and a numbered report is built. A report is never edited afterwards: if something changes, the next report comes out. The author reviews each report and approves it before the dashboard shows it (D-331). In the dashboard, each report opens as a presentation and downloads as a PDF (D-333, D-347).

[[diagrama:ciclo_calidad]]

## 9. Failure register

The register, `docs/calidad/plan_mitigacion.json`, keeps every failure the project went through and how it was solved. It helps not to repeat mistakes and shows how each one is corrected.

Each failure has a category (data, code or operation), a station of the git flow (the path of a change, from the idea to the deployment) and its occurrences. What fails in GitHub, the CI or the deployment is in the operation category.

Each occurrence is written in one line per field and in plain language: what happened, the cause, what was done and a comment. The detailed analysis lives in its decision D-xxx (D-354). The professional sees what happened and how it was solved; the diagnosis is the author's (D-345). Each diagnosed failure is recorded before the change that fixes it is published (D-342).

## 10. Incidents of the data sources

An external incident is a failure of the data sources: ODEPA or the INE. For example, a week that is not published or a file that changes its format. Faced with an incident, the load does not pass its checks and the dashboard keeps the last valid load, with its date in sight. Incidents are recorded in `docs/calidad/incidentes_externos.json`, and their response awaits the author's approval (D-334).

**Late sources (D-356).** We publish up to the last week complete in both sources, filling in nothing: that is how the Price overview and the indicators read it; the page «Último dato por canal» shows each source's latest week, labelled (D-365). A recent week a source has not published yet does not block the load: it stays as an external incident and the app shows a quiet notice. The load stops only if a week is missing in the middle of the data, or if the source has gone more than 2 weeks without publishing; in that case the Author also gets an urgent alert.

## 11. Who decides what

- **The author:** sets the goals, the acceptables and the margins; approves each report; decides each change and each publication.
- **The tools:** measure, compare and propose. They never publish or change a threshold on their own.

## 12. A self-assessment, not a certificate

This plan and its reports are a self-assessment by the author. No external body audits them, and they do not replace a certification. Their value is that every number can be checked against the code and the data.

## 13. Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## 14. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-30 | First version of the software quality assurance plan (D-355) |
| 1.1 | 2026-10-30 | Rule for late sources (D-356) |
| 1.2 | 2026-10-30 | The page «Último dato por canal» shows each source's latest week (D-365) |
| 1.3 | 2026-10-30 | The weekly load runs only the data and pipeline tests (D-366) |
