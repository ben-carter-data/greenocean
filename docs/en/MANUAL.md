# Operations Runbook

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Operations Runbook |
| Version | 3.1 |
| Date | 2026-10-30 |
| Status | Current |
| Owner | The author |
| Purpose | State what happens automatically, what is checked and when, and what to do about each failure. |
| Audience | Operation of the project, also without technical training. |
| Related documents | [Software Architecture Document (SAD)](SAD.md) · [Test and Security Plan](PLAN_PRUEBAS.md) · [Glossary](GLOSARIO.md) |

## Contents

1. [In summary](#1-in-summary)
2. [What happens automatically](#2-what-happens-automatically)
3. [What is checked and when](#3-what-is-checked-and-when)
4. [Failures of the weekly load](#4-failures-of-the-weekly-load)
5. [Failures of the published panel](#5-failures-of-the-published-panel)
6. [Recovery](#6-recovery)
7. [Author access and administration](#7-author-access-and-administration)
8. [GitHub guide](#8-github-guide)
9. [Failure register](#9-failure-register)
10. [Known limits](#10-known-limits)
11. [Glossary](#11-glossary)
12. [Version history](#12-version-history)

## 1. In summary

GreenOcean almost runs itself. Every Tuesday the load runs without intervention and, if something fails, the panel keeps showing the last valid load: a half-finished figure is never published. The operations work comes down to looking at one result a week, four tasks on the calendar and, if a failure warning arrives, following the table of section 4. The warning arrives in three ways: GitHub's email, the red run on GitHub and, inside the panel, a red notice above the menu on every page, with a link to the step that failed.

[[diagrama:calendario]]

## 2. What happens automatically

The weekly job (`.github/workflows/semanal.yml`) runs every Tuesday at 12:00 UTC: 09:00 in Chilean summer time and 08:00 in winter time. It downloads the sources, builds and tests the database, publishes it in the «base-actual» release and creates the weekly report. The full sequence, step by step, is in the [load sequence of the SAD](SAD.md#4-the-load-of-each-week).

It can also be launched by hand: from «Operations center», with the «Run pipeline now» button (it requires the control code), or from the workflow page on GitHub.

If a step fails, the following ones do not run and the served database does not change ([ADR-11 · Publish only if the tests pass](ADR.md#adr-11--publish-only-if-the-tests-pass)).

After every load, the quality workflow measures the indicators and proposes the numbered report as the pull request «Actualizar medición de calidad». On every push it only measures and fails if a code indicator is past its acceptable.

## 3. What is checked and when

| When | What is checked or done | Where |
|---|---|---|
| Every Tuesday, after 12:00 UTC | That the run ended green | «Operations» tab of «Operations center», or the GitHub email if it failed |
| Every Tuesday | That the issue «Informe semanal YYYY-MM-DD» (weekly report) exists | Issues of the repository |
| When in doubt about the figures | The quality verdict and the audit controls | «Quality and audit» |
| Every January | Add to `agent/input.csv` the two lines of the new year (wholesale and consumer), with the URL ODEPA publishes on the page of each dataset | `agent/input.csv` |
| Periodically | Copy `agent/downloads` to another disk: the CSV files are not versioned ([ADR-04 · Do not commit the raw data to the repository](ADR.md#adr-04--do-not-commit-the-raw-data-to-the-repository)) and the GitHub cache is deleted if it is not used for 7 days | Another disk of the author |
| Before it expires | Renew the panel's GitHub token; the panel warns when fewer than 14 days are left | App secrets on Streamlit |
| After every weekly load | The pull request «Actualizar medición de calidad»: merge it or close it, delete its branch and run `git pull` | Pull requests of the repository (section 8) |
| On entering as Author | The alert «Acción requerida»; if it starts with «Última medición del …», the report is more than 8 days old and is not today's state | The window the panel opens |

## 4. Failures of the weekly load

[[diagrama:arbol_fallas]]

Each row is a step of the workflow, with its name in `semanal.yml`. The warning reaches the author through GitHub's «Run failed: semanal» email and, in the panel, as a red notice above the menu of every page; the failed step shows in red in «Operations center». The `etl_run` table records only the published loads: the message of a failure is read in the log of the step.

| Step | Symptom | Probable cause | Action |
|---|---|---|---|
| Restore the closed-year files | The step ends with an error | A problem with the GitHub cache | Launch the job again; without the cache, the download fetches every year |
| Get the published database | The step cannot download the database or its fingerprint does not match | The «base-actual» release is not available or its file changed | Check the release on GitHub; if it is missing, publish the database again from a verified local copy |
| Download the ODEPA files | `DOWNLOAD_ERROR` or `UNEXPECTED_HEADER` in the log | ODEPA did not respond, or changed the columns of a file | With `DOWNLOAD_ERROR`, wait a few hours and launch again; with `UNEXPECTED_HEADER`, check the file and adapt the agent |
| Run the ETL (SQLite backup) | `MISSING_WEEKS`, `UNKNOWN_REGION`, `UNKNOWN_CHANNEL` or `DUPLICATE_KEYS` in the log | A week is missing outside the known gaps, ODEPA added a region or a channel, or there are repeated prices | Check the file at ODEPA; a new region or channel is added to the lists of the ETL; a week missing at the source is recorded as a known gap with its decision |
| Build the data warehouse with dbt | A dbt model or test fails, or `TOO_FEW_ROWS` | A business rule is not met, or the load read less than 90 % of the previous one | Read in the log which model or test failed; it usually names the table and the rule |
| Run the tests against the new database | A pytest test fails | The new data breaks something the code assumes, or the backup and the served database do not match | Read which test failed; it usually names the product or the week |
| Publish the database | GitHub rejects the upload of the file or of the pointer | Workflow permissions, or a change on `main` during the load | Check Settings → Actions → Workflow permissions («Read and write») and launch again |
| Publish the weekly report | The issue is not created | Workflow permissions | Check the permissions; the database is already published |

A week a source has not published yet is not a failure: the load publishes up to the last week complete in both sources and the Price overview says so. What does stop the load is `MISSING_WEEKS` (a week missing in the middle of the data) and `LATE_SOURCE` (a source has gone more than 2 weeks without publishing): check ODEPA and fill nothing in; the load comes back by itself when the source publishes. To read any failure without copying by hand, the panel's page «GitHub Actions», as Author, shows the job, the step, the failing tests and the end of the log, with «Copiar».

## 5. Failures of the published panel

| Symptom | Probable cause | Action |
|---|---|---|
| After a push, a page shows `AttributeError` | Streamlit Cloud combined new files with others it had in memory (it happened on 2026-10-12) | In the panel, «Manage app» → ⋮ → **Reboot**, and wait one or two minutes |
| «Operations center» says GitHub did not respond | Without a token, GitHub allows 60 requests per hour, shared by the apps of the same server | None: the panel shows the last saved response and asks again every 5 minutes; with the token configured, the limit rises |
| The panel reports that it does not have the served database | It could not download it from the release when it started | Check that the «base-actual» release exists; the panel downloads it on the next visit |
| The «Run pipeline now» button says the token is missing | The panel's token expired or is not configured | Create a token allowed to launch workflows of this repository and store it as `GITHUB_TOKEN` in the app secrets on Streamlit |

## 6. Recovery

[[diagrama:secuencia_recuperacion]]

| Situation | Procedure |
|---|---|
| A load failed | Fix the cause as in section 4 and launch the job again; meanwhile, the panel shows the last valid load |
| A manual load hangs | In the run's window, «Cancelar» and confirm; if it does not answer, GitHub cuts it after 20 minutes |
| The release lost its file | Rebuild the database on a computer with the data (`python etl/pipeline.py --local`), check that the suite passes and upload the file to the «base-actual» release together with its pointer (`python bi/served_database.py --pointer`) |
| A new copy of the repository has no database | `python bi/served_database.py` downloads the database of the last load and verifies its fingerprint |

## 7. Author access and administration

In «Operations center», «Author access» asks for the control code (the panel's `CONTROL_CODE` secret) and opens with Enter. With the right code, the «Run pipeline now» button, the token-expiry warning and the administration links appear (GitHub tokens, runs and the administration of the app on Streamlit). Without the secret configured, for example in a local copy, the access stays closed.

The code prevents accidental runs; it is not the main barrier. What protects the project is the author's sign-in on GitHub and Streamlit (with two-step verification) and a token with the minimum permissions. There is no limit of attempts for the code: it is an accepted risk, described in the [Test and Security Plan](PLAN_PRUEBAS.md#11-accepted-risks-and-limits). The panel never shows the token or any part of it.

One also enters as Author from the window «Elige tu vista»: the link «Acceso del autor» (Author access), in its corner, the key and Enter (D-369). The «Vista» button, under the logo and above the menu, changes the view, as does a click on the logo (D-373); leaving Author closes its session. The panel uses three secrets, kept in Streamlit (section 8): `CONTROL_CODE`, `GITHUB_TOKEN` (starts and cancels the load) and `GITHUB_READ_TOKEN` (read only, for the page «GitHub Actions»).

## 8. GitHub guide

The links used to run the project, grouped by task.

| Task | Link | What it is for | When to use it | What to click |
|---|---|---|---|---|
| Check failures | [Actions](https://github.com/ben-carter-data/greenocean/actions) | See every run of the three workflows and its state | When the «Run failed» email or the panel's red notice arrives | The red run → the job → the red step |
| Check failures | [Weekly load](https://github.com/ben-carter-data/greenocean/actions/workflows/semanal.yml) | Only the Tuesday loads and the manual ones | Every Tuesday, after 12:00 UTC | The latest run → «weekly-load» |
| Check failures | [Tests](https://github.com/ben-carter-data/greenocean/actions/workflows/pruebas.yml) | Lint, mypy and pytest of every push | After every push | The run of the commit → «pytest» or «lint» |
| Check failures | [Quality](https://github.com/ben-carter-data/greenocean/actions/workflows/calidad.yml) | The quality measure of every push and the weekly report | If the panel or the email warns of an indicator past its acceptable | The run → «medir» → the red step |
| Approve a report | [Pull requests](https://github.com/ben-carter-data/greenocean/pulls) | Review the quality report the workflow proposes | After every weekly load | «Actualizar medición de calidad» → «Files changed» → «Merge pull request», or «Close pull request» |
| Approve a report | [Branches](https://github.com/ben-carter-data/greenocean/branches) | Delete the branch of a report already merged or closed | After merging or closing the pull request | The bin icon next to the branch «informe-calidad/…» |
| Settings | [Actions · General](https://github.com/ben-carter-data/greenocean/settings/actions) | Workflow permissions to write and open pull requests | If a publication or a pull request is rejected | «Workflow permissions» → «Read and write» and «Allow GitHub Actions to create and approve pull requests» |
| Settings | [Release «base-actual»](https://github.com/ben-carter-data/greenocean/releases/tag/base-actual) | The served database the panel reads | If the panel cannot find its database | Check that the file `datos.duckdb` is in «Assets» |
| Settings | [Issues](https://github.com/ben-carter-data/greenocean/issues) | The weekly report of every published load | Every Tuesday | «Informe semanal» with its date |
| The app | [Panel publicado](https://monitor-precios-hito1-d4hfucgaifcebbwahgrzwf.streamlit.app) | The app the visitor sees | After every push, to confirm the change | Choose the view; as Author, type the key and Enter |
| The app | [Streamlit Community Cloud](https://share.streamlit.io) | The panel's secrets and its restart | When renewing a token or if the panel shows a module error | The app → ⋮ → «Settings» → «Secrets», or «Reboot» |

**Two rules.** Do not edit files on GitHub's website: every change is made on the author's computer and sent with a push, so local and remote main do not drift apart. After merging a pull request on the website, bring the change with `git pull` before working.

## 9. Failure register

Every diagnosed and solved failure is recorded in `docs/calidad/plan_mitigacion.json` before the push that fixes it. Each occurrence has the date, what happened, the cause, what was done and a comment, in one line per field and in plain language; the long analysis goes in its decision D-xxx. The register reads in «Git workflow» → «Incident log»; the professional sees what happened and how it was solved, the diagnosis is the author's.

## 10. Known limits

| Limit | Value | Source |
|---|---|---|
| Maximum size of a release file | 2 GB; the served database weighs about 14 MB | GitHub documentation on releases, read on 2026-10-24 |
| GitHub Actions cache | Deleted if it is not used for 7 days; that week the job downloads every year | GitHub Actions documentation, read on 2026-10-24 |
| GitHub API requests without a token | 60 per hour | GitHub API documentation |
| Cloud architecture | Not adopted while the data is public, weekly and small | [ADR-31 · Do not use a cloud data warehouse](ADR.md#adr-31--do-not-use-a-cloud-data-warehouse) and [Capacity and growth in the SAD](SAD.md#9-capacity-and-growth) |

## 11. Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## 12. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-12 | First version, as a page of the project (D-043) |
| 1.1 | 2026-10-16 | Side-menu navigation and new pages (D-090 to D-099) |
| 1.2 | 2026-10-17 | Documentation and sources reorganized (D-105, D-106, D-110, D-118) |
| 1.3 | 2026-10-19 | Operations center and operation of the load |
| 1.4 | 2026-10-20 | SQL queries (D-184, D-185) |
| 1.5 | 2026-10-21 | Quality and audit in one view (D-220) |
| 1.6 | 2026-10-23 | Security as a process and monitoring (D-249); download as the printed page (D-248) |
| 1.7 | 2026-10-24 | Deployment and pipeline (D-251, D-255); Stack and evidence (D-266); served database in a release (D-270) |
| 2.0 | 2026-10-25 | Runbook format: symptom, cause, action, recovery, periodic tasks and limits with their source (D-279, professional documentation) |
| 3.0 | 2026-10-25 | A summary at the start, the calendar, the fault tree and the recovery sequence as diagrams (D-290, documents for every reader) |
| 3.1 | 2026-10-30 | GitHub guide and failure register; late sources, the weekly quality report, the manual load window, entering as Author and the three secrets (D-339 to D-363) |
