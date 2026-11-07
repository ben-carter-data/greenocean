# Project closure record

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Project closure record |
| Version | 1.1 |
| Date | 2026-11-07 |
| Status | Current |
| Owner | The author |
| Purpose | To leave in writing how the project started, what it set out to show, what was found in the data, what was learned and whom it serves, now that it moves into maintenance. |
| Audience | Recruiters and technical reviewers, data and business professionals, and the author. |
| Related documents | [Product Requirements Document (PRD)](PRD.md) · [Software Architecture Document (SAD)](../arquitectura/SAD.md) · [Software Quality Assurance Plan (SQAP)](../calidad/PLAN_DE_CALIDAD.md) · [Glossary](GLOSARIO.md) |

## Contents

1. [In short](#1-in-short)
2. [How it started](#2-how-it-started)
3. [What was expected and what was found](#3-what-was-expected-and-what-was-found)
4. [How the work was done](#4-how-the-work-was-done)
5. [The roles](#5-the-roles)
6. [What was learned](#6-what-was-learned)
7. [Surprises in the data](#7-surprises-in-the-data)
8. [Strong and weaker points](#8-strong-and-weaker-points)
9. [Whom it serves](#9-whom-it-serves)
10. [What remains](#10-what-remains)
11. [Glossary](#11-glossary)
12. [Version history](#12-version-history)

## 1. In short

GreenOcean closes as a portfolio project on 2026-11-04, three and a half weeks after its first commit. It keeps running on its own: every Tuesday it downloads the ODEPA prices and the INE food CPI, checks them and publishes a panel in two languages. This record tells how it started, what it set out to show, what was found in the data and what was learned.

- **What remains in place:** a weekly pipeline with 69 explained transformation rules, 20 controls, 1,505 automated tests that recompute the figures, 14 quality indicators, 9 documents in Spanish and English and 519 recorded decisions.
- **What was shown:** that a «simple» public source hides data engineering work, and that this work can be left in plain sight: every figure of the panel can be traced to the ODEPA row it came from.
- **Status:** closed and in maintenance. No feature is pending; known technical debts remain, listed in section 10.

## 2. How it started

The project was born on 2026-10-11 as a portfolio exercise with one concrete goal: to build, end to end, a data pipeline on a Chilean public source and to show how the work is done, not only what is known. In the first two days four milestones were closed: the download of the files and their raw load, the ETL with its rules, a minimal panel with indicators and the automatic load of every Tuesday.

- **Vision:** that anyone in Chile can know, from official data, how food prices move.
- **Mission:** to publish every week prices that are checked and easy to read, and to improve the process with every load.
- **What it set out to show:** the four competences the author wanted to consolidate: data engineering, business systems analysis (BSA), business intelligence (BI) and operations (DevOps), plus a fifth one that runs through the others: working with an artificial intelligence assistant under written rules.

[[diagrama:linea_proyecto]]

## 3. What was expected and what was found

At the start, the three sources looked simple: public CSV files, with clear columns, that only had to be downloaded, normalised and crossed. Reality showed up in the last week, when the data tests began to fail.

- **The units of sale.** ODEPA writes the unit of each price by hand: «$/bandeja 18 kilos», «$/cien», «$/12 canastillos 125/170 gramos», «$/kilo (en caja de 17 kilos)». Some 200 different forms, reviewed one by one; 12,185 rows were left without a readable unit and are published without a price per kilo, never with a guessed one.
- **The volume.** The volume column counts packages, not kilos: the ODEPA bulletin says so and the data confirms it (99.997 % of the rows fit). With that reading, the weekly wholesale price came to weight the kilos or units each package brings.
- **Packages that change.** A product sold one week in an 18-kilo tray and the next in a 10-kilo tray seems to rise or fall in price when nothing has happened. Since then every variation compares only the same package (RN-15); 1,003 changes were left out of the comparison.
- **Sources that run late.** One source can publish days after the other. The panel publishes up to the last complete week in both, filling in nothing.

How it was handled: with tests that recompute every figure from the raw rows, not tests that only check that the rule was applied; with a written rule for every transformation, saying which problem it solves and what would happen without it ([[vista:Transformation rules]]); and by marking as an inference whatever the source does not confirm.

[[diagrama:esperado_real]]

## 4. How the work was done

The work advanced in short stages, each closed with green tests and a written decision. After the milestones came the panel with its diagrams, the documents (PRD, SAD, ADR, SQAP, test plan and runbook), the quality plan with its weekly reports, the English version of the whole app, the Weekly dashboard in four steps and, at the end, the thorough review of the data.

- **Acceptance criteria.** The author set them and they did not change: comparisons only between compatible week, region and unit; rules and rejections explained; indicators traceable to their query; auditable loads; and a load with errors never reaches the panel.
- **Quality management.** A quality plan (SQAP) with 14 indicators, 8 of code and 6 of data, measured on every push; 42 failures diagnosed and resolved, each with its cause, its containment and its corrective action ([[vista:Changes and incidents]]); and tests that walk every page in both languages.
- **Rules for working with artificial intelligence.** The assistant executed under rules written in the repository: only what is needed, a warning before heavy work, one-paragraph reports, never inventing a figure, never pushing without approval. Every change of behaviour was left in a numbered decision; today there are 519.

## 5. The roles

- **The author, as data engineer:** designed the flow (ingestion, landing in SQLite, bronze in Parquet, dbt on DuckDB and the database published in a release), decided what is tested and demanded that the tests recompute the figures, not merely apply the rule.
- **The author, as business systems analyst (BSA):** defined the acceptance criteria, the official name of everything, what blocks a publication and what only warns, and reviewed the app locally before every push. Found contradictions between diagrams by looking at the app and asked for tests that would prevent them.
- **The artificial intelligence assistant:** wrote code, tests and documents; measured the impact of every data rule before applying it and proposed options with their consequences. The decisions were the author's.

## 6. What was learned

- **About data engineering:** that the right rule comes from looking at the rows, not from assuming them; that a change of composition (regions that come and go, packages that change) is mistaken for a price change unless like is compared with like; and that a temporary tolerance is written down with its exit date.
- **About the business:** how ODEPA publishes and what each column means; that a price alert is only useful if it discounts seasonality and the package; and that the business question rules over the technique: the panel starts with the region, the channel and the family because that is how people buy and sell.
- **About DevOps**, which was not the author's speciality: automating the load in GitHub Actions with retries, publishing the database in a release, running the tests on two Python versions on every push, measuring code quality in the same checks, rotating secrets and, the most expensive lesson, testing before a push with the same database the checks use.
- **About the use of artificial intelligence:** that it performs when it has written rules, acceptance criteria and someone who reviews; and that its best contribution was to measure and to propose, not to decide.

## 7. Surprises in the data

- **The jump of 2022.** According to the INE food CPI, food rose 24.7 % in 2022, the largest jump since 2010. Since 2023 it rises between 3.6 % and 5.2 % a year: the rise eased, but prices did not come back ([[vista:Analysis]]).
- **The Maule kiwi.** The alert for wholesale Kiwi Hayward Especial marked a rise of 25.6 % in one week. Comparing only the same package, the rise was 8.8 % and the alert went away: Maule had moved from an 18-kilo tray to a 10-kilo tray.
- **What is not published.** 12,185 quotes have no unit that can be read; before, some were read wrongly. Today they stay out of the price per kilo and in plain sight in the catalogue of controls.

## 8. Strong and weaker points

Strong:

- Complete traceability: from the figure of the panel to the ODEPA row, through a written rule and a test that recomputes it.
- Quality measured, not declared: 14 indicators on every push, weekly reports and a failure register with before and after.
- Living documentation: nine documents that read their figures from the database and print from the page, in Spanish and English.

Weaker:

- The panel lives in a single file of almost 10,000 lines: it works, but it is hard to maintain for someone new.
- The full suite takes about 15 minutes in the checks of each push; locally, five.
- Three readings of the data are still inferences without confirmation from ODEPA, marked as such.
- A single deployment, on Streamlit Community Cloud, without a container that reproduces it elsewhere.

## 9. Whom it serves

- **The author:** to consolidate, with a real case, data engineering, BSA, BI, DevOps and work with artificial intelligence under rules.
- **Recruiters and technical reviewers:** as evidence of how the author works: written decisions, tests, measured quality and acknowledged failures.
- **Data professionals:** as an example of what must be done to a public source before publishing a figure.
- **Researchers and teachers:** as a reviewed base of food prices in Chile, with every rule in sight and the original files within reach.

[[diagrama:para_quien]]

## 10. What remains

- To publish the project in a data engineering community and receive the review of more experienced professionals; this record is the first piece for that conversation.
- To pay the debts of section 8 if the project keeps growing: splitting the panel into modules, shortening the suite and packaging the deployment.
- To keep going deeper where the author felt least firm: DevOps beyond GitHub Actions, statistics for the alerts and the design of data tests at scale.

## 11. Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## 12. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-11-04 | First version, on closing the project as a portfolio piece (D-529) |
| 1.1 | 2026-11-07 | No pending query to ODEPA: the three inferences stay as such (D-534) |
